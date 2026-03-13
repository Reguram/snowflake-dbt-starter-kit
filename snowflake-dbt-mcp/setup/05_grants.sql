/*
=============================================================================
Step 5: RBAC Grants — Access Control for MCP Server & Tools
=============================================================================
Grants the DBT_MCP_ROLE access to:
  1. The MCP SERVER object itself
  2. Each individual tool (UDF / stored procedure)
  3. Underlying data objects (tables, views, schemas)
=============================================================================
*/

USE ROLE ACCOUNTADMIN;

-- ==========================================
-- 1. Grant MCP Server access to the role
-- ==========================================
GRANT USAGE ON MCP SERVER DBT_DEV.MCP_TOOLS.DBT_AGENT_MCP
    TO ROLE DBT_MCP_ROLE;


-- ==========================================
-- 2. Grant USAGE on each tool
-- ==========================================

-- Tool: generate_dbt_model (UDF)
GRANT USAGE ON FUNCTION DBT_DEV.MCP_TOOLS.GENERATE_DBT_MODEL(VARCHAR, VARCHAR)
    TO ROLE DBT_MCP_ROLE;

-- Tool: review_sql (UDF)
GRANT USAGE ON FUNCTION DBT_DEV.MCP_TOOLS.REVIEW_SQL(VARCHAR, VARCHAR)
    TO ROLE DBT_MCP_ROLE;

-- Tool: check_data_quality (Stored Procedure)
GRANT USAGE ON PROCEDURE DBT_DEV.MCP_TOOLS.CHECK_DATA_QUALITY(VARCHAR, VARCHAR)
    TO ROLE DBT_MCP_ROLE;

-- Tool: generate_semantic_view_ddl (UDF)
GRANT USAGE ON FUNCTION DBT_DEV.MCP_TOOLS.GENERATE_SEMANTIC_VIEW_DDL(VARCHAR, VARCHAR, VARCHAR)
    TO ROLE DBT_MCP_ROLE;

-- Tool: generate_streamlit_app (UDF)
GRANT USAGE ON FUNCTION DBT_DEV.MCP_TOOLS.GENERATE_STREAMLIT_APP(VARCHAR, VARCHAR)
    TO ROLE DBT_MCP_ROLE;

-- Tool: execute_dbt_query (Stored Procedure)
GRANT USAGE ON PROCEDURE DBT_DEV.MCP_TOOLS.EXECUTE_DBT_QUERY(VARCHAR)
    TO ROLE DBT_MCP_ROLE;


-- ==========================================
-- 3. Grant access to underlying data
-- ==========================================

-- Source data (read-only)
-- ⚠️ Replace with your actual source database/schema if not using TPC-H
-- SET SOURCE_DB = 'SNOWFLAKE_SAMPLE_DATA';
-- SET SOURCE_SCHEMA = 'TPCH_SF1';
GRANT USAGE ON DATABASE SNOWFLAKE_SAMPLE_DATA TO ROLE DBT_MCP_ROLE;
GRANT USAGE ON SCHEMA SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 TO ROLE DBT_MCP_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA SNOWFLAKE_SAMPLE_DATA.TPCH_SF1
    TO ROLE DBT_MCP_ROLE;

-- dbt output database
GRANT USAGE ON DATABASE DBT_DEV TO ROLE DBT_MCP_ROLE;
GRANT USAGE ON ALL SCHEMAS IN DATABASE DBT_DEV TO ROLE DBT_MCP_ROLE;
GRANT SELECT ON ALL TABLES IN DATABASE DBT_DEV TO ROLE DBT_MCP_ROLE;
GRANT SELECT ON ALL VIEWS IN DATABASE DBT_DEV TO ROLE DBT_MCP_ROLE;
GRANT SELECT ON FUTURE TABLES IN DATABASE DBT_DEV TO ROLE DBT_MCP_ROLE;
GRANT SELECT ON FUTURE VIEWS IN DATABASE DBT_DEV TO ROLE DBT_MCP_ROLE;

-- Warehouse
GRANT USAGE ON WAREHOUSE DBT_AGENT_WH TO ROLE DBT_MCP_ROLE;

-- Semantic view (for CORTEX_ANALYST_MESSAGE tool)
-- This only applies after dbt has been run and the semantic view has been created
-- GRANT SELECT ON VIEW DBT_DEV.SEMANTIC.SEM_REVENUE_ANALYSIS TO ROLE DBT_MCP_ROLE;


-- ==========================================
-- 4. Assign the role to your user
-- Replace <YOUR_USERNAME> with your Snowflake username
-- ==========================================
-- GRANT ROLE DBT_MCP_ROLE TO USER <YOUR_USERNAME>;


-- ==========================================
-- 5. Verify grants
-- ==========================================
SHOW GRANTS TO ROLE DBT_MCP_ROLE;
SHOW GRANTS ON MCP SERVER DBT_DEV.MCP_TOOLS.DBT_AGENT_MCP;
