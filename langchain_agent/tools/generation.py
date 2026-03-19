"""Code generation tools — create/modify staging, intermediate, and mart dbt models.

Ported from scripts/medallion_agent.py and snowflake-dbt-mcp/server.py.
"""

import json
from pathlib import Path
from typing import Optional

import yaml
from langchain_core.tools import tool

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


def _upsert_model_in_schema_yml(schema_path: Path, model_name: str, description: str):
    """Add or update a model entry in a schema.yml file."""
    if schema_path.exists():
        data = yaml.safe_load(schema_path.read_text()) or {}
    else:
        data = {"version": 2, "models": []}

    if "models" not in data:
        data["models"] = []

    existing = next((m for m in data["models"] if m.get("name") == model_name), None)
    if existing:
        existing["description"] = description
    else:
        data["models"].append({"name": model_name, "description": description})

    schema_path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))


@tool
def generate_silver_model(
    source_name: str,
    model_name: str,
    sql: str,
    description: str = "",
) -> str:
    """Write a silver (intermediate) layer dbt model to disk.

    Args:
        source_name: Source subdirectory (e.g. 'japan_ecomm_data').
        model_name: Model name without .sql (e.g. 'int_orders_enriched').
        sql: Complete dbt SQL for the model.
        description: Model description for schema.yml.
    """
    out_dir = MODELS_DIR / "intermediate" / source_name
    out_dir.mkdir(parents=True, exist_ok=True)

    sql_path = out_dir / f"{model_name}.sql"
    sql_path.write_text(sql)

    schema_path = out_dir / "schema.yml"
    _upsert_model_in_schema_yml(schema_path, model_name, description or f"Intermediate model: {model_name}")

    return json.dumps({
        "created": str(sql_path.relative_to(PROJECT_ROOT)),
        "schema": str(schema_path.relative_to(PROJECT_ROOT)),
        "model_name": model_name,
    })


@tool
def generate_gold_model(
    source_name: str,
    model_name: str,
    sql: str,
    description: str = "",
) -> str:
    """Write a gold (marts) layer dbt model to disk.

    Args:
        source_name: Source subdirectory (e.g. 'japan_ecomm_data').
        model_name: Model name without .sql (e.g. 'fct_orders' or 'dim_customers').
        sql: Complete dbt SQL for the model.
        description: Model description for schema.yml.
    """
    out_dir = MODELS_DIR / "marts" / source_name
    out_dir.mkdir(parents=True, exist_ok=True)

    sql_path = out_dir / f"{model_name}.sql"
    sql_path.write_text(sql)

    schema_path = out_dir / "schema.yml"
    _upsert_model_in_schema_yml(schema_path, model_name, description or f"Mart model: {model_name}")

    return json.dumps({
        "created": str(sql_path.relative_to(PROJECT_ROOT)),
        "schema": str(schema_path.relative_to(PROJECT_ROOT)),
        "model_name": model_name,
    })


@tool
def modify_model(model_name: str, new_sql: str) -> str:
    """Update an existing dbt model's SQL on disk.

    Args:
        model_name: Model name without .sql extension.
        new_sql: The new/updated SQL for the model.
    """
    from langchain_agent.tools.exploration import _find_model_path, _resolve_table_name

    resolved = _resolve_table_name(model_name)
    path = _find_model_path(resolved)
    if path is None:
        return json.dumps({"error": f"Model '{model_name}' not found on disk"})

    path.write_text(new_sql)
    return json.dumps({
        "modified": str(path.relative_to(PROJECT_ROOT)),
        "model_name": resolved,
    })


@tool
def generate_staging_model(
    source_name: str,
    table_name: str,
    columns: list[dict],
    description: str = "",
) -> str:
    """Scaffold a staging model + schema entry from a source table definition.

    Args:
        source_name: dbt source name (e.g. 'japan_ecomm_data').
        table_name: Raw table name in Snowflake.
        columns: List of column dicts with 'name' and 'type' keys.
        description: Optional model description.
    """
    model_name = f"stg_{source_name}__{table_name.lower()}"

    # Generate SQL
    col_lines = []
    for col in columns:
        col_lines.append(f"        {col['name'].lower()}")
    cols_str = ",\n".join(col_lines)

    sql = (
        f"with source as (\n"
        f"    select * from {{{{ source('{source_name}', '{table_name}') }}}}\n"
        f"),\n\n"
        f"renamed as (\n"
        f"    select\n"
        f"{cols_str}\n"
        f"    from source\n"
        f")\n\n"
        f"select * from renamed\n"
    )

    out_dir = MODELS_DIR / "staging" / source_name
    out_dir.mkdir(parents=True, exist_ok=True)

    sql_path = out_dir / f"{model_name}.sql"
    sql_path.write_text(sql)

    # Generate schema entry
    schema_path = out_dir / "schema.yml"
    _upsert_model_in_schema_yml(
        schema_path,
        model_name,
        description or f"Staged {table_name.lower()} from {source_name} — renamed columns, 1:1 with source",
    )

    return json.dumps({
        "created": str(sql_path.relative_to(PROJECT_ROOT)),
        "schema": str(schema_path.relative_to(PROJECT_ROOT)),
        "model_name": model_name,
    })
