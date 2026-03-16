"""
Snowflake dbt MCP Server — LOCAL FALLBACK
==========================================
This is the LOCAL stdio-based MCP server for offline/development use.

For production, use the Snowflake Managed MCP Server instead.
See: snowflake-dbt-mcp/setup/ for Snowflake-native setup scripts.

To switch between local and managed:
  - Managed: Set "streamableHttp" in .vscode/mcp.json (default)
  - Local:   Set "stdio" in .vscode/mcp.json (see commented section)

Tools:
  - generate_dbt_model: Scaffold staging model + schema YAML from a source table
  - generate_semantic_view: Produce Semantic View DDL + YAML from a mart model
  - run_dbt_command: Execute dbt CLI commands with scoped selectors
  - review_sql: Static analysis of SQL models for best practices
  - check_data_quality: Run dbt tests and return pass/fail summary
  - generate_streamlit_app: Scaffold Streamlit-in-Snowflake app from a model

Run:
  python server.py
  # or: uvx mcp run snowflake-dbt-mcp/server.py
"""

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.server.stdio import run_stdio
    from mcp.types import TextContent, Tool
except ImportError:
    print("MCP SDK not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("snowflake-dbt-mcp")

# ---------------------------------------------------------------------------
# Determine project root (parent of snowflake-dbt-mcp/)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------
server = Server("snowflake-dbt-mcp")


# ===== Tool: generate_dbt_model ===========================================

def _generate_staging_sql(source_name: str, table_name: str, columns: list[str]) -> str:
    """Generate a staging model SQL file from source metadata."""
    col_renames = []
    for col in columns:
        clean = col.lower().strip()
        col_renames.append(f"        {col.lower()} as {clean}")

    cols_str = ",\n".join(col_renames)
    return f"""with source as (
    select * from {{{{ source('{source_name}', '{table_name}') }}}}
),

renamed as (
    select
{cols_str}
    from source
)

select * from renamed
"""


def _generate_schema_yml(model_name: str, columns: list[str], source_desc: str = "") -> str:
    """Generate schema.yml entry for a staging model."""
    col_entries = []
    for col in columns:
        clean = col.lower().strip()
        col_entries.append(f"      - name: {clean}\n        description: \"\"")

    cols_yaml = "\n".join(col_entries)
    return f"""version: 2

models:
  - name: {model_name}
    description: "{source_desc or f'Staged {model_name}'}"
    columns:
{cols_yaml}
"""


# ===== Tool: generate_semantic_view ========================================

def _generate_semantic_view_ddl(model_name: str, dimensions: list[dict], metrics: list[dict]) -> str:
    """Generate Snowflake Semantic View DDL."""
    dim_lines = []
    for d in dimensions:
        comment = d.get("description", "")
        dim_lines.append(f"    {d['name']} AS DIMENSION COMMENT '{comment}'")

    metric_lines = []
    for m in metrics:
        agg = m.get("type", "SUM").upper()
        expr = m.get("expression", m["name"])
        comment = m.get("description", "")
        metric_lines.append(f"    {m['name']} AS {agg}({expr}) COMMENT '{comment}'")

    dims = ",\n".join(dim_lines)
    mets = ",\n".join(metric_lines)

    return f"""CREATE OR REPLACE SEMANTIC VIEW {{{{target.database}}}}.{{{{target.schema}}}}.{model_name.upper()}
  COMMENT = 'Auto-generated semantic view for {model_name}'
AS SELECT * FROM {{{{ref('{model_name}')}}}}
COLUMNS (
{dims}
)
METRICS (
{mets}
);
"""


# ===== Tool: review_sql ===================================================

_SQL_REVIEW_RULES = [
    {
        "id": "NO_SELECT_STAR_MARTS",
        "pattern": r"select\s+\*(?!.*\bfrom\b.*\bcte\b)",
        "message": "Avoid SELECT * in marts/semantic models — explicitly list columns",
        "severity": "warning",
        "applies_to": ["marts", "semantic"],
    },
    {
        "id": "HARDCODED_SCHEMA",
        "pattern": r"(?:from|join)\s+\w+\.\w+\.\w+",
        "message": "Hard-coded database.schema.table detected — use {{ source() }} or {{ ref() }}",
        "severity": "error",
    },
    {
        "id": "MISSING_REF",
        "pattern": r"(?:from|join)\s+(?!.*\{\{)(\w+)\s",
        "message": "Possible direct table reference without {{ ref() }} or {{ source() }}",
        "severity": "warning",
    },
    {
        "id": "NO_LIMIT",
        "pattern": r"\bLIMIT\s+\d+",
        "message": "LIMIT clause found — usually shouldn't be in production models",
        "severity": "info",
    },
    {
        "id": "NAMING_STG",
        "pattern": r"",  # checked programmatically
        "message": "Staging model should follow stg_<source>__<table> naming",
        "severity": "warning",
    },
]


def _review_sql(sql_content: str, file_path: str = "") -> list[dict]:
    """Run static analysis rules against SQL content."""
    issues = []
    lines = sql_content.split("\n")

    for rule in _SQL_REVIEW_RULES:
        if rule["id"] == "NAMING_STG":
            # Check naming convention for staging files
            if "staging" in file_path and not Path(file_path).stem.startswith("stg_"):
                issues.append({
                    "rule": rule["id"],
                    "severity": rule["severity"],
                    "message": rule["message"],
                    "line": 0,
                })
            continue

        if rule.get("applies_to"):
            if not any(layer in file_path for layer in rule["applies_to"]):
                continue

        pattern = rule["pattern"]
        if not pattern:
            continue

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("--") or stripped.startswith("{#"):
                continue
            if re.search(pattern, line, re.IGNORECASE):
                issues.append({
                    "rule": rule["id"],
                    "severity": rule["severity"],
                    "message": rule["message"],
                    "line": i,
                    "content": line.strip()[:120],
                })

    # Check for missing tests (heuristic: no schema.yml sibling)
    if file_path:
        model_dir = Path(file_path).parent
        schema_file = model_dir / "schema.yml"
        if not schema_file.exists():
            issues.append({
                "rule": "MISSING_SCHEMA_YML",
                "severity": "warning",
                "message": f"No schema.yml found in {model_dir.name}/ — models lack test definitions",
                "line": 0,
            })

    return issues


# ===== Tool: generate_streamlit_app ========================================

def _generate_streamlit_app(model_name: str, app_title: str = "") -> str:
    """Generate a Streamlit-in-Snowflake app template."""
    title = app_title or f"{model_name.replace('_', ' ').title()} Dashboard"
    return f'''"""
{title}
Auto-generated Streamlit-in-Snowflake app for {model_name}
"""
import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="{title}", layout="wide")
st.title("{title}")

session = get_active_session()

# --- Sidebar filters ---
st.sidebar.header("Filters")

# Load data
@st.cache_data(ttl=600)
def load_data():
    return session.table("{model_name.upper()}").to_pandas()

df = load_data()

# Dynamic filters based on string columns
string_cols = df.select_dtypes(include=["object"]).columns.tolist()
filters = {{}}
for col in string_cols[:5]:  # Limit to first 5 string columns
    unique_vals = sorted(df[col].dropna().unique().tolist())
    selected = st.sidebar.multiselect(col.replace("_", " ").title(), unique_vals)
    if selected:
        filters[col] = selected

# Apply filters
filtered_df = df.copy()
for col, vals in filters.items():
    filtered_df = filtered_df[filtered_df[col].isin(vals)]

# --- KPI Cards ---
st.subheader("Key Metrics")
col1, col2, col3, col4 = st.columns(4)

numeric_cols = filtered_df.select_dtypes(include=["number"]).columns.tolist()
if len(numeric_cols) >= 1:
    col1.metric("Total Records", f"{{len(filtered_df):,}}")
if len(numeric_cols) >= 2:
    col2.metric(numeric_cols[0].replace("_", " ").title(), f"{{filtered_df[numeric_cols[0]].sum():,.2f}}")
if len(numeric_cols) >= 3:
    col3.metric(numeric_cols[1].replace("_", " ").title(), f"{{filtered_df[numeric_cols[1]].sum():,.2f}}")
if len(numeric_cols) >= 4:
    col4.metric(numeric_cols[2].replace("_", " ").title(), f"{{filtered_df[numeric_cols[2]].mean():,.2f}}")

# --- Charts ---
st.subheader("Data Explorer")

date_cols = filtered_df.select_dtypes(include=["datetime64"]).columns.tolist()
if date_cols:
    chart_date = st.selectbox("Date column", date_cols)
    chart_metric = st.selectbox("Metric", numeric_cols)
    if chart_date and chart_metric:
        chart_data = filtered_df.groupby(chart_date)[chart_metric].sum().reset_index()
        st.line_chart(chart_data, x=chart_date, y=chart_metric)

# --- Data Table ---
st.subheader("Raw Data")
st.dataframe(filtered_df.head(1000), use_container_width=True)

# --- Cortex AI Chat ---
st.subheader("Ask a Question (Cortex AI)")
user_question = st.text_input("Ask about this data:")
if user_question:
    prompt = f"""You are a data analyst. Answer the following question about the {{model_name}} dataset.
Available columns: {{', '.join(df.columns.tolist())}}
Sample data (first 5 rows): {{df.head().to_string()}}

Question: {{user_question}}"""

    try:
        result = session.sql(
            "SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', ?)",
            params=[prompt]
        ).collect()
        st.write(result[0][0])
    except Exception as e:
        st.error(f"Cortex call failed: {{e}}")
'''


# ===== MCP Tool Definitions ================================================

# ===== Medallion Advisor Helpers =============================================

def _list_models_by_layer(layer: str = "all") -> dict:
    """List dbt model files organized by medallion layer."""
    models_dir = PROJECT_ROOT / "models"
    result = {}
    layers = ["staging", "intermediate", "marts"] if layer == "all" else [layer]

    for l in layers:
        layer_dir = models_dir / l
        layer_models = []
        if layer_dir.exists():
            for source_dir in sorted(layer_dir.iterdir()):
                if source_dir.is_dir():
                    for f in sorted(source_dir.glob("*.sql")):
                        layer_models.append({
                            "name": f.stem,
                            "source": source_dir.name,
                            "path": str(f.relative_to(PROJECT_ROOT)),
                        })
                elif source_dir.suffix == ".sql":
                    layer_models.append({"name": source_dir.stem, "source": "root", "path": str(source_dir.relative_to(PROJECT_ROOT))})
        result[l] = layer_models
    return result


def _read_model_sql(model_name: str) -> dict:
    """Read the SQL of a dbt model file."""
    models_dir = PROJECT_ROOT / "models"
    for layer in ["staging", "intermediate", "marts", "semantic"]:
        layer_dir = models_dir / layer
        if layer_dir.exists():
            for sql_file in layer_dir.rglob(f"{model_name}.sql"):
                return {
                    "model": model_name,
                    "layer": layer,
                    "path": str(sql_file.relative_to(PROJECT_ROOT)),
                    "sql": sql_file.read_text(),
                }
    return {"error": f"Model '{model_name}' not found"}


def _write_model(layer: str, source_name: str, model_name: str, sql: str, description: str = "") -> dict:
    """Write a dbt model SQL file and update schema.yml."""
    import yaml as _yaml

    target_dir = PROJECT_ROOT / "models" / layer / source_name
    target_dir.mkdir(parents=True, exist_ok=True)

    sql_path = target_dir / f"{model_name}.sql"
    sql_path.write_text(sql)

    schema_path = target_dir / "schema.yml"
    if schema_path.exists():
        with open(schema_path) as f:
            data = _yaml.safe_load(f) or {}
    else:
        data = {"version": 2, "models": []}
    if "models" not in data:
        data["models"] = []
    existing = next((m for m in data["models"] if m.get("name") == model_name), None)
    if existing:
        existing["description"] = description or f"Generated {layer} model"
    else:
        data["models"].append({"name": model_name, "description": description or f"Generated {layer} model"})
    with open(schema_path, "w") as f:
        _yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    return {
        "created": str(sql_path.relative_to(PROJECT_ROOT)),
        "schema": str(schema_path.relative_to(PROJECT_ROOT)),
    }


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="generate_dbt_model",
            description="Generate a dbt staging model SQL + schema.yml entry from a source table name and columns",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_name": {
                        "type": "string",
                        "description": "dbt source name (e.g., 'tpch')",
                    },
                    "table_name": {
                        "type": "string",
                        "description": "Source table name (e.g., 'ORDERS')",
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of column names from the source table",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional model description",
                        "default": "",
                    },
                },
                "required": ["source_name", "table_name", "columns"],
            },
        ),
        Tool(
            name="generate_semantic_view",
            description="Generate Snowflake Semantic View DDL + dbt YAML from a mart model",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "description": "Name of the dbt mart model to create a semantic view for",
                    },
                    "dimensions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string", "default": ""},
                            },
                            "required": ["name"],
                        },
                        "description": "Dimension columns",
                    },
                    "metrics": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string", "default": "SUM"},
                                "expression": {"type": "string"},
                                "description": {"type": "string", "default": ""},
                            },
                            "required": ["name", "expression"],
                        },
                        "description": "Metric definitions",
                    },
                },
                "required": ["model_name", "dimensions", "metrics"],
            },
        ),
        Tool(
            name="run_dbt_command",
            description="Execute a dbt CLI command (run, test, build, compile, ls) with optional selector",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": ["run", "test", "build", "compile", "ls", "debug", "deps"],
                        "description": "dbt command to execute",
                    },
                    "select": {
                        "type": "string",
                        "description": "dbt node selector (e.g., 'stg_tpch__orders+', 'tag:staging')",
                        "default": "",
                    },
                    "full_refresh": {
                        "type": "boolean",
                        "description": "Run with --full-refresh flag",
                        "default": False,
                    },
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="review_sql",
            description="Static analysis of a SQL model — checks naming, ref usage, hard-coded values, missing tests",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql_content": {
                        "type": "string",
                        "description": "SQL content to review",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to the SQL file (for context-aware rules)",
                        "default": "",
                    },
                },
                "required": ["sql_content"],
            },
        ),
        Tool(
            name="check_data_quality",
            description="Run dbt tests and return pass/fail summary, optionally scoped to specific models",
            inputSchema={
                "type": "object",
                "properties": {
                    "select": {
                        "type": "string",
                        "description": "dbt selector to scope tests (e.g., 'fct_orders', 'tag:marts')",
                        "default": "",
                    },
                },
            },
        ),
        Tool(
            name="generate_streamlit_app",
            description="Scaffold a Streamlit-in-Snowflake app from a mart or semantic model",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "description": "dbt model name to build the app for",
                    },
                    "app_title": {
                        "type": "string",
                        "description": "Title for the Streamlit app",
                        "default": "",
                    },
                },
                "required": ["model_name"],
            },
        ),
        # ── Medallion Advisor Tools ──
        Tool(
            name="list_medallion_models",
            description="List dbt models by medallion layer: 'staging' (bronze), 'intermediate' (silver), 'marts' (gold), or 'all'",
            inputSchema={
                "type": "object",
                "properties": {
                    "layer": {
                        "type": "string",
                        "enum": ["all", "staging", "intermediate", "marts"],
                        "description": "Medallion layer to list",
                        "default": "all",
                    },
                },
            },
        ),
        Tool(
            name="read_model_sql",
            description="Read the SQL source code of a specific dbt model by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "description": "Exact model name without .sql extension",
                    },
                },
                "required": ["model_name"],
            },
        ),
        Tool(
            name="suggest_silver_model",
            description="Suggest a silver (intermediate) dbt model with SQL given a source model and business description",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_models": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of staging model names to base the silver model on",
                    },
                    "description": {
                        "type": "string",
                        "description": "Natural language description of the desired transformation",
                    },
                },
                "required": ["source_models", "description"],
            },
        ),
        Tool(
            name="suggest_gold_model",
            description="Suggest a gold (marts) dbt model — fact or dimension — with SQL",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_models": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of model names (staging or intermediate) to base the gold model on",
                    },
                    "model_type": {
                        "type": "string",
                        "enum": ["fact", "dimension"],
                        "description": "Whether this is a fact table (fct_) or dimension table (dim_)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Natural language description of the desired mart",
                    },
                },
                "required": ["source_models", "model_type", "description"],
            },
        ),
        Tool(
            name="write_medallion_model",
            description="Write a generated silver or gold layer dbt model to disk",
            inputSchema={
                "type": "object",
                "properties": {
                    "layer": {
                        "type": "string",
                        "enum": ["intermediate", "marts"],
                        "description": "Target layer — intermediate (silver) or marts (gold)",
                    },
                    "source_name": {
                        "type": "string",
                        "description": "Source subdirectory name (e.g., 'free_company_data')",
                    },
                    "model_name": {
                        "type": "string",
                        "description": "Model name (e.g., 'int_orders_enriched' or 'fct_revenue')",
                    },
                    "sql": {
                        "type": "string",
                        "description": "Complete dbt SQL for the model",
                    },
                    "description": {
                        "type": "string",
                        "description": "Model description for schema.yml",
                        "default": "",
                    },
                },
                "required": ["layer", "source_name", "model_name", "sql"],
            },
        ),
    ]


# ===== Tool Handlers ========================================================

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "generate_dbt_model":
        source_name = arguments["source_name"]
        table_name = arguments["table_name"]
        columns = arguments["columns"]
        description = arguments.get("description", "")

        model_name = f"stg_{source_name}__{table_name.lower()}"
        sql = _generate_staging_sql(source_name, table_name, columns)
        schema = _generate_schema_yml(model_name, columns, description)

        return [TextContent(
            type="text",
            text=f"## Generated: {model_name}\n\n"
                 f"### SQL (`models/staging/{model_name}.sql`)\n```sql\n{sql}\n```\n\n"
                 f"### Schema YAML (add to `models/staging/schema.yml`)\n```yaml\n{schema}\n```",
        )]

    elif name == "generate_semantic_view":
        model_name = arguments["model_name"]
        dimensions = arguments["dimensions"]
        metrics = arguments["metrics"]

        ddl = _generate_semantic_view_ddl(model_name, dimensions, metrics)
        return [TextContent(
            type="text",
            text=f"## Semantic View DDL for {model_name}\n\n```sql\n{ddl}\n```",
        )]

    elif name == "run_dbt_command":
        command = arguments["command"]
        select = arguments.get("select", "")
        full_refresh = arguments.get("full_refresh", False)

        # Whitelist allowed commands
        allowed = {"run", "test", "build", "compile", "ls", "debug", "deps"}
        if command not in allowed:
            return [TextContent(type="text", text=f"Error: command '{command}' not allowed")]

        cmd = ["dbt", command]
        if select:
            # Sanitize selector to prevent injection
            safe_select = re.sub(r'[^a-zA-Z0-9_+:.\-*/]', '', select)
            cmd.extend(["--select", safe_select])
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
            output = result.stdout + ("\n" + result.stderr if result.stderr else "")
            status = "SUCCESS" if result.returncode == 0 else "FAILED"
            return [TextContent(type="text", text=f"## dbt {command} — {status}\n\n```\n{output[:5000]}\n```")]
        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text=f"## dbt {command} — TIMEOUT\n\nCommand exceeded 300s limit")]
        except FileNotFoundError:
            return [TextContent(type="text", text="## Error\n\ndbt CLI not found. Install with: pip install dbt-snowflake")]

    elif name == "review_sql":
        sql_content = arguments["sql_content"]
        file_path = arguments.get("file_path", "")
        issues = _review_sql(sql_content, file_path)

        if not issues:
            return [TextContent(type="text", text="## SQL Review: All Clear\n\nNo issues found.")]

        lines = ["## SQL Review Results\n"]
        for issue in issues:
            icon = {"error": "X", "warning": "!", "info": "i"}.get(issue["severity"], "?")
            lines.append(f"- [{icon}] **{issue['rule']}** (line {issue['line']}): {issue['message']}")
            if "content" in issue:
                lines.append(f"  `{issue['content']}`")
        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "check_data_quality":
        select = arguments.get("select", "")
        cmd = ["dbt", "test"]
        if select:
            safe_select = re.sub(r'[^a-zA-Z0-9_+:.\-*/]', '', select)
            cmd.extend(["--select", safe_select])

        try:
            result = subprocess.run(
                cmd,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=300,
            )
            output = result.stdout + ("\n" + result.stderr if result.stderr else "")
            status = "ALL PASSED" if result.returncode == 0 else "FAILURES DETECTED"
            return [TextContent(type="text", text=f"## Data Quality Check — {status}\n\n```\n{output[:5000]}\n```")]
        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text="## Data Quality Check — TIMEOUT")]
        except FileNotFoundError:
            return [TextContent(type="text", text="## Error\n\ndbt CLI not found")]

    elif name == "generate_streamlit_app":
        model_name = arguments["model_name"]
        app_title = arguments.get("app_title", "")
        code = _generate_streamlit_app(model_name, app_title)
        return [TextContent(
            type="text",
            text=f"## Streamlit App for {model_name}\n\n```python\n{code}\n```",
        )]

    # ── Medallion Advisor Tool Handlers ──

    elif name == "list_medallion_models":
        layer = arguments.get("layer", "all")
        result = _list_models_by_layer(layer)
        formatted = json.dumps(result, indent=2)
        return [TextContent(type="text", text=f"## Models by Layer\n\n```json\n{formatted}\n```")]

    elif name == "read_model_sql":
        model_name = arguments["model_name"]
        result = _read_model_sql(model_name)
        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]
        return [TextContent(
            type="text",
            text=f"## {result['model']} ({result['layer']})\n\nPath: `{result['path']}`\n\n```sql\n{result['sql']}\n```",
        )]

    elif name == "suggest_silver_model":
        source_models = arguments["source_models"]
        description = arguments["description"]
        # Read source model SQL for context
        sources_context = []
        for m in source_models:
            info = _read_model_sql(m)
            if "sql" in info:
                sources_context.append(f"### {m} ({info['layer']})\n```sql\n{info['sql']}\n```")
            else:
                sources_context.append(f"### {m}\n(not found on disk)")

        suggestion = (
            f"## Suggested Silver (Intermediate) Model\n\n"
            f"**Business Requirement:** {description}\n\n"
            f"**Source Models:**\n\n" + "\n\n".join(sources_context) + "\n\n"
            f"### Suggested SQL\n\n"
            f"Create a file like `models/intermediate/<source>/int_<name>.sql` with a CTE-based model that:\n"
            f"- References source models with `{{{{ ref('{source_models[0]}') }}}}`\n"
            f"- Applies business logic: {description}\n"
            f"- Uses Snowflake-native functions\n\n"
            f"Use the `write_medallion_model` tool to save the model after finalizing the SQL."
        )
        return [TextContent(type="text", text=suggestion)]

    elif name == "suggest_gold_model":
        source_models = arguments["source_models"]
        model_type = arguments["model_type"]
        description = arguments["description"]
        prefix = "fct_" if model_type == "fact" else "dim_"

        sources_context = []
        for m in source_models:
            info = _read_model_sql(m)
            if "sql" in info:
                sources_context.append(f"### {m} ({info['layer']})\n```sql\n{info['sql']}\n```")
            else:
                sources_context.append(f"### {m}\n(not found on disk)")

        suggestion = (
            f"## Suggested Gold ({model_type.title()}) Model\n\n"
            f"**Prefix:** `{prefix}`\n"
            f"**Business Requirement:** {description}\n\n"
            f"**Source Models:**\n\n" + "\n\n".join(sources_context) + "\n\n"
            f"### Guidelines\n\n"
            f"- Name: `{prefix}<entity>` (e.g., `{prefix}orders`)\n"
            f"- Use `dbt_utils.generate_surrogate_key()` for surrogate keys\n"
            f"- Explicitly list all columns (no SELECT *)\n"
            f"- Include pk tests (unique + not_null) in schema.yml\n\n"
            f"Use the `write_medallion_model` tool to save the model after finalizing the SQL."
        )
        return [TextContent(type="text", text=suggestion)]

    elif name == "write_medallion_model":
        layer = arguments["layer"]
        source_name = arguments["source_name"]
        model_name = arguments["model_name"]
        sql = arguments["sql"]
        description = arguments.get("description", "")

        result = _write_model(layer, source_name, model_name, sql, description)
        return [TextContent(
            type="text",
            text=f"## Model Written\n\n- SQL: `{result['created']}`\n- Schema: `{result['schema']}`\n\nRun `dbt build --select {model_name}` to materialize.",
        )]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ===== Main =================================================================

async def main():
    logger.info("Starting Snowflake dbt MCP Server...")
    async with run_stdio(server):
        pass

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
