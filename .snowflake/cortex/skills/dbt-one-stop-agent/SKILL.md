---
name: dbt-one-stop-agent
description: >
  Unified, context-aware dbt agent combining ALL project capabilities: source discovery,
  staging/intermediate/marts model generation, Cortex Analyst semantic model creation,
  Snowflake Agent deployment, Snowflake Intelligence registration, code review,
  data quality checks, medallion architecture advising, dbt CLI operations, and Streamlit app
  scaffolding. Always reads existing project state before generating code — produces models that
  fit the existing project rather than generic boilerplate.
  Use when: building any dbt model, discovering new data sources, creating semantic models,
  deploying agents, enabling Snowflake Intelligence, reviewing code, checking data quality,
  or asking questions about the project.
  Triggers: onboard, discover, build, generate, semantic model, cortex analyst, agent, intelligence,
  pipeline, end-to-end, rbac, cortex role, semantic views for domain.
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "4.0"
---

# dbt One-Stop Agent

> **Unified agent** that replaces separate scripts for source discovery, model generation,
> semantic views, code review, and medallion advising. One tool for the entire dbt lifecycle.

## What This Skill Does

| Capability | Description |
|-----------|-------------|
| **Source Discovery** | Connects to any Snowflake database/schema, discovers tables, auto-generates staging models with proper naming, tests, and documentation |
| **Model Generation** | Creates intermediate (silver) and marts (gold) models with context-aware SQL — reads existing models before generating |
| **Cortex Analyst Semantic Models** | Generates YAML semantic models with synonyms, sample_values, verified_queries, and custom_instructions — uploaded to Snowflake stage for `CORTEX_ANALYST_MESSAGE()` NL querying |
| **Domain Semantic Views** | Batch-generate semantic views for ALL marts in a domain with auto-classified dims/metrics and verified queries |
| **Cortex Agent Creation** | Generate Cortex Agent SQL bundling all semantic views for a domain as `cortex_analyst_text_to_sql` tools |
| **End-to-End Pipeline** | Full pipeline: Discover → Stage → Marts → Validate → Semantic Views → Agent — one command |
| **Snowflake Agent Deployment** | Creates Cortex Agents (`CREATE AGENT`) wired to semantic models for text-to-SQL |
| **Snowflake Intelligence** | Registers agents with Snowflake Intelligence for org-wide natural language querying in the Snowsight UI |
| **RBAC / Security** | Least-privilege `CORTEX_ANALYST_ROLE` for Copilot/Analyst — never ACCOUNTADMIN |
| **Code Review** | Static analysis against project conventions: naming, `ref()` usage, hard-coded schemas, missing tests |
| **Data Quality** | Runs dbt tests, profiles columns for null rates and cardinality, validates data pipelines |
| **Medallion Advising** | Suggests silver/gold models based on existing bronze data using Cortex LLM |
| **dbt Operations** | Run, build, test, compile, seed via dbt CLI |
| **Streamlit Apps** | Generate Streamlit-in-Snowflake dashboards from mart models |

## When to Invoke This Skill

- User asks to build, generate, or scaffold any dbt model
- User wants to discover or onboard a new data source
- User asks about project state ("what sources do I have?")
- User wants a Cortex Analyst semantic model (YAML) for NL querying
- User wants to create a Snowflake Agent for text-to-SQL
- User wants to register an agent with Snowflake Intelligence
- User asks for code review or data quality checks
- User wants to run dbt commands
- User asks about medallion architecture or layer design
- User wants a Streamlit dashboard
- User wants to run the full end-to-end pipeline (discover → semantic → agent)
- User asks about semantic views for all marts in a domain
- User asks about RBAC, roles, or security for Cortex Copilot
- User wants to create a domain-level Cortex Agent

## Context-Awareness (CRITICAL)

This agent is **NOT deterministic/generic**. Before generating ANY code, it:

1. **Reads existing models** — understands what staging, intermediate, marts models already exist
2. **Profiles actual data** — queries Snowflake for column types, cardinality, null rates
3. **Inspects schema.yml** — knows which tests and descriptions are already defined
4. **Understands the DAG** — resolves model references and avoids generating duplicates
5. **Checks naming conventions** — ensures output matches `stg_<source>__<table>`, `int_<desc>`, `fct_<entity>`, `dim_<entity>`

## How to Run

### Interactive CLI (Cortex-powered chat)
```bash
python scripts/dbt_agent.py
```

### Single Question
```bash
python scripts/dbt_agent.py --ask "What sources do I have?"
```

### MCP Server (VS Code / Cortex Code)
```bash
python scripts/dbt_agent.py --mcp
```

## Available Tools

| Tool | Parameters | What It Does |
|------|-----------|-------------|
| `project_context` | *(none)* | Get project summary: sources, model counts, layer breakdown |
| `discover_source` | `source_database`, `source_schema`, `source_name?`, `dry_run?` | Discover tables and generate staging + mart models |
| `list_sources` | `source_name?` | List dbt source definitions |
| `list_models` | `layer?`, `source_name?` | List models by layer |
| `read_model` | `model_name` | Read a model's SQL source code |
| `sample_data` | `table_or_model`, `limit?` | Query sample rows from Snowflake |
| `describe_table` | `table_or_model` | Get column metadata + row count |
| `profile_data` | `table_or_model`, `max_columns?` | Profile: distinct counts, null rates, cardinality |
| `run_query` | `sql` | Execute read-only SQL query |
| `generate_model` | `layer`, `source_name`, `model_name`, `sql`, `description?` | Create/update any dbt model + schema.yml |
| `generate_semantic_model` | `model_name`, `source_name?` | Generate Cortex Analyst YAML semantic model from a mart |
| `upload_semantic_model` | `yaml_filename` | Upload YAML to `@<DB>.SEMANTIC.CORTEX_ANALYST_MODELS` stage |
| `deploy_agent` | `model_name`, `agent_name?`, `warehouse?` | Create Snowflake Agent wired to semantic model YAML |
| `register_intelligence` | `agent_name` | Register agent with Snowflake Intelligence UI |
| `review_sql` | `model_name?`, `sql_content?` | Static analysis for best practices |
| `check_data_quality` | `select?` | Run dbt tests |
| `run_dbt` | `command`, `select?`, `full_refresh?` | Execute dbt CLI commands |
| `generate_streamlit_app` | `model_name`, `app_title?` | Scaffold Streamlit dashboard |
| `generate_domain_semantic_views` | `domain`, `overwrite?`, `dry_run?` | Auto-generate semantic views for ALL marts in a domain |
| `create_domain_agent` | `domain`, `database?`, `register_si?`, `dry_run?` | Create Cortex Agent SQL bundling all semantic views for a domain |
| `run_end_to_end_pipeline` | `domain`, `skip_discover?`, `register_si?`, `source_database?`, `source_schema?`, `source_name?`, `overwrite?`, `dry_run?` | Full pipeline: Discover → Stage → Marts → Build → Semantic → Agent |

## Workflow Examples

### Discover a New Data Source
```
User: "Discover tables in COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC"
Agent:
  1. Calls project_context() to see current state
  2. Calls discover_source(source_database="COVID19_EPIDEMIOLOGICAL_DATA", source_schema="PUBLIC", source_name="covid19_data")
  3. Reports: tables found, staging models created, mart models created
  4. Auto-runs dbt build for the new models
```

### Build a Silver Model
```
User: "Create an intermediate model that enriches orders with customer data"
Agent:
  1. Calls list_models(layer="staging") to find source models
  2. Calls read_model("stg_tpch__orders") to understand columns
  3. Calls read_model("stg_tpch__customers") to understand join keys
  4. Calls profile_data("stg_tpch__orders") to check cardinality
  5. Generates int_orders_enriched with proper joins and naming
  6. Auto-builds and reports results
```

### Create a Cortex Analyst Semantic Model
```
User: "Create a semantic model for fct_orders"
Agent:
  1. Reads fct_orders model and schema.yml
  2. Profiles columns from Snowflake (cardinality, nulls, sample values)
  3. Auto-classifies: time_dimensions (dates), dimensions (categories), facts (metrics)
  4. Generates synonyms, sample_values per column
  5. Writes 3-5 verified_queries and tests them via run_query()
  6. Writes custom_instructions for text-to-SQL accuracy
  7. Saves YAML to cortex-analyst-models/semantic_<name>.yaml
  8. Uploads to @<DB>.SEMANTIC.CORTEX_ANALYST_MODELS stage
  9. Tests with CORTEX_ANALYST_MESSAGE()
```

### Deploy a Snowflake Agent + Snowflake Intelligence
```
User: "Deploy an agent for fct_orders and register with Snowflake Intelligence"
Agent:
  1. Verifies semantic model YAML exists on stage (or generates it first)
  2. Derives variables: DATABASE, SCHEMA, WAREHOUSE from profiles.yml/dbt_project.yml
  3. Generates CREATE AGENT SQL with cortex_analyst_text_to_sql tool spec
  4. Executes CREATE AGENT via run_query()
  5. Registers with: ALTER SNOWFLAKE INTELLIGENCE ... ADD AGENT
  6. Grants permissions: USAGE on agent, warehouse, stage, schema
  7. Verifies: DESCRIBE AGENT, test question via Snowflake Intelligence UI
```

## Review Enforcement

All model writes are **automatically reviewed** before being written to disk. This is a code-level gate — it cannot be skipped by the LLM.

### How it works
- `generate_model` and `write_medallion_model` run static analysis before writing
- `discover_source` reviews generated mart models before writing (staging models are template-trusted)
- After auto-build, each generated model is reviewed and results are returned to the LLM

### Severity levels

| Severity | Effect | Example |
|----------|--------|---------|
| **error** | **Blocks write** — returns `REVIEW_BLOCKED` | Hard-coded `database.schema.table` (use `ref()`/`source()`) |
| **warning** | Write succeeds, reported in response | `SELECT *` in marts, missing `ref()`, naming violations |
| **info** | Write succeeds, reported in response | `LIMIT` clause in production model |

### Review rules

| Rule ID | Pattern | Severity |
|---------|---------|----------|
| `HARDCODED_SCHEMA` | `FROM/JOIN db.schema.table` | error |
| `NO_SELECT_STAR_MARTS` | `SELECT *` in marts/semantic | warning |
| `MISSING_REF` | Direct table reference without `ref()`/`source()` | warning |
| `NO_LIMIT` | `LIMIT N` in model SQL | info |
| `NAMING_STG` | Staging model not prefixed `stg_` | warning |

### Force bypass
Pass `force=True` (agent) or `force=true` (MCP) to write despite error-severity issues. The errors are still reported in the response `review` field.

## Project Conventions

- **Staging**: `stg_<source>__<table>` — 1:1 with source, rename columns to snake_case
- **Intermediate**: `int_<description>` — joins, dedup, business logic
- **Marts**: `fct_<entity>` (facts) or `dim_<entity>` (dimensions) — consumption-ready
- **Semantic Models**: `cortex-analyst-models/semantic_<name>.yaml` — Cortex Analyst YAML files
- Always use `{{ ref() }}` and `{{ source() }}`
- Use CTEs, not subqueries
- Use `dbt_utils.generate_surrogate_key()` for surrogate keys
- Every model must have a schema.yml entry with description and tests

---

## Cortex Analyst Semantic Model Workflow

> This is the **agentic workflow** for creating Cortex Analyst YAML semantic models,
> deploying Snowflake Agents, and registering with Snowflake Intelligence.
> Reference: `$cortex-analyst-semantic-model` skill for full specification.

### Phase 1: Generate YAML Semantic Model

For a given mart model (e.g., `fct_orders`):

#### 1.1 — Profile columns via MCP

```sql
-- Column metadata
SELECT column_name, data_type, is_nullable
FROM <DATABASE>.information_schema.columns
WHERE table_schema = 'DBT_MARTS' AND table_name = '<TABLE>'
ORDER BY ordinal_position;

-- Cardinality per column
SELECT '<COL>' AS col, COUNT(DISTINCT "<COL>") AS distinct_count,
       COUNT(*) - COUNT("<COL>") AS null_count
FROM <DATABASE>.DBT_MARTS.<TABLE>;

-- Sample values
SELECT DISTINCT "<COL>" FROM <DATABASE>.DBT_MARTS.<TABLE>
WHERE "<COL>" IS NOT NULL LIMIT 5;
```

#### 1.2 — Classify columns

| Column Pattern | YAML Section | default_aggregation |
|---------------|--------------|--------------------|
| DATE / TIMESTAMP | `time_dimensions` | — |
| VARCHAR / BOOLEAN (low cardinality) | `dimensions` | — |
| VARCHAR (high cardinality, e.g. names) | `dimensions` | — |
| NUMBER / FLOAT (`*_amount`, `*_sales`, `*_total`, `*_count`) | `facts` | `sum` |
| NUMBER / FLOAT (`*_rate`, `*_pct`, `*_ratio`, `*_avg`) | `facts` | `avg` |
| Surrogate key (`*_id`, `*_key`) | `primary_key` | exclude from dims/facts |
| ETL columns (`*_loaded`, `*_etl`) | skip | — |

**Use AI reasoning on actual sample values** — don't rely on regex alone.

#### 1.3 — Generate synonyms (2–5 per column)

Examples:
- `ITEM_CATEGORY` → `["category", "product type", "product category"]`
- `MAKER` → `["brand", "manufacturer", "vendor"]`
- `TOTAL_VIEWS` → `["views", "page views", "impressions"]`

#### 1.4 — Generate and TEST verified queries

Create 3–5 verified queries covering these patterns:

| Pattern | Example |
|---------|--------|
| Summary | "What is the total revenue?" |
| Time Trend | "Show sales by month" |
| Top-N | "Top 10 brands by revenue" |
| Dimensional | "Revenue by category and month" |
| Filtered | "Sales for electronics in 2024" |

**CRITICAL:** Execute each query via `run_query()` to verify it works. Fix syntax errors
(double-quote column names). Only include passing queries in the YAML.

#### 1.5 — Write custom_instructions

Free text that maps business terms to SQL:
```
- "revenue" means SUM(TOTAL_SALES)
- "last month" means DATEADD('month', -1, CURRENT_DATE())
- Always order trend queries by date DESC
- Column names are UPPER_CASE in Snowflake
```

#### 1.6 — Assemble YAML

Write to `cortex-analyst-models/semantic_<source_name>_<entity>.yaml`:

```yaml
name: SEM_<ENTITY>
tables:
  - name: FCT_<ENTITY>
    description: |
      <Multi-line: grain, features, business context>
    base_table:
      database: <TARGET_DB>     # From profiles.yml (e.g., DBT_DEV)
      schema: DBT_MARTS         # Where mart TABLE lives
      table: FCT_<ENTITY>
    dimensions:
      - name: <COL>
        synonyms: [<syn1>, <syn2>]
        description: <desc>
        expr: <COL>
        data_type: <TYPE>
        sample_values: [<val1>, <val2>]
    time_dimensions:
      - name: <DATE_COL>
        synonyms: [<syn1>]
        description: <desc>
        expr: <DATE_COL>
        data_type: DATE
        sample_values: ["2024-01-01"]
    facts:
      - name: <METRIC>
        synonyms: [<syn1>, <syn2>]
        description: <desc>
        expr: <METRIC>
        data_type: NUMBER
        default_aggregation: sum
        sample_values: [100, 500]
    primary_key:
      columns: [<pk_col>]
verified_queries:
  - name: <query_name>
    question: "<NL question>"
    use_as_onboarding_question: true
    sql: "<TESTED SQL>"
    verified_by: cortex_code_agent
    verified_at: <unix_timestamp>
custom_instructions: |
  <Free text for text-to-SQL accuracy>
```

**Schema distinction:**
- `base_table.schema` = `DBT_MARTS` (where data lives)
- Upload stage = `SEMANTIC` schema (where YAML files go)

### Phase 2: Upload to Snowflake Stage

Use pure-SQL TEMP TABLE → COPY INTO (works in Cortex Code, no local filesystem):

```sql
-- Ensure stage exists
CREATE STAGE IF NOT EXISTS <TARGET_DB>.SEMANTIC.CORTEX_ANALYST_MODELS
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  COMMENT = 'Internal stage for Cortex Analyst YAML semantic models';

-- Upload via temp table
CREATE OR REPLACE TEMPORARY TABLE <TARGET_DB>.SEMANTIC.TEMP_YAML_CONTENT (LINE_CONTENT VARCHAR)
AS SELECT $$
<ENTIRE YAML CONTENT>
$$;

COPY INTO @<TARGET_DB>.SEMANTIC.CORTEX_ANALYST_MODELS/<filename>.yaml
  FROM (SELECT LINE_CONTENT FROM <TARGET_DB>.SEMANTIC.TEMP_YAML_CONTENT)
  FILE_FORMAT = (TYPE = 'CSV' COMPRESSION = 'NONE' FIELD_DELIMITER = 'NONE' RECORD_DELIMITER = 'NONE')
  SINGLE = TRUE OVERWRITE = TRUE HEADER = FALSE;

-- Verify
LIST @<TARGET_DB>.SEMANTIC.CORTEX_ANALYST_MODELS PATTERN = '.*<filename>.*';

-- Clean up
DROP TABLE IF EXISTS <TARGET_DB>.SEMANTIC.TEMP_YAML_CONTENT;
```

### Phase 3: Test with Cortex Analyst

```sql
SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_MESSAGE(
  '@<TARGET_DB>.SEMANTIC.CORTEX_ANALYST_MODELS/<filename>.yaml',
  [{'role': 'user', 'content': '<test question from verified_queries>'}]
);
```

If incorrect, refine synonyms / verified_queries / custom_instructions and re-upload.

### Phase 4: Deploy Snowflake Agent

#### 4.1 — Derive variables from project context (do NOT ask user)

| Variable | Source |
|----------|--------|
| `DATABASE` | `profiles.yml` → target `database` |
| `SCHEMA` | `SEMANTIC` (where agents + stage live) |
| `WAREHOUSE` | `profiles.yml` or `dbt_project.yml` |
| `AGENT_NAME` | `AGENT_` + uppercase entity (e.g., `AGENT_SALES_ANALYSIS`) |
| `YAML_FILENAME` | From Phase 1 output |

#### 4.2 — Check for existing agent

```sql
SHOW AGENTS IN SCHEMA <DATABASE>.SEMANTIC;
```

- If exists → use `CREATE OR REPLACE`
- If different agent covers same tables → warn about overlap

#### 4.3 — Create the agent

```sql
CREATE OR REPLACE AGENT <DATABASE>.SEMANTIC.<AGENT_NAME>
  COMMENT = '<description of what data and questions it handles>'
  FROM SPECIFICATION $$
  {
    "models": {"orchestration": "auto"},
    "tools": [{
      "tool_spec": {
        "type": "cortex_analyst_text_to_sql",
        "name": "analyst",
        "description": "<what tables, data, and question types this covers>"
      }
    }],
    "tool_resources": {
      "analyst": {
        "semantic_model_file": "@<DATABASE>.SEMANTIC.CORTEX_ANALYST_MODELS/<filename>.yaml",
        "execution_environment": {
          "type": "warehouse",
          "warehouse": "<WAREHOUSE>"
        }
      }
    }
  }
  $$;
```

**Multi-model agents:** If the domain has multiple YAML files, add one tool per YAML:
```json
"tools": [
  {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "sales", "description": "..."}},
  {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "products", "description": "..."}}
],
"tool_resources": {
  "sales": {"semantic_model_file": "@stage/sales.yaml", ...},
  "products": {"semantic_model_file": "@stage/products.yaml", ...}
}
```
Best practice: 5–10 tools per agent max.

#### 4.4 — Verify agent

```sql
DESCRIBE AGENT <DATABASE>.SEMANTIC.<AGENT_NAME>;
```

### Phase 5: Register with Snowflake Intelligence

#### 5.1 — Ensure SI object exists

```sql
SHOW SNOWFLAKE INTELLIGENCES;
-- If empty:
CREATE SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;
```

#### 5.2 — Register the agent

```sql
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT
  ADD AGENT <DATABASE>.SEMANTIC.<AGENT_NAME>;
```

#### 5.3 — Grant permissions

```sql
-- For the consuming role (e.g., DBT_ROLE or ANALYST_ROLE)
GRANT USAGE ON DATABASE <DATABASE> TO ROLE <ROLE>;
GRANT USAGE ON SCHEMA <DATABASE>.SEMANTIC TO ROLE <ROLE>;
GRANT USAGE ON AGENT <DATABASE>.SEMANTIC.<AGENT_NAME> TO ROLE <ROLE>;
GRANT USAGE ON WAREHOUSE <WAREHOUSE> TO ROLE <ROLE>;
GRANT READ ON STAGE <DATABASE>.SEMANTIC.CORTEX_ANALYST_MODELS TO ROLE <ROLE>;
GRANT SELECT ON ALL TABLES IN SCHEMA <DATABASE>.DBT_MARTS TO ROLE <ROLE>;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE <ROLE>;
```

#### 5.4 — Verify end-to-end

```sql
SHOW AGENTS IN SCHEMA <DATABASE>.SEMANTIC;
SHOW SNOWFLAKE INTELLIGENCES;
-- Then in Snowsight: AI & ML → Snowflake Intelligence → select agent → ask a question
```

### Phase Summary

| Phase | What Happens | Output |
|-------|-------------|--------|
| 1. Generate YAML | Profile data, classify columns, synonyms, verified queries | `cortex-analyst-models/semantic_<name>.yaml` |
| 2. Upload | TEMP TABLE → COPY INTO stage | File on `@<DB>.SEMANTIC.CORTEX_ANALYST_MODELS` |
| 3. Test | `CORTEX_ANALYST_MESSAGE()` call | Validated NL → SQL response |
| 4. Deploy Agent | `CREATE AGENT` with tool spec | Agent object in `SEMANTIC` schema |
| 5. Register SI | `ALTER SNOWFLAKE INTELLIGENCE ADD AGENT` | Agent visible in Snowsight Intelligence UI |

---

## RBAC / Security for Cortex Copilot

> **NEVER use ACCOUNTADMIN** for Cortex Copilot, Cortex Analyst, or Snowflake Intelligence.

### Role Hierarchy

```
ACCOUNTADMIN  (one-time setup only)
  └── DBT_ROLE  (dbt build, model deployment)
        └── CORTEX_ANALYST_ROLE  (Cortex Copilot / Analyst / Intelligence)
```

### CORTEX_ANALYST_ROLE Permissions

| Can | Cannot |
|-----|--------|
| SELECT from mart tables | Create/alter/drop ANY objects |
| Read semantic views | Access staging or intermediate schemas |
| Read staged YAML files | Modify source data |
| Use the warehouse | Manage roles, users, or warehouses |
| Invoke Cortex Agents | Access ACCOUNT_USAGE or ORGANIZATION_USAGE |
| Query via Snowflake Intelligence | — |

### Setup SQL

Run `scripts/snowflake_cortex_rbac_setup.sql` as ACCOUNTADMIN (one-time):

```sql
USE ROLE ACCOUNTADMIN;
CREATE ROLE IF NOT EXISTS CORTEX_ANALYST_ROLE;

-- Read-only access to marts and semantic views
GRANT USAGE ON DATABASE DBT_DEV TO ROLE CORTEX_ANALYST_ROLE;
GRANT USAGE ON SCHEMA DBT_DEV.DBT_MARTS TO ROLE CORTEX_ANALYST_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA DBT_DEV.DBT_MARTS TO ROLE CORTEX_ANALYST_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA DBT_DEV.DBT_MARTS TO ROLE CORTEX_ANALYST_ROLE;
GRANT USAGE ON SCHEMA DBT_DEV.SEMANTIC TO ROLE CORTEX_ANALYST_ROLE;
GRANT READ ON STAGE DBT_DEV.SEMANTIC.CORTEX_ANALYST_MODELS TO ROLE CORTEX_ANALYST_ROLE;
GRANT USAGE ON WAREHOUSE DBT_AGENT_WH TO ROLE CORTEX_ANALYST_ROLE;

-- Hierarchy: DBT_ROLE inherits CORTEX_ANALYST_ROLE
GRANT ROLE CORTEX_ANALYST_ROLE TO ROLE DBT_ROLE;
```

For Copilot users, set the session role:
```sql
USE ROLE CORTEX_ANALYST_ROLE;
-- Or set as default: ALTER USER <user> SET DEFAULT_ROLE = 'CORTEX_ANALYST_ROLE';
```

---

## End-to-End Pipeline

> Full pipeline: **Discover → Stage → Marts → Validate → Snowflake Semantic Views → Cortex Analyst YAML → Agent**
>
> **IMPORTANT**: When operating as a GitHub Copilot agent (not via MCP/CLI tools), you MUST
> follow the inline step-by-step instructions below to create semantic views by reading/writing
> files directly. Do NOT just reference tool names like `generate_domain_semantic_views()` — those
> only work via the MCP server (`dbt_agent.py`). Instead, follow the manual file creation steps below.

---

### Pipeline Overview

| Step | What Happens | Output |
|------|-------------|--------|
| 1. Discover & Profile | Connect to Snowflake, discover tables, profile columns | Source metadata |
| 2. Generate Staging | Create `stg_<source>__<table>.sql` + `_sources.yml` + `schema.yml` | `models/staging/<source>/` |
| 3. Generate Marts | Create `fct_<entity>.sql` / `dim_<entity>.sql` + `schema.yml` | `models/marts/<source>/` |
| 4. dbt Build & Validate | `dbt build --select "source:<source>+"` | Materialized models + test results |
| 5. Create Snowflake Semantic Views | Create `sem_<name>.sql` + `sem_<name>.yml` for each mart | `models/semantic/sem_<name>/` |
| 6. Build Semantic Views | `dbt build --select tag:semantic` | Semantic views in Snowflake + verified queries attached |
| 7. (Optional) Cortex Analyst YAML | Generate YAML for richer NL metadata (synonyms, sample_values) | `cortex-analyst-models/` |
| 8. (Optional) Deploy Agent | CREATE AGENT SQL bundling semantic views | `ddl/cortex-analyst/deploy_agent_<domain>.sql` |

---

### Step 5 — Create Snowflake Semantic Views (DETAILED — follow these steps exactly)

> **This is the step that was previously missing inline instructions.** When working as a
> Copilot agent, you MUST create these files manually — do NOT skip to Cortex Analyst YAML.
> Snowflake Semantic Views are the primary mechanism for Cortex Analyst NL querying.

For EACH mart model (`fct_*`, `dim_*`, `summary_*`) in `models/marts/<domain>/`:

#### 5.1 — Read the mart model and its schema.yml

```
1. Read models/marts/<domain>/schema.yml → get column names, descriptions, tests
2. Read models/marts/<domain>/fct_<entity>.sql → understand the SQL, grain, joins
3. Identify: table alias to use in TABLES(), all columns for classification
```

#### 5.2 — Classify columns into dimensions and metrics

Apply these rules to EACH column:

| Column Pattern | Classification | Semantic View Section |
|---------------|---------------|----------------------|
| `*_date`, `*_at`, `*_timestamp`, `date`, `month`, `year` | Time dimension | `DIMENSIONS` |
| `*_status`, `*_type`, `*_category`, `*_segment`, `*_flag`, `is_*`, `has_*` | Categorical dimension | `DIMENSIONS` |
| `*_name`, `*_region`, `*_country`, `*_city`, `*_code`, `maker`, `brand` | Entity dimension | `DIMENSIONS` |
| `*_amount`, `*_revenue`, `*_sales`, `*_cost`, `*_total`, `*_quantity`, `*_count` | Metric (SUM) | `METRICS` with `SUM()` |
| `*_rate`, `*_pct`, `*_ratio`, `*_avg`, `average_*` | Metric (AVG) | `METRICS` with `AVG()` |
| `*_key`, `*_id`, `*_sk` | Key — **SKIP** | Do not include |
| `*_loaded_at`, `*_etl_*` | ETL — **SKIP** | Do not include |

**Use the column descriptions from schema.yml + actual SQL context to resolve ambiguous cases.**

#### 5.3 — Create the semantic view SQL file

Create directory and file: `models/semantic/sem_<name>/sem_<name>.sql`

**Template** (copy and adapt — do NOT deviate from this structure):

```sql
{{
  config(
    materialized = 'semantic_view',
    schema = 'SEMANTIC',
    tags = ['semantic', 'sem_<name>'],
    post_hook = [
      "{{ publish_verified_queries() }}"
    ]
  )
}}

TABLES (
  t AS {{ ref('fct_<entity>') }}
)
DIMENSIONS (
  t.<dim_col_1> AS <dim_col_1>
    COMMENT = '<description from schema.yml or inferred>',
  t.<dim_col_2> AS <dim_col_2>
    COMMENT = '<description>'
)
METRICS (
  t.<metric_alias> AS SUM(<metric_col>)
    COMMENT = '<description>',
  t.<metric_alias_2> AS AVG(<metric_col_2>)
    COMMENT = '<description>'
)
COMMENT = '<One-line description of what this semantic view enables for Cortex Analyst>'

- AI_SQL_GENERATION $$
- <Instruction 1: map business terms to columns>
- <Instruction 2: how to handle time queries>
- <Instruction 3: default aggregations and orderings>
$$
```

**Rules:**
- The `config()` block uses `materialized = 'semantic_view'` — this is provided by `dbt_packages/dbt_semantic_view`
- `schema = 'SEMANTIC'` is already set in `dbt_project.yml` for the semantic folder but include it explicitly
- The `post_hook` calls `publish_verified_queries()` which reads verified queries from the `.yml` and attaches them
- Use `{{ ref('fct_<entity>') }}` in `TABLES()` — NEVER hard-code database/schema names
- The table alias (e.g., `t` or `sales`) is used in `DIMENSIONS()` and `METRICS()`
- Every dimension and metric MUST have a `COMMENT`
- `AI_SQL_GENERATION` block guides Cortex Analyst text-to-SQL behavior

#### 5.4 — Create the semantic view YAML file

Create: `models/semantic/sem_<name>/sem_<name>.yml`

**Template:**

```yaml
version: 2

models:
  - name: sem_<name>
    description: >
      Semantic view for <domain> analytics built from <mart_model>.
      Grain: one row per (<grain columns>).
      Enables Cortex Analyst natural language querying over <domain> data.
    config:
      meta:
        verified_queries:
          - name: <descriptive_query_name_1>
            question: "<Natural language business question>"
            verified_at: <unix_timestamp_seconds>
            verified_by: copilot_agent
            sql: >
              SELECT <dimension>, SUM(<metric>) AS total
              FROM t
              GROUP BY <dimension>
              ORDER BY total DESC
          - name: <descriptive_query_name_2>
            question: "<Time-trend question>"
            verified_at: <unix_timestamp_seconds>
            verified_by: copilot_agent
            sql: >
              SELECT <date_dim>, SUM(<metric>) AS total
              FROM t
              GROUP BY <date_dim>
              ORDER BY <date_dim> DESC
              LIMIT 30
          - name: <descriptive_query_name_3>
            question: "<Dimensional breakdown question>"
            verified_at: <unix_timestamp_seconds>
            verified_by: copilot_agent
            sql: >
              SELECT <dim1>, <dim2>, SUM(<metric>) AS total
              FROM t
              GROUP BY <dim1>, <dim2>
              ORDER BY total DESC
```

**Verified query rules:**
- `sql` uses the **table alias** from `TABLES()` (e.g., `t` or `sales`), NOT the physical table name
- `verified_at` is a Unix timestamp in seconds (use current epoch, e.g., `1745452800`)
- Write 3–5 queries covering: summary, time trend, top-N, dimensional breakdown, filtered
- If you have MCP access, test each query via `run_query()` first — only include passing queries

#### 5.5 — Example: Complete semantic view for `fct_sales`

**File: `models/semantic/sem_revenue_analysis/sem_revenue_analysis.sql`**
```sql
{{
  config(
    materialized = 'semantic_view',
    schema = 'SEMANTIC',
    tags = ['semantic', 'sem_revenue_analysis'],
    post_hook = [
      "{{ publish_verified_queries() }}"
    ]
  )
}}

TABLES (
  sales AS {{ ref('fct_sales') }}
)
DIMENSIONS (
  sales.sales_date AS sales_date
    COMMENT = 'Date of sales activity',
  sales.maker AS maker
    COMMENT = 'Manufacturer or brand of the item sold',
  sales.item_category AS item_category
    COMMENT = 'Product category (Smartphone or Other)'
)
METRICS (
  sales.total_revenue AS SUM(total_sales)
    COMMENT = 'Total sales revenue',
  sales.total_transactions AS SUM(transaction_count)
    COMMENT = 'Total number of transactions',
  sales.avg_price AS AVG(average_price)
    COMMENT = 'Average item price'
)
COMMENT = 'Revenue analysis by maker, category, and time for Cortex Analyst'

- AI_SQL_GENERATION $$
- When users ask about "revenue", "sales", or "transactions", query this semantic view.
- total_sales is the primary revenue metric — always use SUM aggregation.
- For time-based queries, group by sales_date.
- maker represents the manufacturer or brand.
- item_category is either "Smartphone" or "Other".
$$
```

**File: `models/semantic/sem_revenue_analysis/sem_revenue_analysis.yml`**
```yaml
version: 2

models:
  - name: sem_revenue_analysis
    description: >
      Semantic view for sales analytics built from fct_sales.
      Grain: one row per (sales_date, maker, item_category).
      Enables Cortex Analyst natural language querying over revenue data.
    config:
      meta:
        verified_queries:
          - name: total_revenue_by_maker
            question: "What is the total revenue by maker?"
            verified_at: 1745452800
            verified_by: copilot_agent
            sql: >
              SELECT maker, SUM(total_sales) AS total_revenue
              FROM sales
              GROUP BY maker
              ORDER BY total_revenue DESC
          - name: daily_sales_trend
            question: "Show the daily sales trend"
            verified_at: 1745452800
            verified_by: copilot_agent
            sql: >
              SELECT sales_date, SUM(total_sales) AS total_revenue
              FROM sales
              GROUP BY sales_date
              ORDER BY sales_date DESC
              LIMIT 30
          - name: revenue_by_category
            question: "What is the revenue breakdown by item category?"
            verified_at: 1745452800
            verified_by: copilot_agent
            sql: >
              SELECT item_category,
                     SUM(total_sales) AS total_revenue,
                     SUM(transaction_count) AS total_transactions
              FROM sales
              GROUP BY item_category
              ORDER BY total_revenue DESC
```

#### 5.6 — Build the semantic views

```bash
# Compile first to catch Jinja errors
dbt compile --select tag:semantic

# Build — creates semantic views in Snowflake + attaches verified queries via post-hook
dbt build --select tag:semantic
```

#### 5.7 — Verify in Snowflake (if MCP access available)

```sql
-- Check semantic views exist
SHOW SEMANTIC VIEWS IN SCHEMA <DATABASE>.SEMANTIC;

-- Read the full definition including verified queries
SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('<DATABASE>.SEMANTIC.SEM_<NAME>');
```

---

### For an existing domain (marts already built):

```
User: "Create semantic views and an agent for japan_ecomm_data"
Agent:
  1. Read models/marts/japan_ecomm_data/schema.yml → list all mart models and columns
  2. For EACH mart model (fct_*, dim_*, summary_*):
     a. Classify columns into dimensions vs metrics (Step 5.2 rules)
     b. Create models/semantic/sem_<name>/sem_<name>.sql (Step 5.3 template)
     c. Create models/semantic/sem_<name>/sem_<name>.yml (Step 5.4 template)
  3. Run: dbt build --select tag:semantic
     → Materializes semantic views in Snowflake
     → publish_verified_queries() post-hook attaches verified queries
  4. (Optional) Generate Cortex Agent SQL with all semantic views as tools
     → Output: ddl/cortex-analyst/deploy_agent_japan_ecomm_data.sql
  5. Report: semantic views created, build results, next steps
```

### For a brand-new source:

```
User: "Onboard MY_DATABASE.MY_SCHEMA and create an agent"
Agent:
  1. Profile source table (Step 1 from onboard-new-source)
  2. Generate staging models: stg_<source>__<table>.sql + _sources.yml + schema.yml
  3. Generate mart models: fct_<entity>.sql + schema.yml
  4. Run: dbt build --select "source:<source>+"
  5. For EACH mart model created in step 3:
     a. Classify columns into dimensions vs metrics (Step 5.2 rules)
     b. Create models/semantic/sem_<name>/sem_<name>.sql (Step 5.3 template)
     c. Create models/semantic/sem_<name>/sem_<name>.yml (Step 5.4 template)
  6. Run: dbt build --select tag:semantic
  7. (Optional) Generate Cortex Analyst YAML for richer NL metadata
  8. (Optional) Generate Cortex Agent SQL
  9. Report: full pipeline output, agent SQL location, RBAC instructions
```

### CLI Shortcuts (when using scripts directly)

```bash
# Existing domain — via scripts
python scripts/generate_semantic_views_for_domain.py --domain japan_ecomm_data
dbt build --select tag:semantic
python scripts/create_domain_agent.py --domain japan_ecomm_data --register-si

# New source — one command
python scripts/end_to_end_pipeline.py \
  --source-database MY_DB --source-schema MY_SCHEMA --register-si

# Existing domain — one command
python scripts/end_to_end_pipeline.py --domain japan_ecomm_data --skip-discover --register-si
```

### Pipeline Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/generate_semantic_views_for_domain.py` | Batch-generate semantic views for all marts in a domain |
| `scripts/create_domain_agent.py` | Create Cortex Agent SQL bundling all semantic views |
| `scripts/end_to_end_pipeline.py` | Full orchestrator: discover → semantic → agent |
| `scripts/snowflake_cortex_rbac_setup.sql` | CORTEX_ANALYST_ROLE setup (least-privilege) |

---

## Related Skills

| Skill | Invoke with | When to use |
|-------|------------|-------------|
| `$onboard-new-source` | `$onboard-new-source` | Full pipeline: source → staging → marts → semantic model |
| `$snowflake-semantic-view-creator` | `$snowflake-semantic-view-creator` | Detailed Snowflake Semantic View creation (dbt_semantic_view package) |
| `$cortex-analyst-semantic-model` | `$cortex-analyst-semantic-model` | Standalone YAML generation for existing marts (full spec reference) |
