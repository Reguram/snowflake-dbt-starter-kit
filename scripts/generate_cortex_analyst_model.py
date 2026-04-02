#!/usr/bin/env python3
"""
Cortex Analyst Semantic Model Generator
========================================
Generates Cortex Analyst YAML semantic model files from dbt mart models.
Connects to Snowflake to profile columns, auto-classifies dimensions/facts,
generates synonyms, sample_values, verified_queries, and custom_instructions.

Output YAML follows the Snowflake Cortex Analyst Semantic Model Specification:
  https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/semantic-model-spec

Usage:
  # Single model
  python scripts/generate_cortex_analyst_model.py --model fct_sales

  # Dry run (preview only)
  python scripts/generate_cortex_analyst_model.py --model fct_sales --dry-run

  # Batch: all fct_* and summary_* models
  python scripts/generate_cortex_analyst_model.py --batch

  # Batch including dim_* models
  python scripts/generate_cortex_analyst_model.py --batch --include-dims

  # Skip verified query testing (offline mode)
  python scripts/generate_cortex_analyst_model.py --model fct_sales --skip-verify

  # Upload to Snowflake stage after generation
  python scripts/generate_cortex_analyst_model.py --model fct_sales --upload-stage

Requirements:
  pip install snowflake-connector-python pyyaml
"""

import argparse
import math
import os
import re
import sys
import time
from pathlib import Path

try:
    import snowflake.connector
except ImportError:
    print("Error: snowflake-connector-python not installed. Run: pip install snowflake-connector-python")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("Error: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUT_DIR = PROJECT_ROOT / "cortex-analyst-models"
DDL_SEMANTIC_DIR = PROJECT_ROOT / "ddl" / "semantic"
SEMANTIC_DIR = MODELS_DIR / "semantic"


# ─── Snowflake Connection ───────────────────────────────────

def get_connection():
    """Create a Snowflake connection from env vars or profiles.yml."""
    account = os.environ.get("SNOWFLAKE_ACCOUNT")
    user = os.environ.get("SNOWFLAKE_USER")
    password = os.environ.get("SNOWFLAKE_PASSWORD")
    role = os.environ.get("SNOWFLAKE_ROLE", "DBT_ROLE")
    warehouse = os.environ.get("SNOWFLAKE_WAREHOUSE", "DBT_AGENT_WH")
    database = os.environ.get("SNOWFLAKE_DATABASE", "DBT_DEV")

    if not all([account, user, password]):
        profiles_path = Path.home() / ".dbt" / "profiles.yml"
        if profiles_path.exists():
            with open(profiles_path) as f:
                profiles = yaml.safe_load(f)
            for profile in profiles.values():
                if isinstance(profile, dict) and "outputs" in profile:
                    target = profile.get("target", "dev")
                    output = profile["outputs"].get(target, {})
                    if output.get("type") == "snowflake":
                        account = output.get("account", account)
                        user = output.get("user", user)
                        password = output.get("password", password)
                        role = output.get("role", role)
                        warehouse = output.get("warehouse", warehouse)
                        database = output.get("database", database)
                        break

    if not all([account, user, password]):
        print("ERROR: Snowflake credentials not found.")
        print("Set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD env vars")
        print("Or configure ~/.dbt/profiles.yml")
        sys.exit(1)

    return snowflake.connector.connect(
        account=account, user=user, password=password,
        role=role, warehouse=warehouse, database=database,
    )


# ─── Column Classification ──────────────────────────────────

TIME_PATTERNS = re.compile(r"(date|_at$|timestamp|month|quarter|year|period)", re.IGNORECASE)
CATEGORICAL_PATTERNS = re.compile(
    r"(status|type|category|segment|priority|tier|flag|is_|has_|level|class|group)", re.IGNORECASE
)
ENTITY_PATTERNS = re.compile(
    r"(name|region|country|nation|city|brand|department|state|county|province|code|maker|vendor|"
    r"supplier|manufacturer|site|exchange|ticker|fips|iso)", re.IGNORECASE
)
SUM_PATTERNS = re.compile(
    r"(price|revenue|amount|cost|discount|quantity|qty|total|sales|profit|count|volume|beds|"
    r"patients|cases|difference|hospitalized|deaths|views|purchases)", re.IGNORECASE
)
AVG_PATTERNS = re.compile(r"(average|avg|rate|percentage|pct|ratio|conversion)", re.IGNORECASE)
MAX_PATTERNS = re.compile(r"(max_|maximum|peak)", re.IGNORECASE)
SKIP_PATTERNS = re.compile(r"(_sk$|_hash$|_loaded|_etl|_batch|_placeholder)", re.IGNORECASE)
PK_PATTERNS = re.compile(r"(_key$|_id$)", re.IGNORECASE)


def classify_column(col_name, col_type, cardinality=None):
    """Classify a column as dimension, time_dimension, fact, or skip.

    Returns: (classification, agg_type_or_subtype)
      - ("time_dimension", None)
      - ("dimension", "categorical"|"entity")
      - ("fact", "sum"|"avg"|"max"|"count")
      - ("skip", None)
    """
    if SKIP_PATTERNS.search(col_name):
        return "skip", None

    # Primary/surrogate keys — skip for semantic model
    if PK_PATTERNS.search(col_name) and col_type.startswith("VARCHAR"):
        # Hash-based surrogate keys — skip
        if col_name.endswith("_key"):
            return "skip", None
        # Foreign-key-like IDs — could be entity dimension
        return "dimension", "entity"

    # Time dimensions
    if col_type in ("DATE", "TIMESTAMP_NTZ", "TIMESTAMP_LTZ", "TIMESTAMP_TZ"):
        return "time_dimension", None
    if TIME_PATTERNS.search(col_name) and "NUMBER" in col_type:
        # Year/month as NUMBER → dimension not metric
        return "dimension", "categorical"

    # Boolean → categorical dimension
    if col_type == "BOOLEAN":
        return "dimension", "categorical"

    # Categorical dimensions
    if CATEGORICAL_PATTERNS.search(col_name):
        return "dimension", "categorical"

    # Entity dimensions
    if ENTITY_PATTERNS.search(col_name):
        return "dimension", "entity"

    # Numeric types → facts
    if col_type.startswith("NUMBER") or col_type in ("FLOAT", "DOUBLE", "DECIMAL"):
        if AVG_PATTERNS.search(col_name):
            return "fact", "avg"
        if MAX_PATTERNS.search(col_name):
            return "fact", "max"
        if SUM_PATTERNS.search(col_name):
            return "fact", "sum"
        # Default numeric → sum
        return "fact", "sum"

    # VARCHAR with low cardinality → dimension
    if col_type.startswith("VARCHAR") and cardinality is not None and cardinality < 50:
        return "dimension", "categorical"

    # Fallback: VARCHAR → dimension
    if col_type.startswith("VARCHAR"):
        return "dimension", "entity"

    return "skip", None


def humanize_name(col_name):
    """Generate human-readable description from snake_case column name."""
    return col_name.replace("_", " ").strip().capitalize()


def generate_synonyms(col_name, col_type, classification):
    """Generate natural language synonyms for a column."""
    base = col_name.lower().replace("_", " ")
    synonyms = []

    # Common synonym patterns by name
    syn_map = {
        "date": ["trading date", "report date", "period date"],
        "name": ["title", "label"],
        "region": ["area", "territory", "geography"],
        "country": ["nation", "country name"],
        "state": ["province", "region", "state name"],
        "category": ["type", "classification", "group"],
        "status": ["state", "condition"],
        "total_sales": ["revenue", "sales amount", "total revenue"],
        "total_cases": ["cumulative cases", "case total"],
        "price": ["cost", "unit price", "amount"],
        "count": ["number of", "total count", "quantity"],
        "volume": ["trading volume", "amount"],
    }

    for key, syns in syn_map.items():
        if key in col_name.lower():
            synonyms.extend(syns)
            break

    # Generic synonyms from column name parts
    parts = col_name.lower().split("_")
    if len(parts) > 1:
        synonyms.append(" ".join(parts))
    if "total" in parts:
        without_total = [p for p in parts if p != "total"]
        if without_total:
            synonyms.append(" ".join(without_total))

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for s in synonyms:
        if s.lower() not in seen and s.lower() != base:
            seen.add(s.lower())
            unique.append(s)

    return unique[:5]  # Cap at 5 synonyms


# ─── Snowflake Profiling ────────────────────────────────────

def profile_columns(conn, database, schema, table):
    """Query Snowflake for column metadata, cardinality, and sample values."""
    cursor = conn.cursor()

    # Get column types
    cursor.execute(
        "SELECT column_name, data_type "
        "FROM information_schema.columns "
        "WHERE table_catalog = %s AND table_schema = %s AND table_name = %s "
        "ORDER BY ordinal_position",
        (database.upper(), schema.upper(), table.upper()),
    )
    columns = []
    for row in cursor.fetchall():
        columns.append({"name": row[0], "type": row[1], "name_lower": row[0].lower()})

    if not columns:
        cursor.close()
        return columns

    # Get cardinality + sample values for each column
    for col in columns:
        col_upper = col["name"].upper()
        try:
            # Cardinality
            cursor.execute(
                f'SELECT COUNT(DISTINCT "{col_upper}") '
                f'FROM "{database.upper()}"."{schema.upper()}"."{table.upper()}" '
                f"SAMPLE (1000 ROWS)"
            )
            result = cursor.fetchone()
            col["cardinality"] = result[0] if result else None

            # Sample values (top 3 distinct non-null values)
            cursor.execute(
                f'SELECT DISTINCT "{col_upper}" '
                f'FROM "{database.upper()}"."{schema.upper()}"."{table.upper()}" '
                f'WHERE "{col_upper}" IS NOT NULL '
                f"LIMIT 5"
            )
            samples = [str(row[0]) for row in cursor.fetchall()]
            col["sample_values"] = samples[:3]
        except Exception:
            col["cardinality"] = None
            col["sample_values"] = []

    cursor.close()
    return columns


def test_query(conn, sql):
    """Execute a SQL query and return True if it succeeds, False otherwise."""
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        cursor.fetchone()
        return True
    except Exception:
        return False
    finally:
        cursor.close()


# ─── Existing Metadata Bridge ───────────────────────────────

def load_existing_semantic_view_metadata(model_name):
    """Load dimension/metric metadata from existing semantic view YAML if available."""
    # Try ddl/semantic/ YAML files
    base = model_name.replace("fct_", "").replace("summary_", "").replace("dim_", "")
    yaml_candidates = [
        DDL_SEMANTIC_DIR / f"sem_{base}.yaml",
        DDL_SEMANTIC_DIR / f"sem_{model_name.replace('fct_', '')}.yaml",
    ]
    for yaml_path in yaml_candidates:
        if yaml_path.exists():
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            if data and "tables" in data:
                return data
    return None


def load_schema_yml_metadata(model_name):
    """Load column metadata from the mart model's schema.yml."""
    # Search for schema.yml files under models/marts/
    for schema_file in MODELS_DIR.rglob("schema.yml"):
        if "staging" in str(schema_file) or "semantic" in str(schema_file):
            continue
        with open(schema_file) as f:
            data = yaml.safe_load(f) or {}
        for model in data.get("models", []):
            if model.get("name") == model_name:
                return model
    return None


# ─── Verified Query Generation ──────────────────────────────

def generate_verified_queries(model_name, database, schema, dimensions, time_dims, facts):
    """Generate 3-5 verified SQL queries for common analytical patterns."""
    fqn = f"{database}.{schema}.{model_name.upper()}"
    queries = []
    timestamp = int(time.time())

    # Query 1: Summary aggregation
    if facts:
        fact_aggs = ", ".join(
            f'SUM("{f["name"].upper()}") AS total_{f["name"].lower()}'
            for f in facts[:3]
        )
        queries.append({
            "name": f"{model_name}_summary",
            "question": f"What is the overall summary of {model_name.replace('_', ' ')}?",
            "use_as_onboarding_question": True,
            "sql": f"SELECT {fact_aggs} FROM {fqn}",
            "verified_by": "Auto-generated",
            "verified_at": timestamp,
        })

    # Query 2: Time trend (if time dimension exists)
    if time_dims and facts:
        td = time_dims[0]
        fact = facts[0]
        queries.append({
            "name": f"{model_name}_time_trend",
            "question": f"Show the trend of {fact['name'].replace('_', ' ')} over time",
            "use_as_onboarding_question": True,
            "sql": (
                f'SELECT "{td["name"].upper()}", '
                f'SUM("{fact["name"].upper()}") AS total_{fact["name"].lower()} '
                f"FROM {fqn} "
                f'GROUP BY "{td["name"].upper()}" '
                f'ORDER BY "{td["name"].upper()}" DESC '
                f"LIMIT 30"
            ),
            "verified_by": "Auto-generated",
            "verified_at": timestamp,
        })

    # Query 3: Top-N by dimension (if categorical dimension exists)
    cat_dims = [d for d in dimensions if d.get("subtype") == "categorical" or d.get("subtype") == "entity"]
    if cat_dims and facts:
        dim = cat_dims[0]
        fact = facts[0]
        queries.append({
            "name": f"top_{dim['name'].lower()}_by_{fact['name'].lower()}",
            "question": f"What are the top {dim['name'].replace('_', ' ')}s by {fact['name'].replace('_', ' ')}?",
            "sql": (
                f'SELECT "{dim["name"].upper()}", '
                f'SUM("{fact["name"].upper()}") AS total_{fact["name"].lower()} '
                f"FROM {fqn} "
                f'GROUP BY "{dim["name"].upper()}" '
                f'ORDER BY total_{fact["name"].lower()} DESC '
                f"LIMIT 10"
            ),
            "verified_by": "Auto-generated",
            "verified_at": timestamp,
        })

    # Query 4: Time + dimension breakdown
    if time_dims and cat_dims and facts:
        td = time_dims[0]
        dim = cat_dims[0]
        fact = facts[0]
        queries.append({
            "name": f"{fact['name'].lower()}_by_{dim['name'].lower()}_over_time",
            "question": (
                f"Show {fact['name'].replace('_', ' ')} by "
                f"{dim['name'].replace('_', ' ')} over the last 30 days"
            ),
            "sql": (
                f'SELECT "{td["name"].upper()}", "{dim["name"].upper()}", '
                f'SUM("{fact["name"].upper()}") AS total_{fact["name"].lower()} '
                f"FROM {fqn} "
                f'GROUP BY "{td["name"].upper()}", "{dim["name"].upper()}" '
                f'ORDER BY "{td["name"].upper()}" DESC '
                f"LIMIT 100"
            ),
            "verified_by": "Auto-generated",
            "verified_at": timestamp,
        })

    # Query 5: Recent data snapshot
    if time_dims and facts:
        td = time_dims[0]
        cols = ", ".join(
            f'"{c["name"].upper()}"'
            for c in (dimensions + time_dims + facts)[:6]
        )
        queries.append({
            "name": f"most_recent_{model_name}",
            "question": f"What is the most recent data in {model_name.replace('_', ' ')}?",
            "sql": (
                f"SELECT {cols} FROM {fqn} "
                f'ORDER BY "{td["name"].upper()}" DESC LIMIT 5'
            ),
            "verified_by": "Auto-generated",
            "verified_at": timestamp,
        })

    return queries[:5]


def generate_custom_instructions(model_name, dimensions, time_dims, facts):
    """Generate custom instructions for text-to-SQL accuracy."""
    lines = []

    # Time dimension instructions
    for td in time_dims:
        lines.append(
            f"Always include the {td['name']} field when showing time-series data to provide context."
        )
        lines.append(
            f"When showing trends, order by {td['name']} DESC to show most recent data first."
        )
        lines.append(
            f"For 'most recent' or 'latest' queries, use ORDER BY {td['name']} DESC LIMIT 1."
        )

    # Fact instructions
    for f in facts:
        agg = f.get("default_aggregation", "sum").upper()
        lines.append(f"Use {agg}({f['name']}) when aggregating {f['name'].replace('_', ' ')}.")

    # Dimension instructions
    cat_dims = [d for d in dimensions if d.get("data_type", "").startswith("VARCHAR")]
    if cat_dims:
        lines.append(
            "String comparisons are case-insensitive — convert user input to uppercase for consistency."
        )

    # Generic instructions
    lines.append(
        f"The table name is {model_name.upper()}. Use fully qualified references when possible."
    )

    return "\n".join(lines)


# ─── YAML Generation ────────────────────────────────────────

def build_cortex_analyst_yaml(
    model_name, database, schema, dimensions, time_dims, facts,
    relationships=None, verified_queries=None, custom_instructions=None,
):
    """Build the Cortex Analyst YAML semantic model structure."""
    table_entry = {
        "name": model_name.upper(),
        "description": f"Semantic model for {model_name.replace('_', ' ')} — auto-generated from dbt mart model.",
        "base_table": {
            "database": database.upper(),
            "schema": schema.upper(),
            "table": model_name.upper(),
        },
    }

    # Dimensions
    yaml_dims = []
    for d in dimensions:
        entry = {
            "name": d["name"].upper(),
            "expr": d["name"].upper(),
            "data_type": d.get("data_type", "VARCHAR"),
            "description": d.get("description", humanize_name(d["name"])),
        }
        syns = d.get("synonyms") or generate_synonyms(d["name"], d.get("data_type", "VARCHAR"), "dimension")
        if syns:
            entry["synonyms"] = syns
        samples = d.get("sample_values", [])
        if samples:
            entry["sample_values"] = [str(s) for s in samples]
        yaml_dims.append(entry)
    if yaml_dims:
        table_entry["dimensions"] = yaml_dims

    # Time dimensions
    yaml_time_dims = []
    for td in time_dims:
        entry = {
            "name": td["name"].upper(),
            "expr": td["name"].upper(),
            "data_type": td.get("data_type", "DATE"),
            "description": td.get("description", humanize_name(td["name"])),
        }
        syns = td.get("synonyms") or generate_synonyms(td["name"], "DATE", "time_dimension")
        if syns:
            entry["synonyms"] = syns
        samples = td.get("sample_values", [])
        if samples:
            entry["sample_values"] = [str(s) for s in samples]
        yaml_time_dims.append(entry)
    if yaml_time_dims:
        table_entry["time_dimensions"] = yaml_time_dims

    # Facts
    yaml_facts = []
    for f in facts:
        entry = {
            "name": f["name"].upper(),
            "expr": f["name"].upper(),
            "data_type": f.get("data_type", "NUMBER(18,2)"),
            "description": f.get("description", humanize_name(f["name"])),
            "default_aggregation": f.get("default_aggregation", "sum"),
        }
        syns = f.get("synonyms") or generate_synonyms(f["name"], "NUMBER", "fact")
        if syns:
            entry["synonyms"] = syns
        samples = f.get("sample_values", [])
        if samples:
            entry["sample_values"] = [str(s) for s in samples]
        yaml_facts.append(entry)
    if yaml_facts:
        table_entry["facts"] = yaml_facts

    # Primary key (dimensions that should be unique together)
    pk_cols = [td["name"].upper() for td in time_dims]
    pk_cols.extend(d["name"].upper() for d in dimensions if d.get("subtype") in ("categorical", "entity"))
    if pk_cols:
        table_entry["primary_key"] = {"columns": pk_cols[:4]}  # Cap at 4 PK columns

    # Assemble the full model
    model = {
        "name": f"SEM_{model_name.upper().replace('FCT_', '').replace('SUMMARY_', '').replace('DIM_', '')}",
        "tables": [table_entry],
    }

    if relationships:
        model["relationships"] = relationships

    if verified_queries:
        model["verified_queries"] = verified_queries

    if custom_instructions:
        model["custom_instructions"] = custom_instructions

    return model


# ─── Model Discovery ────────────────────────────────────────

def find_mart_models(include_dims=False):
    """Find all mart model SQL files matching fct_*, summary_*, and optionally dim_*."""
    models = []
    marts_dir = MODELS_DIR / "marts"
    if not marts_dir.exists():
        return models

    for sql_file in marts_dir.rglob("*.sql"):
        name = sql_file.stem
        if name.startswith("fct_") or name.startswith("summary_"):
            models.append(name)
        elif include_dims and name.startswith("dim_"):
            models.append(name)

    return sorted(models)


def find_model_file(model_name):
    """Find the SQL file for a model in the models directory."""
    for sql_file in MODELS_DIR.rglob(f"{model_name}.sql"):
        return sql_file
    return None


# ─── Main Orchestration ─────────────────────────────────────

def process_model(model_name, conn, database, schema, dry_run=False, skip_verify=False):
    """Generate a Cortex Analyst YAML semantic model for a single mart model."""
    print(f"\n{'='*60}")
    print(f"  Processing: {model_name}")
    print(f"{'='*60}")

    # Step 1: Check for existing semantic view metadata (bridge)
    existing_sv = load_existing_semantic_view_metadata(model_name)
    if existing_sv:
        print(f"  Found existing semantic view metadata — bridging dimensions/metrics")

    # Step 2: Load schema.yml metadata
    schema_meta = load_schema_yml_metadata(model_name)
    if schema_meta:
        print(f"  Found schema.yml entry with {len(schema_meta.get('columns', []))} columns")

    # Step 3: Profile columns from Snowflake
    columns = []
    if conn:
        try:
            columns = profile_columns(conn, database, schema, model_name.upper())
            print(f"  Profiled {len(columns)} columns from Snowflake")
        except Exception as e:
            print(f"  Warning: Snowflake profiling failed: {e}")

    # Fallback to schema.yml columns if no Snowflake profiling
    if not columns and schema_meta:
        for col in schema_meta.get("columns", []):
            columns.append({
                "name": col["name"],
                "type": "VARCHAR",  # Default type when we can't profile
                "name_lower": col["name"].lower(),
                "sample_values": [],
                "cardinality": None,
            })
        print(f"  Fell back to {len(columns)} columns from schema.yml")

    if not columns:
        print(f"  ERROR: No column information for {model_name}")
        return None

    # Step 4: Classify columns
    dimensions = []
    time_dims = []
    facts = []
    skipped = []

    for col in columns:
        col_name = col.get("name_lower", col["name"].lower())
        classification, subtype = classify_column(
            col_name, col.get("type", "VARCHAR"), col.get("cardinality")
        )

        # Enrich with schema.yml description if available
        desc = humanize_name(col_name)
        if schema_meta:
            for sc in schema_meta.get("columns", []):
                if sc["name"].lower() == col_name:
                    desc = sc.get("description", desc)
                    break

        entry = {
            "name": col_name,
            "data_type": col.get("type", "VARCHAR"),
            "description": desc,
            "sample_values": col.get("sample_values", []),
            "subtype": subtype,
        }

        if classification == "time_dimension":
            time_dims.append(entry)
        elif classification == "dimension":
            dimensions.append(entry)
        elif classification == "fact":
            entry["default_aggregation"] = subtype or "sum"
            facts.append(entry)
        else:
            skipped.append(col_name)

    print(f"  Classification:")
    print(f"    Time dimensions: {len(time_dims)} — {', '.join(d['name'] for d in time_dims)}")
    print(f"    Dimensions:      {len(dimensions)} — {', '.join(d['name'] for d in dimensions)}")
    print(f"    Facts:           {len(facts)} — {', '.join(f['name'] for f in facts)}")
    print(f"    Skipped:         {len(skipped)} — {', '.join(skipped)}")

    if not facts:
        print(f"  WARNING: No facts detected — model may not be suitable for Cortex Analyst")

    # Step 5: Generate verified queries
    verified_queries = generate_verified_queries(
        model_name, database, schema, dimensions, time_dims, facts
    )

    # Step 6: Test verified queries against Snowflake
    if conn and not skip_verify and verified_queries:
        print(f"  Testing {len(verified_queries)} verified queries...")
        tested = []
        for vq in verified_queries:
            success = test_query(conn, vq["sql"])
            status = "PASS" if success else "FAIL"
            print(f"    [{status}] {vq['name']}")
            if success:
                tested.append(vq)
        verified_queries = tested
        print(f"  {len(verified_queries)} queries passed verification")
    elif skip_verify:
        print(f"  Skipping query verification (--skip-verify)")

    # Step 7: Generate custom instructions
    custom_instructions = generate_custom_instructions(
        model_name, dimensions, time_dims, facts
    )

    # Step 8: Build YAML
    yaml_model = build_cortex_analyst_yaml(
        model_name=model_name,
        database=database,
        schema=schema,
        dimensions=dimensions,
        time_dims=time_dims,
        facts=facts,
        relationships=None,  # Single-table models don't have relationships
        verified_queries=verified_queries if verified_queries else None,
        custom_instructions=custom_instructions,
    )

    # Step 9: Output
    yaml_content = yaml.dump(yaml_model, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # Determine output filename
    sem_name = model_name.replace("fct_", "").replace("summary_", "").replace("dim_", "")
    output_filename = f"semantic_{sem_name}.yaml"

    if dry_run:
        print(f"\n  --- DRY RUN: {output_filename} ---")
        print(yaml_content)
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / output_filename
        output_path.write_text(yaml_content)
        print(f"\n  Wrote: {output_path.relative_to(PROJECT_ROOT)}")

    return yaml_model


def main():
    parser = argparse.ArgumentParser(
        description="Generate Cortex Analyst YAML semantic models from dbt mart models"
    )
    parser.add_argument(
        "--model", help="Name of a specific mart model (e.g., fct_sales)"
    )
    parser.add_argument(
        "--batch", action="store_true",
        help="Generate for all fct_* and summary_* mart models"
    )
    parser.add_argument(
        "--include-dims", action="store_true",
        help="Include dim_* models in batch mode"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview output without writing files"
    )
    parser.add_argument(
        "--skip-verify", action="store_true",
        help="Skip testing verified queries against Snowflake"
    )
    parser.add_argument(
        "--upload-stage", action="store_true",
        help="Upload generated YAML to Snowflake stage after generation"
    )
    parser.add_argument(
        "--database", default=os.environ.get("SNOWFLAKE_DATABASE", "DBT_DEV"),
        help="Snowflake database (default: SNOWFLAKE_DATABASE env or DBT_DEV)"
    )
    parser.add_argument(
        "--schema", default="DBT_MARTS",
        help="Snowflake schema where mart tables reside (default: DBT_MARTS)"
    )
    args = parser.parse_args()

    if not args.model and not args.batch:
        parser.error("Specify --model <name> or --batch")

    # Determine models to process
    if args.batch:
        models = find_mart_models(include_dims=args.include_dims)
        if not models:
            print("ERROR: No mart models found in models/marts/")
            sys.exit(1)
        print(f"Batch mode: found {len(models)} mart models")
    else:
        model_file = find_model_file(args.model)
        if not model_file:
            print(f"ERROR: Model '{args.model}' not found in {MODELS_DIR}")
            sys.exit(1)
        models = [args.model]

    # Connect to Snowflake
    conn = None
    try:
        conn = get_connection()
        print("Connected to Snowflake")
    except Exception as e:
        print(f"Warning: Could not connect to Snowflake: {e}")
        if not args.skip_verify:
            print("Continuing without Snowflake profiling (use --skip-verify to suppress)")

    # Process each model
    generated = []
    failed = []
    for model_name in models:
        try:
            result = process_model(
                model_name, conn, args.database, args.schema,
                dry_run=args.dry_run, skip_verify=args.skip_verify,
            )
            if result:
                generated.append(model_name)
            else:
                failed.append(model_name)
        except Exception as e:
            print(f"  ERROR processing {model_name}: {e}")
            failed.append(model_name)

    if conn:
        conn.close()

    # Upload to stage if requested
    if args.upload_stage and generated and not args.dry_run:
        print(f"\nUploading {len(generated)} YAML files to Snowflake stage...")
        upload_script = PROJECT_ROOT / "scripts" / "upload_semantic_model_to_stage.py"
        if upload_script.exists():
            import subprocess
            subprocess.run(
                [sys.executable, str(upload_script), "--all"],
                cwd=str(PROJECT_ROOT),
            )
        else:
            print("  Upload script not found. Run: python scripts/upload_semantic_model_to_stage.py")

    # Summary
    print(f"\n{'='*60}")
    print(f"  Summary")
    print(f"{'='*60}")
    print(f"  Generated: {len(generated)} models")
    if failed:
        print(f"  Failed:    {len(failed)} models — {', '.join(failed)}")
    if not args.dry_run and generated:
        print(f"  Output:    {OUTPUT_DIR.relative_to(PROJECT_ROOT)}/")
        print(f"\n  Next steps:")
        print(f"    1. Review generated YAML files in cortex-analyst-models/")
        print(f"    2. Upload to Snowflake stage (SEMANTIC schema):")
        print(f"       python scripts/upload_semantic_model_to_stage.py --all")
        print(f"    3. Test with Cortex Analyst:")
        print(f"       SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_MESSAGE(")
        print(f"         '@{args.database}.SEMANTIC.CORTEX_ANALYST_MODELS/<file>.yaml',")
        print(f"         'What is the summary?'")
        print(f"       );")


if __name__ == "__main__":
    main()
