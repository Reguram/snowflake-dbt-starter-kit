"""
dbt Agent App — Streamlit-in-Snowflake
======================================
Chat interface + panels for Model Generation, Data Quality, and Code Review.
Uses Snowflake Cortex LLM functions for natural language interaction.
"""
import json

import streamlit as st
from snowflake.snowpark.context import get_active_session

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="dbt Agent", page_icon="🔧", layout="wide")

session = get_active_session()

# Enable cross-region inference so Cortex models work regardless of region
try:
    session.sql("ALTER SESSION SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION'").collect()
except Exception:
    pass  # May already be set or require higher privileges

# ---------------------------------------------------------------------------
# System prompt (dbt conventions baked in)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a Snowflake dbt expert assistant. You help users with:
- Building dbt models (staging, intermediate, marts, semantic views)
- Snowflake SQL best practices
- Data quality testing
- Code review

Follow these conventions:
- Staging models: stg_<source>__<table> with renamed columns
- Intermediate: int_<description> for business logic
- Marts: fct_ (facts) and dim_ (dimensions) for consumption
- Semantic views: sem_<analysis> with metrics and dimensions
- Always use {{ ref() }} and {{ source() }}, never hard-code schemas
- Use CTEs, not subqueries
- Primary keys need unique + not_null tests
- Use dbt_utils.generate_surrogate_key() for surrogate keys
- Use Snowflake-native functions: DATEADD, DATEDIFF, DATE_TRUNC

Available source data: SNOWFLAKE_SAMPLE_DATA.TPCH_SF1
Tables: ORDERS, CUSTOMER, LINEITEM, NATION, REGION, SUPPLIER, PART, PARTSUPP
"""

CORTEX_MODEL = "mistral-large2"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def call_cortex(prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
    """Call Snowflake Cortex COMPLETE function."""
    messages = json.dumps([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ])
    try:
        result = session.sql(
            "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?)",
            params=[CORTEX_MODEL, messages],
        ).collect()
        return result[0][0]
    except Exception as e:
        return f"Cortex error: {e}"


def run_query(sql: str):
    """Execute SQL via Snowpark and return pandas DataFrame."""
    try:
        return session.sql(sql).to_pandas()
    except Exception as e:
        st.error(f"Query error: {e}")
        return None


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.title("🔧 dbt Agent")
page = st.sidebar.radio(
    "Navigate",
    ["💬 Chat", "📦 Model Generator", "✅ Data Quality", "🔍 Code Review", "📊 Dashboard"],
)

# ---------------------------------------------------------------------------
# Page: Chat
# ---------------------------------------------------------------------------
if page == "💬 Chat":
    st.title("💬 dbt Assistant")
    st.caption(f"Powered by Snowflake Cortex ({CORTEX_MODEL})")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about dbt, Snowflake, or this project..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Build context from conversation history
                context = "\n".join(
                    f"{m['role']}: {m['content']}"
                    for m in st.session_state.messages[-5:]
                )
                full_prompt = f"Conversation context:\n{context}\n\nRespond to the latest user message."
                response = call_cortex(full_prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# ---------------------------------------------------------------------------
# Page: Model Generator
# ---------------------------------------------------------------------------
elif page == "📦 Model Generator":
    st.title("📦 dbt Model Generator")

    col1, col2 = st.columns(2)
    with col1:
        source_name = st.text_input("Source name", value="tpch")
        table_name = st.selectbox(
            "Source table",
            ["ORDERS", "CUSTOMER", "LINEITEM", "NATION", "REGION", "SUPPLIER", "PART", "PARTSUPP"],
        )
    with col2:
        model_type = st.selectbox("Model type", ["staging", "intermediate", "mart", "semantic"])
        description = st.text_area("Description (optional)")

    if st.button("🚀 Generate Model", type="primary"):
        prompt = f"""Generate a dbt {model_type} model for the {table_name} table from source '{source_name}'.
Description: {description or 'Standard ' + model_type + ' model'}

Return:
1. The complete SQL model file
2. The schema.yml entry with tests
3. File path where it should be saved

Follow all project conventions strictly."""

        with st.spinner("Generating..."):
            result = call_cortex(prompt)
            st.markdown(result)

# ---------------------------------------------------------------------------
# Page: Data Quality
# ---------------------------------------------------------------------------
elif page == "✅ Data Quality":
    st.title("✅ Data Quality Dashboard")

    st.subheader("Test Coverage")
    # Query information_schema for tables (if available)
    models = [
        "stg_tpch__orders", "stg_tpch__customers", "stg_tpch__lineitem",
        "stg_tpch__nations", "stg_tpch__regions",
        "int_orders_enriched",
        "fct_orders", "dim_customers",
        "sem_revenue_analysis",
    ]

    test_types = {
        "stg_tpch__orders": ["unique", "not_null", "relationships", "accepted_values"],
        "stg_tpch__customers": ["unique", "not_null", "accepted_values"],
        "stg_tpch__lineitem": ["not_null", "dbt_expectations"],
        "fct_orders": ["unique", "not_null", "relationships"],
        "dim_customers": ["unique", "not_null", "accepted_values"],
    }

    for model in models:
        tests = test_types.get(model, ["not_null"])
        status = "✅" if len(tests) >= 2 else "⚠️"
        st.write(f"{status} **{model}** — Tests: {', '.join(tests)}")

    st.divider()
    st.subheader("Custom Quality Check")
    quality_query = st.text_area(
        "SQL quality check (returns failing rows)",
        value="select * from fct_orders where net_revenue < 0 and order_status = 'F'",
    )
    if st.button("Run Check"):
        df = run_query(quality_query)
        if df is not None:
            if len(df) == 0:
                st.success("✅ No failing rows found")
            else:
                st.warning(f"⚠️ {len(df)} failing rows")
                st.dataframe(df.head(100))

# ---------------------------------------------------------------------------
# Page: Code Review
# ---------------------------------------------------------------------------
elif page == "🔍 Code Review":
    st.title("🔍 SQL Code Review")

    sql_input = st.text_area(
        "Paste SQL to review",
        height=300,
        value="""select *
from MY_DB.MY_SCHEMA.ORDERS o
join MY_DB.MY_SCHEMA.CUSTOMERS c on o.customer_id = c.customer_id
where o.order_date > '2024-01-01'
LIMIT 100""",
    )

    review_scope = st.multiselect(
        "Check for",
        ["Naming conventions", "Hard-coded references", "Missing ref/source", "SELECT *",
         "LIMIT clauses", "Test coverage", "Snowflake best practices"],
        default=["Hard-coded references", "Missing ref/source", "SELECT *"],
    )

    if st.button("🔍 Review", type="primary"):
        prompt = f"""Review this SQL for a Snowflake dbt project. Check specifically for:
{chr(10).join('- ' + s for s in review_scope)}

SQL:
```sql
{sql_input}
```

For each issue found, provide:
- Severity (ERROR / WARNING / INFO)
- Line number
- Description
- Fix recommendation

End with a summary score (0-10) for production readiness."""

        with st.spinner("Reviewing..."):
            result = call_cortex(prompt)
            st.markdown(result)

# ---------------------------------------------------------------------------
# Page: Dashboard
# ---------------------------------------------------------------------------
elif page == "📊 Dashboard":
    st.title("📊 Revenue Analysis Dashboard")

    # Try to load data from the semantic model
    try:
        @st.cache_data(ttl=600)
        def load_revenue_data():
            return session.sql("""
                select
                    order_year,
                    order_month,
                    market_segment,
                    region_name,
                    customer_tier,
                    count(*) as order_count,
                    sum(net_revenue) as total_revenue,
                    avg(net_revenue) as avg_order_value,
                    sum(total_quantity) as total_quantity
                from sem_revenue_analysis
                group by 1, 2, 3, 4, 5
                order by 1, 2
            """).to_pandas()

        df = load_revenue_data()

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            segments = st.multiselect("Market Segment", sorted(df["MARKET_SEGMENT"].unique()))
        with col2:
            regions = st.multiselect("Region", sorted(df["REGION_NAME"].dropna().unique()))
        with col3:
            tiers = st.multiselect("Customer Tier", sorted(df["CUSTOMER_TIER"].unique()))

        filtered = df.copy()
        if segments:
            filtered = filtered[filtered["MARKET_SEGMENT"].isin(segments)]
        if regions:
            filtered = filtered[filtered["REGION_NAME"].isin(regions)]
        if tiers:
            filtered = filtered[filtered["CUSTOMER_TIER"].isin(tiers)]

        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Orders", f"{filtered['ORDER_COUNT'].sum():,.0f}")
        k2.metric("Total Revenue", f"${filtered['TOTAL_REVENUE'].sum():,.2f}")
        k3.metric("Avg Order Value", f"${filtered['AVG_ORDER_VALUE'].mean():,.2f}")
        k4.metric("Total Quantity", f"{filtered['TOTAL_QUANTITY'].sum():,.0f}")

        # Charts
        st.subheader("Revenue by Month")
        monthly = filtered.groupby("ORDER_MONTH")["TOTAL_REVENUE"].sum().reset_index()
        st.line_chart(monthly, x="ORDER_MONTH", y="TOTAL_REVENUE")

        st.subheader("Revenue by Segment")
        by_segment = filtered.groupby("MARKET_SEGMENT")["TOTAL_REVENUE"].sum().reset_index()
        st.bar_chart(by_segment, x="MARKET_SEGMENT", y="TOTAL_REVENUE")

    except Exception as e:
        st.info(f"Dashboard requires the sem_revenue_analysis model to be materialized. Error: {e}")
        st.write("Run `dbt build` first to materialize all models.")
