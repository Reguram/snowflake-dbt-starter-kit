/*
=============================================================================
Step 2: UDF & Stored Procedure Tools for MCP Server
=============================================================================
These are the custom tools (type: GENERIC) that the Snowflake managed MCP
server will expose. Each function becomes a callable MCP tool.
=============================================================================
*/

USE ROLE ACCOUNTADMIN;
USE DATABASE DBT_DEV;
USE SCHEMA MCP_TOOLS;
USE WAREHOUSE DBT_AGENT_WH;


-- ==========================================
-- Tool 1: GENERATE_DBT_MODEL
-- Given a source table name, returns staging model SQL + schema YAML
-- ==========================================
CREATE OR REPLACE PROCEDURE DBT_DEV.MCP_TOOLS.GENERATE_DBT_MODEL(
    SOURCE_NAME VARCHAR,
    TABLE_NAME VARCHAR,
    SOURCE_DATABASE VARCHAR DEFAULT 'SNOWFLAKE_SAMPLE_DATA',
    SOURCE_SCHEMA VARCHAR DEFAULT 'TPCH_SF1'
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'generate_dbt_model'
EXECUTE AS CALLER
AS
$$
import json

def generate_dbt_model(session, source_name: str, table_name: str,
                       source_database: str = 'SNOWFLAKE_SAMPLE_DATA',
                       source_schema: str = 'TPCH_SF1') -> dict:
    """
    Reads column metadata from INFORMATION_SCHEMA and generates
    a dbt staging model SQL + schema.yml entry.
    """
    # Query column metadata from the source table
    cols_df = session.sql(f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, ORDINAL_POSITION
        FROM {source_database}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{source_schema.upper()}'
          AND TABLE_NAME = '{table_name.upper()}'
        ORDER BY ORDINAL_POSITION
    """).collect()

    if not cols_df:
        return {"error": f"Table {table_name} not found in {source_database}.{source_schema}"}

    columns = [row["COLUMN_NAME"] for row in cols_df]

    # Build model name following convention
    model_name = f"stg_{source_name}__{table_name.lower()}"

    # Generate column renames (UPPER_CASE -> snake_case)
    renames = []
    for col in columns:
        # Remove common prefixes like O_, C_, L_, etc.
        clean = col.lower()
        # Strip single-letter prefix (e.g., O_ORDERKEY -> orderkey)
        parts = clean.split('_', 1)
        if len(parts) > 1 and len(parts[0]) == 1:
            clean = parts[1]
        # Convert to snake_case name
        renames.append(f"        {col.lower()} as {clean}")

    cols_sql = ",\\n".join(renames)

    sql_model = f"""with source as (
    select * from {{{{ source('{source_name}', '{table_name.upper()}') }}}}
),

renamed as (
    select
{cols_sql}
    from source
)

select * from renamed"""

    # Generate schema.yml
    col_yaml_entries = []
    for col in columns:
        clean = col.lower()
        parts = clean.split('_', 1)
        if len(parts) > 1 and len(parts[0]) == 1:
            clean = parts[1]
        col_yaml_entries.append(f"      - name: {clean}\\n        description: \\\"\\\"")

    cols_yaml = "\\n".join(col_yaml_entries)
    schema_yml = f"""version: 2

models:
  - name: {model_name}
    description: \"Staged {table_name.lower()} from {source_name}\"
    columns:
{cols_yaml}"""

    return {
        "model_name": model_name,
        "file_path": f"models/staging/{model_name}.sql",
        "sql": sql_model,
        "schema_yml": schema_yml,
        "columns_found": len(columns)
    }
$$;


-- ==========================================
-- Tool 2: REVIEW_SQL
-- Static analysis of SQL code for dbt best practices
-- ==========================================
CREATE OR REPLACE FUNCTION DBT_DEV.MCP_TOOLS.REVIEW_SQL(
    SQL_CONTENT VARCHAR,
    FILE_PATH VARCHAR DEFAULT ''
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
HANDLER = 'review_sql'
AS
$$
import json
import re

def review_sql(sql_content: str, file_path: str = '') -> dict:
    """
    Static analysis of SQL for dbt/Snowflake best practices.
    Returns list of issues with severity, rule, and line numbers.
    """
    issues = []
    lines = sql_content.split("\\n")

    rules = [
        {
            "id": "HARDCODED_SCHEMA",
            "pattern": r"(?:from|join)\\s+\\w+\\.\\w+\\.\\w+",
            "message": "Hard-coded database.schema.table — use {{ source() }} or {{ ref() }}",
            "severity": "error",
        },
        {
            "id": "SELECT_STAR",
            "pattern": r"^\\s*select\\s+\\*",
            "message": "SELECT * found — list columns explicitly in marts/semantic models",
            "severity": "warning",
        },
        {
            "id": "LIMIT_CLAUSE",
            "pattern": r"\\bLIMIT\\s+\\d+",
            "message": "LIMIT clause — should not be in production models",
            "severity": "warning",
        },
        {
            "id": "MISSING_REF",
            "pattern": r"(?:from|join)\\s+(?!.*\\{\\{)([A-Za-z_][A-Za-z0-9_]*)\\s",
            "message": "Possible direct table reference without {{ ref() }} or {{ source() }}",
            "severity": "warning",
        },
    ]

    for rule in rules:
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            if re.search(rule["pattern"], line, re.IGNORECASE):
                issues.append({
                    "rule": rule["id"],
                    "severity": rule["severity"],
                    "message": rule["message"],
                    "line": i,
                    "content": stripped[:120],
                })

    # Check naming convention for staging
    if "staging" in file_path:
        import os
        stem = os.path.splitext(os.path.basename(file_path))[0]
        if not stem.startswith("stg_"):
            issues.append({
                "rule": "NAMING_STG",
                "severity": "warning",
                "message": "Staging model should follow stg_<source>__<table> naming",
                "line": 0,
            })

    score = max(0, 10 - len(issues))

    return {
        "issues_found": len(issues),
        "production_readiness_score": score,
        "issues": issues,
        "summary": "All clear" if not issues else f"{len(issues)} issue(s) found"
    }
$$;


-- ==========================================
-- Tool 3: CHECK_DATA_QUALITY
-- Query-based data quality checks
-- ==========================================
CREATE OR REPLACE PROCEDURE DBT_DEV.MCP_TOOLS.CHECK_DATA_QUALITY(
    TABLE_NAME VARCHAR,
    CHECK_TYPE VARCHAR DEFAULT 'all'
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'check_data_quality'
EXECUTE AS CALLER
AS
$$
import json

def check_data_quality(session, table_name: str, check_type: str = 'all') -> dict:
    """
    Run data quality checks on a table.
    check_type: 'all', 'null', 'duplicate', 'row_count'
    """
    results = {"table": table_name, "checks": []}

    try:
        # Row count check
        if check_type in ('all', 'row_count'):
            count_result = session.sql(f"SELECT COUNT(*) as cnt FROM {table_name}").collect()
            row_count = count_result[0]["CNT"]
            results["checks"].append({
                "check": "row_count",
                "status": "pass" if row_count > 0 else "fail",
                "value": row_count,
                "message": f"Table has {row_count:,} rows"
            })

        # Null check on all columns
        if check_type in ('all', 'null'):
            cols_df = session.sql(f"""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table_name.split('.')[-1].upper()}'
                ORDER BY ORDINAL_POSITION
            """).collect()

            for col_row in cols_df[:10]:  # Check first 10 columns
                col_name = col_row["COLUMN_NAME"]
                null_result = session.sql(f"""
                    SELECT COUNT(*) as null_count
                    FROM {table_name}
                    WHERE {col_name} IS NULL
                """).collect()
                null_count = null_result[0]["NULL_COUNT"]
                results["checks"].append({
                    "check": f"null_check_{col_name.lower()}",
                    "status": "pass" if null_count == 0 else "info",
                    "value": null_count,
                    "message": f"{col_name}: {null_count:,} nulls"
                })

        # Duplicate check (first column as PK heuristic)
        if check_type in ('all', 'duplicate'):
            cols_df = session.sql(f"""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table_name.split('.')[-1].upper()}'
                ORDER BY ORDINAL_POSITION
                LIMIT 1
            """).collect()

            if cols_df:
                pk_col = cols_df[0]["COLUMN_NAME"]
                dup_result = session.sql(f"""
                    SELECT COUNT(*) as total, COUNT(DISTINCT {pk_col}) as distinct_count
                    FROM {table_name}
                """).collect()
                total = dup_result[0]["TOTAL"]
                distinct = dup_result[0]["DISTINCT_COUNT"]
                has_dups = total != distinct
                results["checks"].append({
                    "check": f"duplicate_check_{pk_col.lower()}",
                    "status": "fail" if has_dups else "pass",
                    "value": total - distinct,
                    "message": f"{pk_col}: {total - distinct:,} duplicates"
                })

        passed = sum(1 for c in results["checks"] if c["status"] == "pass")
        total = len(results["checks"])
        results["summary"] = f"{passed}/{total} checks passed"
        results["overall_status"] = "pass" if passed == total else "issues_found"

    except Exception as e:
        results["error"] = str(e)
        results["overall_status"] = "error"

    return results
$$;


-- ==========================================
-- Tool 4: GENERATE_SEMANTIC_VIEW_DDL
-- Generate Semantic View DDL from parameters
-- ==========================================
CREATE OR REPLACE FUNCTION DBT_DEV.MCP_TOOLS.GENERATE_SEMANTIC_VIEW_DDL(
    MODEL_NAME VARCHAR,
    DIMENSIONS VARCHAR,  -- JSON array string: [{"name":"col","description":"desc"}, ...]
    METRICS VARCHAR       -- JSON array string: [{"name":"m","type":"SUM","expression":"col","description":"desc"}, ...]
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
HANDLER = 'generate_semantic_view_ddl'
AS
$$
import json

def generate_semantic_view_ddl(model_name: str, dimensions: str, metrics: str) -> dict:
    """Generate Snowflake Semantic View DDL."""
    dims = json.loads(dimensions)
    mets = json.loads(metrics)

    dim_lines = []
    for d in dims:
        comment = d.get("description", "")
        dim_lines.append(f"    {d['name']} AS DIMENSION COMMENT '{comment}'")

    metric_lines = []
    for m in mets:
        agg = m.get("type", "SUM").upper()
        expr = m.get("expression", m["name"])
        comment = m.get("description", "")
        metric_lines.append(f"    {m['name']} AS {agg}({expr}) COMMENT '{comment}'")

    dims_str = ",\\n".join(dim_lines)
    mets_str = ",\\n".join(metric_lines)

    ddl = f"""CREATE OR REPLACE SEMANTIC VIEW DBT_DEV.SEMANTIC.{model_name.upper()}
  COMMENT = 'Auto-generated semantic view for {model_name}'
AS SELECT * FROM DBT_DEV.SEMANTIC.{model_name.upper()}
COLUMNS (
{dims_str}
)
METRICS (
{mets_str}
);"""

    return {
        "model_name": model_name,
        "ddl": ddl,
        "dimensions_count": len(dims),
        "metrics_count": len(mets)
    }
$$;


-- ==========================================
-- Tool 5: GENERATE_STREAMLIT_APP
-- Generate Streamlit-in-Snowflake code
-- ==========================================
CREATE OR REPLACE FUNCTION DBT_DEV.MCP_TOOLS.GENERATE_STREAMLIT_APP(
    MODEL_NAME VARCHAR,
    APP_TITLE VARCHAR DEFAULT ''
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
HANDLER = 'generate_streamlit_app'
AS
$$
def generate_streamlit_app(model_name: str, app_title: str = '') -> dict:
    """Generate Streamlit-in-Snowflake app code."""
    title = app_title or f"{model_name.replace('_', ' ').title()} Dashboard"

    code = f'''import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="{title}", layout="wide")
st.title("{title}")

session = get_active_session()

@st.cache_data(ttl=600)
def load_data():
    return session.table("{model_name.upper()}").to_pandas()

df = load_data()

# Sidebar filters
st.sidebar.header("Filters")
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
c1, c2, c3 = st.columns(3)
c1.metric("Total Records", f"{{len(filtered_df):,}}")
numeric_cols = filtered_df.select_dtypes(include=["number"]).columns.tolist()
if numeric_cols:
    c2.metric(numeric_cols[0].replace("_", " ").title(),
              f"{{filtered_df[numeric_cols[0]].sum():,.2f}}")
if len(numeric_cols) > 1:
    c3.metric(numeric_cols[1].replace("_", " ").title(),
              f"{{filtered_df[numeric_cols[1]].mean():,.2f}}")

# Data table
st.subheader("Data")
st.dataframe(filtered_df.head(1000), use_container_width=True)

# Cortex AI
st.subheader("Ask a Question")
question = st.text_input("Ask about this data:")
if question:
    prompt = f"Analyze the {{model_name}} data. Columns: {{', '.join(df.columns.tolist())}}. Question: {{question}}"
    try:
        result = session.sql("SELECT SNOWFLAKE.CORTEX.COMPLETE(\\'mistral-large2\\', ?)", params=[prompt]).collect()
        st.write(result[0][0])
    except Exception as e:
        st.error(f"Error: {{e}}")
'''

    return {
        "app_title": title,
        "model_name": model_name,
        "code": code,
        "file_path": f"streamlit/{model_name}_app.py"
    }
$$;


-- ==========================================
-- Tool 6: EXECUTE_DBT_QUERY
-- Execute read-only SQL queries (replaces run_dbt_command for Snowflake-managed context)
-- ==========================================
CREATE OR REPLACE PROCEDURE DBT_DEV.MCP_TOOLS.EXECUTE_DBT_QUERY(
    QUERY_TEXT VARCHAR
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'execute_dbt_query'
EXECUTE AS CALLER
AS
$$
import json

def execute_dbt_query(session, query_text: str) -> dict:
    """
    Execute a read-only SQL query and return results.
    Only SELECT and SHOW statements are allowed.
    """
    # Safety: only allow read-only queries
    normalized = query_text.strip().upper()
    allowed_prefixes = ('SELECT', 'SHOW', 'DESCRIBE', 'DESC', 'LIST', 'EXPLAIN')
    if not any(normalized.startswith(p) for p in allowed_prefixes):
        return {
            "error": "Only read-only queries (SELECT, SHOW, DESCRIBE) are allowed",
            "status": "rejected"
        }

    try:
        result = session.sql(query_text).collect()
        # Convert to list of dicts
        rows = []
        for row in result[:100]:  # Limit to 100 rows
            rows.append(row.as_dict())

        return {
            "status": "success",
            "row_count": len(result),
            "rows_returned": len(rows),
            "data": rows
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
$$;
