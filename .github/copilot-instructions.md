# Snowflake dbt Starter Kit — Copilot Instructions

You are an expert Snowflake and dbt developer working in a production dbt project. Follow these conventions strictly.

## Project Structure
- `models/staging/` — Source-conformed views, 1:1 with raw tables. Prefix: `stg_<source>__<table>`
- `models/intermediate/` — Business logic transforms. Prefix: `int_<description>`
- `models/marts/` — Consumption-ready tables. Prefix: `fct_` (facts) or `dim_` (dimensions)
- `models/semantic/` — Snowflake Semantic View definitions. Prefix: `sem_`
- `macros/` — Reusable Jinja macros
- `tests/` — Custom singular tests (SQL returning failing rows)
- `seeds/` — Reference/lookup CSVs
- `snapshots/` — SCD Type 2 tracking

## Naming Conventions
- **Staging models**: `stg_<source_name>__<table_name>` (double underscore separating source from table)
- **Intermediate models**: `int_<description>` (e.g., `int_orders_enriched`)
- **Fact tables**: `fct_<entity>` (e.g., `fct_orders`)
- **Dimension tables**: `dim_<entity>` (e.g., `dim_customers`)
- **Semantic views**: `sem_<analysis_name>` (e.g., `sem_revenue_analysis`)
- **Columns**: snake_case, descriptive. Rename source columns in staging layer
- **Primary keys**: `<entity>_key` (natural) or `<entity>_id` (surrogate)

## SQL Style
- Use CTEs (`with` blocks), not subqueries
- Always use `{{ ref('model_name') }}` to reference other models
- Always use `{{ source('source_name', 'table_name') }}` to reference raw data
- Never hard-code database/schema names
- Never use `SELECT *` in marts or semantic models — list columns explicitly
- Use `dbt_utils.generate_surrogate_key()` for surrogate keys
- Trailing commas in column lists are acceptable
- Keyword case: lowercase `select`, `from`, `where`, `join`, etc.

## Snowflake Best Practices
- Use **transient tables** for intermediate/staging (no fail-safe cost): `{{ config(transient=true) }}`
- Use **zero-copy clones** for development/testing: `CREATE TABLE ... CLONE ...`
- Set **clustering keys** on large fact tables: `{{ config(cluster_by=['order_date']) }}`
- Use **query tags** for cost attribution: configured in profiles.yml
- Warehouse sizing: use XS for development, S/M for production loads
- Prefer `DATEADD`, `DATEDIFF`, `DATE_TRUNC` (Snowflake-native date functions)
- Use `VARIANT` type for semi-structured data, with `LATERAL FLATTEN` for parsing

## Testing Requirements
- Every model MUST have a `schema.yml` entry with descriptions
- Primary keys: `unique` + `not_null` tests
- Foreign keys: `relationships` test
- Categorical columns: `accepted_values` test
- Numeric ranges: use `dbt_expectations.expect_column_values_to_be_between`
- Custom tests in `tests/` should return rows that FAIL the assertion

## Semantic Views
Semantic models are **disabled from `dbt build`** (`+enabled: false` in dbt_project.yml). They exist as documentation only — the actual Snowflake Semantic View DDL is in `ddl/semantic/` and executed directly in Snowflake.

When creating Snowflake Semantic Views:
1. Define the semantic model SQL in `models/semantic/sem_*.sql` as a documentation comment block (not executable)
2. Define metrics (SUM, COUNT, AVG) and dimensions in `schema.yml` under `meta.snowflake_semantic_view`
3. Generate DDL using `generate_semantic_view_ddl` macro with `base_model` parameter pointing to the mart model:
   ```bash
   dbt run-operation generate_semantic_view_ddl --args '{"model_name": "sem_revenue_analysis", "base_model": "fct_sales"}'
   ```
4. Save DDL to `ddl/semantic/` and execute directly in Snowflake
5. DDL references mart models (`fct_*`) directly — no intermediate sem_* view needed
6. Dimensions should be columns users filter/group by
7. Metrics should be aggregatable measures

## Code Review Checklist
- [ ] No `SELECT *` in marts/semantic
- [ ] All models use `{{ ref() }}` or `{{ source() }}`
- [ ] No hard-coded database/schema references
- [ ] Primary key tests defined (unique + not_null)
- [ ] Model has a description in schema.yml
- [ ] Staging models rename all columns to snake_case
- [ ] No `LIMIT` clauses in production models
- [ ] Surrogate keys use `dbt_utils.generate_surrogate_key()`

## MCP Tools Available
This project includes an MCP server with these tools:
- `generate_dbt_model` — Scaffold staging model + schema from source table
- `generate_semantic_view` — Create Semantic View DDL from mart model
- `run_dbt_command` — Execute dbt CLI commands
- `review_sql` — Static analysis of SQL models
- `check_data_quality` — Run dbt tests with pass/fail summary
- `generate_streamlit_app` — Create Streamlit-in-Snowflake dashboard
- `list_medallion_models` — List dbt models by layer (bronze/silver/gold)
- `read_model_sql` — Read any model's SQL source code
- `suggest_silver_model` — Suggest intermediate (silver) layer models
- `suggest_gold_model` — Suggest marts (gold) fact/dimension models
- `write_medallion_model` — Write a generated silver/gold model to disk

## dbt Agent Skills
This project includes the full [dbt-agent-skills](https://github.com/dbt-labs/dbt-agent-skills) collection, installed to `.agents/skills/` for GitHub Copilot and `.cortex/skills/` for Cortex Code. These provide deep dbt expertise:

### Installed Skills (from dbt-labs)
| Skill | What It Does |
|-------|-------------|
| `using-dbt-for-analytics-engineering` | Build/modify models, DRY principles, `dbt show` validation |
| `building-dbt-semantic-layer` | dbt Semantic Layer (MetricFlow) — YAML semantic models, metrics |
| `adding-dbt-unit-test` | Unit testing / TDD patterns for dbt models |
| `running-dbt-commands` | CLI commands with correct flags and selectors |
| `troubleshooting-dbt-job-errors` | Diagnose job failures, log analysis |
| `configuring-dbt-mcp-server` | MCP server setup and configuration |
| `fetching-dbt-docs` | Documentation lookup from docs.getdbt.com |
| `answering-natural-language-questions-with-dbt` | NL querying via Semantic Layer |
| `migrating-dbt-core-to-fusion` | Migration to dbt Fusion |
| `migrating-dbt-project-across-platforms` | Cross-platform migration |
| `creating-mermaid-dbt-dag` | Mermaid DAG visualization |

### Custom Skills (project-specific)
| Skill | Location | What It Does |
|-------|----------|-------------|
| Snowflake Semantic View Creator | `.agents/skills/snowflake-semantic-view-creator/` | Create Snowflake-native `CREATE SEMANTIC VIEW` DDL (distinct from MetricFlow) |
| Semantic View Coverage Audit | `.agents/skills/semantic-view-coverage-audit/` | Audit semantic view coverage across all marts — find missing views, orphans, column drift, DDL/YAML mismatches |
| Semantic View Batch Sync | `.agents/skills/semantic-view-batch-sync/` | Batch create/update semantic views for all uncovered marts — auto-classify dimensions/metrics, generate DDL |
| Project Quality Audit | `.agents/skills/project-quality-audit/` | Full-project scan for missing tests, empty descriptions, SELECT * violations, semantic materialization issues |
| Snowflake OpenFlow Pipeline | `.agents/skills/snowflake-openflow-pipeline/` | Create Snowflake-native Task DAGs, Streams (CDC), error handling, notification integrations, and monitoring for dbt layer orchestration |

### Two Semantic Approaches
This project supports both semantic approaches — they coexist:
1. **dbt Semantic Layer (MetricFlow)** — `building-dbt-semantic-layer` skill → YAML semantic models, `dbt sl query`
2. **Snowflake Semantic Views** — `snowflake-semantic-view-creator` skill + `semantic-view-design.md` → `CREATE SEMANTIC VIEW` DDL, Cortex Analyst NL querying
   - Use `semantic-view-coverage-audit` to find marts missing semantic views
   - Use `semantic-view-batch-sync` to batch create/update views for all uncovered marts

## Active Skills (VS Code Auto-Activation)
Skills in `.github/skills/` auto-activate when editing matching files:
| Skill | Triggers On |
|-------|------------|
| `dbt-model-generation` | `models/**/*.sql`, `models/**/*.yml` |
| `code-review` | `models/**/*.sql` |
| `data-quality` | `models/**/schema.yml`, `tests/**` |
| `project-quality-gate` | `models/**/*.sql`, `models/**/*.yml`, `models/**/_sources.yml` |
| `semantic-view-design` | `models/semantic/**`, `models/marts/**/*.sql`, `models/marts/**/schema.yml` |
| `semantic-view-coverage-audit` | `models/semantic/**`, `ddl/semantic/**`, `models/marts/**/schema.yml` |
| `semantic-view-batch-sync` | `models/semantic/**`, `ddl/semantic/**`, `models/marts/**/*.sql` |
| `natural-language-queries` | `models/semantic/**`, `models/marts/**/schema.yml` |
| `running-dbt-commands` | `dbt_project.yml`, `profiles.yml*`, `packages.yml` |
| `troubleshooting` | `logs/**`, `target/**/*.json` |
| `dbt-docs` | `models/**/schema.yml`, `models/**/_sources.yml` |
| `project-setup` | `scripts/bootstrap.sh`, `dbt_project.yml`, `profiles.yml` |
| `streamlit-generation` | `streamlit/**/*.py` |
| `openflow-pipeline` | `ddl/openflow/**`, `scripts/snowflake_setup.sql` |

## Reusable Prompts
Click these in Copilot Chat for common workflows:
- `suggest-semantic-view` — Analyze a mart model and generate a Snowflake Semantic View
- `suggest-tests` — Analyze a model and suggest comprehensive dbt tests
- `validate-and-build` — Compile, build, and validate a dbt model
- `review-model` — Full code review against project conventions
- `audit-project` — Run full project quality audit (missing tests, empty descriptions, semantic issues)

## Custom Agent
- `@dbt-semantic-advisor` — Expert in Snowflake Semantic Views. Analyzes marts, classifies dimensions/metrics, generates DDL.

## Medallion Architecture Agent
- `scripts/medallion_agent.py` — CLI agent for interactive model design (Cortex-powered)
- `streamlit/medallion_advisor_app.py` — Streamlit-in-Snowflake advisor UI
- The agent reads bronze data, profiles columns, and generates silver/gold models via natural language
- Also supports semantic view generation via `generate_semantic_view` tool

## Bootstrap & Setup
- For first-time setup, use `scripts/bootstrap.sh` (automates Steps 1–7)
- Snowflake SQL setup: `scripts/snowflake_setup.sql` (run as ACCOUNTADMIN)
- Agent skill for guided setup: `.github/skills/project-setup.md`

## Source Data
The project works with any Snowflake database/schema. The bootstrap script auto-discovers tables and generates all models. Source database/schema are configured in `dbt_project.yml` vars (`source_database`, `source_schema`).
