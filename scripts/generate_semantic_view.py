#!/usr/bin/env python3
"""
Snowflake Semantic View Generator
==================================
Reads a mart model's compiled SQL and schema.yml, connects to Snowflake to
profile column metadata, auto-classifies columns as dimensions vs metrics,
and generates:
  1. sem_*.sql model file
  2. schema.yml metadata block with snowflake_semantic_view config
  3. CREATE SEMANTIC VIEW DDL

Usage:
  python scripts/generate_semantic_view.py --model fct_orders
  python scripts/generate_semantic_view.py --model fct_orders --dry-run
  python scripts/generate_semantic_view.py --model fct_orders --analysis-name revenue_analysis

Requirements:
  pip install snowflake-connector-python pyyaml
"""

import argparse
import os
import re
import sys
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

# Dimension patterns
TIME_PATTERNS = re.compile(r"(date|_at$|timestamp|month|quarter|year)", re.IGNORECASE)
CATEGORICAL_PATTERNS = re.compile(r"(status|type|category|segment|priority|tier|flag|is_|has_)", re.IGNORECASE)
ENTITY_PATTERNS = re.compile(r"(name|region|country|nation|city|brand|department)", re.IGNORECASE)

# Metric patterns
SUM_PATTERNS = re.compile(r"(price|revenue|amount|cost|discount|quantity|qty|total|sales|profit)", re.IGNORECASE)
COUNT_PATTERNS = re.compile(r"(key|id)$", re.IGNORECASE)

# Skip patterns
SKIP_PATTERNS = re.compile(r"(_sk$|_hash$|_loaded|_etl|_batch|comment$|description$|address$)", re.IGNORECASE)


def classify_column(col_name, col_type, cardinality=None, null_rate=None):
    """Classify a column as dimension, metric, or skip."""
    if SKIP_PATTERNS.search(col_name):
        return "skip", None

    # Time dimensions
    if col_type in ("DATE", "TIMESTAMP_NTZ", "TIMESTAMP_LTZ", "TIMESTAMP_TZ"):
        return "dimension", "time"
    if TIME_PATTERNS.search(col_name) and col_type.startswith("DATE"):
        return "dimension", "time"

    # Categorical dimensions
    if CATEGORICAL_PATTERNS.search(col_name):
        return "dimension", "categorical"

    # Entity dimensions
    if ENTITY_PATTERNS.search(col_name):
        return "dimension", "entity"

    # Numeric metrics
    if col_type.startswith("NUMBER") or col_type in ("FLOAT", "DOUBLE", "DECIMAL"):
        if SUM_PATTERNS.search(col_name):
            return "metric", "SUM"
        if COUNT_PATTERNS.search(col_name):
            return "metric", "COUNT"
        # Default numeric → metric SUM if name suggests amount
        return "metric", "SUM"

    # VARCHAR with low cardinality → dimension
    if col_type.startswith("VARCHAR") and cardinality is not None and cardinality < 50:
        return "dimension", "categorical"

    # FK columns as entity dimensions
    if COUNT_PATTERNS.search(col_name):
        return "dimension", "entity"

    return "skip", None


def humanize_description(col_name):
    """Generate a human-readable description from a column name."""
    words = col_name.replace("_", " ").strip()
    return words.capitalize()


# ─── Column Profiling ───────────────────────────────────────

def profile_columns(conn, database, schema, table):
    """Query Snowflake to get column metadata and cardinality."""
    cursor = conn.cursor()

    # Get column types from information schema
    cursor.execute(
        "SELECT column_name, data_type "
        "FROM information_schema.columns "
        "WHERE table_catalog = %s AND table_schema = %s AND table_name = %s "
        "ORDER BY ordinal_position",
        (database.upper(), schema.upper(), table.upper())
    )
    columns = []
    for row in cursor.fetchall():
        columns.append({"name": row[0].lower(), "type": row[1]})

    # Get cardinality for VARCHAR columns (sample-based)
    varchar_cols = [c for c in columns if c["type"].startswith("VARCHAR")]
    if varchar_cols:
        cardinality_exprs = ", ".join(
            f"COUNT(DISTINCT \"{c['name'].upper()}\") AS \"{c['name']}_card\""
            for c in varchar_cols
        )
        cursor.execute(
            f"SELECT {cardinality_exprs} FROM \"{database.upper()}\".\"{schema.upper()}\".\"{table.upper()}\" SAMPLE (1000 ROWS)"
        )
        result = cursor.fetchone()
        if result:
            for i, c in enumerate(varchar_cols):
                c["cardinality"] = result[i]

    cursor.close()
    return columns


# ─── Generation ─────────────────────────────────────────────

def find_model_file(model_name):
    """Find the SQL file for a model in the models directory."""
    for sql_file in MODELS_DIR.rglob(f"{model_name}.sql"):
        return sql_file
    return None


def find_schema_yml(model_dir):
    """Find schema.yml in the model's directory."""
    schema_path = model_dir / "schema.yml"
    if schema_path.exists():
        return schema_path
    return None


def generate_semantic_model_sql(model_name, analysis_name, dimensions, metrics):
    """Generate the sem_*.sql model file content."""
    dim_cols = ",\n    ".join(d["name"] for d in dimensions)
    metric_cols = ",\n    ".join(m["name"] for m in metrics)

    # Add time grain derivations for date columns
    time_dims = [d for d in dimensions if d.get("subtype") == "time"]
    derived_lines = []
    for td in time_dims:
        base = td["name"]
        if not any(d["name"].endswith("_month") for d in dimensions):
            derived_lines.append(f"    date_trunc('month', {base}) as {base.replace('_date', '')}_month")
        if not any(d["name"].endswith("_quarter") for d in dimensions):
            derived_lines.append(f"    date_trunc('quarter', {base}) as {base.replace('_date', '')}_quarter")
        if not any(d["name"].endswith("_year") for d in dimensions):
            derived_lines.append(f"    extract(year from {base}) as {base.replace('_date', '')}_year")

    derived_block = ""
    if derived_lines:
        derived_block = "\n    -- Derived time dimensions\n" + ",\n".join(derived_lines) + ","

    sql = f"""-- models/semantic/sem_{analysis_name}.sql
{{{{ config(materialized='view') }}}}

with base as (
    select * from {{{{ ref('{model_name}') }}}}
)

select
    -- Dimensions
    {dim_cols},{derived_block}

    -- Metrics (raw columns for aggregation in Semantic View)
    {metric_cols}

from base
"""
    return sql


def generate_schema_yml_block(analysis_name, dimensions, metrics):
    """Generate the schema.yml metadata block."""
    sv_dims = []
    for d in dimensions:
        sv_dims.append({
            "name": d["name"],
            "description": d.get("description", humanize_description(d["name"]))
        })

    sv_metrics = []
    for m in metrics:
        sv_metrics.append({
            "name": m.get("metric_name", f"total_{m['name']}"),
            "type": m.get("agg_type", "SUM"),
            "expression": m["name"],
            "description": m.get("description", humanize_description(m["name"]))
        })

    model_block = {
        "name": f"sem_{analysis_name}",
        "description": f"Semantic view base model for {analysis_name.replace('_', ' ')}. Auto-generated.",
        "meta": {
            "snowflake_semantic_view": {
                "name": f"SEM_{analysis_name.upper()}",
                "description": f"{analysis_name.replace('_', ' ').title()} semantic view",
                "dimensions": sv_dims,
                "metrics": sv_metrics,
            }
        }
    }
    return model_block


def generate_ddl(analysis_name, database, schema, dimensions, metrics):
    """Generate the CREATE SEMANTIC VIEW DDL using current Snowflake syntax."""
    table_alias = f"sem_{analysis_name}"
    fqn = f"{database}.{schema}.SEM_{analysis_name.upper()}"
    base_table = f"{database}.SEMANTIC.SEM_{analysis_name.upper()}"

    dim_lines = []
    for d in dimensions:
        desc = d.get("description", humanize_description(d["name"]))
        dim_lines.append(
            f"    {table_alias}.{d['name']} AS {d['name']}\n"
            f"      COMMENT = '{desc}'"
        )

    metric_lines = []
    for m in metrics:
        agg = m.get("agg_type", "SUM")
        name = m.get("metric_name", f"total_{m['name']}")
        expr = m["name"]
        desc = m.get("description", humanize_description(m["name"]))
        metric_lines.append(
            f"    {table_alias}.{name} AS {agg}({expr})\n"
            f"      COMMENT = '{desc}'"
        )

    dimensions_sql = ",\n".join(dim_lines)
    metrics_sql = ",\n".join(metric_lines)

    ddl = f"""CREATE OR REPLACE SEMANTIC VIEW {fqn}
  TABLES (
    {table_alias} AS {base_table}
  )
  DIMENSIONS (
{dimensions_sql}
  )
  METRICS (
{metrics_sql}
  )
  COMMENT = '{analysis_name.replace("_", " ").title()} semantic view';"""
    return ddl


# ─── Main ───────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate Snowflake Semantic View from a dbt mart model")
    parser.add_argument("--model", required=True, help="Name of the mart model (e.g., fct_orders)")
    parser.add_argument("--analysis-name", help="Name for the semantic view (default: derived from model name)")
    parser.add_argument("--dry-run", action="store_true", help="Preview output without writing files")
    parser.add_argument("--skip-profile", action="store_true", help="Skip Snowflake column profiling (use file-based classification only)")
    args = parser.parse_args()

    model_name = args.model
    analysis_name = args.analysis_name or model_name.replace("fct_", "").replace("dim_", "") + "_analysis"

    print(f"Generating Semantic View for model: {model_name}")
    print(f"Analysis name: {analysis_name}")
    print()

    # Find the model file
    model_file = find_model_file(model_name)
    if not model_file:
        print(f"ERROR: Model '{model_name}' not found in {MODELS_DIR}")
        sys.exit(1)
    print(f"Found model: {model_file.relative_to(PROJECT_ROOT)}")

    # Profile columns from Snowflake or use schema.yml
    columns = []
    if not args.skip_profile:
        try:
            conn = get_connection()
            database = os.environ.get("SNOWFLAKE_DATABASE", "DBT_DEV")
            # Determine schema from model path
            schema = "DBT_MARTS"
            columns = profile_columns(conn, database, schema, model_name.upper())
            conn.close()
            print(f"Profiled {len(columns)} columns from Snowflake")
        except Exception as e:
            print(f"Warning: Could not profile from Snowflake: {e}")
            print("Falling back to schema.yml-based classification")

    # If no Snowflake profile, try schema.yml
    if not columns:
        schema_file = find_schema_yml(model_file.parent)
        if schema_file:
            with open(schema_file) as f:
                schema_data = yaml.safe_load(f)
            for model_def in schema_data.get("models", []):
                if model_def.get("name") == model_name:
                    for col in model_def.get("columns", []):
                        columns.append({"name": col["name"], "type": "VARCHAR"})
                    break
        if not columns:
            print("ERROR: No column information available. Run with Snowflake access or ensure schema.yml exists.")
            sys.exit(1)
        print(f"Found {len(columns)} columns from schema.yml")

    # Classify columns
    dimensions = []
    metrics = []
    skipped = []
    for col in columns:
        classification, subtype = classify_column(
            col["name"], col.get("type", "VARCHAR"),
            cardinality=col.get("cardinality")
        )
        if classification == "dimension":
            dimensions.append({
                "name": col["name"],
                "subtype": subtype,
                "description": humanize_description(col["name"])
            })
        elif classification == "metric":
            agg_type = subtype or "SUM"
            metric_name = col["name"]
            if agg_type == "COUNT":
                metric_name = f"{col['name'].replace('_key', '').replace('_id', '')}_count"
            elif not col["name"].startswith("total_"):
                metric_name = f"total_{col['name']}"
            metrics.append({
                "name": col["name"],
                "agg_type": agg_type,
                "metric_name": metric_name,
                "description": humanize_description(col["name"])
            })
        else:
            skipped.append(col["name"])

    print(f"\nClassification results:")
    print(f"  Dimensions: {len(dimensions)} — {', '.join(d['name'] for d in dimensions)}")
    print(f"  Metrics:    {len(metrics)} — {', '.join(m['name'] for m in metrics)}")
    print(f"  Skipped:    {len(skipped)} — {', '.join(skipped)}")

    if not dimensions or not metrics:
        print("\nERROR: Need at least 1 dimension and 1 metric to create a Semantic View")
        sys.exit(1)

    # Generate outputs
    sql_content = generate_semantic_model_sql(model_name, analysis_name, dimensions, metrics)
    schema_block = generate_schema_yml_block(analysis_name, dimensions, metrics)
    database = os.environ.get("SNOWFLAKE_DATABASE", "DBT_DEV")
    ddl = generate_ddl(analysis_name, database, "SEMANTIC", dimensions, metrics)

    if args.dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN — Preview only, no files written")
        print("=" * 60)
        print(f"\n--- models/semantic/sem_{analysis_name}.sql ---")
        print(sql_content)
        print(f"\n--- schema.yml block ---")
        print(yaml.dump({"models": [schema_block]}, default_flow_style=False, sort_keys=False))
        print(f"\n--- CREATE SEMANTIC VIEW DDL ---")
        print(ddl)
    else:
        # Write files
        SEMANTIC_DIR.mkdir(parents=True, exist_ok=True)

        sql_path = SEMANTIC_DIR / f"sem_{analysis_name}.sql"
        sql_path.write_text(sql_content)
        print(f"\nWrote: {sql_path.relative_to(PROJECT_ROOT)}")

        # Append to or create schema.yml
        schema_path = SEMANTIC_DIR / "schema.yml"
        if schema_path.exists():
            with open(schema_path) as f:
                existing = yaml.safe_load(f) or {}
            models_list = existing.get("models", [])
            # Remove existing entry if present
            models_list = [m for m in models_list if m.get("name") != f"sem_{analysis_name}"]
            models_list.append(schema_block)
            existing["models"] = models_list
        else:
            existing = {"version": 2, "models": [schema_block]}

        with open(schema_path, "w") as f:
            yaml.dump(existing, f, default_flow_style=False, sort_keys=False)
        print(f"Wrote: {schema_path.relative_to(PROJECT_ROOT)}")

        ddl_path = SEMANTIC_DIR / f"sem_{analysis_name}_ddl.sql"
        ddl_path.write_text(ddl)
        print(f"Wrote: {ddl_path.relative_to(PROJECT_ROOT)}")

        print(f"\nNext steps:")
        print(f"  1. Review and customize the generated files")
        print(f"  2. Run: dbt build --select sem_{analysis_name}")
        print(f"  3. Execute the DDL in Snowsight: {ddl_path.relative_to(PROJECT_ROOT)}")
        print(f"  4. Test with Cortex Analyst")


if __name__ == "__main__":
    main()
