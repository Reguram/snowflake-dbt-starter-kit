---
name: dbt-one-stop-agent
description: >
  Unified, context-aware dbt orchestrator that routes to 50 specialized skills across the entire
  Snowflake + dbt lifecycle: source discovery, staging/intermediate/marts model generation,
  Cortex Analyst semantic model creation, Snowflake Agent deployment, Snowflake Intelligence
  registration, code review, data quality checks, medallion architecture advising, dbt CLI
  operations, Streamlit app scaffolding, Dynamic Tables, Iceberg, Snowpark, ML, data governance,
  cost analysis, security, and more.
  Always reads existing project state before generating code — produces models that fit the
  existing project rather than generic boilerplate. Delegates to specialized skills when deeper
  expertise is needed.
  Use when: building any dbt model, discovering new data sources, creating semantic models,
  deploying agents, enabling Snowflake Intelligence, reviewing code, checking data quality,
  or asking questions about the project — or ANY Snowflake platform task.
  Triggers: onboard, discover, build, generate, semantic model, cortex analyst, agent, intelligence,
  pipeline, end-to-end, rbac, cortex role, semantic views for domain.
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "5.0"
---

# dbt One-Stop Agent

> **Unified orchestrator** that combines 50 specialized skills for the entire dbt + Snowflake
> lifecycle. Handles tasks directly when it can, delegates to specialized skills when deeper
> expertise is needed. One entry point for everything.

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
| **Skill Routing** | Delegates to 50 specialized skills when tasks require deeper Snowflake platform expertise |

---

## Skill Routing Table (50 Skills)

> This agent acts as the **orchestrator**. For tasks it handles directly (model generation,
> source discovery, semantic views, code review), it executes inline. For everything else,
> it delegates to the appropriate specialized skill below.

### Delegation Rules

1. **Handle directly** — dbt model CRUD, source discovery, semantic views, code review, dbt CLI, end-to-end pipeline
2. **Delegate immediately** — Snowflake platform tasks (Dynamic Tables, Iceberg, Snowpark, ML, etc.)
3. **Delegate for depth** — When a task this agent handles needs deeper expertise (e.g., complex unit tests → `adding-dbt-unit-test`, advanced semantic view debugging → `semantic-view`)
4. **Chain skills** — Multi-domain tasks may require reading multiple skills in sequence (e.g., onboard source → create semantic view → deploy agent → register with SI)

### Category 1: dbt Core Workflow

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `using-dbt-for-analytics-engineering` | model, SQL, ref, source, transform, pipeline | **Handle directly** — this agent's core capability. Delegate for unfamiliar dbt features |
| `adding-dbt-unit-test` | unit test, TDD, mock, test model logic | **Delegate** — specialized YAML format and mocking patterns |
| `running-dbt-commands` | dbt build, dbt run, dbt test, dbt compile, dbt show | **Handle directly** via `run_dbt` tool. Delegate for complex selectors or unfamiliar flags |
| `fetching-dbt-docs` | dbt docs, documentation, dbt features, dbt Cloud | **Delegate** — retrieves docs.getdbt.com pages in LLM-friendly format |
| `creating-mermaid-dbt-dag` | DAG, lineage diagram, mermaid, visualize dependencies | **Delegate** — generates Mermaid flowcharts from manifest or code |
| `onboard-new-source` | onboard, new source, discover, add source, build pipeline | **Handle directly** — core discovery workflow. Delegate for complex multi-source scenarios |
| `troubleshooting-dbt-job-errors` | job failed, dbt Cloud error, intermittent failure, logs | **Delegate** — specialized in dbt Cloud log analysis and Admin API |
| `project-quality-audit` | audit, quality check, validate, pre-deploy, missing tests | **Handle directly** via `review_sql` + `check_data_quality`. Delegate for full-project scan |

### Category 2: Semantic Layer & NL Querying

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `building-dbt-semantic-layer` | semantic model, metric, MetricFlow, measure, dimension, `dbt sl` | **Delegate** — MetricFlow YAML is distinct from Snowflake Semantic Views |
| `answering-natural-language-questions-with-dbt` | "What were total sales?", KPI, analytics question, NL query | **Delegate** — translates business questions to SQL via Semantic Layer |
| `snowflake-semantic-view-creator` | semantic view, CREATE SEMANTIC VIEW, `dbt_semantic_view` package | **Handle directly** for creation. Delegate for advanced `dbt_semantic_view` package features |
| `semantic-view` | create/debug/fix/optimize semantic view, VQR, verified queries | **Delegate** — entry point for ALL semantic view operations including debugging |
| `semantic-view-batch-sync` | batch semantic views, sync, enable Cortex Analyst for all marts | **Handle directly** via `generate_domain_semantic_views`. Delegate for complex sync scenarios |
| `semantic-view-coverage-audit` | audit semantic views, coverage, missing views, orphaned, drift | **Handle directly** — scans marts vs semantic views. Delegate for detailed gap analysis |
| `cortex-analyst-semantic-model` | Cortex Analyst YAML, semantic model YAML, `CORTEX_ANALYST_MESSAGE` | **Handle directly** — core YAML generation workflow. Delegate for full spec reference |
| `cortex-agent` | create agent, debug agent, list agents, Snowflake Intelligence, SI | **Handle directly** for creation/registration. Delegate for agent debugging/evaluation |
| `dashboard` | dashboard, KPI report, executive summary, widgets, charts | **Delegate** — specialized DashboardSpec JSON format |

### Category 3: Data Quality & Governance

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `data-quality` | data quality, DMF, quality score, schema health, SLA alerting | **Delegate** — Snowflake DMFs, table comparison, quality monitoring are beyond dbt tests |
| `data-governance` | governance, masking, PII, GDPR, classify, grants, row access policy | **Delegate** — routes to 5 sub-skills (catalog, masking, classification, maturity, observability) |
| `lineage` | what depends on, impact analysis, upstream, where does this come from | **Delegate** — Snowflake ACCOUNT_USAGE lineage, column-level tracing |

### Category 4: Snowflake Platform

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `dynamic-tables` | dynamic table, DT, target lag, incremental refresh, UPSTREAM_FAILED | **Delegate** — specialized in DT creation, optimization, troubleshooting |
| `iceberg` | iceberg, catalog integration, external volume, Glue, CLD, auto-refresh | **Delegate** — catalog integrations, external volumes, auto-refresh |
| `snowflake-notebooks` | notebook, .ipynb, workspace notebook, SQL cell, Snowpark session | **Delegate** — creates/edits Snowflake Workspace notebooks |
| `snowflake-postgres` | postgres, pg, create instance, health check, pg_lake, diagnostics | **Delegate** — Snowflake Postgres instance management |
| `snowpark` | Snowpark, UDF, stored procedure, deploy Python, `snow snowpark` | **Delegate** — Python UDF/SP deployment via CLI |
| `snowpark-connect` | snowpark connect, SCOS, PySpark migration, Spark Connect | **Delegate** — PySpark → Snowpark Connect migration |
| `cortex-ai-functions` | classify, extract, sentiment, summarize, parse PDF, OCR, AI_COMPLETE | **Delegate** — routes to correct Cortex AI function |
| `integrations` | integration, API integration, catalog integration, notification | **Delegate** — all Snowflake integration types |
| `openflow` | Openflow, NiFi, data replication, connector deployment | **Delegate** — NiFi-based data integration |
| `data-cleanrooms` | clean room, DCR, collaboration, audience overlap, activation | **Delegate** — Snowflake Data Clean Room workflows |
| `data-products` | data product, internal marketplace, org listing, share across accounts | **Delegate** — organizational listings and Internal Marketplace |
| `declarative` | declarative, share data, cross account, application package, TYPE=DATA | **Delegate** — declarative sharing with versioned app packages |
| `machine-learning` | train model, ML, model registry, feature store, HPO, distributed | **Delegate** — routes to ML sub-skills (training, registry, inference, etc.) |
| `workload-performance-analysis` | spilling, pruning, cache hit, clustering, slow query, SOS, QAS | **Delegate** — SQL execution analysis via ACCOUNT_USAGE |

### Category 5: Infrastructure & DevOps

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `configuring-dbt-mcp-server` | MCP server, dbt MCP, configure MCP, Claude Desktop, Cursor | **Delegate** — MCP config JSON and connectivity validation |
| `deploy-to-spcs` | SPCS, Docker, container, deploy to Snowflake, Snowpark Container | **Delegate** — containerized app deployment |
| `dbt-projects-on-snowflake` | `snow dbt`, EXECUTE DBT PROJECT, deployed dbt project object | **Delegate** — dbt-as-Snowflake-object (NOT normal dbt dev) |
| `dcm` | DCM, Database Change Management, `snow dcm`, manifest.yml, DEFINE | **Delegate** — infrastructure-as-code for Snowflake objects |
| `migrating-dbt-core-to-fusion` | Fusion migration, migration errors, dbt Fusion, auto-fixable | **Delegate** — migration error triage |
| `migrating-dbt-project-across-platforms` | migrate platform, Snowflake to Databricks, cross-platform dbt | **Delegate** — cross-platform SQL dialect differences |
| `snowconvert-assessment` | SnowConvert, assessment, migration waves, SSIS, ETL analysis | **Delegate** — workload migration assessment |

### Category 6: Visualization & Apps

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `developing-with-streamlit` | streamlit, st., app.py, beautify, CSS, theme, custom component | **Handle directly** for basic scaffolding via `generate_streamlit_app`. Delegate for styling, custom components, deployment |
| `build-react-app` | React, Next.js, dashboard app, data app, analytics tool | **Delegate** — React/Next.js data apps with Snowflake |

### Category 7: Security & Cost

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `cost-intelligence` | cost, credits, spending, budget, warehouse cost, top spenders | **Delegate** — all Snowflake cost/billing analysis |
| `network-security` | network policy, network rule, IP allowlist, SaaS rules | **Delegate** — network policies and rules |
| `key-and-secret-management` | TSS, CMK, BYOK, encryption key, key rotation, rekeying | **Delegate** — Tri-Secret Secure and key management |
| `trust-center` | Trust Center, security findings, CIS benchmark, scanner | **Delegate** — security finding analysis and remediation |
| `organization-management` | org, accounts, org users, org spending, globalorgadmin | **Delegate** — org-level management and ORGANIZATION_USAGE |

### Category 8: Meta / Tooling

| Skill | Triggers | Delegation |
|-------|----------|------------|
| `skill_development` | create skill, new skill, audit skill, capture session as skill | **Delegate** — skill authoring and review |
| `cortex-code-guide` | cortex guide, cortex help, cortex commands, #table, sessions | **Delegate** — Cortex Code CLI reference |

---

### How Routing Works

```
User Request
    │
    ▼
┌──────────────────────────────┐
│  dbt One-Stop Agent (this)   │
│  1. Parse intent              │
│  2. Check skill routing table │
│  3. Read project context      │
└──────────┬───────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
 HANDLE        DELEGATE
 DIRECTLY      TO SKILL
    │             │
    │             ├── Read SKILL.md for the matched skill
    │             ├── Follow its instructions
    │             └── Return to one-stop agent for next step
    │
    ├── Source discovery
    ├── Model generation (stg/int/fct/dim)
    ├── Semantic view creation
    ├── Cortex Analyst YAML generation
    ├── Agent deployment + SI registration
    ├── Code review (static analysis)
    ├── dbt CLI commands
    └── End-to-end pipeline orchestration
```

### Multi-Skill Chaining Examples

| User Request | Skills Chained (in order) |
|-------------|--------------------------|
| "Onboard MY_DB.MY_SCHEMA and create an agent" | `onboard-new-source` → `snowflake-semantic-view-creator` → `cortex-agent` |
| "Add unit tests for fct_orders" | `adding-dbt-unit-test` |
| "What were total sales last quarter?" | `answering-natural-language-questions-with-dbt` |
| "Audit the project before deployment" | `project-quality-audit` → `semantic-view-coverage-audit` |
| "Create a Streamlit dashboard for sales data" | `developing-with-streamlit` (handle basic via `generate_streamlit_app`, delegate for styling) |
| "Deploy fct_orders as a dynamic table" | `dynamic-tables` |
| "Classify PII columns in my marts" | `data-governance` (→ sensitive-data-classification sub-skill) |
| "Show me Snowflake costs by warehouse" | `cost-intelligence` |
| "Train an ML model on my mart data" | `machine-learning` |
| "Create an Iceberg table from my mart" | `iceberg` |
| "Debug why my semantic view returns wrong SQL" | `semantic-view` |
| "Migrate this project from Databricks to Snowflake" | `migrating-dbt-project-across-platforms` |
| "Set up network policy for my Snowflake account" | `network-security` |
| "Create a Data Clean Room collaboration" | `data-cleanrooms` |
| "Visualize my dbt DAG as a Mermaid diagram" | `creating-mermaid-dbt-dag` |
| "Share my mart data with another Snowflake account" | `declarative` or `data-products` |
| "Create a DCM project for my database objects" | `dcm` |
| "Analyze query performance for slow queries" | `workload-performance-analysis` |

## When to Invoke This Skill

### Direct Handling (core dbt workflow)
- User asks to build, generate, or scaffold any dbt model
- User wants to discover or onboard a new data source
- User asks about project state ("what sources do I have?")
- User wants a Cortex Analyst semantic model (YAML) for NL querying
- User wants to create a Snowflake Agent for text-to-SQL
- User wants to register an agent with Snowflake Intelligence
- User asks for code review or data quality checks
- User wants to run dbt commands
- User asks about medallion architecture or layer design
- User wants a Streamlit dashboard (basic scaffolding)
- User wants to run the full end-to-end pipeline (discover → semantic → agent)
- User asks about semantic views for all marts in a domain
- User asks about RBAC, roles, or security for Cortex Copilot
- User wants to create a domain-level Cortex Agent

### Delegation (routes to specialized skills)
- User asks about **unit tests** → delegate to `adding-dbt-unit-test`
- User asks a **business question** about data → delegate to `answering-natural-language-questions-with-dbt`
- User wants **MetricFlow semantic models** (not Snowflake Semantic Views) → delegate to `building-dbt-semantic-layer`
- User wants to **debug a semantic view** → delegate to `semantic-view`
- User wants a **Mermaid DAG diagram** → delegate to `creating-mermaid-dbt-dag`
- User has a **dbt Cloud job failure** → delegate to `troubleshooting-dbt-job-errors`
- User wants **dbt documentation lookup** → delegate to `fetching-dbt-docs`
- User asks about **Dynamic Tables** → delegate to `dynamic-tables`
- User asks about **Iceberg tables** → delegate to `iceberg`
- User wants to **create/edit a Snowflake notebook** → delegate to `snowflake-notebooks`
- User wants to **deploy Snowpark UDFs/SPs** → delegate to `snowpark`
- User wants to **use Cortex AI functions** (classify, extract, sentiment) → delegate to `cortex-ai-functions`
- User asks about **data governance, masking, PII** → delegate to `data-governance`
- User asks about **data quality DMFs** (beyond dbt tests) → delegate to `data-quality`
- User asks about **data lineage** → delegate to `lineage`
- User asks about **Snowflake costs/credits** → delegate to `cost-intelligence`
- User wants to **deploy to SPCS** → delegate to `deploy-to-spcs`
- User wants a **React/Next.js data app** → delegate to `build-react-app`
- User wants **advanced Streamlit** (styling, components, deployment) → delegate to `developing-with-streamlit`
- User asks about **network policies** → delegate to `network-security`
- User asks about **encryption/key management** → delegate to `key-and-secret-management`
- User asks about **Trust Center security findings** → delegate to `trust-center`
- User asks about **org management** → delegate to `organization-management`
- User wants to **train ML models** → delegate to `machine-learning`
- User asks about **Data Clean Rooms** → delegate to `data-cleanrooms`
- User wants to **share data cross-account** → delegate to `declarative` or `data-products`
- User asks about **MCP server configuration** → delegate to `configuring-dbt-mcp-server`
- User wants **DCM infrastructure-as-code** → delegate to `dcm`
- User asks about **dbt-as-Snowflake-object** (`snow dbt`) → delegate to `dbt-projects-on-snowflake`
- User wants to **migrate to Fusion** → delegate to `migrating-dbt-core-to-fusion`
- User wants to **migrate across platforms** → delegate to `migrating-dbt-project-across-platforms`
- User asks about **SnowConvert assessment** → delegate to `snowconvert-assessment`
- User asks about **query performance** (spilling, pruning) → delegate to `workload-performance-analysis`
- User asks about **Openflow/NiFi** → delegate to `openflow`
- User asks about **Snowflake Postgres** → delegate to `snowflake-postgres`
- User asks about **Snowpark Connect/PySpark migration** → delegate to `snowpark-connect`
- User wants to **create/audit a skill** → delegate to `skill_development`
- User asks about **Cortex Code CLI** → delegate to `cortex-code-guide`
- User wants an **interactive dashboard** (DashboardSpec) → delegate to `dashboard`
- User wants **Snowflake integrations** (API, catalog, storage) → delegate to `integrations`

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

## Related Skills — Complete Reference (50 Skills)

> **All skills live in `.agents/skills/<skill-name>/SKILL.md`.**
> Read the SKILL.md file before delegating to ensure you follow its specific instructions.

### dbt Core Workflow (9 skills)

| Skill | When to Use |
|-------|-------------|
| `using-dbt-for-analytics-engineering` | Building/modifying dbt models, writing SQL with `ref()`/`source()`, creating tests, validating with `dbt show` |
| `adding-dbt-unit-test` | Creating unit test YAML definitions with mocked inputs and expected outputs, TDD for dbt |
| `running-dbt-commands` | Formatting and executing dbt CLI commands with correct flags, selectors, and environment handling |
| `fetching-dbt-docs` | Retrieving dbt documentation pages from docs.getdbt.com in LLM-friendly format |
| `creating-mermaid-dbt-dag` | Generating Mermaid flowchart diagrams of dbt model lineage and dependencies |
| `onboard-new-source` | End-to-end source onboarding: profile → staging → marts → build → semantic view |
| `troubleshooting-dbt-job-errors` | Diagnosing dbt Cloud/platform job failures via log analysis, Admin API, git history |
| `project-quality-audit` | Full-project scan: missing PK tests, empty descriptions, `SELECT *` violations, semantic issues |
| `dbt-one-stop-agent` | This agent — unified orchestrator for the entire lifecycle |

### Semantic Layer & NL Querying (9 skills)

| Skill | When to Use |
|-------|-------------|
| `building-dbt-semantic-layer` | Creating/modifying MetricFlow components: semantic models, metrics, dimensions, entities, measures |
| `answering-natural-language-questions-with-dbt` | Translating business questions to SQL via Semantic Layer or ad-hoc queries |
| `snowflake-semantic-view-creator` | Creating Snowflake-native Semantic Views via `dbt_semantic_view` package (DDL-like SQL) |
| `semantic-view` | **Entry point** for ALL semantic view operations: create, debug, optimize, VQR suggestions |
| `semantic-view-batch-sync` | Batch creating/updating semantic views for all uncovered marts |
| `semantic-view-coverage-audit` | Auditing coverage: missing views, orphaned views, stale DDL, column drift |
| `cortex-analyst-semantic-model` | Agentic YAML generation with synonyms, sample_values, verified_queries, custom_instructions |
| `cortex-agent` | **Entry point** for ALL Cortex Agent operations: create, debug, evaluate, list, delete |
| `dashboard` | Creating interactive DashboardSpec JSON dashboards with charts, tables, markdown widgets |

### Data Quality & Governance (3 skills)

| Skill | When to Use |
|-------|-------------|
| `data-quality` | Snowflake DMF monitoring, table comparison, quality scoring, SLA alerting, ad-hoc quality scans |
| `data-governance` | Masking policies, row access policies, PII classification, governance/observability maturity |
| `lineage` | Impact analysis, root cause debugging, column-level tracing, dependency analysis |

### Snowflake Platform (14 skills)

| Skill | When to Use |
|-------|-------------|
| `dynamic-tables` | Creating, optimizing, monitoring, troubleshooting Snowflake Dynamic Tables |
| `iceberg` | Iceberg tables, catalog integrations (Glue/Unity/Polaris), external volumes, CLD, auto-refresh |
| `snowflake-notebooks` | Creating/editing Workspace notebooks (.ipynb) with SQL cells and Snowpark |
| `snowflake-postgres` | Snowflake Postgres instance management: create, suspend, resume, health checks, pg_lake |
| `snowpark` | Deploying Snowpark Python: UDFs, UDAFs, UDTFs, stored procedures via `snow snowpark` CLI |
| `snowpark-connect` | Migrating PySpark workloads to Snowpark Connect (SCOS) |
| `cortex-ai-functions` | Routing to Cortex AI functions: AI_CLASSIFY, AI_EXTRACT, AI_SENTIMENT, AI_SUMMARIZE, AI_PARSE_DOCUMENT |
| `integrations` | Managing Snowflake integrations: API, catalog, external access, notification, security, storage |
| `openflow` | NiFi-based data integration: connector deployment, configuration, diagnostics |
| `data-cleanrooms` | Data Clean Room workflows: collaborations, data offerings, audience overlap, activations |
| `data-products` | Organizational listings for Snowflake Internal Marketplace cross-account sharing |
| `declarative` | Declarative sharing with application packages (TYPE=DATA) for versioned cross-account data |
| `machine-learning` | ML sub-skills: model training, registry, inference, feature store, distributed training, HPO |
| `workload-performance-analysis` | SQL execution analysis: spilling, pruning, cache hits, clustering keys, SOS/QAS candidates |

### Infrastructure & DevOps (7 skills)

| Skill | When to Use |
|-------|-------------|
| `configuring-dbt-mcp-server` | MCP server config JSON, authentication setup, connectivity validation |
| `deploy-to-spcs` | Deploying Docker containers to Snowpark Container Services (SPCS) |
| `dbt-projects-on-snowflake` | dbt projects deployed AS Snowflake objects via `snow dbt` CLI (not normal dbt dev) |
| `dcm` | Database Change Management: infrastructure-as-code for Snowflake objects |
| `migrating-dbt-core-to-fusion` | Triaging dbt-core → Fusion migration errors (auto-fixable, guided, blocked) |
| `migrating-dbt-project-across-platforms` | Cross-platform dbt migration (e.g., Snowflake ↔ Databricks) via Fusion |
| `snowconvert-assessment` | SnowConvert assessment reports for workload migration (waves, ETL analysis) |

### Visualization & Apps (2 skills)

| Skill | When to Use |
|-------|-------------|
| `developing-with-streamlit` | Creating, editing, debugging, styling, and deploying Streamlit-in-Snowflake apps |
| `build-react-app` | Building React/Next.js data apps connected to Snowflake |

### Security & Cost (5 skills)

| Skill | When to Use |
|-------|-------------|
| `cost-intelligence` | All Snowflake cost/billing: credits, warehouse costs, budgets, resource monitors, anomalies |
| `network-security` | Network policies and rules: IP allowlists, hybrid policies, SaaS rules |
| `key-and-secret-management` | Tri-Secret Secure (CMK/BYOK), key rotation, periodic data rekeying |
| `trust-center` | Trust Center security findings: CIS benchmarks, scanners, remediation guidance |
| `organization-management` | Org-level management: accounts, users, spending, security posture, ORGANIZATION_USAGE |

### Meta / Tooling (2 skills)

| Skill | When to Use |
|-------|-------------|
| `skill_development` | Creating, documenting, or auditing skills for Cortex Code |
| `cortex-code-guide` | Cortex Code CLI reference: commands, shortcuts, sessions, MCP, agents |
