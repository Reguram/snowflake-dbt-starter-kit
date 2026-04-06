-- =============================================================================
-- Deploy Cortex Agent + Register in Snowflake Intelligence (Generic Template)
-- =============================================================================
-- This is a REFERENCE TEMPLATE. Do NOT hardcode model-specific values here.
-- The cortex-analyst-semantic-model skill (Phase 9) generates concrete SQL
-- dynamically for any source by replacing the <PLACEHOLDER> tokens below.
--
-- Manual usage: Copy this template, replace all <PLACEHOLDER> values, and
-- execute in Cortex Code or a Snowflake Worksheet.
-- =============================================================================

-- ─── Placeholders (replace ALL before executing) ────────────────────────────
-- <DATABASE>      : Target database (e.g., DBT_DEV)
-- <SCHEMA>        : Schema containing agents + stage (e.g., SEMANTIC)
-- <STAGE>         : Stage name holding YAML files (e.g., CORTEX_ANALYST_MODELS)
-- <YAML_FILENAME> : YAML file on stage (e.g., semantic_sales_analysis.yaml)
-- <AGENT_NAME>    : Agent object name (e.g., AGENT_SALES_ANALYSIS)
-- <AGENT_DESC>    : Human-readable description for the agent
-- <TOOL_DESC>     : Description of what data/questions the tool covers
-- <WAREHOUSE>     : Warehouse for query execution (e.g., DBT_AGENT_WH)
-- <ROLE>          : Role to grant permissions to (e.g., DBT_ROLE)
-- <MARTS_SCHEMA>  : Schema containing mart tables (e.g., DBT_MARTS)

-- ─── Step 1: Verify YAML is on stage ───────────────────────────────────────
LIST @<DATABASE>.<SCHEMA>.<STAGE>;
-- Confirm your YAML file appears, is uncompressed, and has a reasonable size.

-- ─── Step 2: Create Cortex Agent ───────────────────────────────────────────
-- The agent wraps the staged YAML and exposes it as a cortex_analyst_text_to_sql
-- tool. semantic_model_file points directly to the YAML — no CREATE SEMANTIC
-- VIEW needed. The YAML provides richer metadata (synonyms, verified_queries,
-- custom_instructions) than a Semantic View object.

CREATE OR REPLACE AGENT <DATABASE>.<SCHEMA>.<AGENT_NAME>
  COMMENT = '<AGENT_DESC>'
  FROM SPECIFICATION $$
  {
    "models": {"orchestration": "auto"},
    "tools": [
      {
        "tool_spec": {
          "type": "cortex_analyst_text_to_sql",
          "name": "analyst",
          "description": "<TOOL_DESC>"
        }
      }
    ],
    "tool_resources": {
      "analyst": {
        "semantic_model_file": "@<DATABASE>.<SCHEMA>.<STAGE>/<YAML_FILENAME>",
        "execution_environment": {
          "type": "warehouse",
          "warehouse": "<WAREHOUSE>"
        }
      }
    }
  }
  $$;

-- ─── Step 3: Verify Agent ──────────────────────────────────────────────────
SHOW AGENTS IN SCHEMA <DATABASE>.<SCHEMA>;
DESCRIBE AGENT <DATABASE>.<SCHEMA>.<AGENT_NAME>;

-- ─── Step 4: Ensure Snowflake Intelligence object exists ───────────────────
SHOW SNOWFLAKE INTELLIGENCES;
-- If no rows returned, uncomment and run:
-- CREATE SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;

-- ─── Step 5: Register Agent in Snowflake Intelligence ──────────────────────
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT
  ADD AGENT <DATABASE>.<SCHEMA>.<AGENT_NAME>;

-- ─── Step 6: Grant Permissions ─────────────────────────────────────────────
GRANT USAGE ON DATABASE <DATABASE> TO ROLE <ROLE>;
GRANT USAGE ON SCHEMA <DATABASE>.<SCHEMA> TO ROLE <ROLE>;
GRANT USAGE ON AGENT <DATABASE>.<SCHEMA>.<AGENT_NAME> TO ROLE <ROLE>;
GRANT USAGE ON WAREHOUSE <WAREHOUSE> TO ROLE <ROLE>;
GRANT READ ON STAGE <DATABASE>.<SCHEMA>.<STAGE> TO ROLE <ROLE>;
GRANT SELECT ON ALL TABLES IN SCHEMA <DATABASE>.<MARTS_SCHEMA> TO ROLE <ROLE>;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE <ROLE>;

-- ─── Step 7: Test ──────────────────────────────────────────────────────────
-- Programmatic test:
-- SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_MESSAGE(
--     '@<DATABASE>.<SCHEMA>.<STAGE>/<YAML_FILENAME>',
--     [{'role': 'user', 'content': '<sample question>'}]
-- );
--
-- Or: Snowsight → AI & ML → Snowflake Intelligence → select agent → ask question

-- ─── Multi-Model Agent Pattern ─────────────────────────────────────────────
-- If a domain has multiple YAML files, add multiple tools to one agent:
--
-- "tools": [
--   {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "sales",  "description": "..."}},
--   {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "market", "description": "..."}}
-- ],
-- "tool_resources": {
--   "sales":  {"semantic_model_file": "@stage/sales.yaml",  "execution_environment": {...}},
--   "market": {"semantic_model_file": "@stage/market.yaml", "execution_environment": {...}}
-- }
--
-- Best practice: 5-10 tools per agent max. Separate agents for unrelated domains.
