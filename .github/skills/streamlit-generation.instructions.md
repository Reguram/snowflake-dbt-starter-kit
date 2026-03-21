---
applyTo: "streamlit/**/*.py"
description: "Streamlit-in-Snowflake app patterns — Snowpark session, Cortex AI chat, dashboard layouts, deployment SQL. Auto-activates when editing Streamlit app files."
---

# Skill: Streamlit-in-Snowflake App Generation

## When to Use
Use this skill when asked to create a Streamlit app that runs inside Snowflake.

## Architecture
- Streamlit apps run on Snowflake's managed Streamlit runtime
- Access data via `snowflake.snowpark.context.get_active_session()`
- No external connections needed — all data access is through Snowpark
- AI features use `SNOWFLAKE.CORTEX.COMPLETE()` for LLM capabilities

## App Structure Template
```python
import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="App Title", layout="wide")
st.title("App Title")

session = get_active_session()

# Load data
@st.cache_data(ttl=600)
def load_data():
    return session.table("TABLE_NAME").to_pandas()

# Build UI...
```

## Common Patterns

### Data Dashboard
- Sidebar filters (multiselect, date range)
- KPI cards in columns
- Charts (line, bar, area) from pandas data
- Data table with pagination

### Cortex AI Chat
```python
user_question = st.text_input("Ask a question:")
if user_question:
    prompt = f"Context: ... Question: {user_question}"
    result = session.sql(
        "SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', ?)",
        params=[prompt]
    ).collect()
    st.write(result[0][0])
```

### Deployment
```sql
CREATE STAGE IF NOT EXISTS my_streamlit_stage;
PUT file://streamlit/app.py @my_streamlit_stage AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

CREATE OR REPLACE STREAMLIT my_app
  ROOT_LOCATION = '@my_streamlit_stage'
  MAIN_FILE = 'app.py'
  QUERY_WAREHOUSE = 'DBT_AGENT_WH';
```

## Best Practices
- Use `@st.cache_data(ttl=600)` for expensive queries
- Limit dataframe sizes with `.limit()` before `.to_pandas()`
- Use Snowflake-native functions for aggregation (push compute to warehouse)
- Handle Cortex errors gracefully with try/except
- Keep system prompts concise but include schema context
