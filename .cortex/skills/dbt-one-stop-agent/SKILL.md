---
name: dbt-one-stop-agent
description: >
  Unified, context-aware dbt agent combining ALL project capabilities: source discovery,
  staging/intermediate/marts model generation, Snowflake Semantic View creation, code review,
  data quality checks, medallion architecture advising, dbt CLI operations, and Streamlit app
  scaffolding. Always reads existing project state before generating code — produces models that
  fit the existing project rather than generic boilerplate.
  Use when: building any dbt model, discovering new data sources, creating semantic views,
  reviewing code, checking data quality, or asking questions about the project.
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "2.0"
---

# dbt One-Stop Agent

> **Unified agent** that replaces separate scripts for source discovery, model generation,
> semantic views, code review, and medallion advising. One tool for the entire dbt lifecycle.

## What This Skill Does

| Capability | Description |
|-----------|-------------|
| **Source Discovery** | Connects to any Snowflake database/schema, discovers tables, auto-generates staging models with proper naming, tests, and documentation |
| **Model Generation** | Creates intermediate (silver) and marts (gold) models with context-aware SQL — reads existing models before generating |
| **Semantic Views** | Auto-classifies columns as dimensions/metrics from actual Snowflake metadata, generates `CREATE SEMANTIC VIEW` DDL for Cortex Analyst |
| **Code Review** | Static analysis against project conventions: naming, `ref()` usage, hard-coded schemas, missing tests |
| **Data Quality** | Runs dbt tests, profiles columns for null rates and cardinality, validates data pipelines |
| **Medallion Advising** | Suggests silver/gold models based on existing bronze data using Cortex LLM |
| **dbt Operations** | Run, build, test, compile, seed via dbt CLI |
| **Streamlit Apps** | Generate Streamlit-in-Snowflake dashboards from mart models |

## When to Invoke This Skill

- User asks to build, generate, or scaffold any dbt model
- User wants to discover or onboard a new data source
- User asks about project state ("what sources do I have?")
- User wants a semantic view or Cortex Analyst integration
- User asks for code review or data quality checks
- User wants to run dbt commands
- User asks about medallion architecture or layer design
- User wants a Streamlit dashboard

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
| `generate_semantic_view` | `model_name`, `analysis_name?` | Generate Semantic View DDL from a mart |
| `review_sql` | `model_name?`, `sql_content?` | Static analysis for best practices |
| `check_data_quality` | `select?` | Run dbt tests |
| `run_dbt` | `command`, `select?`, `full_refresh?` | Execute dbt CLI commands |
| `generate_streamlit_app` | `model_name`, `app_title?` | Scaffold Streamlit dashboard |

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

### Create a Semantic View
```
User: "Create a semantic view for fct_orders"
Agent:
  1. Reads fct_orders model and schema.yml
  2. Profiles columns from Snowflake
  3. Auto-classifies dimensions (dates, categories) and metrics (revenue, quantity)
  4. Generates sem_orders_analysis.sql + CREATE SEMANTIC VIEW DDL
```

## Project Conventions

- **Staging**: `stg_<source>__<table>` — 1:1 with source, rename columns to snake_case
- **Intermediate**: `int_<description>` — joins, dedup, business logic
- **Marts**: `fct_<entity>` (facts) or `dim_<entity>` (dimensions) — consumption-ready
- **Semantic**: `sem_<analysis_name>` — Snowflake Semantic View definitions
- Always use `{{ ref() }}` and `{{ source() }}`
- Use CTEs, not subqueries
- Use `dbt_utils.generate_surrogate_key()` for surrogate keys
- Every model must have a schema.yml entry with description and tests
