#!/usr/bin/env python3
"""
Medallion Architecture Advisor Agent
=====================================
An AI agent that reads your bronze (staging) layer data, suggests silver
(intermediate) and gold (marts) layer transformations, and generates dbt
models based on natural language feedback.

The agent uses Snowflake Cortex LLM functions — no external API keys needed.

Usage:
  # Interactive chat mode (default)
  python scripts/medallion_agent.py

  # Non-interactive: ask a single question
  python scripts/medallion_agent.py --ask "What silver models should I create for free_company_data?"

  # Specify Cortex model
  python scripts/medallion_agent.py --model llama3.1-70b

Requirements:
  pip install snowflake-connector-python pyyaml
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import snowflake.connector
except ImportError:
    print("snowflake-connector-python not installed. Run: pip install snowflake-connector-python")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"

# Default Cortex model — can be overridden via --model flag
DEFAULT_CORTEX_MODEL = "mistral-large2"


# ─── Name Resolution ─────────────────────────────────────────

def _get_all_model_names():
    """Build a lookup of all dbt model file stems across all layers."""
    names = []
    for layer in ["staging", "intermediate", "marts", "semantic"]:
        layer_dir = MODELS_DIR / layer
        if layer_dir.exists():
            for sql_file in layer_dir.rglob("*.sql"):
                names.append(sql_file.stem)
    return names


def _resolve_table_name(table_or_model):
    """Resolve a user/LLM-provided table name to the actual dbt model name.

    Handles these cases:
      - "japan_ecomm_data.MALL_MARKETS_YEARLY_REPORT"    -> strip prefix
      - "MALL_MARKETS_YEARLY_REPORT"                      -> find matching model
      - "stg_japan_ecomm_data__mall_markets_yearly_report" -> exact match
      - "STG_JAPAN_ECOMM_DATA__MALL_MARKETS_YEARLY_REPORT" -> lowercase match

    Returns the actual model name (lowercase, as on disk) that matches
    the Snowflake object name (uppercase).
    """
    # Normalize: strip whitespace
    name = table_or_model.strip()

    # Strip source directory prefix (e.g. "japan_ecomm_data.TABLE" -> "TABLE")
    if "." in name:
        name = name.rsplit(".", 1)[-1]

    all_models = _get_all_model_names()
    name_lower = name.lower()

    # 1) Exact match (case-insensitive)
    for m in all_models:
        if m.lower() == name_lower:
            return m

    # 2) Suffix match — the user said "MALL_MARKETS_YEARLY_REPORT" and the
    #    actual model is "stg_japan_ecomm_data__mall_markets_yearly_report"
    #    or "fct_mall_markets_yearly_report"
    suffix_matches = [m for m in all_models if m.lower().endswith(name_lower)]
    if len(suffix_matches) == 1:
        return suffix_matches[0]

    # 3) Contains match (partial table name)
    contains_matches = [m for m in all_models if name_lower in m.lower()]
    if len(contains_matches) == 1:
        return contains_matches[0]

    # 4) If multiple matches, prefer staging > marts > intermediate
    if suffix_matches:
        for prefix in ["stg_", "fct_", "dim_", "summary_", "int_"]:
            for m in suffix_matches:
                if m.startswith(prefix):
                    return m
        return suffix_matches[0]

    if contains_matches:
        return contains_matches[0]

    # 5) Fallback: return as-is (uppercase for Snowflake)
    return name


# ─── Snowflake Connection ────────────────────────────────────

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
            import yaml
            with open(profiles_path) as f:
                profiles = yaml.safe_load(f)
            for profile_name, profile in profiles.items():
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
    # Enable cross-region inference so Cortex models work regardless of region
    try:
        conn.cursor().execute("ALTER SESSION SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION'")
    except Exception:
        pass  # Parameter may not be available; admin can set at account level
    return conn


# ─── Agent Tools ────────────────────────────────────────────

def tool_list_sources(conn, source_name=None):
    """List dbt sources discovered in the project (reads _sources.yml files).
    If source_name is provided, only return that source."""
    import yaml
    sources = []
    staging_dir = MODELS_DIR / "staging"
    if not staging_dir.exists():
        return {"sources": [], "message": "No staging directory found"}

    for source_dir in sorted(staging_dir.iterdir()):
        if not source_dir.is_dir():
            continue
        if source_name and source_dir.name != source_name:
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
                })
    return {"sources": sources}


def tool_list_models(conn, layer="all", source_name=None):
    """List dbt models by layer (staging/intermediate/marts/all).
    If source_name is provided, only return models from that source subdirectory."""
    models = {"staging": [], "intermediate": [], "marts": []}

    for layer_name in models:
        layer_dir = MODELS_DIR / layer_name
        if layer_dir.exists():
            for source_dir in sorted(layer_dir.iterdir()):
                if source_dir.is_dir():
                    if source_name and source_dir.name != source_name:
                        continue
                    for f in sorted(source_dir.glob("*.sql")):
                        models[layer_name].append({
                            "name": f.stem,
                            "source": source_dir.name,
                            "path": str(f.relative_to(PROJECT_ROOT)),
                        })
                elif source_dir.suffix == ".sql" and not source_name:
                    models[layer_name].append({
                        "name": source_dir.stem,
                        "source": "root",
                        "path": str(source_dir.relative_to(PROJECT_ROOT)),
                    })

    if layer != "all":
        return {layer: models.get(layer, [])}
    return models


def tool_read_model(conn, model_name):
    """Read the SQL content of a dbt model by name."""
    model_name = _resolve_table_name(model_name)
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


def tool_sample_data(conn, table_or_model, limit=10):
    """Sample rows from a Snowflake table or dbt model output.

    Queries the built table in DBT_STAGING/DBT_MARTS schemas.
    """
    table_or_model = _resolve_table_name(table_or_model)
    cursor = conn.cursor()

    # Try marts first, then staging
    schemas_to_try = ["DBT_MARTS", "DBT_STAGING", "DBT_INTERMEDIATE"]
    for schema in schemas_to_try:
        try:
            cursor.execute(f'SELECT * FROM DBT_DEV.{schema}."{table_or_model}" LIMIT {int(limit)}')
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return {
                "table": table_or_model,
                "schema": schema,
                "columns": columns,
                "row_count": len(rows),
                "sample": [dict(zip(columns, row)) for row in rows],
            }
        except Exception:
            continue

    # Try with lowercase (dbt default naming)
    for schema in schemas_to_try:
        try:
            cursor.execute(f"SELECT * FROM DBT_DEV.{schema}.{table_or_model} LIMIT {int(limit)}")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return {
                "table": table_or_model,
                "schema": schema,
                "columns": columns,
                "row_count": len(rows),
                "sample": [dict(zip(columns, row)) for row in rows],
            }
        except Exception:
            continue

    cursor.close()
    return {"error": f"Table/model '{table_or_model}' not found in DBT_STAGING/DBT_MARTS/DBT_INTERMEDIATE"}


def tool_describe_table(conn, table_or_model):
    """Get column metadata + row count for a built dbt model."""
    table_or_model = _resolve_table_name(table_or_model)
    cursor = conn.cursor()

    schemas_to_try = ["DBT_MARTS", "DBT_STAGING", "DBT_INTERMEDIATE"]
    for schema in schemas_to_try:
        try:
            # Get columns
            cursor.execute(f"DESCRIBE TABLE DBT_DEV.{schema}.{table_or_model}")
            columns = []
            for row in cursor:
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[3] == "Y",
                })

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM DBT_DEV.{schema}.{table_or_model}")
            row_count = cursor.fetchone()[0]

            cursor.close()
            return {
                "table": table_or_model,
                "schema": schema,
                "columns": columns,
                "column_count": len(columns),
                "row_count": row_count,
            }
        except Exception:
            continue

    cursor.close()
    return {"error": f"Table/model '{table_or_model}' not found"}


def tool_profile_data(conn, table_or_model, max_columns=20):
    """Profile a table: distinct counts, null rates, min/max for numerics."""
    table_or_model = _resolve_table_name(table_or_model)
    desc = tool_describe_table(conn, table_or_model)
    if "error" in desc:
        return desc

    schema = desc["schema"]
    columns = desc["columns"][:max_columns]
    cursor = conn.cursor()

    parts = []
    for col in columns:
        col_name = col["name"]
        parts.append(f'COUNT(DISTINCT "{col_name}") AS "{col_name}_distinct"')
        parts.append(f'SUM(CASE WHEN "{col_name}" IS NULL THEN 1 ELSE 0 END) AS "{col_name}_nulls"')

    query = f'SELECT COUNT(*) AS total_rows, {", ".join(parts)} FROM DBT_DEV.{schema}.{table_or_model}'

    try:
        cursor.execute(query)
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
        null_pct = round(nulls / total * 100, 1) if total > 0 else 0
        profile.append({
            "column": col["name"],
            "type": col["type"],
            "distinct_values": distinct,
            "null_count": nulls,
            "null_pct": null_pct,
            "cardinality_ratio": round(distinct / total, 4) if total > 0 else 0,
        })

    return {
        "table": table_or_model,
        "total_rows": total,
        "profile": profile,
    }


def tool_run_query(conn, sql):
    """Execute a read-only SQL query and return results."""
    # Safety: only allow SELECT, SHOW, DESCRIBE, WITH
    normalized = sql.strip().upper()
    if not any(normalized.startswith(kw) for kw in ("SELECT", "SHOW", "DESCRIBE", "WITH")):
        return {"error": "Only SELECT/SHOW/DESCRIBE/WITH queries are allowed"}

    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchmany(100)  # Limit to 100 rows
        cursor.close()
        return {
            "columns": columns,
            "rows": [dict(zip(columns, row)) for row in rows],
            "row_count": len(rows),
        }
    except Exception as e:
        cursor.close()
        return {"error": str(e)}


def tool_generate_silver_model(conn, source_name, model_name, sql, description=""):
    """Write a silver (intermediate) layer dbt model to disk."""
    target_dir = MODELS_DIR / "intermediate" / source_name
    target_dir.mkdir(parents=True, exist_ok=True)

    # Write SQL file
    sql_path = target_dir / f"{model_name}.sql"
    sql_path.write_text(sql)

    # Write or update schema.yml
    schema_path = target_dir / "schema.yml"
    _upsert_model_in_schema_yml(schema_path, model_name, description or f"Intermediate model: {model_name}")

    return {
        "created": str(sql_path.relative_to(PROJECT_ROOT)),
        "schema": str(schema_path.relative_to(PROJECT_ROOT)),
        "model_name": model_name,
        "layer": "intermediate",
    }


def tool_generate_gold_model(conn, source_name, model_name, sql, description=""):
    """Write a gold (marts) layer dbt model to disk."""
    target_dir = MODELS_DIR / "marts" / source_name
    target_dir.mkdir(parents=True, exist_ok=True)

    sql_path = target_dir / f"{model_name}.sql"
    sql_path.write_text(sql)

    schema_path = target_dir / "schema.yml"
    _upsert_model_in_schema_yml(schema_path, model_name, description or f"Mart model: {model_name}")

    return {
        "created": str(sql_path.relative_to(PROJECT_ROOT)),
        "schema": str(schema_path.relative_to(PROJECT_ROOT)),
        "model_name": model_name,
        "layer": "marts",
    }


def tool_modify_model(conn, model_name, new_sql):
    """Update an existing model's SQL content."""
    for layer in ["staging", "intermediate", "marts", "semantic"]:
        layer_dir = MODELS_DIR / layer
        if layer_dir.exists():
            for sql_file in layer_dir.rglob(f"{model_name}.sql"):
                sql_file.write_text(new_sql)
                return {
                    "modified": str(sql_file.relative_to(PROJECT_ROOT)),
                    "model_name": model_name,
                }
    return {"error": f"Model '{model_name}' not found"}


def tool_run_dbt(conn, select, full_refresh=False):
    """Run dbt build for specific models and return the output."""
    import subprocess

    cmd = ["dbt", "build", "--select"] + select.split()
    if full_refresh:
        cmd.append("--full-refresh")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = result.stdout + result.stderr
        if len(output) > 4000:
            output = output[:4000] + "\n... (truncated)"
        return {
            "command": " ".join(cmd),
            "exit_code": result.returncode,
            "success": result.returncode == 0,
            "output": output,
        }
    except subprocess.TimeoutExpired:
        return {"error": "dbt command timed out after 300 seconds"}
    except FileNotFoundError:
        return {"error": "dbt CLI not found. Ensure dbt is installed and in PATH."}
    except Exception as e:
        return {"error": f"Failed to run dbt: {e}"}


def _upsert_model_in_schema_yml(schema_path, model_name, description):
    """Add or update a model entry in schema.yml."""
    import yaml

    if schema_path.exists():
        with open(schema_path) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {"version": 2, "models": []}

    if "models" not in data:
        data["models"] = []

    # Check if model already exists
    existing = next((m for m in data["models"] if m.get("name") == model_name), None)
    if existing:
        existing["description"] = description
    else:
        data["models"].append({"name": model_name, "description": description})

    with open(schema_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# ─── Tool Registry ──────────────────────────────────────────

TOOLS = {
    "list_sources": {
        "fn": tool_list_sources,
        "description": "List dbt source definitions (bronze layer). Returns source names, databases, schemas, and table lists. Use source_name to filter to a specific source.",
        "params": {"source_name": "string (optional — filter to a specific source, e.g. 'japan_ecomm_data')"},
    },
    "list_models": {
        "fn": tool_list_models,
        "description": "List dbt models by layer. Use source_name to filter to a specific source. layer can be 'staging', 'intermediate', 'marts', or 'all'.",
        "params": {"layer": "string (default: 'all')", "source_name": "string (optional — filter to a specific source)"},
    },
    "read_model": {
        "fn": tool_read_model,
        "description": "Read the SQL source code of a specific dbt model.",
        "params": {"model_name": "string — exact model file name without .sql"},
    },
    "sample_data": {
        "fn": tool_sample_data,
        "description": "Query sample rows from a built dbt model table in Snowflake.",
        "params": {"table_or_model": "string — model/table name", "limit": "int (default: 10)"},
    },
    "describe_table": {
        "fn": tool_describe_table,
        "description": "Get column metadata (names, types, nullability) and row count for a built model.",
        "params": {"table_or_model": "string — model/table name"},
    },
    "profile_data": {
        "fn": tool_profile_data,
        "description": "Profile a table: distinct value counts, null rates, cardinality ratios per column.",
        "params": {"table_or_model": "string", "max_columns": "int (default: 20)"},
    },
    "run_query": {
        "fn": tool_run_query,
        "description": "Execute a read-only SQL query (SELECT/SHOW/DESCRIBE) against Snowflake.",
        "params": {"sql": "string — SQL query"},
    },
    "generate_silver_model": {
        "fn": tool_generate_silver_model,
        "description": "Create a new intermediate (silver) layer dbt model. Writes .sql and updates schema.yml.",
        "params": {"source_name": "string", "model_name": "string (e.g. int_orders_enriched)", "sql": "string — full dbt SQL", "description": "string"},
    },
    "generate_gold_model": {
        "fn": tool_generate_gold_model,
        "description": "Create a new marts (gold) layer dbt model. Writes .sql and updates schema.yml.",
        "params": {"source_name": "string", "model_name": "string (e.g. fct_revenue)", "sql": "string — full dbt SQL", "description": "string"},
    },
    "modify_model": {
        "fn": tool_modify_model,
        "description": "Update an existing dbt model's SQL. Overwrites the .sql file.",
        "params": {"model_name": "string", "new_sql": "string — complete new SQL"},
    },
    "run_dbt": {
        "fn": tool_run_dbt,
        "description": "Run dbt build for specific models. Compiles, runs, and tests the model in Snowflake.",
        "params": {"select": "string — dbt selector (e.g. 'int_monthly_transactions_cleaned' or '+fct_revenue')", "full_refresh": "bool (default: false)"},
    },
}


# ─── Cortex LLM Integration ─────────────────────────────────

SYSTEM_PROMPT = """\
You are a Snowflake dbt expert agent specializing in medallion architecture.
You help users build and refine their data pipeline across three layers:

- **Bronze (staging)**: Source-conformed views — already auto-generated by discover_and_generate.py
- **Silver (intermediate)**: Cleaned, conformed, business-logic transforms — joins, deduplication, type casting, business rules
- **Gold (marts)**: Consumption-ready fact and dimension tables — aggregations, surrogate keys, final business metrics

You have access to tools to inspect the current project, query actual data, and generate new models.

## TOOL CALLING FORMAT

When you need to use a tool, respond with EXACTLY this format (one tool per block):
```tool
TOOL_NAME(param1="value1", param2="value2")
```

Available tools:
{tool_descriptions}

## CONVENTIONS

- Staging models: `stg_<source>__<table>` (auto-generated, do NOT modify)
- Silver models: `int_<description>` (e.g., `int_orders_enriched`, `int_companies_deduped`)
- Gold models: `fct_<entity>` (facts) or `dim_<entity>` (dimensions)
- Always use `{{{{ ref('model_name') }}}}` to reference other models
- Always use `{{{{ source('source_name', 'TABLE_NAME') }}}}` to reference raw data
- Use CTEs (WITH blocks), not subqueries
- Never hardcode database/schema names
- Use `dbt_utils.generate_surrogate_key()` for surrogate keys
- Use Snowflake-native date functions: DATE_TRUNC, DATEADD, DATEDIFF

## WORKFLOW

1. First, explore what's available: list sources, list models, describe tables
2. Sample actual data to understand the content
3. Profile columns to find patterns, nulls, cardinality
4. Suggest silver/gold models with clear explanations
5. When the user approves, generate the model using generate_silver_model or generate_gold_model
6. After generating, AUTOMATICALLY run `run_dbt(select="model_name")` for each generated model — do NOT ask the user to run dbt manually
7. Report the build results (pass/fail) to the user

## IMPORTANT: FILTERING

When the user mentions or asks about a specific source (e.g. "japan_ecomm_data"), ALWAYS pass `source_name` to `list_sources` and `list_models` to avoid returning unrelated data. Only omit source_name when the user explicitly asks to see ALL sources.

Always explain your reasoning before generating code. Ask clarifying questions if the user's intent is ambiguous.
"""


def build_tool_descriptions():
    """Build a formatted string of all tool descriptions for the system prompt."""
    lines = []
    for name, info in TOOLS.items():
        params = ", ".join(f'{k}={v}' for k, v in info["params"].items())
        lines.append(f"- `{name}({params})` — {info['description']}")
    return "\n".join(lines)


def call_cortex(conn, messages, model=DEFAULT_CORTEX_MODEL):
    """Call Snowflake Cortex COMPLETE with a list of messages."""
    cursor = conn.cursor()
    messages_json = json.dumps(messages)
    try:
        cursor.execute(
            "SELECT SNOWFLAKE.CORTEX.COMPLETE(%s, %s)",
            (model, messages_json),
        )
        result = cursor.fetchone()[0]
        cursor.close()

        # Cortex may return a JSON object with a "choices" key
        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict):
                if "choices" in parsed:
                    return parsed["choices"][0].get("messages", parsed["choices"][0].get("message", {}).get("content", result))
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
    """Extract tool calls from the LLM response.

    Looks for:
    ```tool
    TOOL_NAME(param1="value1", param2="value2")
    ```

    Handles multi-line SQL params with triple-quoted strings and
    parentheses inside string values.
    """
    # Step 1: Extract the content of each ```tool ... ``` block
    block_pattern = r'```tool\s*\n(.*?)\n\s*```'
    blocks = re.findall(block_pattern, response_text, re.DOTALL)

    calls = []
    for block in blocks:
        block = block.strip()
        # Step 2: Split TOOL_NAME( ... ) using first '(' and last ')'
        paren_idx = block.find('(')
        if paren_idx == -1:
            continue
        tool_name = block[:paren_idx].strip()
        last_paren = block.rfind(')')
        if last_paren <= paren_idx:
            continue
        params_str = block[paren_idx + 1:last_paren]

        # Step 3: Parse key=value params
        # Supports triple-quoted strings ("""...""", '''...'''),
        # regular quoted strings, and bare integers.
        params = {}
        param_pattern = (
            r'(\w+)\s*=\s*(?:'
            r'"""(.*?)"""|'           # group 2: triple double-quoted
            r"'''(.*?)'''|"              # group 3: triple single-quoted
            r'"((?:[^"\\]|\\.)*)"|'  # group 4: double-quoted
            r"'((?:[^'\\]|\\.)*)'|"  # group 5: single-quoted
            r'(\d+)'                     # group 6: bare integer
            r')'
        )
        for m in re.finditer(param_pattern, params_str, re.DOTALL):
            key = m.group(1)
            # Pick first non-None capture group (2-6)
            str_value = next(
                (g for g in (m.group(2), m.group(3), m.group(4), m.group(5)) if g is not None),
                None,
            )
            if str_value is not None:
                value = str_value.strip()
                value = value.replace('\\n', '\n').replace('\\t', '\t')
                value = value.replace('\\"', '"').replace("\\'", "'")
            elif m.group(6) is not None:
                value = int(m.group(6))
            else:
                continue
            params[key] = value
        calls.append((tool_name, params))

    return calls


def execute_tool(conn, tool_name, params):
    """Execute a named tool with the given parameters."""
    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}

    fn = TOOLS[tool_name]["fn"]
    try:
        return fn(conn, **params)
    except TypeError as e:
        return {"error": f"Invalid parameters for {tool_name}: {e}"}
    except Exception as e:
        return {"error": f"Tool execution failed: {e}"}


def _auto_build_generated_models(conn, executed_calls):
    """After a round of tool calls, auto-run dbt build for any newly generated models.

    Args:
        conn: Snowflake connection
        executed_calls: list of (tool_name, result_dict) from the round
    Returns:
        list of build result strings for feedback
    """
    generated = []
    for tool_name, result in executed_calls:
        if tool_name in ("generate_silver_model", "generate_gold_model") and "created" in result:
            generated.append(result["model_name"])

    if not generated:
        return []

    build_results = []
    # Build all generated models in one dbt command (dbt resolves dependency order)
    selector = " ".join(generated)
    print(f"\n  [Auto-building {len(generated)} model(s): {selector}...]")
    build_result = tool_run_dbt(conn, select=selector)
    if build_result.get("success"):
        print(f"  [Build PASSED \u2714]")
    else:
        print(f"  [Build FAILED \u2718 — see output below]")
        output = build_result.get("output", build_result.get("error", ""))
        # Print last 30 lines of output for visibility
        lines = output.strip().splitlines()
        for line in lines[-30:]:
            print(f"    {line}")
    build_results.append(f"Auto-build result for [{selector}]:\n{json.dumps(build_result, indent=2, default=str)}")
    return build_results


# ─── Agent Loop ──────────────────────────────────────────────

def run_agent(conn, model=DEFAULT_CORTEX_MODEL, initial_question=None):
    """Run the interactive agent loop."""
    tool_descs = build_tool_descriptions()
    system_prompt = SYSTEM_PROMPT.format(tool_descriptions=tool_descs)

    messages = [{"role": "system", "content": system_prompt}]

    print("\n" + "=" * 60)
    print("  Medallion Architecture Advisor")
    print("  Powered by Snowflake Cortex")
    print("=" * 60)
    print("\nI can help you build silver (intermediate) and gold (marts)")
    print("layer models from your existing bronze (staging) data.")
    print("\nExamples:")
    print('  "What sources do I have?"')
    print('  "Show me sample data from the free_company_data staging table"')
    print('  "Suggest silver layer models for japan_ecomm_data"')
    print('  "Create a dimension table for countries from free_company_data"')
    print('\nType "quit" or "exit" to end.\n')

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

        # Call Cortex
        response = call_cortex(conn, messages, model)

        # Check for tool calls in the response
        tool_calls = parse_tool_calls(response)

        if tool_calls:
            # Execute tools and feed results back
            # Print the text before tool calls
            clean_response = re.sub(r'```tool\s*\n.*?\n\s*```', '', response, flags=re.DOTALL).strip()
            if clean_response:
                print(f"Agent: {clean_response}\n")

            tool_results = []
            executed_calls = []  # (tool_name, raw_result_dict)
            for tool_name, params in tool_calls:
                print(f"  [Calling {tool_name}...]")
                result = execute_tool(conn, tool_name, params)
                executed_calls.append((tool_name, result))
                # Truncate large results for LLM context
                result_str = json.dumps(result, indent=2, default=str)
                if len(result_str) > 8000:
                    result_str = result_str[:8000] + "\n... (truncated)"
                tool_results.append(f"Tool {tool_name} returned:\n{result_str}")
                # Also print a summary for the user
                if "error" in result:
                    print(f"  [Error: {result['error']}]")
                elif "created" in result:
                    print(f"  [Created: {result['created']}]")
                elif "modified" in result:
                    print(f"  [Modified: {result['modified']}]")
                else:
                    print(f"  [Done]")

            # Auto-build any models generated in this round
            build_feedback = _auto_build_generated_models(conn, executed_calls)
            tool_results.extend(build_feedback)

            # Feed tool results back to LLM for interpretation
            messages.append({"role": "assistant", "content": response})
            tool_context = "\n\n".join(tool_results)
            messages.append({"role": "user", "content": f"Tool results:\n{tool_context}\n\nPlease interpret these results and continue helping the user."})

            # Loop: keep calling Cortex until it responds without tool calls
            MAX_TOOL_ROUNDS = 10
            for _round in range(MAX_TOOL_ROUNDS):
                follow_up = call_cortex(conn, messages, model)
                next_tool_calls = parse_tool_calls(follow_up)

                if not next_tool_calls:
                    # No more tool calls — print final answer
                    print(f"\nAgent: {follow_up}\n")
                    messages.append({"role": "assistant", "content": follow_up})
                    break

                # More tool calls — execute them and feed back
                clean_follow = re.sub(r'```tool\s*\n.*?\n\s*```', '', follow_up, flags=re.DOTALL).strip()
                if clean_follow:
                    print(f"\nAgent: {clean_follow}\n")

                tool_results = []
                executed_calls = []
                for t_name, t_params in next_tool_calls:
                    print(f"  [Calling {t_name}...]")
                    result = execute_tool(conn, t_name, t_params)
                    executed_calls.append((t_name, result))
                    result_str = json.dumps(result, indent=2, default=str)
                    if len(result_str) > 8000:
                        result_str = result_str[:8000] + "\n... (truncated)"
                    tool_results.append(f"Tool {t_name} returned:\n{result_str}")
                    if "error" in result:
                        print(f"  [Error: {result['error']}]")
                    elif "created" in result:
                        print(f"  [Created: {result['created']}]")
                    elif "modified" in result:
                        print(f"  [Modified: {result['modified']}]")
                    else:
                        print(f"  [Done]")

                # Auto-build any models generated in this round
                build_feedback = _auto_build_generated_models(conn, executed_calls)
                tool_results.extend(build_feedback)

                messages.append({"role": "assistant", "content": follow_up})
                tool_context = "\n\n".join(tool_results)
                messages.append({"role": "user", "content": f"Tool results:\n{tool_context}\n\nPlease interpret these results and continue helping the user."})
        else:
            print(f"Agent: {response}\n")
            messages.append({"role": "assistant", "content": response})

        # Keep conversation history manageable (last 20 messages + system)
        if len(messages) > 21:
            messages = [messages[0]] + messages[-20:]

        user_input = input("You: ").strip()

    print("\nGoodbye!")


# ─── CLI Entry Point ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Medallion Architecture Advisor Agent")
    parser.add_argument("--model", default=DEFAULT_CORTEX_MODEL,
                        help=f"Cortex LLM model (default: {DEFAULT_CORTEX_MODEL})")
    parser.add_argument("--ask", help="Ask a single question (non-interactive mode)")
    args = parser.parse_args()

    conn = get_connection()

    if args.ask:
        run_agent(conn, model=args.model, initial_question=args.ask)
    else:
        run_agent(conn, model=args.model)

    conn.close()


if __name__ == "__main__":
    main()
