"""Advanced tools — semantic view DDL and Streamlit app generation.

Ported from snowflake-dbt-mcp/server.py.
"""

import json
from typing import Optional

from langchain_core.tools import tool


@tool
def generate_semantic_view(
    model_name: str,
    dimensions: list[dict],
    metrics: list[dict],
) -> str:
    """Generate Snowflake Semantic View DDL from a dbt mart model.

    Args:
        model_name: Base dbt model name (e.g. 'fct_orders').
        dimensions: List of dimension dicts with 'name', 'type', 'expression' (optional).
        metrics: List of metric dicts with 'name', 'expression' (e.g. 'SUM(amount)').
    """
    dim_lines = []
    for d in dimensions:
        expr = d.get("expression", d["name"])
        dim_lines.append(f"    {d['name']} {d.get('type', 'VARCHAR')} AS {expr}")

    metric_lines = []
    for m in metrics:
        metric_lines.append(f"    {m['name']} AS {m['expression']}")

    schema = "SEMANTIC"
    view_name = f"sem_{model_name}"

    ddl = (
        f"CREATE OR REPLACE SEMANTIC VIEW {schema}.{view_name}\n"
        f"  BASE TABLE = DBT_MARTS.{model_name.upper()}\n"
        f"  DIMENSIONS (\n"
        f"{chr(10).join(dim_lines)}\n"
        f"  )\n"
        f"  METRICS (\n"
        f"{chr(10).join(metric_lines)}\n"
        f"  );\n"
    )

    return json.dumps({
        "view_name": view_name,
        "ddl": ddl,
    })


@tool
def generate_streamlit_app(model_name: str, app_title: str = "") -> str:
    """Generate a Streamlit-in-Snowflake dashboard app for a dbt model.

    Args:
        model_name: dbt model name to query for the dashboard.
        app_title: Display title for the app. Defaults to model name.
    """
    title = app_title or model_name.replace("_", " ").title()
    table_ref = f"DBT_MARTS.{model_name.upper()}"

    code = f'''"""Streamlit dashboard for {model_name}."""
import streamlit as st

st.set_page_config(page_title="{title}", layout="wide")
st.title("{title}")

# Get Snowflake session
from snowflake.snowpark.context import get_active_session
session = get_active_session()

# Load data
@st.cache_data(ttl=600)
def load_data():
    return session.table("{table_ref}").to_pandas()

df = load_data()

# Key metrics
st.subheader("Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Rows", f"{{len(df):,}}")
col2.metric("Columns", f"{{len(df.columns)}}")

numeric_cols = df.select_dtypes(include="number").columns.tolist()
if numeric_cols:
    col3.metric(f"Sum of {{numeric_cols[0]}}", f"{{df[numeric_cols[0]].sum():,.0f}}")

# Filters
st.subheader("Explore Data")
string_cols = df.select_dtypes(include="object").columns.tolist()
if string_cols:
    filter_col = st.selectbox("Filter by", string_cols)
    filter_vals = st.multiselect(
        f"Select {{filter_col}} values",
        options=sorted(df[filter_col].dropna().unique()),
    )
    if filter_vals:
        df = df[df[filter_col].isin(filter_vals)]

# Charts
if numeric_cols and string_cols:
    st.bar_chart(df.groupby(string_cols[0])[numeric_cols[0]].sum())

# Raw data
with st.expander("Raw Data"):
    st.dataframe(df)
'''

    return json.dumps({
        "model_name": model_name,
        "title": title,
        "code": code,
    })
