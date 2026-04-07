---
description: "Discover and fully onboard a new Snowflake source — staging, intermediate, marts, tests, and semantic view"
---
# Onboard New Source — Full Medallion Pipeline

Discover and onboard a new Snowflake source table into this dbt project, building all medallion
layers (staging → intermediate → marts) with tests, documentation, and a Snowflake Semantic View.

---

## Parameters (replace before running)

| Parameter | Example value | Description |
|-----------|--------------|-------------|
| `{{SOURCE_DATABASE}}` | `AMAZON_AND_ECOMMERCE_WEBSITES_PRODUCT_VIEWS_AND_PURCHASES` | Snowflake database containing the source |
| `{{SOURCE_SCHEMA}}` | `DATAFEEDS` | Schema inside that database |
| `{{SOURCE_TABLE}}` | `PRODUCT_VIEWS_AND_PURCHASES` | Raw table name (UPPER_CASE as it appears in Snowflake) |
| `{{SOURCE_NAME}}` | `datafeeds` | Short snake_case alias used for model and folder naming |
| `{{STAGING_MODEL}}` | `stg_datafeeds__product_views_and_purchases` | Auto-derived: `stg_<source_name>__<table_lower>` |

---

## Step 0 — Read project context FIRST (mandatory, do not skip)

Before generating any file:

1. Use `project_context` (or `list_medallion_models`) to understand existing sources and models.
2. Use `list_sources` to check if a source entry for `{{SOURCE_NAME}}` already exists in
   `models/staging/{{SOURCE_NAME}}/_sources.yml`. If it does, diff rather than overwrite.
3. Scan `models/staging/`, `models/intermediate/`, `models/marts/` for any existing models that
   already reference `{{SOURCE_TABLE}}` or `{{SOURCE_NAME}}`. Report any duplicates before proceeding.
4. Read `dbt_project.yml` to confirm target schema names (`DBT_STAGING`, `DBT_INTERMEDIATE`,
   `DBT_MARTS`) and the `generate_schema_name` macro override behaviour.

---

## Step 1 — Profile the source table

Use `describe_table` and `profile_data` (or `discover_source`) on
`{{SOURCE_DATABASE}}.{{SOURCE_SCHEMA}}.{{SOURCE_TABLE}}`.

Report:
- Row count and column list with data types.
- Candidate primary key column(s): any column with **0 nulls + 100 % distinct values**.
- Date/timestamp columns (candidates for clustering keys).
- High-cardinality VARCHAR columns → likely **dimensions** in the semantic view.
- Numeric / float columns → likely **metrics** (SUM / AVG / COUNT) in the semantic view.
- Columns with <5 distinct values → candidates for `accepted_values` tests.
- Columns with >10 % nulls → flag for `not_null` test exclusion.

---

## Step 2 — Generate the staging layer

Create the following files. Follow all conventions strictly.

### `models/staging/{{SOURCE_NAME}}/_sources.yml`
```yaml
version: 2

sources:
  - name: {{SOURCE_NAME}}
    description: "Raw source from {{SOURCE_DATABASE}}.{{SOURCE_SCHEMA}}"
    database: "{{SOURCE_DATABASE}}"
    schema: "{{SOURCE_SCHEMA}}"
    quoting:
      identifier: true
    tables:
      - name: {{SOURCE_TABLE}}
        description: "<one-sentence description derived from column profiling>"
        columns:
          # List every column with:
          #   - unique + not_null on the PK column(s) found in Step 1
          #   - accepted_values on any column with <5 distinct values
```

### `models/staging/{{SOURCE_NAME}}/{{STAGING_MODEL}}.sql`
```sql
{{config(materialized='view', tags=['staging'])}}

with source as (
    select * from {{ source('{{SOURCE_NAME}}', '{{SOURCE_TABLE}}') }}
),

staged as (
    select
        -- rename UPPER_CASE source columns to snake_case here
        -- cast types where needed (e.g. TRY_TO_DATE, TRY_TO_NUMBER)
        -- do NOT add any business logic
    from source
)

select * from staged
```

Rules:
- Rename all source columns to `snake_case`.
- Cast strings to proper types (dates, numbers) using `TRY_TO_DATE` / `TRY_TO_NUMBER`.
- Never use `SELECT *` in the `staged` CTE — list every column explicitly.
- The PK column from Step 1 becomes `<entity>_key` (natural key) or gets a surrogate key via
  `{{ dbt_utils.generate_surrogate_key([...]) }}` if there is no reliable natural key.

### `models/staging/{{SOURCE_NAME}}/schema.yml`
```yaml
version: 2

models:
  - name: {{STAGING_MODEL}}
    description: "Staged {{SOURCE_TABLE}} from {{SOURCE_NAME}} — renamed columns, 1:1 with source"
    columns:
      # Every column with a description
      # PK column: unique + not_null tests
      # Low-cardinality columns: accepted_values test
      # Numeric ranges: dbt_expectations.expect_column_values_to_be_between
```

---

## Step 3 — Suggest intermediate model (only if justified)

Analyze the staged columns. Generate an intermediate model **only if at least one of these is true**:
- Multiple join-worthy foreign key columns exist that would need resolving.
- Date-based windowing / running totals are needed before aggregation.
- Complex exploding of VARIANT / array columns is required.

If NO intermediate model is justified, state the reason and skip to Step 4.

If justified, create:

### `models/intermediate/{{SOURCE_NAME}}/int_{{SOURCE_NAME}}__<description>.sql`
```sql
{{config(materialized='view', transient=true, tags=['intermediate'])}}

with staged as (
    select * from {{ ref('{{STAGING_MODEL}}') }}
),

enriched as (
    select
        -- business logic here, NO raw source references
    from staged
)

select * from enriched
```

Add an entry to `models/intermediate/{{SOURCE_NAME}}/schema.yml`.

---

## Step 4 — Suggest mart models (only if justified)

Based on the profiled data, suggest up to **two** mart models — one fact and/or one dimension.
Justify each suggestion with the grain and intended consumers.

Name the models:
- Fact: `fct_<entity>` (e.g. `fct_product_views`)
- Dimension: `dim_<entity>` (e.g. `dim_product`)

### Fact model: `models/marts/{{SOURCE_NAME}}/fct_<entity>.sql`
```sql
{{config(
    materialized='table',
    tags=['marts'],
    cluster_by=['<date_column>']   -- only if a date column exists
)}}

with source as (
    select * from {{ ref('{{STAGING_MODEL}}') }}
    -- or ref to intermediate model if Step 3 generated one
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['<pk_cols>']) }} as <entity>_id,
        -- all dimensions and measures; no SELECT *
    from source
)

select * from final
```

### Dimension model (only if high-cardinality lookup columns exist): `models/marts/{{SOURCE_NAME}}/dim_<entity>.sql`

Add schema.yml entries for every mart model with:
- `unique` + `not_null` on the surrogate key
- `relationships` test back to the staging model FK
- `dbt_expectations.expect_column_values_to_be_between` on numeric measures

---

## Step 5 — Run dbt build

```bash
dbt build --select "source:{{SOURCE_NAME}}+"
```

Use `run_dbt_command` (MCP) or the CLI directly. Report:
- Pass / fail count per model.
- Any test failures with the failing row count and column name.
- Compilation errors with the exact line and suggested fix.
- Execution time per model.

If any step fails, diagnose and fix before proceeding to Step 6.

---

## Step 6 — Generate Snowflake Semantic View

For each mart model generated in Step 4, create a Snowflake-native Semantic View
(NOT dbt Semantic Layer / MetricFlow).

### Classification rules (derive from Step 1 profile)
| Column type | Classify as |
|-------------|-------------|
| DATE / TIMESTAMP | dimension (+ derived `EXTRACT(YEAR…)`, `DATE_TRUNC('month'…)`) |
| VARCHAR high-cardinality (>100 distinct) | dimension |
| VARCHAR low-cardinality (<50 distinct) | dimension with `accepted_values` hint |
| INT / FLOAT / NUMBER aggregatable | metric (`SUM`, `AVG`, `COUNT`, `MAX`, `MIN`) |
| Surrogate key / FK | exclude from semantic view |

### Files to generate

**`models/semantic/sem_<entity>.sql`** — documentation comment block only (not executable):
```sql
{{
  config(
    enabled=false,
    tags=['semantic']
  )
}}
-- Semantic view metadata for sem_<entity>.
-- Actual DDL is in ddl/semantic/sem_<entity>_ddl.sql
-- Execute that file directly in Snowflake.
```

**`models/semantic/schema.yml`** — add entry with `meta.snowflake_semantic_view`:
```yaml
- name: sem_<entity>
  description: "Semantic view for <entity> — natural language querying via Cortex Analyst"
  meta:
    snowflake_semantic_view:
      base_model: fct_<entity>
      dimensions:
        - name: <dim_col>
          description: "<description>"
      metrics:
        - name: <metric_col>
          aggregation: SUM   # or AVG / COUNT / MAX / MIN
          description: "<description>"
```

**`ddl/semantic/sem_<entity>_ddl.sql`** — executable Snowflake DDL:
```sql
CREATE OR REPLACE SEMANTIC VIEW <target_db>.SEMANTIC.SEM_<ENTITY>
  TABLES (
    <alias> AS <target_db>.DBT_MARTS.FCT_<ENTITY>
  )
  DIMENSIONS (
    <alias>.<dim_col> AS <dim_col>
      COMMENT = '<description>',
    -- derived time dimensions:
    <alias>.period_month AS DATE_TRUNC('month', <date_col>)
      COMMENT = 'Month derived from <date_col>',
    <alias>.period_year AS EXTRACT(YEAR FROM <date_col>)
      COMMENT = 'Year derived from <date_col>'
  )
  METRICS (
    <alias>.<metric_col> AS SUM(<metric_col>)
      COMMENT = '<description>'
  )
  COMMENT = '<one-line description of what this view enables>';
```

Use `generate_semantic_view` MCP tool if available to auto-detect dimensions/metrics from
Snowflake column metadata, then verify / adjust the output.

---

## Step 7 — Final checklist

Before handing back, verify every item:

- [ ] `_sources.yml` created with `database:` and `schema:` hard-coded (allowed in _sources.yml only)
- [ ] Staging model uses `{{ source('{{SOURCE_NAME}}', '{{SOURCE_TABLE}}') }}`
- [ ] All mart/intermediate models use `{{ ref('model_name') }}` — no raw schema references
- [ ] No `SELECT *` in ANY mart or semantic model
- [ ] No `LIMIT` clause in any production model
- [ ] Every model has a `schema.yml` entry with a non-empty `description`
- [ ] PK column(s) have `unique` + `not_null` tests
- [ ] Surrogate keys use `{{ dbt_utils.generate_surrogate_key([...]) }}`
- [ ] `dbt build` passed with 0 test failures
- [ ] `ddl/semantic/sem_<entity>_ddl.sql` created and reviewed
- [ ] `models/semantic/` has `enabled: false` config (semantic models are never materialized by dbt)
