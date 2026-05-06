# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

A production-ready dbt project for Snowflake with medallion architecture, an auto-discovery script that generates dbt models from any Snowflake database, a Snowflake Managed MCP Server, a Streamlit app, and an evaluation framework comparing Cortex Code vs Claude Code.

---

## Environment Setup

```bash
# Create and activate venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install dbt-snowflake mcp

# Or use the one-command bootstrap (interactive, handles everything)
chmod +x scripts/bootstrap.sh && ./scripts/bootstrap.sh
```

Snowflake connection goes in `~/.dbt/profiles.yml` (profile name: `snowflake_dbt_starter_kit`). Use `profiles.yml.template` as the starting point. Environment variables (`SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, etc.) are the preferred auth method.

---

## Common dbt Commands

```bash
dbt deps                                        # Install packages (dbt_utils, dbt_expectations)
dbt debug                                       # Validate connection
dbt seed                                        # Load seed files
dbt build                                       # Build all models + run all tests

# Selective builds
dbt build --select <model_name>                 # Single model + its tests
dbt build --select "source:covid19_data+"       # All models from one source
dbt build --select tag:staging                  # All staging models
dbt build --select tag:marts                    # All mart models

# Semantic models are disabled by default — enable explicitly for testing
dbt build --select tag:semantic --vars '{"semantic_enabled": true}'

dbt test --select <model_name>                  # Run tests for one model
dbt run --select <model_name>                   # Run model without tests
dbt compile --select <model_name>               # Compile SQL without executing
```

---

## Auto-Discovery Script

Connects to any Snowflake database, profiles all columns, and generates a complete set of dbt models (staging + marts + source YAML + schema tests):

```bash
# Interactive mode
python scripts/discover_and_generate.py

# CLI mode
python scripts/discover_and_generate.py \
  --source-database MY_DB \
  --source-schema MY_SCHEMA \
  --source-name my_source

# Preview without writing files
python scripts/discover_and_generate.py --source-database MY_DB --source-schema MY_SCHEMA --dry-run

# Regenerate an existing source
python scripts/discover_and_generate.py --source-database MY_DB --source-schema MY_SCHEMA --source-name my_source --overwrite
```

Each source produces: `models/staging/<source_name>/` and `models/marts/<source_name>/`, each with its own `_sources.yml` (hardcoded database/schema) and `schema.yml` with tests.

---

## Architecture

### Medallion Layers

| Layer | Materialization | Schema | Purpose |
|---|---|---|---|
| Staging | view | `DBT_STAGING` | 1:1 clean/rename of source tables. Each model is a trio: `<model>.sql`, `schema.yml` entry, and `<model>.md` transformation spec (source of truth — only columns needing transforms are listed; excluded columns are called out; everything else is moved as-is). |
| Intermediate | view | `DBT_INTERMEDIATE` | Joins and business logic |
| Marts | table | `DBT_MARTS` | Analytical facts, dims, summaries |
| Semantic | disabled | `SEMANTIC` | Metadata for natural-language queries |

Default source: `COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC` (Snowflake Marketplace dataset). Controlled by `vars.source_database` and `vars.source_schema` in `dbt_project.yml`.

Multiple sources coexist under `models/staging/<source_name>/` — each is fully self-contained and can be built independently with `dbt build --select "source:<source_name>+"`.

### Critical: Schema Name Override

`macros/generate_schema_name.sql` overrides dbt's default schema naming. Instead of the standard `<target_schema>_<custom_schema>` convention, this macro uses `custom_schema_name` directly. This means models deploy to exactly `DBT_STAGING`, `DBT_INTERMEDIATE`, `DBT_MARTS` — not `PUBLIC_DBT_STAGING`, etc. **Do not remove this macro.**

### Semantic Views

Two approaches exist side-by-side:
1. **dbt semantic models** in `models/semantic/` — disabled (`+enabled: false`) in the main build. Contain `snowflake_semantic_view` metadata in schema.yml for the `generate_semantic_view_ddl` macro.
2. **Raw DDL** in `ddl/semantic/` — YAML + SQL file pairs executed directly in Snowflake (the primary production approach).

`macros/generate_semantic_view_ddl.sql` generates `CREATE OR REPLACE SEMANTIC VIEW` DDL from dbt model metadata. `scripts/generate_semantic_view.py` is a standalone script for the same purpose.

### Openflow Pipelines

Snowflake-native pipeline DDL (Tasks + Streams) lives in `ddl/openflow/`. The `snowflake-openflow-pipeline` skill in `.agents/skills/` generates this DDL — it orchestrates dbt layer refreshes using `CREATE TASK` DAGs and `CREATE STREAM` for CDC.

### MCP Server

`snowflake-dbt-mcp/server.py` is a local Python MCP server. For production, the Snowflake Managed MCP Server is set up via SQL scripts in `snowflake-dbt-mcp/setup/` (run 01–05 in order as ACCOUNTADMIN). VS Code configuration is in `.vscode/mcp.json`.

---

## Skills System

- `.agents/skills/` — 50 active skills available to AI agents (17 original + 33 bundled)
- `bundled_skills/` — source directory of 33 Snowflake-specific skills (already copied into `.agents/skills/`)
- `skills-lock.json` — SHA-locked hashes for 11 upstream `dbt-labs/dbt-agent-skills` skills

Custom project skills (in `.agents/skills/`): `dbt-one-stop-agent`, `project-quality-audit`, `semantic-view-batch-sync`, `semantic-view-coverage-audit`, `snowflake-openflow-pipeline`, `snowflake-semantic-view-creator`.

See `SKILLS_COMPARISON.md` for a full inventory and description of all 50 skills.

---

## Key Packages

- `dbt-labs/dbt_utils` `>=1.1.0,<2.0.0` — standard dbt utilities
- `metaplane/dbt_expectations` `0.10.4` — data quality tests (use `metaplane/`, NOT the deprecated `calogica/`)

---

## Important Gotchas

- **Wrong schema placement**: If models land in the wrong schema (e.g., `PUBLIC` instead of `DBT_MARTS`), verify `macros/generate_schema_name.sql` exists — it's the fix.
- **`dbt_expectations` deprecation**: Use `metaplane/dbt_expectations` in `packages.yml`, not `calogica/dbt_expectations`.
- **Semantic models**: Always disabled in `dbt build` by default. They exist only to hold metadata for DDL generation — the actual Semantic Views are created directly in Snowflake from `ddl/semantic/`.
- **Source env vars**: If you get `Env var required but not provided: SNOWFLAKE_ACCOUNT`, add exports to `~/.zshrc` and run `source ~/.zshrc`.
- **Insufficient privileges**: Run the GRANT statements from `scripts/snowflake_setup.sql` as ACCOUNTADMIN in Snowsight.
