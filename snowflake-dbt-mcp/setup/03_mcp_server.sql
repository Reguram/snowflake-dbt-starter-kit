/*
=============================================================================
Step 3: CREATE MCP SERVER — Snowflake Managed MCP Server
=============================================================================
This script creates the Snowflake Managed MCP Server that exposes:
  - GENERIC tools (UDFs/stored procedures from 02_udf_tools.sql)
  - CORTEX_ANALYST_MESSAGE tool (semantic view for natural language queries)
  - SYSTEM_EXECUTE_SQL tool (ad-hoc SQL execution)
=============================================================================
*/

USE ROLE ACCOUNTADMIN;
USE DATABASE DBT_DEV;
USE SCHEMA MCP_TOOLS;

-- Create the MCP Server object
-- Note: No AUTH_SECURITY_INTEGRATION needed — PATs work at the user level
CREATE OR REPLACE MCP SERVER DBT_DEV.MCP_TOOLS.DBT_AGENT_MCP
FROM SPECIFICATION $$
  tools:
    - name: "generate_dbt_model"
      type: "GENERIC"
      identifier: "DBT_DEV.MCP_TOOLS.GENERATE_DBT_MODEL"
      description: "Generate a dbt staging model SQL file and schema.yml from a source table. Reads column metadata from INFORMATION_SCHEMA and produces a properly named stg_<source>__<table> model with column renames. Accepts optional source_database and source_schema parameters (defaults to SNOWFLAKE_SAMPLE_DATA.TPCH_SF1)."
      title: "Generate dbt Model"

    - name: "review_sql"
      type: "GENERIC"
      identifier: "DBT_DEV.MCP_TOOLS.REVIEW_SQL"
      description: "Static analysis of SQL code for dbt and Snowflake best practices. Checks for hardcoded schemas, SELECT *, LIMIT clauses, missing ref()/source(), and naming conventions. Returns a production readiness score (0-10)."
      title: "Review SQL"

    - name: "check_data_quality"
      type: "GENERIC"
      identifier: "DBT_DEV.MCP_TOOLS.CHECK_DATA_QUALITY"
      description: "Run data quality checks on a Snowflake table. Checks include row count, null analysis, and duplicate detection. Returns pass/fail status for each check."
      title: "Check Data Quality"

    - name: "generate_semantic_view_ddl"
      type: "GENERIC"
      identifier: "DBT_DEV.MCP_TOOLS.GENERATE_SEMANTIC_VIEW_DDL"
      description: "Generate Snowflake Semantic View DDL from a list of dimensions and metrics. Outputs CREATE SEMANTIC VIEW statement ready to execute."
      title: "Generate Semantic View DDL"

    - name: "generate_streamlit_app"
      type: "GENERIC"
      identifier: "DBT_DEV.MCP_TOOLS.GENERATE_STREAMLIT_APP"
      description: "Generate a Streamlit-in-Snowflake application from a model/table name. Creates a complete dashboard with filters, KPIs, data table, and Cortex AI integration."
      title: "Generate Streamlit App"

    - name: "execute_query"
      type: "GENERIC"
      identifier: "DBT_DEV.MCP_TOOLS.EXECUTE_DBT_QUERY"
      description: "Execute a read-only SQL query against the Snowflake database. Supports SELECT, SHOW, DESCRIBE, and EXPLAIN statements. Returns up to 100 rows."
      title: "Execute Query"

    - name: "revenue_analyst"
      type: "CORTEX_ANALYST_MESSAGE"
      identifier: "DBT_DEV.SEMANTIC.SEM_REVENUE_ANALYSIS"
      description: "Ask natural language questions about revenue data using the Semantic View. E.g. 'What are the top 10 customers by total revenue?' or 'Show monthly revenue trend'."
      title: "Revenue Analyst"

    - name: "run_sql"
      type: "GENERIC"
      identifier: "DBT_DEV.MCP_TOOLS.EXECUTE_DBT_QUERY"
      description: "Execute SQL statements against the Snowflake database. Supports SELECT, SHOW, DESCRIBE, and EXPLAIN. Returns up to 100 rows as JSON. Use this for ad-hoc queries, table discovery, and data inspection."
      title: "Run SQL"
$$;

-- Verify the MCP server was created
SHOW MCP SERVERS IN SCHEMA DBT_DEV.MCP_TOOLS;
DESCRIBE MCP SERVER DBT_DEV.MCP_TOOLS.DBT_AGENT_MCP;
