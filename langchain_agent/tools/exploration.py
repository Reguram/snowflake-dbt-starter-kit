"""Data exploration tools — list sources, describe tables, sample data, profile, etc.

Ported from scripts/medallion_agent.py tool functions.
"""

import json
import re
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from langchain_agent.snowflake_conn import get_connection

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


# ─── Helpers ──────────────────────────────────────────────────

def _get_all_model_names() -> list[str]:
    """Scan models/ for all .sql file stems."""
    names = []
    for layer in ("staging", "intermediate", "marts", "semantic"):
        layer_dir = MODELS_DIR / layer
        if layer_dir.exists():
            for sql_file in layer_dir.rglob("*.sql"):
                names.append(sql_file.stem)
    return names


def _resolve_table_name(table_or_model: str) -> str:
    """Resolve user-provided table/model name to the actual dbt model name on disk.

    Handles:
      - "source.TABLE" prefix stripping
      - Case-insensitive exact match
      - Suffix match (TABLE -> stg_source__table)
      - Contains match (partial name)
      - Priority: stg_ > fct_ > dim_ > int_
    """
    name = table_or_model.strip()
    if "." in name:
        name = name.rsplit(".", 1)[-1]

    all_models = _get_all_model_names()
    name_lower = name.lower()

    for m in all_models:
        if m.lower() == name_lower:
            return m

    suffix_matches = [m for m in all_models if m.lower().endswith(name_lower)]
    if len(suffix_matches) == 1:
        return suffix_matches[0]

    contains_matches = [m for m in all_models if name_lower in m.lower()]
    if len(contains_matches) == 1:
        return contains_matches[0]

    if suffix_matches:
        for prefix in ("stg_", "fct_", "dim_", "summary_", "int_"):
            for m in suffix_matches:
                if m.startswith(prefix):
                    return m
        return suffix_matches[0]

    if contains_matches:
        return contains_matches[0]

    return name


def _find_model_path(model_name: str) -> Optional[Path]:
    """Find the .sql file for a model across all layers."""
    for layer in ("staging", "intermediate", "marts", "semantic"):
        layer_dir = MODELS_DIR / layer
        if layer_dir.exists():
            for sql_file in layer_dir.rglob("*.sql"):
                if sql_file.stem == model_name:
                    return sql_file
    return None


# ─── Tools ───────────────────────────────────────────────────

@tool
def list_sources(source_name: Optional[str] = None) -> str:
    """List dbt sources from _sources.yml files.

    Args:
        source_name: Filter to a specific source. Omit to list all.
    """
    import yaml

    staging_dir = MODELS_DIR / "staging"
    if not staging_dir.exists():
        return json.dumps({"error": "No staging directory found"})

    results = []
    for yml_file in staging_dir.rglob("_sources.yml"):
        with open(yml_file) as f:
            data = yaml.safe_load(f)
        for src in data.get("sources", []):
            name = src.get("name", "")
            if source_name and source_name.lower() not in name.lower():
                continue
            tables = [
                {
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "column_count": len(t.get("columns", [])),
                }
                for t in src.get("tables", [])
            ]
            results.append({
                "source": name,
                "database": src.get("database", ""),
                "schema": src.get("schema", ""),
                "tables": tables,
            })

    return json.dumps(results, indent=2)


@tool
def list_models(layer: str = "all", source_name: Optional[str] = None) -> str:
    """List dbt models grouped by layer (staging / intermediate / marts / semantic).

    Args:
        layer: Filter to a specific layer or 'all'.
        source_name: Filter to models containing this source name.
    """
    layers = (
        [layer]
        if layer != "all"
        else ["staging", "intermediate", "marts", "semantic"]
    )
    results = {}
    for lyr in layers:
        layer_dir = MODELS_DIR / lyr
        if not layer_dir.exists():
            continue
        models = []
        for sql_file in sorted(layer_dir.rglob("*.sql")):
            name = sql_file.stem
            if source_name and source_name.lower() not in name.lower():
                subdir = sql_file.parent.name
                if source_name.lower() not in subdir.lower():
                    continue
            models.append({
                "name": name,
                "path": str(sql_file.relative_to(PROJECT_ROOT)),
            })
        if models:
            results[lyr] = models

    return json.dumps(results, indent=2)


@tool
def read_model(model_name: str) -> str:
    """Read the SQL source of a dbt model from disk.

    Args:
        model_name: Model name (without .sql extension).
    """
    resolved = _resolve_table_name(model_name)
    path = _find_model_path(resolved)
    if path is None:
        return json.dumps({"error": f"Model '{model_name}' not found on disk"})
    sql = path.read_text()
    return json.dumps({
        "model": resolved,
        "path": str(path.relative_to(PROJECT_ROOT)),
        "sql": sql,
    })


@tool
def sample_data(table_or_model: str, limit: int = 10) -> str:
    """Query sample rows from a Snowflake table or dbt model.

    Args:
        table_or_model: Table or model name.
        limit: Number of rows to return (default 10, max 50).
    """
    limit = min(max(1, limit), 50)
    resolved = _resolve_table_name(table_or_model)

    conn = get_connection()
    cursor = conn.cursor()

    # Try the resolved model name as a Snowflake object
    candidates = [
        resolved.upper(),
        f"DBT_STAGING.{resolved.upper()}",
        f"DBT_INTERMEDIATE.{resolved.upper()}",
        f"DBT_MARTS.{resolved.upper()}",
    ]

    for candidate in candidates:
        try:
            cursor.execute(f"SELECT * FROM {candidate} LIMIT {limit}")
            columns = [desc[0] for desc in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            cursor.close()
            return json.dumps({
                "table": candidate,
                "columns": columns,
                "row_count": len(rows),
                "rows": rows,
            }, indent=2, default=str)
        except Exception:
            continue

    cursor.close()
    return json.dumps({"error": f"Could not find table/view for '{table_or_model}'"})


@tool
def describe_table(table_or_model: str) -> str:
    """Get column metadata (name, type, nullable) for a Snowflake table or dbt model.

    Args:
        table_or_model: Table or model name.
    """
    resolved = _resolve_table_name(table_or_model)
    conn = get_connection()
    cursor = conn.cursor()

    candidates = [
        resolved.upper(),
        f"DBT_STAGING.{resolved.upper()}",
        f"DBT_INTERMEDIATE.{resolved.upper()}",
        f"DBT_MARTS.{resolved.upper()}",
    ]

    for candidate in candidates:
        try:
            cursor.execute(f"DESCRIBE TABLE {candidate}")
            columns = []
            for row in cursor:
                columns.append({
                    "name": row[0],
                    "type": row[1].split("(")[0].upper(),
                    "nullable": row[3] == "Y",
                })
            cursor.close()
            return json.dumps({
                "table": candidate,
                "column_count": len(columns),
                "columns": columns,
            }, indent=2)
        except Exception:
            continue

    cursor.close()
    return json.dumps({"error": f"Could not describe '{table_or_model}'"})


@tool
def profile_data(table_or_model: str, max_columns: int = 20) -> str:
    """Profile column cardinality, null counts, and basic stats for a table.

    Args:
        table_or_model: Table or model name.
        max_columns: Maximum columns to profile (default 20).
    """
    resolved = _resolve_table_name(table_or_model)
    conn = get_connection()
    cursor = conn.cursor()

    candidates = [
        resolved.upper(),
        f"DBT_STAGING.{resolved.upper()}",
        f"DBT_INTERMEDIATE.{resolved.upper()}",
        f"DBT_MARTS.{resolved.upper()}",
    ]

    for candidate in candidates:
        try:
            cursor.execute(f"DESCRIBE TABLE {candidate}")
            col_info = []
            for row in cursor:
                base_type = row[1].split("(")[0].upper()
                col_info.append({"name": row[0], "type": base_type})
            break
        except Exception:
            continue
    else:
        cursor.close()
        return json.dumps({"error": f"Could not profile '{table_or_model}'"})

    profilable = col_info[: max_columns]
    parts = []
    for c in profilable:
        parts.append(f"COUNT(DISTINCT \"{c['name']}\")")
        parts.append(f"SUM(CASE WHEN \"{c['name']}\" IS NULL THEN 1 ELSE 0 END)")

    query = f'SELECT COUNT(*), {", ".join(parts)} FROM {candidate}'
    try:
        cursor.execute(query)
        row = cursor.fetchone()
    except Exception as e:
        cursor.close()
        return json.dumps({"error": f"Profile query failed: {e}"})

    total = row[0]
    profiles = []
    for i, c in enumerate(profilable):
        distinct = row[1 + i * 2]
        nulls = row[2 + i * 2]
        profiles.append({
            "column": c["name"],
            "type": c["type"],
            "distinct": distinct,
            "nulls": nulls,
            "total": total,
            "null_pct": round(nulls / total * 100, 1) if total else 0,
        })

    cursor.close()
    return json.dumps({"table": candidate, "total_rows": total, "profiles": profiles}, indent=2, default=str)


@tool
def run_query(sql: str) -> str:
    """Execute a read-only SQL query against Snowflake and return results.

    Only SELECT, SHOW, DESCRIBE, and WITH statements are allowed.

    Args:
        sql: SQL query to execute.
    """
    normalized = sql.strip().upper()
    if not any(
        normalized.startswith(prefix)
        for prefix in ("SELECT", "SHOW", "DESCRIBE", "WITH", "DESC")
    ):
        return json.dumps({"error": "Only SELECT, SHOW, DESCRIBE, and WITH queries are allowed"})

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchmany(100)
        result = [dict(zip(columns, r)) for r in rows]
        cursor.close()
        return json.dumps({
            "columns": columns,
            "row_count": len(result),
            "rows": result,
        }, indent=2, default=str)
    except Exception as e:
        cursor.close()
        return json.dumps({"error": str(e)})
