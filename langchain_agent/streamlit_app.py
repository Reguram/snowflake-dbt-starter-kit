"""Unified Streamlit app — LangChain-powered dbt agent with multiple pages.

Consolidates medallion_advisor_app.py + dbt_agent_app.py into one app
with a conversational agent, data explorer, and model generator.

Run locally:
    streamlit run langchain_agent/streamlit_app.py
"""

import json

import streamlit as st

st.set_page_config(page_title="dbt Agent — LangChain", page_icon="🏗️", layout="wide")


# ─── Connection Helper ────────────────────────────────────────

@st.cache_resource
def get_agent():
    """Build the LangChain agent once and cache it."""
    from langchain_agent.agent import build_agent
    from langchain_agent.skills.router import get_skill_instructions

    return build_agent, get_skill_instructions


def invoke_agent(user_input: str, session_id: str = "default"):
    """Invoke the agent with skill routing and conversation history."""
    from langchain_agent.agent import build_agent_with_history
    from langchain_agent.skills.router import get_skill_instructions
    from langchain_agent.callbacks import StreamlitCallbackHandler

    skill_instructions = get_skill_instructions(user_input)

    agent = build_agent_with_history(skill_instructions=skill_instructions)

    response_container = st.empty()
    callbacks = [StreamlitCallbackHandler(response_container)]

    result = agent.invoke(
        {"input": user_input},
        config={
            "configurable": {"session_id": session_id},
            "callbacks": callbacks,
        },
    )
    return result.get("output", str(result))


# ─── Sidebar ──────────────────────────────────────────────────

page = st.sidebar.radio(
    "Navigate",
    [
        "💬 Chat Advisor",
        "🔍 Data Explorer",
        "🏗️ Model Generator",
        "📝 Code Review",
        "✅ Data Quality",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Powered by**")
st.sidebar.markdown("LangChain + Snowflake Cortex")

# ─── Page: Chat Advisor ──────────────────────────────────────

if page == "💬 Chat Advisor":
    st.title("💬 dbt Chat Advisor")
    st.caption("Conversational agent with full tool access — ask anything about your dbt project")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask me about your dbt project..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = invoke_agent(prompt)
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

# ─── Page: Data Explorer ─────────────────────────────────────

elif page == "🔍 Data Explorer":
    st.title("🔍 Data Explorer")

    tab1, tab2, tab3 = st.tabs(["Sources", "Profile", "Query"])

    with tab1:
        st.subheader("dbt Sources")
        source_filter = st.text_input("Filter by source name", key="src_filter")
        if st.button("List Sources", key="btn_sources"):
            from langchain_agent.tools.exploration import list_sources

            result = list_sources.invoke({"source_name": source_filter or None})
            st.json(json.loads(result))

    with tab2:
        st.subheader("Column Profiler")
        table_name = st.text_input("Table / model name", key="prof_table")
        if st.button("Profile", key="btn_profile"):
            from langchain_agent.tools.exploration import profile_data

            result = profile_data.invoke({"table_or_model": table_name})
            data = json.loads(result)
            if "error" in data:
                st.error(data["error"])
            else:
                st.metric("Total Rows", f"{data.get('total_rows', 0):,}")
                st.dataframe(data.get("profiles", []))

    with tab3:
        st.subheader("SQL Query")
        sql = st.text_area("Enter SELECT query", height=150, key="sql_query")
        if st.button("Run Query", key="btn_query"):
            from langchain_agent.tools.exploration import run_query

            result = run_query.invoke({"sql": sql})
            data = json.loads(result)
            if "error" in data:
                st.error(data["error"])
            else:
                st.dataframe(data.get("rows", []))

# ─── Page: Model Generator ───────────────────────────────────

elif page == "🏗️ Model Generator":
    st.title("🏗️ Model Generator")

    gen_tab1, gen_tab2, gen_tab3 = st.tabs(["Silver (Intermediate)", "Gold (Marts)", "Auto-Discover"])

    with gen_tab1:
        st.subheader("Generate Silver Model")
        col1, col2 = st.columns(2)
        with col1:
            src = st.text_input("Source name", key="silver_src")
            name = st.text_input("Model name (e.g. int_orders_enriched)", key="silver_name")
        with col2:
            desc = st.text_input("Description", key="silver_desc")

        sql = st.text_area("Model SQL", height=300, key="silver_sql")

        if st.button("Generate Silver Model", key="btn_silver"):
            from langchain_agent.tools.generation import generate_silver_model

            result = generate_silver_model.invoke({
                "source_name": src,
                "model_name": name,
                "sql": sql,
                "description": desc,
            })
            data = json.loads(result)
            if "error" in data:
                st.error(data["error"])
            else:
                st.success(f"Created: {data['created']}")

    with gen_tab2:
        st.subheader("Generate Gold Model")
        col1, col2 = st.columns(2)
        with col1:
            g_src = st.text_input("Source name", key="gold_src")
            g_name = st.text_input("Model name (e.g. fct_orders)", key="gold_name")
        with col2:
            g_desc = st.text_input("Description", key="gold_desc")

        g_sql = st.text_area("Model SQL", height=300, key="gold_sql")

        if st.button("Generate Gold Model", key="btn_gold"):
            from langchain_agent.tools.generation import generate_gold_model

            result = generate_gold_model.invoke({
                "source_name": g_src,
                "model_name": g_name,
                "sql": g_sql,
                "description": g_desc,
            })
            data = json.loads(result)
            if "error" in data:
                st.error(data["error"])
            else:
                st.success(f"Created: {data['created']}")

    with gen_tab3:
        st.subheader("Auto-Discover & Generate Staging")
        col1, col2, col3 = st.columns(3)
        with col1:
            a_src = st.text_input("Source name", key="auto_src")
        with col2:
            a_db = st.text_input("Database", key="auto_db")
        with col3:
            a_schema = st.text_input("Schema", key="auto_schema")

        if st.button("Discover & Generate", key="btn_auto"):
            from langchain_agent.tools.discovery import auto_generate_staging

            with st.spinner("Discovering tables..."):
                result = auto_generate_staging.invoke({
                    "source_name": a_src,
                    "database": a_db,
                    "schema": a_schema,
                })
            data = json.loads(result)
            if "error" in data:
                st.error(data["error"])
            else:
                st.success(f"Discovered {data['tables_discovered']} tables, created {data['models_created']} models")
                st.json(data["files"])

# ─── Page: Code Review ───────────────────────────────────────

elif page == "📝 Code Review":
    st.title("📝 SQL Code Review")

    sql_input = st.text_area("Paste SQL to review", height=300, key="review_sql")
    file_path = st.text_input("File path (optional, for context)", key="review_path")

    if st.button("Review SQL", key="btn_review"):
        from langchain_agent.tools.dbt_ops import review_sql

        result = review_sql.invoke({"sql_content": sql_input, "file_path": file_path})
        data = json.loads(result)
        if data.get("status") == "clean":
            st.success("✅ No issues found!")
        else:
            st.warning(f"Found {data.get('count', 0)} issue(s)")
            for issue in data.get("issues", []):
                severity_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(
                    issue["severity"], "⚪"
                )
                st.markdown(
                    f"{severity_icon} **{issue['rule']}** (line {issue['line']}): "
                    f"{issue['message']}\n> `{issue.get('content', '')}`"
                )

# ─── Page: Data Quality ──────────────────────────────────────

elif page == "✅ Data Quality":
    st.title("✅ Data Quality Tests")

    select = st.text_input("dbt selector (optional, e.g. 'stg_japan_ecomm_data')", key="dq_select")

    if st.button("Run Tests", key="btn_dq"):
        from langchain_agent.tools.dbt_ops import check_data_quality

        with st.spinner("Running dbt test..."):
            result = check_data_quality.invoke({"select": select})
        data = json.loads(result)
        if data.get("all_passed"):
            st.success("✅ All tests passed!")
        else:
            st.error("❌ Some tests failed")
        with st.expander("Full Output"):
            st.code(data.get("output", data.get("error", "")))
