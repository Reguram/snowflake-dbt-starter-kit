-- =============================================================================
-- Snowflake RBAC Setup for Cortex Analyst / Copilot / Intelligence
-- =============================================================================
-- PURPOSE: Create a LEAST-PRIVILEGE role hierarchy so that Cortex Copilot,
--          Cortex Analyst, and Snowflake Intelligence never run as ACCOUNTADMIN.
--
-- Role Hierarchy:
--   ACCOUNTADMIN  (one-time setup only — never used at runtime)
--       └── DBT_ROLE  (dbt build, model deployment)
--             └── CORTEX_ANALYST_ROLE  (Cortex Analyst / Copilot / Intelligence)
--
-- CORTEX_ANALYST_ROLE can:
--   ✓ Read mart tables (SELECT)
--   ✓ Read semantic views (USAGE on SEMANTIC schema)
--   ✓ Read staged YAML files (READ on internal stage)
--   ✓ Use the warehouse (USAGE)
--   ✓ Invoke Cortex Agents (USAGE on AGENT)
--   ✓ Query via Snowflake Intelligence
--
-- CORTEX_ANALYST_ROLE cannot:
--   ✗ Create/alter/drop ANY objects
--   ✗ Access staging or intermediate schemas
--   ✗ Modify source data
--   ✗ Manage roles, users, or warehouses
--   ✗ Access ACCOUNT_USAGE or ORGANIZATION_USAGE
-- =============================================================================

-- Run as ACCOUNTADMIN (one-time setup)
USE ROLE ACCOUNTADMIN;

-- ─── 1. Create the Cortex Analyst Role ─────────────────────────────────────
CREATE ROLE IF NOT EXISTS CORTEX_ANALYST_ROLE
  COMMENT = 'Least-privilege role for Cortex Analyst, Copilot, and Snowflake Intelligence. Read-only access to marts, semantic views, and agents.';

-- ─── 2. Database & Schema Access (read-only) ──────────────────────────────
GRANT USAGE ON DATABASE DBT_DEV TO ROLE CORTEX_ANALYST_ROLE;

-- Marts — read-only SELECT on all current and future tables
GRANT USAGE ON SCHEMA DBT_DEV.DBT_MARTS TO ROLE CORTEX_ANALYST_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA DBT_DEV.DBT_MARTS TO ROLE CORTEX_ANALYST_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA DBT_DEV.DBT_MARTS TO ROLE CORTEX_ANALYST_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA DBT_DEV.DBT_MARTS TO ROLE CORTEX_ANALYST_ROLE;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA DBT_DEV.DBT_MARTS TO ROLE CORTEX_ANALYST_ROLE;

-- Semantic schema — usage + read semantic views + read staged YAML files
GRANT USAGE ON SCHEMA DBT_DEV.SEMANTIC TO ROLE CORTEX_ANALYST_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA DBT_DEV.SEMANTIC TO ROLE CORTEX_ANALYST_ROLE;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA DBT_DEV.SEMANTIC TO ROLE CORTEX_ANALYST_ROLE;

-- Internal stage for Cortex Analyst YAML models (read-only)
GRANT READ ON STAGE DBT_DEV.SEMANTIC.CORTEX_ANALYST_MODELS TO ROLE CORTEX_ANALYST_ROLE;

-- ─── 3. Warehouse Access ───────────────────────────────────────────────────
GRANT USAGE ON WAREHOUSE DBT_AGENT_WH TO ROLE CORTEX_ANALYST_ROLE;

-- ─── 4. Agent Permissions ──────────────────────────────────────────────────
-- Grant USAGE on all current agents in the SEMANTIC schema
-- (future agents must be granted manually or via a post-deploy hook)
GRANT USAGE ON ALL AGENTS IN SCHEMA DBT_DEV.SEMANTIC TO ROLE CORTEX_ANALYST_ROLE;

-- ─── 5. Snowflake Intelligence Access ──────────────────────────────────────
-- Uncomment after creating the SI object:
-- GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT
--   TO ROLE CORTEX_ANALYST_ROLE;

-- ─── 6. Source Data Access (read-only for NL querying context) ─────────────
-- Only if Cortex Analyst needs to query source tables directly (rare):
-- GRANT USAGE ON DATABASE COVID19_EPIDEMIOLOGICAL_DATA TO ROLE CORTEX_ANALYST_ROLE;
-- GRANT USAGE ON SCHEMA COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC TO ROLE CORTEX_ANALYST_ROLE;
-- GRANT SELECT ON ALL TABLES IN SCHEMA COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC
--   TO ROLE CORTEX_ANALYST_ROLE;

-- ─── 7. Role Hierarchy ────────────────────────────────────────────────────
-- DBT_ROLE inherits CORTEX_ANALYST_ROLE (so dbt devs also get analyst access)
GRANT ROLE CORTEX_ANALYST_ROLE TO ROLE DBT_ROLE;

-- ─── 8. Assign to Users ───────────────────────────────────────────────────
-- Direct assignment for analysts / Copilot users who don't need dbt build perms
-- GRANT ROLE CORTEX_ANALYST_ROLE TO USER <ANALYST_USER>;

-- For Cortex Copilot / Snowflake Intelligence sessions:
-- Users should set their session role to CORTEX_ANALYST_ROLE:
--   USE ROLE CORTEX_ANALYST_ROLE;
-- Or configure it as the default role for analyst users:
-- ALTER USER <ANALYST_USER> SET DEFAULT_ROLE = 'CORTEX_ANALYST_ROLE';

-- ─── 9. Verify Grants ─────────────────────────────────────────────────────
SHOW GRANTS TO ROLE CORTEX_ANALYST_ROLE;

SELECT 'CORTEX_ANALYST_ROLE setup complete!' AS status;

-- =============================================================================
-- USAGE NOTES
-- =============================================================================
-- 1. Cortex Copilot: Set session role to CORTEX_ANALYST_ROLE before using
--    Copilot in Snowsight. This ensures Copilot only sees marts + semantic views.
--
-- 2. Cortex Analyst: Agents created in SEMANTIC schema are accessible via
--    CORTEX_ANALYST_ROLE. The agent's warehouse is DBT_AGENT_WH (XS).
--
-- 3. Snowflake Intelligence: After registering agents, grant SI object usage
--    to CORTEX_ANALYST_ROLE (Step 5 above).
--
-- 4. Adding new domains: When a new mart schema or agent is created, run:
--    GRANT SELECT ON ALL TABLES IN SCHEMA DBT_DEV.<NEW_MARTS_SCHEMA>
--      TO ROLE CORTEX_ANALYST_ROLE;
--    GRANT USAGE ON AGENT DBT_DEV.SEMANTIC.<NEW_AGENT>
--      TO ROLE CORTEX_ANALYST_ROLE;
--
-- 5. NEVER grant ACCOUNTADMIN or SYSADMIN to Cortex sessions.
--    CORTEX_ANALYST_ROLE is read-only by design.
-- =============================================================================
