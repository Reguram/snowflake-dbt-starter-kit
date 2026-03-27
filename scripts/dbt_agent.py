#!/usr/bin/env python3
"""
dbt One-Stop Agent
==================
A unified, context-aware agent that amalgamates all project capabilities:

  1. Source Discovery   — discover tables from any Snowflake database/schema
  2. Model Generation   — scaffold staging, intermediate, and marts models
  3. Semantic Views     — auto-classify dimensions/metrics, generate DDL
  4. Code Review        — static analysis against project conventions
  5. Data Quality       — run/check dbt tests, profile data
  6. Medallion Advising — Cortex-powered suggestions for silver/gold models
  7. dbt Operations     — run, build, test, compile via CLI

Context-Awareness:
  Before generating ANY code, the agent reads existing models, profiles actual
  data, inspects schema.yml files, and understands the DAG — producing code
  that fits the existing project rather than generic boilerplate.

Works in:
  - CLI interactive mode:        python scripts/dbt_agent.py
  - CLI single-question mode:    python scripts/dbt_agent.py --ask "..."
  - MCP server mode (VS Code):   python scripts/dbt_agent.py --mcp
  - Cortex Code (via SKILL.md):  imported as a module

Usage:
  # Interactive chat (default)
  python scripts/dbt_agent.py

  # Single question
  python scripts/dbt_agent.py --ask "Discover tables in COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC"

  # MCP server for VS Code / Cortex Code
  python scripts/dbt_agent.py --mcp

Requirements:
  pip install snowflake-connector-python pyyaml mcp
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import snowflake.connector
except ImportError:
    print("snowflake-connector-python not installed. Run: pip install snowflake-connector-python")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

# ─── Paths ───────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

DEFAULT_CORTEX_MODEL = "mistral-large2"


def _find_dbt_executable():
    """Discover the dbt CLI executable.

    Checks (in order):
      1. <virtualenv>/bin/dbt  (venv-installed dbt)
      2. shutil.which('dbt')   (PATH lookup)
      3. [sys.executable, '-m', 'dbt']  (python -m dbt fallback)
    Returns a list suitable for subprocess (e.g. ['dbt'] or ['/path/python', '-m', 'dbt']).
    Returns None if dbt cannot be found.
    """
    # 1. Check virtualenv
    venv_dbt = Path(sys.prefix) / "bin" / "dbt"
    if venv_dbt.exists():
        return [str(venv_dbt)]
    # Windows variant
    venv_dbt_win = Path(sys.prefix) / "Scripts" / "dbt.exe"
    if venv_dbt_win.exists():
        return [str(venv_dbt_win)]

    # 2. Check PATH
    path_dbt = shutil.which("dbt")
    if path_dbt:
        return [path_dbt]

    # 3. Try python -m dbt
    try:
        result = subprocess.run(
            [sys.executable, "-m", "dbt", "--version"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            return [sys.executable, "-m", "dbt"]
    except Exception:
        pass

    return None


# =============================================================================
# CONNECTION
# =============================================================================

def get_connection():
    """Create a Snowflake connection from env vars or ~/.dbt/profiles.yml."""
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
            for _name, profile in profiles.items():
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
        sys.exit(1)

    conn = snowflake.connector.connect(
        account=account, user=user, password=password,
        role=role, warehouse=warehouse, database=database,
    )
    try:
        conn.cursor().execute("ALTER SESSION SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION'")
    except Exception:
        pass
    return conn


# =============================================================================
# CONTEXT ENGINE — reads existing project state before generating anything
# =============================================================================

class ProjectContext:
    """Reads and caches the current state of the dbt project for context-aware generation."""

    def __init__(self):
        self._sources_cache = None
        self._models_cache = None
        self._dag_cache = None

    def get_all_sources(self):
        """Read all _sources.yml files and return source definitions."""
        if self._sources_cache is not None:
            return self._sources_cache
        sources = []
        staging_dir = MODELS_DIR / "staging"
        if not staging_dir.exists():
            self._sources_cache = sources
            return sources
        for source_dir in sorted(staging_dir.iterdir()):
            if not source_dir.is_dir():
                continue
            sources_yml = source_dir / "_sources.yml"
            if sources_yml.exists():
                with open(sources_yml) as f:
                    data = yaml.safe_load(f)
                for src in data.get("sources", []):
                    tables = [t["name"] for t in src.get("tables", [])]
                    sources.append({
                        "source_name": src["name"],
                        "database": src.get("database", ""),
                        "schema": src.get("schema", ""),
                        "tables": tables,
                        "table_count": len(tables),
                        "dir": source_dir.name,
                    })
        self._sources_cache = sources
        return sources

    def get_all_models(self, layer="all"):
        """List all dbt model files organized by layer."""
        layers = ["staging", "intermediate", "marts", "semantic"] if layer == "all" else [layer]
        result = {}
        for l in layers:
            layer_dir = MODELS_DIR / l
            layer_models = []
            if layer_dir.exists():
                for item in sorted(layer_dir.iterdir()):
                    if item.is_dir():
                        for f in sorted(item.glob("*.sql")):
                            layer_models.append({
                                "name": f.stem,
                                "source": item.name,
                                "path": str(f.relative_to(PROJECT_ROOT)),
                            })
                    elif item.suffix == ".sql":
                        layer_models.append({
                            "name": item.stem,
                            "source": "root",
                            "path": str(item.relative_to(PROJECT_ROOT)),
                        })
            result[l] = layer_models
        return result

    def get_model_names(self):
        """Get a flat list of all model file stems."""
        names = []
        for layer in ["staging", "intermediate", "marts", "semantic"]:
            layer_dir = MODELS_DIR / layer
            if layer_dir.exists():
                for sql_file in layer_dir.rglob("*.sql"):
                    names.append(sql_file.stem)
        return names

    def read_model_sql(self, model_name):
        """Read the SQL content of a model by name."""
        model_name = self.resolve_model_name(model_name)
        for layer in ["staging", "intermediate", "marts", "semantic"]:
            layer_dir = MODELS_DIR / layer
            if layer_dir.exists():
                for sql_file in layer_dir.rglob(f"{model_name}.sql"):
                    return {
                        "model": model_name,
                        "layer": layer,
                        "path": str(sql_file.relative_to(PROJECT_ROOT)),
                        "sql": sql_file.read_text(),
                    }
        return {"error": f"Model '{model_name}' not found"}

    def read_schema_yml(self, model_name):
        """Read the schema.yml entry for a model (tests, descriptions, meta)."""
        model_name = self.resolve_model_name(model_name)
        for layer in ["staging", "intermediate", "marts", "semantic"]:
            layer_dir = MODELS_DIR / layer
            if layer_dir.exists():
                for schema_path in layer_dir.rglob("schema.yml"):
                    with open(schema_path) as f:
                        data = yaml.safe_load(f)
                    if data and "models" in data:
                        for m in data["models"]:
                            if m.get("name") == model_name:
                                return {"model": model_name, "schema": m, "path": str(schema_path.relative_to(PROJECT_ROOT))}
        return {"error": f"No schema.yml entry for '{model_name}'"}

    def get_existing_tests(self, source_name):
        """Get all test definitions for models in a source subdirectory."""
        tests = {}
        for layer in ["staging", "intermediate", "marts"]:
            schema_path = MODELS_DIR / layer / source_name / "schema.yml"
            if schema_path.exists():
                with open(schema_path) as f:
                    data = yaml.safe_load(f)
                if data and "models" in data:
                    for m in data["models"]:
                        model_tests = []
                        for col in m.get("columns", []):
                            for t in col.get("tests", []):
                                model_tests.append({"column": col["name"], "test": t})
                        if model_tests:
                            tests[m["name"]] = model_tests
        return tests

    def resolve_model_name(self, name):
        """Resolve a user-provided name to the actual model file name."""
        name = name.strip()
        if "." in name:
            name = name.rsplit(".", 1)[-1]
        all_models = self.get_model_names()
        name_lower = name.lower()

        # Exact match
        for m in all_models:
            if m.lower() == name_lower:
                return m

        # Suffix match
        suffix_matches = [m for m in all_models if m.lower().endswith(name_lower)]
        if len(suffix_matches) == 1:
            return suffix_matches[0]

        # Contains match
        contains_matches = [m for m in all_models if name_lower in m.lower()]
        if len(contains_matches) == 1:
            return contains_matches[0]

        # Priority: stg > fct > dim > int
        for matches in [suffix_matches, contains_matches]:
            if matches:
                for prefix in ["stg_", "fct_", "dim_", "summary_", "int_"]:
                    for m in matches:
                        if m.startswith(prefix):
                            return m
                return matches[0]

        return name

    def resolve_to_source_fqn(self, model_or_table):
        """Resolve a model name to its source fully-qualified table name (DB.SCHEMA.TABLE).

        Used as a fallback when the dbt model is not yet built in Snowflake.
        Returns None if no source mapping is found.
        """
        name = model_or_table.strip()

        # Already fully qualified (3 parts with dots)
        if name.count(".") >= 2:
            return name

        # Try to find a source that maps to this model
        # Model naming convention: stg_<source>__<table>
        for prefix in ["stg_", "fct_", "dim_", "summary_", "int_"]:
            if name.startswith(prefix):
                name_without_prefix = name[len(prefix):]
                break
        else:
            name_without_prefix = name

        # Check if model name has source__table pattern
        if "__" in name_without_prefix:
            source_part, table_part = name_without_prefix.split("__", 1)
        else:
            source_part, table_part = None, name_without_prefix

        for src in self.get_all_sources():
            # Match by source name
            if source_part and src["source_name"].lower() != source_part.lower():
                continue
            # Match by table name
            for tbl in src.get("tables", []):
                if tbl.lower() == table_part.upper() or tbl.lower() == table_part.lower():
                    db = src["database"]
                    schema = src["schema"]
                    return f"{db}.{schema}.{tbl}"
            # If source matched but table not found by exact name, try uppercase
            if source_part:
                for tbl in src.get("tables", []):
                    if tbl.upper() == table_part.upper().replace("_", "_"):
                        db = src["database"]
                        schema = src["schema"]
                        return f"{db}.{schema}.{tbl}"
        return None

    def get_project_summary(self):
        """Get a high-level summary of the project state."""
        sources = self.get_all_sources()
        models = self.get_all_models()
        return {
            "sources": [{"name": s["source_name"], "database": s["database"],
                         "schema": s["schema"], "tables": s["table_count"]} for s in sources],
            "models": {layer: len(items) for layer, items in models.items()},
            "total_models": sum(len(items) for items in models.values()),
        }

    def invalidate(self):
        """Clear cached state after writes."""
        self._sources_cache = None
        self._models_cache = None
        self._dag_cache = None


# Global context instance
ctx = ProjectContext()


# =============================================================================
# HELPERS — naming, SQL identifiers, column classification
# =============================================================================

def _sql_identifier(name):
    """Quote a SQL identifier if needed for Snowflake."""
    if re.match(r'^[A-Z_][A-Z0-9_]*$', name):
        return name.lower()
    return f'"{name}"'


def _yaml_safe_name(name):
    if any(ch in name for ch in ':{}[]&*?|>!%@`#,'):
        return f'"{name}"'
    return name


def _strip_prefix(col_name, table_name):
    """Strip common single-letter prefixes from column names."""
    lower = col_name.lower()
    parts = lower.split("_", 1)
    if len(parts) > 1 and len(parts[0]) == 1:
        return parts[1]
    if len(parts) > 1 and len(parts[0]) == 2:
        table_lower = table_name.lower()
        if table_lower.startswith(parts[0]):
            return parts[1]
    return lower


def _humanize(name):
    return name.replace("_", " ").strip().capitalize()


# Column classification patterns
_TIME_PAT = re.compile(r"(date|_at$|timestamp|month|quarter|year)", re.IGNORECASE)
_CAT_PAT = re.compile(r"(status|type|category|segment|priority|tier|flag|is_|has_)", re.IGNORECASE)
_ENTITY_PAT = re.compile(r"(name|region|country|nation|city|brand|department)", re.IGNORECASE)
_SUM_PAT = re.compile(r"(price|revenue|amount|cost|discount|quantity|qty|total|sales|profit)", re.IGNORECASE)
_COUNT_PAT = re.compile(r"(key|id)$", re.IGNORECASE)
_SKIP_PAT = re.compile(r"(_sk$|_hash$|_loaded|_etl|_batch|comment$|description$|address$)", re.IGNORECASE)


def classify_column(col_name, col_type, cardinality=None):
    """Classify a column as dimension, metric, or skip."""
    if _SKIP_PAT.search(col_name):
        return "skip", None
    if col_type in ("DATE", "TIMESTAMP_NTZ", "TIMESTAMP_LTZ", "TIMESTAMP_TZ") or _TIME_PAT.search(col_name):
        return "dimension", "time"
    if _CAT_PAT.search(col_name):
        return "dimension", "categorical"
    if _ENTITY_PAT.search(col_name):
        return "dimension", "entity"
    if col_type.startswith("NUMBER") or col_type in ("FLOAT", "DOUBLE", "DECIMAL"):
        if _SUM_PAT.search(col_name):
            return "metric", "sum"
        if _COUNT_PAT.search(col_name):
            return "dimension", "entity"
        return "metric", "sum"
    if col_type.startswith("VARCHAR") and cardinality is not None and cardinality < 50:
        return "dimension", "categorical"
    if _COUNT_PAT.search(col_name):
        return "dimension", "entity"
    return None, None


# SQL review rules
_REVIEW_RULES = [
    {"id": "NO_SELECT_STAR_MARTS", "pattern": r"select\s+\*(?!.*\bfrom\b.*\bcte\b)",
     "message": "Avoid SELECT * in marts/semantic — list columns explicitly",
     "severity": "warning", "applies_to": ["marts", "semantic"]},
    {"id": "HARDCODED_SCHEMA", "pattern": r"(?:from|join)\s+\w+\.\w+\.\w+",
     "message": "Hard-coded database.schema.table — use {{ source() }} or {{ ref() }}",
     "severity": "error"},
    {"id": "MISSING_REF", "pattern": r"(?:from|join)\s+(?!.*\{\{)(\w+)\s",
     "message": "Direct table reference without {{ ref() }} or {{ source() }}",
     "severity": "warning"},
    {"id": "NO_LIMIT", "pattern": r"\bLIMIT\s+\d+",
     "message": "LIMIT clause — shouldn't be in production models",
     "severity": "info"},
]


def _enforce_review(sql_content, file_path=""):
    """Run review rules and return structured result with gate decision.

    Returns dict with can_proceed (True when no severity=error issues),
    errors, warnings, info lists, and all_issues.
    """
    issues = []
    lines = sql_content.split("\n")
    for rule in _REVIEW_RULES:
        if rule.get("applies_to") and not any(l in file_path for l in rule["applies_to"]):
            continue
        if not rule["pattern"]:
            continue
        for i, line_text in enumerate(lines, 1):
            stripped = line_text.strip()
            if stripped.startswith("--") or stripped.startswith("{#"):
                continue
            if re.search(rule["pattern"], line_text, re.IGNORECASE):
                issues.append({"rule": rule["id"], "severity": rule["severity"],
                               "message": rule["message"], "line": i, "content": stripped[:120]})

    # Naming check
    if "staging" in file_path:
        stem = Path(file_path).stem
        if not stem.startswith("stg_"):
            issues.append({"rule": "NAMING_STG", "severity": "warning",
                           "message": "Staging model should follow stg_<source>__<table> naming", "line": 0})

    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]
    info = [i for i in issues if i["severity"] == "info"]
    return {"can_proceed": len(errors) == 0, "errors": errors, "warnings": warnings, "info": info, "all_issues": issues}


# =============================================================================
# TOOL IMPLEMENTATIONS — each is context-aware
# =============================================================================

def _derive_source_name(source_database, source_schema):
    """Derive a sensible default source_name from database/schema.

    The source_name determines folder names under models/staging/<name>/ and
    models/marts/<name>/, plus model prefixes (stg_<name>__<table>).
    Rules:
      - If schema is descriptive (not PUBLIC/RAW/etc.), strip noise suffixes
        like _DATA, _DATASET from the schema name
      - If schema is generic, derive from database name with the same stripping
      - Always lowercase with underscores
    """
    generic_schemas = {"public", "raw", "data", "raw_data",
                       "information_schema", "default", "main", "dbo"}
    noise_suffixes = ("_data", "_dataset", "_database", "_sample", "_demo",
                      "_free", "_open")
    schema_lower = source_schema.lower().strip()
    db_lower = source_database.lower().strip()

    def _clean_name(raw):
        """Strip noise suffixes and version-like tokens (e.g. _sf1)."""
        name = re.sub(r'[^a-z0-9_]', '_', raw).strip('_')
        # Strip noise suffixes (repeat to handle stacked suffixes)
        for _ in range(3):
            for sfx in noise_suffixes:
                if name.endswith(sfx) and len(name) > len(sfx):
                    name = name[:-len(sfx)]
        # Strip version-like suffixes (_sf1, _v2, _s3, etc.)
        name = re.sub(r'_(?:sf|[sv])\d+$', '', name)
        return name.strip('_')

    if schema_lower not in generic_schemas:
        # Schema is descriptive — clean it up
        cleaned = _clean_name(schema_lower)
        return cleaned if cleaned else schema_lower

    # Schema is generic — derive from database name
    # Remove broad noise words then clean
    noise_words = {"data", "dataset", "database", "free", "sample", "open",
                   "demo", "snowflake", "for", "and", "the"}
    words = re.split(r'[_\-\s]+', db_lower)
    meaningful = [w for w in words if w and w not in noise_words]

    if not meaningful:
        meaningful = [w for w in words if w]  # fallback: use all words

    # Take up to 3 meaningful words, join with underscore, then clean
    name = "_".join(meaningful[:3])
    name = re.sub(r'[^a-z0-9_]', '', name).strip('_')
    return name or schema_lower


def tool_discover_source(conn, source_database, source_schema, source_name=None, dry_run=False):
    """Discover tables in a Snowflake database/schema and generate staging + mart models.

    This is the FULL pipeline from discover_and_generate.py, made context-aware:
    it checks what already exists before generating.
    """
    if not source_name:
        source_name = _derive_source_name(source_database, source_schema)

    # Check what already exists
    existing_models = ctx.get_all_models()
    existing_staging = [m["name"] for m in existing_models.get("staging", [])
                        if m.get("source") == source_name]

    cursor = conn.cursor()

    # Discover tables
    cursor.execute(f"""
        SELECT TABLE_NAME, TABLE_TYPE, ROW_COUNT, COMMENT
        FROM {source_database}.INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{source_schema.upper()}'
          AND TABLE_TYPE IN ('BASE TABLE', 'VIEW')
        ORDER BY TABLE_NAME
    """)
    tables = []
    for row in cursor:
        tables.append({
            "name": row[0], "type": row[1],
            "row_count": row[2] or 0, "comment": row[3] or "",
        })

    if not tables:
        cursor.close()
        return {"error": f"No tables found in {source_database}.{source_schema}"}

    # Get columns for each table
    for table in tables:
        try:
            cursor.execute(f'DESCRIBE TABLE {source_database}.{source_schema}."{table["name"]}"')
            columns = []
            for col_row in cursor:
                columns.append({
                    "name": col_row[0],
                    "data_type": col_row[1].split("(")[0].upper(),
                    "nullable": col_row[3] == "Y" if len(col_row) > 3 else True,
                    "comment": col_row[8] if len(col_row) > 8 else "",
                })
            table["columns"] = columns
        except Exception:
            table["columns"] = []

    cursor.close()

    # Report what's new vs existing
    new_tables = [t for t in tables
                  if f"stg_{source_name}__{t['name'].lower()}" not in existing_staging]
    skipped = [t for t in tables
               if f"stg_{source_name}__{t['name'].lower()}" in existing_staging]

    if dry_run:
        return {
            "source": f"{source_database}.{source_schema}",
            "source_name": source_name,
            "tables_found": len(tables),
            "new_tables": [t["name"] for t in new_tables],
            "already_exist": [t["name"] for t in skipped],
            "dry_run": True,
        }

    # Import the generator functions from discover_and_generate
    sys.path.insert(0, str(SCRIPTS_DIR))
    from discover_and_generate import (
        generate_sources_yml, generate_staging_sql, generate_staging_schema_yml,
        generate_overview_mart, generate_mart_schema_yml,
        detect_primary_key, verify_uniqueness, profile_columns,
        classify_columns, generate_summary_mart,
    )

    # Verify PKs
    conn2 = get_connection()
    verified_pks = {}
    for table in tables:
        pk = detect_primary_key(table["columns"], table["name"])
        if pk:
            verified_pks[table["name"]] = verify_uniqueness(
                conn2, source_database, source_schema, table["name"], pk)

    # Profile columns
    table_profiles = {}
    for table in tables:
        table_profiles[table["name"]] = profile_columns(
            conn2, source_database, source_schema, table["name"], table["columns"])
    conn2.close()

    # Generate files
    staging_dir = MODELS_DIR / "staging" / source_name
    marts_dir = MODELS_DIR / "marts" / source_name
    staging_dir.mkdir(parents=True, exist_ok=True)
    marts_dir.mkdir(parents=True, exist_ok=True)

    files_created = []

    # _sources.yml
    sources_yml = generate_sources_yml(source_name, source_database, source_schema, tables, verified_pks)
    (staging_dir / "_sources.yml").write_text(sources_yml)
    files_created.append(f"models/staging/{source_name}/_sources.yml")

    # Staging models
    for table in tables:
        model_name = f"stg_{source_name}__{table['name'].lower()}"
        sql = generate_staging_sql(source_name, table["name"], table["columns"])
        (staging_dir / f"{model_name}.sql").write_text(sql)
        files_created.append(f"models/staging/{source_name}/{model_name}.sql")

    # schema.yml
    schema_yml = generate_staging_schema_yml(source_name, tables, verified_pks)
    (staging_dir / "schema.yml").write_text(schema_yml)
    files_created.append(f"models/staging/{source_name}/schema.yml")

    # Marts — review before writing (fct_* and summary_* are not template-trusted)
    mart_review_issues = []
    fct_name, fct_sql = generate_overview_mart(source_name, tables)
    if fct_name:
        fct_path = f"models/marts/{source_name}/{fct_name}.sql"
        review = _enforce_review(fct_sql, fct_path)
        if not review["can_proceed"]:
            mart_review_issues.append({"model": fct_name, "issues": review["all_issues"]})
        else:
            (marts_dir / f"{fct_name}.sql").write_text(fct_sql)
            files_created.append(fct_path)
            if review["warnings"] or review["info"]:
                mart_review_issues.append({"model": fct_name, "issues": review["warnings"] + review["info"]})

    # Summary marts
    mart_schema_models = []
    if fct_name and f"models/marts/{source_name}/{fct_name}.sql" in files_created:
        mart_schema_models.append({"name": fct_name, "description": f"Detail fact table from {source_name}"})
    for table in tables:
        profile = table_profiles.get(table["name"], {})
        classified = classify_columns(table["columns"], table["name"], profile)
        s_name, s_sql = generate_summary_mart(source_name, table, classified)
        if s_name and s_sql:
            s_path = f"models/marts/{source_name}/{s_name}.sql"
            review = _enforce_review(s_sql, s_path)
            if not review["can_proceed"]:
                mart_review_issues.append({"model": s_name, "issues": review["all_issues"]})
            else:
                (marts_dir / f"{s_name}.sql").write_text(s_sql)
                files_created.append(s_path)
                mart_schema_models.append({"name": s_name, "description": f"Summary from {table['name']}"})
                if review["warnings"] or review["info"]:
                    mart_review_issues.append({"model": s_name, "issues": review["warnings"] + review["info"]})

    mart_schema = generate_mart_schema_yml(source_name, mart_schema_models)
    if mart_schema:
        (marts_dir / "schema.yml").write_text(mart_schema)
        files_created.append(f"models/marts/{source_name}/schema.yml")

    ctx.invalidate()

    result = {
        "source": f"{source_database}.{source_schema}",
        "source_name": source_name,
        "tables_discovered": len(tables),
        "files_created": files_created,
        "file_count": len(files_created),
        "new_tables": [t["name"] for t in new_tables],
        "already_existed": [t["name"] for t in skipped],
    }
    if mart_review_issues:
        result["mart_review_issues"] = mart_review_issues
    return result


def tool_list_sources(conn, source_name=None):
    """List dbt source definitions (reads _sources.yml)."""
    sources = ctx.get_all_sources()
    if source_name:
        sources = [s for s in sources if s["source_name"] == source_name or s["dir"] == source_name]
    return {"sources": sources}


def tool_list_models(conn, layer="all", source_name=None):
    """List dbt models by layer, optionally filtered by source."""
    models = ctx.get_all_models(layer)
    if source_name:
        models = {l: [m for m in items if m.get("source") == source_name]
                  for l, items in models.items()}
    return models


def tool_read_model(conn, model_name):
    """Read the SQL source code of a dbt model."""
    return ctx.read_model_sql(model_name)


def tool_sample_data(conn, table_or_model, limit=10):
    """Sample rows from a built dbt model or source table in Snowflake."""
    resolved = ctx.resolve_model_name(table_or_model)
    cursor = conn.cursor()
    limit = int(limit)

    # Try built dbt model first
    for schema in ["DBT_MARTS", "DBT_STAGING", "DBT_INTERMEDIATE", "SEMANTIC"]:
        for fmt in [f'"{resolved}"', resolved, resolved.upper()]:
            try:
                cursor.execute(f"SELECT * FROM DBT_DEV.{schema}.{fmt} LIMIT {limit}")
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                cursor.close()
                return {
                    "table": resolved, "schema": schema,
                    "columns": columns, "row_count": len(rows),
                    "sample": [dict(zip(columns, row)) for row in rows],
                }
            except Exception:
                continue

    # Fallback: try source table (model may not be built yet)
    source_fqn = ctx.resolve_to_source_fqn(table_or_model)
    if source_fqn:
        try:
            cursor.execute(f"SELECT * FROM {source_fqn} LIMIT {limit}")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            cursor.close()
            return {
                "table": source_fqn, "schema": "(source table)",
                "columns": columns, "row_count": len(rows),
                "sample": [dict(zip(columns, row)) for row in rows],
                "note": f"Queried source table directly — dbt model '{resolved}' is not built yet. Run `dbt build --select {resolved}` to materialize it.",
            }
        except Exception:
            pass

    # Fallback: if input looks fully qualified, try it directly
    if "." in table_or_model and table_or_model.count(".") >= 2:
        try:
            cursor.execute(f"SELECT * FROM {table_or_model} LIMIT {limit}")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            cursor.close()
            return {
                "table": table_or_model, "schema": "(direct query)",
                "columns": columns, "row_count": len(rows),
                "sample": [dict(zip(columns, row)) for row in rows],
            }
        except Exception:
            pass

    cursor.close()
    return {"error": f"Table/model '{table_or_model}' not found. The dbt model may not be built yet — try `run_dbt(command='build', select='{resolved}')` first, or use `run_query(sql='SELECT * FROM <DATABASE>.<SCHEMA>.<TABLE> LIMIT 10')` to query the source directly."}


def tool_describe_table(conn, table_or_model):
    """Get column metadata + row count for a dbt model or source table."""
    resolved = ctx.resolve_model_name(table_or_model)
    cursor = conn.cursor()

    # Try built dbt model first
    for schema in ["DBT_MARTS", "DBT_STAGING", "DBT_INTERMEDIATE", "SEMANTIC"]:
        try:
            cursor.execute(f"DESCRIBE TABLE DBT_DEV.{schema}.{resolved}")
            columns = [{"name": r[0], "type": r[1], "nullable": r[3] == "Y"} for r in cursor]
            cursor.execute(f"SELECT COUNT(*) FROM DBT_DEV.{schema}.{resolved}")
            row_count = cursor.fetchone()[0]
            cursor.close()
            return {"table": resolved, "schema": schema,
                    "columns": columns, "column_count": len(columns), "row_count": row_count}
        except Exception:
            continue

    # Fallback: try source table (model may not be built yet)
    source_fqn = ctx.resolve_to_source_fqn(table_or_model)
    if source_fqn:
        try:
            cursor.execute(f"DESCRIBE TABLE {source_fqn}")
            columns = [{"name": r[0], "type": r[1], "nullable": r[3] == "Y"} for r in cursor]
            cursor.execute(f"SELECT COUNT(*) FROM {source_fqn}")
            row_count = cursor.fetchone()[0]
            cursor.close()
            return {"table": source_fqn, "schema": "(source table)",
                    "columns": columns, "column_count": len(columns), "row_count": row_count,
                    "note": f"Described source table directly — dbt model '{resolved}' is not built yet. Run `dbt build --select {resolved}` to materialize it."}
        except Exception:
            pass

    # Fallback: if input looks fully qualified, try it directly
    if "." in table_or_model and table_or_model.count(".") >= 2:
        try:
            cursor.execute(f"DESCRIBE TABLE {table_or_model}")
            columns = [{"name": r[0], "type": r[1], "nullable": r[3] == "Y"} for r in cursor]
            cursor.execute(f"SELECT COUNT(*) FROM {table_or_model}")
            row_count = cursor.fetchone()[0]
            cursor.close()
            return {"table": table_or_model, "schema": "(direct query)",
                    "columns": columns, "column_count": len(columns), "row_count": row_count}
        except Exception:
            pass

    cursor.close()
    return {"error": f"Table/model '{table_or_model}' not found. The dbt model may not be built yet — try `run_dbt(command='build', select='{resolved}')` first, or use `run_query(sql='DESCRIBE TABLE <DATABASE>.<SCHEMA>.<TABLE>')` to describe the source directly."}


def tool_profile_data(conn, table_or_model, max_columns=20):
    """Profile a table: distinct counts, null rates, cardinality ratios."""
    desc = tool_describe_table(conn, table_or_model)
    if "error" in desc:
        return desc

    # Use the table reference from describe_table (may be source FQN or dbt model)
    table_ref = desc["table"]
    schema = desc["schema"]
    columns = desc["columns"][:int(max_columns)]
    cursor = conn.cursor()

    parts = []
    for col in columns:
        parts.append(f'COUNT(DISTINCT "{col["name"]}") AS "{col["name"]}_d"')
        parts.append(f'SUM(CASE WHEN "{col["name"]}" IS NULL THEN 1 ELSE 0 END) AS "{col["name"]}_n"')

    # Build the FROM clause — use FQN for source tables, qualified name for dbt models
    if schema.startswith("("):
        # Source table or direct query — table_ref is already fully qualified
        from_clause = table_ref
    else:
        from_clause = f"DBT_DEV.{schema}.{table_ref}"

    try:
        cursor.execute(f'SELECT COUNT(*) AS t, {", ".join(parts)} FROM {from_clause}')
        row = cursor.fetchone()
        cursor.close()
    except Exception as e:
        cursor.close()
        return {"error": str(e)}

    total = row[0]
    profile = []
    for i, col in enumerate(columns):
        distinct = row[1 + i * 2]
        nulls = row[2 + i * 2]
        profile.append({
            "column": col["name"], "type": col["type"],
            "distinct_values": distinct,
            "null_pct": round(nulls / total * 100, 1) if total > 0 else 0,
            "cardinality_ratio": round(distinct / total, 4) if total > 0 else 0,
        })
    result = {"table": table_ref, "total_rows": total, "profile": profile}
    if "note" in desc:
        result["note"] = desc["note"]
    return result


def tool_run_query(conn, sql):
    """Execute a read-only SQL query (SELECT/SHOW/DESCRIBE/WITH)."""
    normalized = sql.strip().upper()
    if not any(normalized.startswith(kw) for kw in ("SELECT", "SHOW", "DESCRIBE", "WITH")):
        return {"error": "Only SELECT/SHOW/DESCRIBE/WITH queries are allowed"}

    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchmany(100)
        cursor.close()
        return {"columns": columns, "rows": [dict(zip(columns, r)) for r in rows], "row_count": len(rows)}
    except Exception as e:
        cursor.close()
        return {"error": str(e)}


def tool_generate_model(conn, layer, source_name, model_name, sql, description="", force=False):
    """Write a new dbt model (any layer) with context awareness.

    Before writing, runs _enforce_review() to gate on severity=error issues.
    If errors found and force=False, returns REVIEW_BLOCKED with issue details.
    Checks existing models to avoid conflicts and updates schema.yml alongside the SQL.
    """
    # Enforce code review before writing
    file_path = str(MODELS_DIR / layer / source_name / f"{model_name}.sql")
    review = _enforce_review(sql, file_path)
    if not review["can_proceed"] and not force:
        return {
            "error": "REVIEW_BLOCKED",
            "message": "Code review found error-severity issues that must be fixed before writing.",
            "errors": review["errors"],
            "warnings": review["warnings"],
            "info": review["info"],
            "model_name": model_name,
            "hint": "Fix the errors and retry, or pass force=True to bypass.",
        }

    # Check if model already exists
    existing = ctx.read_model_sql(model_name)
    action = "updated" if "sql" in existing else "created"

    target_dir = MODELS_DIR / layer / source_name
    target_dir.mkdir(parents=True, exist_ok=True)

    sql_path = target_dir / f"{model_name}.sql"
    sql_path.write_text(sql)

    # Update schema.yml
    schema_path = target_dir / "schema.yml"
    if schema_path.exists():
        with open(schema_path) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {"version": 2, "models": []}
    if "models" not in data:
        data["models"] = []

    entry = next((m for m in data["models"] if m.get("name") == model_name), None)
    if entry:
        entry["description"] = description or entry.get("description", f"Generated {layer} model")
    else:
        data["models"].append({"name": model_name, "description": description or f"Generated {layer} model"})

    with open(schema_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    ctx.invalidate()
    result = {
        "action": action,
        "created": str(sql_path.relative_to(PROJECT_ROOT)),
        "schema": str(schema_path.relative_to(PROJECT_ROOT)),
        "model_name": model_name,
        "layer": layer,
    }
    # Include review warnings/info even when write succeeds
    if review["warnings"] or review["info"] or (force and review["errors"]):
        result["review"] = {
            "errors": review["errors"],
            "warnings": review["warnings"],
            "info": review["info"],
        }
    return result


def tool_generate_semantic_view(conn, model_name, analysis_name=None):
    """Generate a Snowflake Semantic View from a mart model.

    Context-aware: reads the model SQL, profiles columns from Snowflake,
    auto-classifies dimensions vs metrics, and generates:
      - sem_*.sql model
      - schema.yml metadata
      - CREATE SEMANTIC VIEW DDL
    """
    if not analysis_name:
        analysis_name = model_name.replace("fct_", "").replace("dim_", "") + "_analysis"

    script_path = SCRIPTS_DIR / "generate_semantic_view.py"
    if not script_path.exists():
        return {"error": "generate_semantic_view.py not found"}

    cmd = [sys.executable, str(script_path), "--model", model_name, "--analysis-name", analysis_name]
    try:
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=120)
        output = result.stdout + result.stderr
        if result.returncode == 0:
            ctx.invalidate()
            return {
                "success": True, "analysis_name": analysis_name,
                "files": [f"models/semantic/sem_{analysis_name}.sql",
                          "models/semantic/schema.yml",
                          f"models/semantic/sem_{analysis_name}_ddl.sql"],
                "output": output[:3000],
            }
        return {"error": output[:3000]}
    except subprocess.TimeoutExpired:
        return {"error": "Semantic view generation timed out"}
    except Exception as e:
        return {"error": str(e)}


def tool_review_sql(conn, model_name=None, sql_content=None):
    """Review SQL for best-practice violations. Context-aware: reads the model if only name provided."""
    if not sql_content and model_name:
        info = ctx.read_model_sql(model_name)
        if "error" in info:
            return info
        sql_content = info["sql"]
        file_path = info.get("path", "")
    else:
        file_path = ""

    if not sql_content:
        return {"error": "Provide model_name or sql_content"}

    issues = []
    lines = sql_content.split("\n")
    for rule in _REVIEW_RULES:
        if rule.get("applies_to") and not any(l in file_path for l in rule["applies_to"]):
            continue
        if not rule["pattern"]:
            continue
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("--") or stripped.startswith("{#"):
                continue
            if re.search(rule["pattern"], line, re.IGNORECASE):
                issues.append({
                    "rule": rule["id"], "severity": rule["severity"],
                    "message": rule["message"], "line": i,
                    "content": line.strip()[:120],
                })

    # Check naming
    if "staging" in file_path and model_name and not model_name.startswith("stg_"):
        issues.append({"rule": "NAMING_STG", "severity": "warning",
                       "message": "Staging model should follow stg_<source>__<table> naming", "line": 0})

    # Check for schema.yml
    if model_name:
        schema_info = ctx.read_schema_yml(model_name)
        if "error" in schema_info:
            issues.append({"rule": "MISSING_SCHEMA_YML", "severity": "warning",
                           "message": "No schema.yml entry — model lacks description and tests", "line": 0})

    return {"model": model_name or "(inline)", "issues": issues, "issue_count": len(issues),
            "status": "clean" if not issues else "issues_found"}


def tool_check_data_quality(conn, select=""):
    """Run dbt tests and return pass/fail summary."""
    dbt_cmd = _find_dbt_executable()
    if not dbt_cmd:
        return {"error": "dbt CLI not found. Install it with: pip install dbt-snowflake"}

    cmd = dbt_cmd + ["test", "--quiet"]
    if select:
        safe = re.sub(r'[^a-zA-Z0-9_+:.\-*/]', '', select)
        cmd.extend(["--select", safe])

    try:
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=300)
        output = result.stdout + result.stderr
        return {
            "command": " ".join(cmd),
            "success": result.returncode == 0,
            "status": "ALL PASSED" if result.returncode == 0 else "FAILURES DETECTED",
            "output": output[:4000],
        }
    except subprocess.TimeoutExpired:
        return {"error": "dbt test timed out (300s)"}
    except FileNotFoundError:
        return {"error": "dbt CLI not found. Install it with: pip install dbt-snowflake"}


def tool_run_dbt(conn, command, select="", full_refresh=False):
    """Execute a dbt CLI command (run/test/build/compile/ls/debug/deps)."""
    allowed = {"run", "test", "build", "compile", "ls", "debug", "deps", "seed"}
    if command not in allowed:
        return {"error": f"Command '{command}' not allowed. Use: {', '.join(sorted(allowed))}"}

    dbt_cmd = _find_dbt_executable()
    if not dbt_cmd:
        return {"error": "dbt CLI not found. Install it with: pip install dbt-snowflake"}

    cmd = dbt_cmd + [command]
    if select:
        safe = re.sub(r'[^a-zA-Z0-9_+:.\-*/]', '', select)
        cmd.extend(["--select", safe])
    if full_refresh:
        cmd.append("--full-refresh")

    try:
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=300)
        output = result.stdout + result.stderr
        if len(output) > 4000:
            output = output[:4000] + "\n... (truncated)"
        ctx.invalidate()
        return {
            "command": " ".join(cmd),
            "exit_code": result.returncode,
            "success": result.returncode == 0,
            "output": output,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"dbt {command} timed out (300s)"}
    except FileNotFoundError:
        return {"error": "dbt CLI not found. Install it with: pip install dbt-snowflake"}


def tool_project_context(conn):
    """Get the current project summary: sources, model counts, layer breakdown."""
    return ctx.get_project_summary()


def tool_generate_streamlit_app(conn, model_name, app_title=""):
    """Generate a Streamlit-in-Snowflake app from a mart model."""
    title = app_title or f"{model_name.replace('_', ' ').title()} Dashboard"

    # Context-aware: read the model to understand its columns
    model_info = ctx.read_model_sql(model_name)
    model_sql_hint = ""
    if "sql" in model_info:
        model_sql_hint = f"-- Based on model: {model_info['path']}\n"

    code = f'''"""
{title}
Auto-generated Streamlit-in-Snowflake app for {model_name}
{model_sql_hint}"""
import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="{title}", layout="wide")
st.title("{title}")

session = get_active_session()

@st.cache_data(ttl=600)
def load_data():
    return session.table("{model_name.upper()}").to_pandas()

df = load_data()

# Dynamic filters
string_cols = df.select_dtypes(include=["object"]).columns.tolist()
filters = {{}}
for col in string_cols[:5]:
    unique_vals = sorted(df[col].dropna().unique().tolist())
    selected = st.sidebar.multiselect(col.replace("_", " ").title(), unique_vals)
    if selected:
        filters[col] = selected

filtered_df = df.copy()
for col, vals in filters.items():
    filtered_df = filtered_df[filtered_df[col].isin(vals)]

# KPIs
st.subheader("Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Records", f"{{len(filtered_df):,}}")
numeric_cols = filtered_df.select_dtypes(include=["number"]).columns.tolist()
if numeric_cols:
    col2.metric(numeric_cols[0].replace("_", " ").title(), f"{{filtered_df[numeric_cols[0]].sum():,.2f}}")
if len(numeric_cols) > 1:
    col3.metric(numeric_cols[1].replace("_", " ").title(), f"{{filtered_df[numeric_cols[1]].sum():,.2f}}")

# Chart
date_cols = filtered_df.select_dtypes(include=["datetime64"]).columns.tolist()
if date_cols and numeric_cols:
    chart_data = filtered_df.groupby(date_cols[0])[numeric_cols[0]].sum().reset_index()
    st.line_chart(chart_data, x=date_cols[0], y=numeric_cols[0])

# Data table
st.dataframe(filtered_df.head(1000), use_container_width=True)
'''
    # Write file
    streamlit_dir = PROJECT_ROOT / "streamlit"
    streamlit_dir.mkdir(exist_ok=True)
    app_path = streamlit_dir / f"{model_name}_app.py"
    app_path.write_text(code)

    return {
        "created": str(app_path.relative_to(PROJECT_ROOT)),
        "model": model_name,
        "title": title,
    }


# =============================================================================
# TOOL REGISTRY
# =============================================================================

# Tools that only read/write local files — no Snowflake connection needed
_FILE_ONLY_TOOLS = {
    "project_context", "list_sources", "list_models", "read_model",
    "review_sql", "generate_model", "generate_streamlit_app",
}

# Tools that require a live Snowflake connection for SQL execution
_SQL_TOOLS = {
    "discover_source", "sample_data", "describe_table", "profile_data",
    "run_query", "generate_semantic_view", "check_data_quality", "run_dbt",
}


TOOLS = {
    "project_context": {
        "fn": tool_project_context,
        "description": "Get a summary of the current project: sources, model counts per layer, total models. Call this FIRST to understand the project.",
        "params": {},
    },
    "discover_source": {
        "fn": tool_discover_source,
        "description": "Discover tables in a Snowflake database/schema and auto-generate staging + mart models. "
                       "IMPORTANT: Always provide source_name — it determines folder names (models/staging/<source_name>/) "
                       "and model prefixes (stg_<source_name>__<table>). Ask the user or derive a short, descriptive name.",
        "params": {"source_database": "string — Snowflake database name",
                   "source_schema": "string — Snowflake schema name",
                   "source_name": "string — short name for this source (used as folder name and model prefix). "
                                  "If omitted, auto-derived from database/schema name. "
                                  "Examples: 'ecommerce_data', 'covid19_data', 'census_data'",
                   "dry_run": "bool (optional — preview without writing files)"},
    },
    "list_sources": {
        "fn": tool_list_sources,
        "description": "List dbt source definitions (bronze layer). Use source_name to filter.",
        "params": {"source_name": "string (optional)"},
    },
    "list_models": {
        "fn": tool_list_models,
        "description": "List dbt models by layer (staging/intermediate/marts/semantic/all). Use source_name to filter.",
        "params": {"layer": "string (default: 'all')", "source_name": "string (optional)"},
    },
    "read_model": {
        "fn": tool_read_model,
        "description": "Read the SQL source code of a dbt model.",
        "params": {"model_name": "string"},
    },
    "sample_data": {
        "fn": tool_sample_data,
        "description": "Query sample rows from a built dbt model in Snowflake.",
        "params": {"table_or_model": "string", "limit": "int (default: 10)"},
    },
    "describe_table": {
        "fn": tool_describe_table,
        "description": "Get column metadata (names, types, nullability) and row count.",
        "params": {"table_or_model": "string"},
    },
    "profile_data": {
        "fn": tool_profile_data,
        "description": "Profile a table: distinct counts, null rates, cardinality ratios per column.",
        "params": {"table_or_model": "string", "max_columns": "int (default: 20)"},
    },
    "run_query": {
        "fn": tool_run_query,
        "description": "Execute a read-only SQL query (SELECT/SHOW/DESCRIBE/WITH).",
        "params": {"sql": "string — SQL query"},
    },
    "generate_model": {
        "fn": tool_generate_model,
        "description": "Create or update a dbt model (any layer). Auto-reviews SQL before writing — blocks on error-severity issues unless force=True. Writes SQL + updates schema.yml.",
        "params": {"layer": "string (staging/intermediate/marts/semantic)",
                   "source_name": "string", "model_name": "string",
                   "sql": "string — full dbt SQL", "description": "string (optional)",
                   "force": "bool (optional, default false) — bypass review errors"},
    },
    "generate_semantic_view": {
        "fn": tool_generate_semantic_view,
        "description": "Generate a Snowflake Semantic View from a mart model. Profiles columns, classifies dims/metrics, creates DDL.",
        "params": {"model_name": "string", "analysis_name": "string (optional)"},
    },
    "review_sql": {
        "fn": tool_review_sql,
        "description": "Static analysis of a model — naming, ref usage, hard-coded values, missing tests. Pass model_name OR sql_content.",
        "params": {"model_name": "string (optional)", "sql_content": "string (optional)"},
    },
    "check_data_quality": {
        "fn": tool_check_data_quality,
        "description": "Run dbt tests and return pass/fail summary. Use select to scope.",
        "params": {"select": "string (optional — dbt selector)"},
    },
    "run_dbt": {
        "fn": tool_run_dbt,
        "description": "Execute a dbt CLI command (run/test/build/compile/ls/debug/deps/seed).",
        "params": {"command": "string", "select": "string (optional)", "full_refresh": "bool (optional)"},
    },
    "generate_streamlit_app": {
        "fn": tool_generate_streamlit_app,
        "description": "Scaffold a Streamlit-in-Snowflake dashboard from a mart model.",
        "params": {"model_name": "string", "app_title": "string (optional)"},
    },
}


# =============================================================================
# CORTEX LLM INTEGRATION — agent loop
# =============================================================================

SYSTEM_PROMPT = """\
You are a Snowflake dbt expert agent — a unified one-stop tool for the entire dbt development lifecycle.
You combine source discovery, model generation, semantic views, code review, data quality, and medallion architecture advising.

## CRITICAL: CONTEXT-AWARENESS

Before generating ANY code, you MUST:
1. Call `project_context()` to understand what exists
2. Call `list_models()` or `list_sources()` to see what's already built
3. Call `read_model()` to understand existing model SQL before suggesting changes
4. Call `describe_table()` or `profile_data()` to understand actual column types and cardinality
5. Only THEN generate code that fits the existing project

NEVER produce generic/boilerplate code. Always base your output on actual project state and data.

## TOOL CALLING FORMAT

When you need to use a tool, respond with EXACTLY this format (one tool per block):
```tool
TOOL_NAME(param1="value1", param2="value2")
```

Available tools:
{tool_descriptions}

## CAPABILITIES

1. **Source Discovery**: Discover new Snowflake data sources and auto-generate staging models
2. **Model Generation**: Create intermediate (silver) and marts (gold) models with proper naming
3. **Semantic Views**: Auto-classify dimensions/metrics and generate CREATE SEMANTIC VIEW DDL
4. **Code Review**: Check models against project conventions (naming, ref usage, tests)
5. **Data Quality**: Run dbt tests, profile data for nulls/cardinality
6. **dbt Operations**: Run, build, test, compile models
7. **Streamlit Apps**: Generate data dashboards from mart models

## CONVENTIONS

- Staging: `stg_<source>__<table>` (auto-generated, rarely modify)
- Intermediate: `int_<description>` (joins, dedup, business logic)
- Marts: `fct_<entity>` (facts) or `dim_<entity>` (dimensions)
- Semantic: `sem_<analysis_name>` (Snowflake Semantic Views)
- Always use `{{{{ ref('model') }}}}` and `{{{{ source('src', 'TABLE') }}}}`
- Never hardcode database/schema names
- Use CTEs, not subqueries
- Use `dbt_utils.generate_surrogate_key()` for surrogate keys

## WORKFLOW

1. Start with `project_context()` to understand current state
2. Explore: list sources, list models, describe/profile tables
3. Plan: explain what you'll build and why
4. Generate: create models using `generate_model()`
5. Build: auto-run `run_dbt(command="build", select="model_name")` after generating
6. Validate: check build output, report results

## SOURCE NAMING

The `source_name` is critical — it determines:
- Folder names under `models/staging/`, `models/intermediate/`, `models/marts/`
- Model prefixes (e.g., `stg_<source_name>__<table>`)
- Source YAML file organization

When calling `discover_source()`, ALWAYS provide `source_name` explicitly.
If the user doesn't specify one, ask them what name to use — don't just default to
the raw schema name. Explain that this name will be used across all generated folders
and model prefixes. The auto-derived name may not match the user's intent.

## FILTERING

When the user asks about a specific source, ALWAYS pass `source_name` to filter results.
"""


def build_tool_descriptions():
    lines = []
    for name, info in TOOLS.items():
        params = ", ".join(f'{k}={v}' for k, v in info["params"].items())
        lines.append(f"- `{name}({params})` — {info['description']}")
    return "\n".join(lines)


def call_cortex(conn, messages, model=DEFAULT_CORTEX_MODEL):
    """Call Snowflake Cortex COMPLETE."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SNOWFLAKE.CORTEX.COMPLETE(%s, %s)", (model, json.dumps(messages)))
        result = cursor.fetchone()[0]
        cursor.close()
        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict):
                if "choices" in parsed:
                    return parsed["choices"][0].get("messages",
                           parsed["choices"][0].get("message", {}).get("content", result))
                if "message" in parsed:
                    return parsed["message"]
                if "content" in parsed:
                    return parsed["content"]
        except (json.JSONDecodeError, KeyError, IndexError):
            pass
        return result
    except Exception as e:
        cursor.close()
        return f"[Cortex error: {e}]"


def parse_tool_calls(response_text):
    """Extract tool calls from ```tool blocks."""
    blocks = re.findall(r'```tool\s*\n(.*?)\n\s*```', response_text, re.DOTALL)
    calls = []
    for block in blocks:
        block = block.strip()
        paren_idx = block.find('(')
        if paren_idx == -1:
            continue
        tool_name = block[:paren_idx].strip()
        last_paren = block.rfind(')')
        if last_paren <= paren_idx:
            continue
        params_str = block[paren_idx + 1:last_paren]

        params = {}
        param_pattern = (
            r'(\w+)\s*=\s*(?:'
            r'"""(.*?)"""|'
            r"'''(.*?)'''|"
            r'"((?:[^"\\]|\\.)*)"|'
            r"'((?:[^'\\]|\\.)*)'|"
            r'(\d+)|'
            r'(True|False)'
            r')'
        )
        for m in re.finditer(param_pattern, params_str, re.DOTALL):
            key = m.group(1)
            str_value = next((g for g in (m.group(2), m.group(3), m.group(4), m.group(5)) if g is not None), None)
            if str_value is not None:
                value = str_value.strip().replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace("\\'", "'")
            elif m.group(6) is not None:
                value = int(m.group(6))
            elif m.group(7) is not None:
                value = m.group(7) == "True"
            else:
                continue
            params[key] = value
        calls.append((tool_name, params))
    return calls


def execute_tool(conn, tool_name, params):
    """Execute a named tool."""
    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}
    fn = TOOLS[tool_name]["fn"]
    try:
        return fn(conn, **params)
    except TypeError as e:
        return {"error": f"Invalid parameters for {tool_name}: {e}"}
    except Exception as e:
        return {"error": f"Tool execution failed: {e}"}


def _auto_build(conn, executed_calls):
    """Auto-build any models that were just generated, then auto-review each."""
    generated = []
    for tool_name, result in executed_calls:
        if tool_name == "generate_model" and isinstance(result, dict) and "model_name" in result:
            generated.append(result["model_name"])
    if not generated:
        return []

    selector = " ".join(generated)
    print(f"\n  [Auto-building {len(generated)} model(s): {selector}...]")
    build_result = tool_run_dbt(conn, command="build", select=selector)
    status = "PASSED" if build_result.get("success") else "FAILED"
    print(f"  [Build {status}]")
    feedback = [f"Auto-build [{selector}]: {json.dumps(build_result, indent=2, default=str)}"]

    # Post-build review for each generated model
    for name in generated:
        print(f"  [Auto-reviewing {name}...]")
        review_result = tool_review_sql(conn, model_name=name)
        feedback.append(f"Auto-review [{name}]: {json.dumps(review_result, indent=2, default=str)}")
        issue_count = review_result.get("issue_count", 0)
        if issue_count > 0:
            print(f"  [Review: {issue_count} issue(s) found in {name}]")
        else:
            print(f"  [Review: {name} is clean]")

    return feedback


# =============================================================================
# AGENT LOOP — interactive or single-question
# =============================================================================

def run_agent(conn, model=DEFAULT_CORTEX_MODEL, initial_question=None):
    """Run the interactive Cortex-powered agent."""
    tool_descs = build_tool_descriptions()
    system_prompt = SYSTEM_PROMPT.format(tool_descriptions=tool_descs)
    messages = [{"role": "system", "content": system_prompt}]

    print("\n" + "=" * 60)
    print("  dbt One-Stop Agent")
    print("  Powered by Snowflake Cortex")
    print("=" * 60)
    print("\nAll capabilities in one place:")
    print("  - Source discovery & staging generation")
    print("  - Medallion architecture (silver/gold) advising")
    print("  - Semantic view creation")
    print("  - Code review & data quality")
    print("  - dbt build/test/compile operations")
    print("  - Streamlit app generation")
    print('\nExamples:')
    print('  "What sources do I have?"')
    print('  "Discover tables from COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC"')
    print('  "Create a semantic view for fct_orders"')
    print('  "Review all my models for best practices"')
    print('  "Build and test all marts models"')
    print('\nType "quit" to exit.\n')

    if initial_question:
        user_input = initial_question
        print(f"You: {user_input}\n")
    else:
        user_input = input("You: ").strip()

    while user_input.lower() not in ("quit", "exit", "q"):
        if not user_input:
            user_input = input("You: ").strip()
            continue

        messages.append({"role": "user", "content": user_input})
        response = call_cortex(conn, messages, model)
        tool_calls = parse_tool_calls(response)

        if tool_calls:
            clean = re.sub(r'```tool\s*\n.*?\n\s*```', '', response, flags=re.DOTALL).strip()
            if clean:
                print(f"Agent: {clean}\n")

            tool_results = []
            executed = []
            for t_name, t_params in tool_calls:
                print(f"  [{t_name}...]")
                result = execute_tool(conn, t_name, t_params)
                executed.append((t_name, result))
                result_str = json.dumps(result, indent=2, default=str)
                if len(result_str) > 8000:
                    result_str = result_str[:8000] + "\n... (truncated)"
                tool_results.append(f"Tool {t_name} returned:\n{result_str}")
                if "error" in result:
                    print(f"  [Error: {result['error'][:200]}]")
                elif "created" in result:
                    print(f"  [Created: {result['created']}]")
                elif "action" in result:
                    print(f"  [{result['action'].title()}: {result.get('created', result.get('model_name', ''))}]")
                else:
                    print(f"  [Done]")

            build_feedback = _auto_build(conn, executed)
            tool_results.extend(build_feedback)

            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": f"Tool results:\n{chr(10).join(tool_results)}\n\nInterpret these results and continue."})

            # Follow-up loop for multi-step tool chains
            failed_calls = set()  # Track failed tool+params to prevent infinite retry loops
            for err_tool, err_result in executed:
                if isinstance(err_result, dict) and "error" in err_result:
                    failed_calls.add(err_tool)

            for _ in range(10):
                follow_up = call_cortex(conn, messages, model)
                next_calls = parse_tool_calls(follow_up)
                if not next_calls:
                    print(f"\nAgent: {follow_up}\n")
                    messages.append({"role": "assistant", "content": follow_up})
                    break

                # Filter out tool calls that already failed with the same name
                # to prevent the LLM from retrying the exact same failing tool
                actionable_calls = []
                skipped_calls = []
                for t_name, t_params in next_calls:
                    if t_name in failed_calls:
                        skipped_calls.append(t_name)
                    else:
                        actionable_calls.append((t_name, t_params))

                if skipped_calls and not actionable_calls:
                    # All calls are retries of failed tools — break the loop
                    skip_msg = f"Skipped retrying already-failed tools: {', '.join(skipped_calls)}. Move on to a different approach or report what you found so far."
                    messages.append({"role": "assistant", "content": follow_up})
                    messages.append({"role": "user", "content": f"STOP: {skip_msg}"})
                    print(f"  [Skipped retrying: {', '.join(skipped_calls)}]")
                    continue

                if not actionable_calls:
                    print(f"\nAgent: {follow_up}\n")
                    messages.append({"role": "assistant", "content": follow_up})
                    break

                clean_f = re.sub(r'```tool\s*\n.*?\n\s*```', '', follow_up, flags=re.DOTALL).strip()
                if clean_f:
                    print(f"\nAgent: {clean_f}\n")

                tool_results = []
                executed = []
                if skipped_calls:
                    tool_results.append(f"NOTE: Tools [{', '.join(skipped_calls)}] were skipped because they already failed. Use a different approach (e.g., run_query with a direct SQL query, or try run_dbt to build the model first).")
                for t_name, t_params in actionable_calls:
                    print(f"  [{t_name}...]")
                    result = execute_tool(conn, t_name, t_params)
                    executed.append((t_name, result))
                    result_str = json.dumps(result, indent=2, default=str)
                    if len(result_str) > 8000:
                        result_str = result_str[:8000] + "\n... (truncated)"
                    tool_results.append(f"Tool {t_name} returned:\n{result_str}")
                    if "error" in result:
                        print(f"  [Error: {result['error'][:200]}]")
                    elif "created" in result:
                        print(f"  [Created: {result['created']}]")
                    else:
                        print(f"  [Done]")

                # Track new failures to prevent retries in subsequent iterations
                for err_tool, err_result in executed:
                    if isinstance(err_result, dict) and "error" in err_result:
                        failed_calls.add(err_tool)

                build_feedback = _auto_build(conn, executed)
                tool_results.extend(build_feedback)
                messages.append({"role": "assistant", "content": follow_up})
                messages.append({"role": "user", "content": f"Tool results:\n{chr(10).join(tool_results)}\n\nInterpret results and continue."})
        else:
            print(f"Agent: {response}\n")
            messages.append({"role": "assistant", "content": response})

        if len(messages) > 21:
            messages = [messages[0]] + messages[-20:]

        user_input = input("You: ").strip()

    print("\nGoodbye!")


# =============================================================================
# MCP SERVER MODE — for VS Code and Cortex Code
# =============================================================================

def run_mcp_server():
    """Run as an MCP server (stdio) for VS Code / Cortex Code integration.

    Architecture:
      - File-only tools (project_context, list_sources, read_model, etc.) run
        without a Snowflake connection — they just read/write local files.
      - SQL tools (discover_source, describe_table, run_query, etc.) lazily
        create a Snowflake connection on first use via profiles.yml.
      - The LLM is NOT called here — Copilot/Claude IS the LLM. This server
        only provides tools for the LLM to orchestrate.
      - When using VS Code with the Snowflake Managed MCP server, Copilot can
        call run_sql on that server for ad-hoc queries AND call this agent's
        tools for dbt-specific operations — both work in parallel.
    """
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import TextContent, Tool
    except ImportError:
        print("MCP SDK not installed. Run: pip install mcp", file=sys.stderr)
        sys.exit(1)

    import asyncio
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("dbt-agent-mcp")

    server = Server("dbt-one-stop-agent")

    # Lazy connection — only created when an SQL tool is called
    _conn_holder = {"conn": None}

    def _get_or_create_conn():
        if _conn_holder["conn"] is None:
            _conn_holder["conn"] = get_connection()
        return _conn_holder["conn"]

    @server.list_tools()
    async def list_tools():
        mcp_tools = []
        for name, info in TOOLS.items():
            properties = {}
            required = []
            for param_name, param_desc in info["params"].items():
                is_optional = "optional" in param_desc.lower() or "default" in param_desc.lower()
                if "bool" in param_desc.lower():
                    properties[param_name] = {"type": "boolean", "description": param_desc}
                elif "int" in param_desc.lower():
                    properties[param_name] = {"type": "integer", "description": param_desc}
                else:
                    properties[param_name] = {"type": "string", "description": param_desc}
                if not is_optional:
                    required.append(param_name)

            mcp_tools.append(Tool(
                name=name,
                description=info["description"],
                inputSchema={"type": "object", "properties": properties, "required": required},
            ))
        return mcp_tools

    @server.call_tool()
    async def call_tool(name, arguments):
        if name not in TOOLS:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        try:
            # File-only tools don't need a real Snowflake connection
            if name in _FILE_ONLY_TOOLS:
                result = TOOLS[name]["fn"](None, **arguments)
            else:
                conn = _get_or_create_conn()
                result = TOOLS[name]["fn"](conn, **arguments)

            formatted = json.dumps(result, indent=2, default=str)

            # Auto-build if a model was just generated
            if name == "generate_model" and isinstance(result, dict) and "model_name" in result:
                build_result = tool_run_dbt(None, command="build", select=result["model_name"])
                formatted += f"\n\n## Auto-Build Result\n```json\n{json.dumps(build_result, indent=2, default=str)}\n```"

                # Auto-review after build
                review_result = tool_review_sql(None, model_name=result["model_name"])
                formatted += f"\n\n## Auto-Review Result\n```json\n{json.dumps(review_result, indent=2, default=str)}\n```"

            return [TextContent(type="text", text=f"## {name}\n\n```json\n{formatted}\n```")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in {name}: {e}")]

    logger.info("Starting dbt One-Stop Agent MCP Server...")

    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(_run())


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="dbt One-Stop Agent — unified source discovery, model generation, "
                    "semantic views, code review, data quality, and medallion advising")
    parser.add_argument("--mcp", action="store_true",
                        help="Run as MCP server (stdio) for VS Code / Cortex Code")
    parser.add_argument("--model", default=DEFAULT_CORTEX_MODEL,
                        help=f"Cortex LLM model (default: {DEFAULT_CORTEX_MODEL})")
    parser.add_argument("--ask", help="Single question (non-interactive mode)")
    args = parser.parse_args()

    if args.mcp:
        run_mcp_server()
    else:
        conn = get_connection()
        run_agent(conn, model=args.model, initial_question=args.ask)
        conn.close()


if __name__ == "__main__":
    main()
