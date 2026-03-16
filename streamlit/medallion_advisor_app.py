"""
Medallion Architecture Advisor — Streamlit-in-Snowflake
========================================================
A conversational AI agent that reads your bronze (staging) layer data
and helps you design & generate silver (intermediate) and gold (marts)
layer dbt models using natural language.

Deploy to Snowflake Streamlit:
  See streamlit/deploy.sql or run:
    CREATE STREAMLIT medallion_advisor_app FROM 'streamlit/' ...
"""
import json
import re

import streamlit as st
from snowflake.snowpark.context import get_active_session

# ─── Config ──────────────────────────────────────────────────
st.set_page_config(page_title="Medallion Advisor", page_icon="🏗️", layout="wide")

session = get_active_session()

# Enable cross-region inference so Cortex models work regardless of region
try:
    session.sql("ALTER SESSION SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION'").collect()
except Exception:
    pass  # May already be set or require higher privileges

CORTEX_MODEL = "mistral-large2"
TARGET_DATABASE = "DBT_DEV"

# ─── System Prompt ───────────────────────────────────────────
SYSTEM_PROMPT = """You are a Snowflake dbt expert agent for medallion architecture.
You help users build data pipelines across three layers:

- **Bronze (staging)**: Source-conformed views — already auto-generated
- **Silver (intermediate)**: Cleaned, joined, business-logic transforms
- **Gold (marts)**: Consumption-ready fact and dimension tables

## Conventions
- Staging: stg_<source>__<table>
- Silver:  int_<description> (e.g., int_orders_enriched)
- Gold:    fct_<entity> (facts) or dim_<entity> (dimensions)
- Always use {{ ref('model_name') }} and {{ source('source', 'TABLE') }}
- Use CTEs (WITH blocks), Snowflake-native date functions
- Never hardcode database/schema names
- Use dbt_utils.generate_surrogate_key() for surrogate keys

When suggesting models, always provide complete dbt SQL with ref() calls.
When the user approves, show the final SQL ready to save.
Explain your reasoning before generating code.
"""

# ─── Helpers ─────────────────────────────────────────────────

def call_cortex(messages: list) -> str:
    """Call Snowflake Cortex COMPLETE with message history."""
    messages_json = json.dumps(messages)
    try:
        result = session.sql(
            "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?)",
            params=[CORTEX_MODEL, messages_json],
        ).collect()
        raw = result[0][0]
        # Parse Cortex response format
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                if "choices" in parsed:
                    msg = parsed["choices"][0]
                    return msg.get("messages", msg.get("message", {}).get("content", raw))
                return parsed.get("message", parsed.get("content", raw))
        except (json.JSONDecodeError, KeyError, IndexError):
            pass
        return raw
    except Exception as e:
        return f"Cortex error: {e}"


def run_query(sql: str):
    """Execute SQL and return pandas DataFrame."""
    try:
        return session.sql(sql).to_pandas()
    except Exception as e:
        st.error(f"Query error: {e}")
        return None


def get_schemas():
    """Get list of schemas in the target database."""
    try:
        df = session.sql(f"SHOW SCHEMAS IN DATABASE {TARGET_DATABASE}").to_pandas()
        return df["name"].tolist()
    except Exception:
        return []


def get_tables_in_schema(schema_name):
    """Get tables/views in a schema."""
    try:
        df = session.sql(f"SHOW TABLES IN {TARGET_DATABASE}.{schema_name}").to_pandas()
        tables = [(r["name"], "TABLE", r.get("rows", 0)) for _, r in df.iterrows()]
    except Exception:
        tables = []
    try:
        df2 = session.sql(f"SHOW VIEWS IN {TARGET_DATABASE}.{schema_name}").to_pandas()
        tables += [(r["name"], "VIEW", None) for _, r in df2.iterrows()]
    except Exception:
        pass
    return tables


def describe_table(schema_name, table_name):
    """Get column metadata for a table."""
    try:
        df = session.sql(
            f'DESCRIBE TABLE {TARGET_DATABASE}.{schema_name}."{table_name}"'
        ).to_pandas()
        return df
    except Exception as e:
        st.error(f"Describe error: {e}")
        return None


def sample_table(schema_name, table_name, limit=10):
    """Get sample rows from a table."""
    try:
        return session.sql(
            f'SELECT * FROM {TARGET_DATABASE}.{schema_name}."{table_name}" LIMIT {int(limit)}'
        ).to_pandas()
    except Exception as e:
        st.error(f"Sample error: {e}")
        return None


def count_rows(schema_name, table_name):
    """Get row count."""
    try:
        result = session.sql(
            f'SELECT COUNT(*) AS cnt FROM {TARGET_DATABASE}.{schema_name}."{table_name}"'
        ).collect()
        return result[0][0]
    except Exception:
        return None


# ─── Sidebar: Data Explorer ─────────────────────────────────
st.sidebar.title("🏗️ Medallion Advisor")
st.sidebar.caption(f"Cortex: {CORTEX_MODEL}")

st.sidebar.divider()
st.sidebar.subheader("📊 Data Explorer")

# Show layer summary
layer_schemas = {
    "🥉 Bronze (Staging)": "DBT_STAGING",
    "🥈 Silver (Intermediate)": "DBT_INTERMEDIATE",
    "🥇 Gold (Marts)": "DBT_MARTS",
}

for label, schema in layer_schemas.items():
    tables = get_tables_in_schema(schema)
    count = len(tables)
    with st.sidebar.expander(f"{label} ({count} models)"):
        if tables:
            for name, kind, rows in sorted(tables):
                row_str = f" ({rows:,} rows)" if rows else ""
                st.write(f"• {name}{row_str}")
        else:
            st.write("No models yet")

st.sidebar.divider()
mode = st.sidebar.radio("Mode", ["💬 Chat Advisor", "🔍 Explore Data", "📝 Generate Model"])

# ─── Page: Chat Advisor ─────────────────────────────────────
if mode == "💬 Chat Advisor":
    st.title("🏗️ Medallion Architecture Advisor")
    st.caption("Describe what you need — I'll suggest silver/gold layer models from your bronze data.")

    # Initialize state
    if "advisor_messages" not in st.session_state:
        st.session_state.advisor_messages = []

    # Show past messages
    for msg in st.session_state.advisor_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Quick action buttons
    if not st.session_state.advisor_messages:
        st.write("**Quick start:**")
        col1, col2, col3 = st.columns(3)
        quick = None
        with col1:
            if st.button("📋 List my bronze models"):
                quick = "What bronze (staging) models and source tables do I have? List them with row counts."
        with col2:
            if st.button("💡 Suggest silver models"):
                quick = "Look at my staging models and suggest what silver (intermediate) layer models I should create. Explain the business logic each would contain."
        with col3:
            if st.button("🏆 Suggest gold models"):
                quick = "Based on my staging data, suggest gold (marts) layer fact and dimension tables. Explain what business questions each would answer."

        if quick:
            st.session_state.advisor_messages.append({"role": "user", "content": quick})
            st.rerun()

    # Chat input
    if prompt := st.chat_input("e.g., 'Create a dim_companies model from free_company_data'"):
        st.session_state.advisor_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing your data..."):
                # Build context with actual data awareness
                bronze_tables = get_tables_in_schema("DBT_STAGING")
                silver_tables = get_tables_in_schema("DBT_INTERMEDIATE")
                gold_tables = get_tables_in_schema("DBT_MARTS")

                data_context = "Current project state:\n"
                data_context += f"- Bronze models: {', '.join(t[0] for t in bronze_tables) if bronze_tables else 'none'}\n"
                data_context += f"- Silver models: {', '.join(t[0] for t in silver_tables) if silver_tables else 'none'}\n"
                data_context += f"- Gold models: {', '.join(t[0] for t in gold_tables) if gold_tables else 'none'}\n"

                # Build full message history
                messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\n" + data_context}]
                for msg in st.session_state.advisor_messages[-10:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})

                response = call_cortex(messages)
                st.markdown(response)
                st.session_state.advisor_messages.append({"role": "assistant", "content": response})

    # Clear chat button
    if st.session_state.advisor_messages:
        if st.button("🗑️ Clear conversation"):
            st.session_state.advisor_messages = []
            st.rerun()

# ─── Page: Explore Data ─────────────────────────────────────
elif mode == "🔍 Explore Data":
    st.title("🔍 Explore Your Data")

    tab1, tab2, tab3 = st.tabs(["Browse Tables", "Profile Columns", "Custom Query"])

    with tab1:
        schema_choice = st.selectbox(
            "Schema",
            ["DBT_STAGING", "DBT_INTERMEDIATE", "DBT_MARTS"],
        )
        tables = get_tables_in_schema(schema_choice)

        if tables:
            table_choice = st.selectbox(
                "Table", [t[0] for t in tables]
            )
            if table_choice:
                col_a, col_b = st.columns(2)
                with col_a:
                    row_count = count_rows(schema_choice, table_choice)
                    st.metric("Row Count", f"{row_count:,}" if row_count else "N/A")
                with col_b:
                    desc_df = describe_table(schema_choice, table_choice)
                    if desc_df is not None:
                        st.metric("Columns", len(desc_df))

                st.subheader("Schema")
                if desc_df is not None:
                    st.dataframe(desc_df[["name", "type", "null?"]], use_container_width=True)

                st.subheader("Sample Data")
                sample_limit = st.slider("Rows", 5, 50, 10)
                sample_df = sample_table(schema_choice, table_choice, sample_limit)
                if sample_df is not None:
                    st.dataframe(sample_df, use_container_width=True)
        else:
            st.info(f"No tables found in {schema_choice}")

    with tab2:
        st.subheader("Column Profiling")
        schema_p = st.selectbox("Schema ", ["DBT_STAGING", "DBT_INTERMEDIATE", "DBT_MARTS"], key="prof_schema")
        tables_p = get_tables_in_schema(schema_p)
        if tables_p:
            table_p = st.selectbox("Table ", [t[0] for t in tables_p], key="prof_table")
            if st.button("Profile", type="primary"):
                desc = describe_table(schema_p, table_p)
                if desc is not None:
                    cols = desc["name"].tolist()[:20]
                    parts = []
                    for c in cols:
                        parts.append(f'COUNT(DISTINCT "{c}") AS "{c}_distinct"')
                        parts.append(f'SUM(CASE WHEN "{c}" IS NULL THEN 1 ELSE 0 END) AS "{c}_nulls"')

                    sql = f'SELECT COUNT(*) AS total, {", ".join(parts)} FROM {TARGET_DATABASE}.{schema_p}."{table_p}"'
                    result = run_query(sql)
                    if result is not None:
                        total = int(result.iloc[0]["TOTAL"])
                        rows = []
                        for c in cols:
                            distinct = int(result.iloc[0][f"{c}_distinct"])
                            nulls = int(result.iloc[0][f"{c}_nulls"])
                            null_pct = round(nulls / total * 100, 1) if total else 0
                            rows.append({
                                "Column": c,
                                "Distinct": distinct,
                                "Nulls": nulls,
                                "Null %": null_pct,
                                "Cardinality": round(distinct / total, 4) if total else 0,
                            })
                        import pandas as pd
                        st.dataframe(pd.DataFrame(rows), use_container_width=True)

    with tab3:
        st.subheader("Run SQL Query")
        sql_input = st.text_area(
            "SQL (read-only queries)",
            value=f"SELECT * FROM {TARGET_DATABASE}.DBT_STAGING.<table_name> LIMIT 10",
            height=150,
        )
        if st.button("▶ Run"):
            normalized = sql_input.strip().upper()
            if not any(normalized.startswith(kw) for kw in ("SELECT", "SHOW", "DESCRIBE", "WITH")):
                st.error("Only SELECT / SHOW / DESCRIBE / WITH queries are allowed.")
            else:
                df = run_query(sql_input)
                if df is not None:
                    st.dataframe(df, use_container_width=True)

# ─── Page: Generate Model ────────────────────────────────────
elif mode == "📝 Generate Model":
    st.title("📝 Generate dbt Model")
    st.caption("Use AI to generate a silver or gold layer model from your existing data.")

    col1, col2 = st.columns(2)

    with col1:
        layer = st.selectbox("Target Layer", ["silver (intermediate)", "gold (marts)"])
        source_schema = st.selectbox(
            "Source Schema",
            ["DBT_STAGING", "DBT_INTERMEDIATE", "DBT_MARTS"],
        )
        source_tables = get_tables_in_schema(source_schema)
        selected_tables = st.multiselect(
            "Source Tables",
            [t[0] for t in source_tables],
        )

    with col2:
        model_name = st.text_input(
            "Model Name",
            placeholder="int_orders_enriched or fct_revenue",
        )
        description = st.text_area("Business Description", placeholder="Describe what this model should do...")

    if selected_tables:
        st.subheader("Selected Table Schemas")
        for t in selected_tables:
            with st.expander(t):
                df = describe_table(source_schema, t)
                if df is not None:
                    st.dataframe(df[["name", "type"]], use_container_width=True)

    if st.button("🤖 Generate with AI", type="primary", disabled=not (model_name and selected_tables and description)):
        with st.spinner("Generating model..."):
            # Get column info for context
            table_schemas = {}
            for t in selected_tables:
                df = describe_table(source_schema, t)
                if df is not None:
                    table_schemas[t] = df[["name", "type"]].to_dict("records")

            prefix = "int_" if "silver" in layer else "fct_" if "fact" in description.lower() else "dim_"
            if not model_name.startswith(("int_", "fct_", "dim_")):
                st.warning(f"Consider prefixing your model name: {prefix}{model_name}")

            prompt = f"""Generate a dbt {layer} model named `{model_name}`.

Business requirement: {description}

Source tables (in {source_schema}):
{json.dumps(table_schemas, indent=2)}

Requirements:
- Use {{ ref('source_model_name') }} to reference staging models (convert table names like STG_SOURCE__TABLE to ref('stg_source__table'))
- Use CTEs
- Follow naming conventions
- Include complete SQL ready to save as a .sql file
- After the SQL, provide the schema.yml entry with tests

IMPORTANT: Return the SQL inside a ```sql code block and the YAML inside a ```yaml code block."""

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            response = call_cortex(messages)
            st.markdown(response)

            # Store for potential follow-up
            st.session_state["last_generated_model"] = {
                "name": model_name,
                "layer": layer,
                "response": response,
            }

    # Follow-up refinement
    if "last_generated_model" in st.session_state:
        st.divider()
        st.subheader("Refine the model")
        feedback = st.text_area("Feedback or changes", placeholder="Add a filter for active records only...")
        if st.button("🔄 Refine"):
            with st.spinner("Refining..."):
                last = st.session_state["last_generated_model"]
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Here is a dbt model I generated:\n{last['response']}"},
                    {"role": "user", "content": f"Please modify it based on this feedback: {feedback}"},
                ]
                response = call_cortex(messages)
                st.markdown(response)
                st.session_state["last_generated_model"]["response"] = response
