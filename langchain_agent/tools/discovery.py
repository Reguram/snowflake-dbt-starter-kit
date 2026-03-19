"""Discovery pipeline tools — discover tables, classify columns, auto-generate staging.

Ported from scripts/discover_and_generate.py.
"""

import json
import re
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from langchain_agent.snowflake_conn import get_connection

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


# ─── Helpers (from discover_and_generate.py) ──────────────────

def _sql_identifier(name: str) -> str:
    if re.match(r"^[A-Z_][A-Z0-9_]*$", name):
        return name.lower()
    return f'"{name}"'


def _strip_prefix(col_name: str, table_name: str) -> str:
    lower = col_name.lower()
    parts = lower.split("_", 1)
    if len(parts) > 1 and len(parts[0]) == 1:
        return parts[1]
    if len(parts) > 1 and len(parts[0]) == 2:
        table_initials = "".join(w[0] for w in table_name.lower().split("_") if w)
        if parts[0] == table_initials[:2]:
            return parts[1]
    return lower


def _detect_primary_key(columns: list[dict], table_name: str) -> Optional[str]:
    for col in columns:
        lower = col["name"].lower()
        if lower.endswith("key") or lower.endswith("id") or lower.endswith("_pk"):
            return col["name"]
    return columns[0]["name"] if columns else None


# ─── Tools ───────────────────────────────────────────────────

@tool
def discover_tables(database: str, schema: str) -> str:
    """Discover all tables and their columns in a Snowflake database/schema.

    Args:
        database: Snowflake database name.
        schema: Snowflake schema name.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT TABLE_NAME, TABLE_TYPE, ROW_COUNT, COMMENT
        FROM {database}.INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{schema.upper()}'
          AND TABLE_TYPE IN ('BASE TABLE', 'VIEW')
        ORDER BY TABLE_NAME
    """)

    tables = []
    for row in cursor:
        tables.append({
            "name": row[0],
            "type": row[1],
            "row_count": row[2],
            "comment": row[3] or "",
        })

    for table in tables:
        cursor.execute(
            f'DESCRIBE TABLE {database}.{schema}."{table["name"]}"'
        )
        table["columns"] = []
        for idx, col_row in enumerate(cursor, start=1):
            raw_type = col_row[1]
            base_type = raw_type.split("(")[0].strip().upper()
            table["columns"].append({
                "name": col_row[0],
                "data_type": base_type,
                "nullable": col_row[3] == "Y",
                "position": idx,
            })

    cursor.close()
    return json.dumps({
        "database": database,
        "schema": schema,
        "table_count": len(tables),
        "tables": tables,
    }, indent=2, default=str)


@tool
def classify_columns(table_or_model: str, database: str = "", schema: str = "") -> str:
    """Classify columns of a table as dimension, measure, date, or primary key.

    Uses column type heuristics and cardinality profiling.

    Args:
        table_or_model: Table name to classify.
        database: Snowflake database (needed if querying raw tables).
        schema: Snowflake schema (needed if querying raw tables).
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Resolve to fully qualified name
    if database and schema:
        fqn = f'{database}.{schema}."{table_or_model}"'
    else:
        from langchain_agent.tools.exploration import _resolve_table_name

        resolved = _resolve_table_name(table_or_model)
        candidates = [
            resolved.upper(),
            f"DBT_STAGING.{resolved.upper()}",
            f"DBT_INTERMEDIATE.{resolved.upper()}",
            f"DBT_MARTS.{resolved.upper()}",
        ]
        fqn = None
        for c in candidates:
            try:
                cursor.execute(f"DESCRIBE TABLE {c}")
                fqn = c
                break
            except Exception:
                continue
        if fqn is None:
            cursor.close()
            return json.dumps({"error": f"Could not find table '{table_or_model}'"})

    # Get column metadata
    try:
        cursor.execute(f"DESCRIBE TABLE {fqn}")
    except Exception as e:
        cursor.close()
        return json.dumps({"error": str(e)})

    columns = []
    for row in cursor:
        base_type = row[1].split("(")[0].strip().upper()
        columns.append({"name": row[0], "data_type": base_type, "nullable": row[3] == "Y"})

    table_name = table_or_model.split(".")[-1].strip('"')

    # Classify columns
    date_types = {"DATE", "TIMESTAMP_NTZ", "TIMESTAMP_LTZ", "TIMESTAMP_TZ"}
    date_keywords = re.compile(r"(date|_time|created|updated|_at$|^at_)", re.IGNORECASE)
    numeric_types = {"NUMBER", "FLOAT", "DECIMAL", "NUMERIC", "DOUBLE", "REAL"}

    pk = _detect_primary_key(columns, table_name)
    dimensions = []
    measures = []
    dates = []

    for col in columns:
        if col["name"] == pk:
            continue
        if col["data_type"] in date_types or date_keywords.search(col["name"]):
            dates.append(col["name"])
        elif col["data_type"] in numeric_types and not (
            col["name"].lower().endswith("key") or col["name"].lower().endswith("id")
        ):
            measures.append(col["name"])
        elif col["data_type"] in ("TEXT", "VARCHAR", "STRING", "CHAR", "BOOLEAN"):
            dimensions.append(col["name"])

    cursor.close()
    return json.dumps({
        "table": table_name,
        "primary_key": pk,
        "dimensions": dimensions,
        "measures": measures,
        "dates": dates,
        "total_columns": len(columns),
    }, indent=2)


@tool
def auto_generate_staging(source_name: str, database: str, schema: str) -> str:
    """Discover tables and auto-generate all staging models + sources.yml.

    Creates models/staging/<source_name>/ with _sources.yml, schema.yml,
    and one stg_<source>__<table>.sql per table.

    Args:
        source_name: Name for the dbt source (used in model naming).
        database: Snowflake database to discover.
        schema: Snowflake schema to discover.
    """
    import yaml

    conn = get_connection()
    cursor = conn.cursor()

    # Discover tables
    cursor.execute(f"""
        SELECT TABLE_NAME, TABLE_TYPE, ROW_COUNT
        FROM {database}.INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{schema.upper()}'
          AND TABLE_TYPE IN ('BASE TABLE', 'VIEW')
        ORDER BY TABLE_NAME
    """)
    tables = []
    for row in cursor:
        tables.append({"name": row[0], "type": row[1], "row_count": row[2]})

    # Get columns for each table
    for table in tables:
        cursor.execute(f'DESCRIBE TABLE {database}.{schema}."{table["name"]}"')
        table["columns"] = []
        for col_row in cursor:
            base_type = col_row[1].split("(")[0].strip().upper()
            table["columns"].append({
                "name": col_row[0],
                "data_type": base_type,
                "nullable": col_row[3] == "Y",
            })

    cursor.close()

    if not tables:
        return json.dumps({"error": f"No tables found in {database}.{schema}"})

    out_dir = MODELS_DIR / "staging" / source_name
    out_dir.mkdir(parents=True, exist_ok=True)

    created_files = []

    # Generate _sources.yml
    sources_data = {
        "version": 2,
        "sources": [{
            "name": source_name,
            "description": f"Auto-discovered source from {database}.{schema}",
            "database": database,
            "schema": schema,
            "quoting": {"identifier": True},
            "tables": [
                {
                    "name": t["name"],
                    "description": f"Raw {t['name'].lower()} table (~{t['row_count'] or 0:,} rows)",
                }
                for t in tables
            ],
        }],
    }
    sources_path = out_dir / "_sources.yml"
    sources_path.write_text(yaml.dump(sources_data, default_flow_style=False, sort_keys=False))
    created_files.append(str(sources_path.relative_to(PROJECT_ROOT)))

    # Generate staging models
    schema_models = []
    for table in tables:
        model_name = f"stg_{source_name}__{table['name'].lower()}"

        col_lines = []
        for col in table["columns"]:
            original = _sql_identifier(col["name"])
            clean = _strip_prefix(col["name"], table["name"])
            clean_sql = _sql_identifier(clean) if clean != col["name"].lower() else original
            if original != clean_sql:
                col_lines.append(f"        {original} as {clean_sql}")
            else:
                col_lines.append(f"        {original}")

        cols_str = ",\n".join(col_lines)
        sql = (
            f"with source as (\n"
            f"    select * from {{{{ source('{source_name}', '{table['name']}') }}}}\n"
            f"),\n\n"
            f"renamed as (\n"
            f"    select\n"
            f"{cols_str}\n"
            f"    from source\n"
            f")\n\n"
            f"select * from renamed\n"
        )

        sql_path = out_dir / f"{model_name}.sql"
        sql_path.write_text(sql)
        created_files.append(str(sql_path.relative_to(PROJECT_ROOT)))

        schema_models.append({
            "name": model_name,
            "description": f"Staged {table['name'].lower()} from {source_name}",
        })

    # Generate schema.yml
    schema_data = {"version": 2, "models": schema_models}
    schema_path = out_dir / "schema.yml"
    schema_path.write_text(yaml.dump(schema_data, default_flow_style=False, sort_keys=False))
    created_files.append(str(schema_path.relative_to(PROJECT_ROOT)))

    return json.dumps({
        "source_name": source_name,
        "tables_discovered": len(tables),
        "models_created": len(tables),
        "files": created_files,
    }, indent=2)
