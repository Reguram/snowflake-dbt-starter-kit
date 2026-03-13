# Task 3: Build a Streamlit Dashboard

## Prompt
Create a Streamlit-in-Snowflake app that shows **order trends** with these features:

1. **KPI cards**: Total orders, Total revenue, Average order value, Total quantity
2. **Line chart**: Monthly revenue trend over time
3. **Bar chart**: Revenue by market segment
4. **Filters**: Date range picker, Market segment multi-select, Region multi-select
5. **Data table**: Top 100 orders by revenue, with pagination
6. **Cortex AI panel**: Text input where users can ask questions about the data, answered by Snowflake Cortex

Requirements:
- Use `snowflake.snowpark.context.get_active_session()` (Snowflake-native)
- Data source: `fct_orders` joined with `dim_customers`
- Cache expensive queries with `@st.cache_data`
- Handle Cortex errors gracefully

## Expected Output
- `streamlit/order_trends_app.py`
- Deploy script or instructions

## Evaluation Dimensions
- Streamlit App Scaffolding (primary)
- Snowflake-native Integration
- Context Awareness

## Scoring Notes
- 5 pts: Runs without modification, all features present, proper Snowflake APIs
- 4 pts: Minor UI issues but functional
- 3 pts: Missing some features, needs edits to run
- 2 pts: Wrong API usage or won't run in Snowflake
- 1 pts: Generic Streamlit code, not Snowflake-native
