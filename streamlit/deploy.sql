-- Deploy Streamlit App to Snowflake
-- Run these commands in a Snowflake worksheet or via SnowSQL

-- 1. Create a stage for the Streamlit app files
CREATE STAGE IF NOT EXISTS DBT_DEV.PUBLIC.STREAMLIT_STAGE
  DIRECTORY = (ENABLE = TRUE);

-- 2. Upload app file to stage
-- Via SnowSQL: PUT file://streamlit/dbt_agent_app.py @DBT_DEV.PUBLIC.STREAMLIT_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- 3. Create the Streamlit app
CREATE OR REPLACE STREAMLIT DBT_DEV.PUBLIC.DBT_AGENT_APP
  ROOT_LOCATION = '@DBT_DEV.PUBLIC.STREAMLIT_STAGE'
  MAIN_FILE = 'dbt_agent_app.py'
  QUERY_WAREHOUSE = 'DBT_AGENT_WH'
  COMMENT = 'dbt Agent — Chat + Model Gen + Data Quality + Code Review';

-- 4. Grant access (adjust role as needed)
-- GRANT USAGE ON STREAMLIT DBT_DEV.PUBLIC.DBT_AGENT_APP TO ROLE ANALYST_ROLE;


CREATE STREAMLIT DBT_DEV.MCP_TOOLS.MEDALLION_ADVISOR_APP
  ROOT_LOCATION = '@DBT_DEV.MCP_TOOLS.STREAMLIT_STAGE'
  MAIN_FILE = 'medallion_advisor_app.py';