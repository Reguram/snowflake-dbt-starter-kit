/*
=============================================================================
Snowflake Managed MCP Server — Setup Script
=============================================================================
This script creates the Snowflake-managed MCP server object and all supporting
UDFs/stored procedures that act as MCP tools.

Run this in a Snowflake worksheet (Snowsight) or via SnowSQL.

Prerequisites:
  - A Snowflake account with ACCOUNTADMIN or a role with CREATE MCP SERVER privilege
  - The dbt project models already materialized (run `dbt build` first)
  - A warehouse (DBT_AGENT_WH) and database (DBT_DEV) created

Order of execution:
  1. setup/01_database_objects.sql   — database, schema, warehouse, roles
  2. setup/02_udf_tools.sql          — UDFs and stored procedures for custom tools
  3. setup/03_mcp_server.sql         — CREATE MCP SERVER with all tools
  4. setup/04_oauth_security.sql     — PAT security integration (replaces OAuth)
  5. setup/05_grants.sql             — RBAC grants for MCP server and tools

=============================================================================
*/

-- ==========================================
-- Step 1: Database & Schema Setup
-- ==========================================
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS DBT_DEV;
CREATE SCHEMA IF NOT EXISTS DBT_DEV.MCP_TOOLS;
CREATE SCHEMA IF NOT EXISTS DBT_DEV.PUBLIC;

-- Warehouse for MCP tool execution
CREATE WAREHOUSE IF NOT EXISTS DBT_AGENT_WH
  WAREHOUSE_SIZE = 'X-SMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  COMMENT = 'Warehouse for dbt agent MCP tools';

-- Role for MCP server operations
CREATE ROLE IF NOT EXISTS DBT_MCP_ROLE
  COMMENT = 'Role for Snowflake managed MCP server operations';

GRANT USAGE ON DATABASE DBT_DEV TO ROLE DBT_MCP_ROLE;
GRANT USAGE ON SCHEMA DBT_DEV.MCP_TOOLS TO ROLE DBT_MCP_ROLE;
GRANT USAGE ON SCHEMA DBT_DEV.PUBLIC TO ROLE DBT_MCP_ROLE;
GRANT USAGE ON WAREHOUSE DBT_AGENT_WH TO ROLE DBT_MCP_ROLE;

-- Grant access to source data for the tools
-- ⚠️ Replace SNOWFLAKE_SAMPLE_DATA with your source database if not using TPC-H
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_SAMPLE_DATA TO ROLE DBT_MCP_ROLE;
