---
name: onboard-gold-layer
description: >
  Gold layer (marts) onboarding: generate fact tables, dimension tables, and summary models
  with surrogate keys, clustering, and comprehensive tests. Validates against project patterns
  and runs dbt build. Works on existing projects (infers patterns) and greenfield projects
  (uses default scaffolding). Portable across dbt projects — no hardcoded paths or names.
  Use when: building fact or dimension tables, creating mart models, generating gold layer,
  adding surrogate keys, building consumption-ready analytics tables.
  Triggers: gold, marts, fact table, dimension table, fct_, dim_, summary, surrogate key.
tools: ["bash", "edit", "mcp"]
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "1.0"
---

# Onboard Gold Layer (Marts)

> Generates consumption-ready mart models — fact tables, dimension tables, and summary models
> with surrogate keys, clustering, aggregations, and comprehensive tests.
> Gold = analytics-ready — aggregated, keyed, tested, documented.

## Prerequisites

Before running this skill, ensure **at least the bronze layer** exists for the source:
- `models/staging/<SOURCE_NAME>/stg_<SOURCE_NAME>__*.sql` ✅

Optionally, a silver (intermediate) layer may exist:
- `models/intermediate/<SOURCE_NAME>/int_<SOURCE_NAME>__*.sql` (if business logic was needed)

The gold layer references whichever upstream layer is appropriate via `{{ ref() }}`.

## Required Inputs

| Parameter | Example | Description |
|-----------|---------|-------------|
| `SOURCE_NAME` | `my_source` | The snake_case source alias (must match upstream layers) |
| `UPSTREAM_MODEL` | `stg_my_source__orders` or `int_my_source__orders_enriched` | Which model to build marts from |
| `ENTITY` | `orders` | The business entity (used in `fct_<entity>`, `dim_<entity>`) |

Derived automatically:
- Fact model: `fct_<entity>` → `models/marts/<SOURCE_NAME>/fct_<entity>.sql`
- Dimension model: `dim_<entity>` → `models/marts/<SOURCE_NAME>/dim_<entity>.sql`
- Summary model: `summary_<table>` → `models/marts/<SOURCE_NAME>/summary_<table>.sql`

---

## Step 1 — Read Project Context & Extract Gold Patterns

### 1.1 — Read project configuration

Read `dbt_project.yml` and extract marts layer config:

| Setting | What to look for |
|---------|-----------------|
| **Marts schema** | `+schema:` under marts layer (e.g., `DBT_MARTS`, `ANALYTICS`) |
| **Marts materialization** | `+materialized:` (usually `table` or `incremental`) |
| **Marts tags** | `+tags:` (e.g., `["marts"]`) |

**Default scaffolding** (use if no marts config exists):
```yaml
marts:
  +materialized: table
  +schema: DBT_MARTS
  +tags: ["marts"]
```

### 1.2 — Discover existing mart models

```bash
ls models/marts/*/
```

If existing mart models exist, read one `fct_*.sql` and one `dim_*.sql` and extract patterns.

**For fact tables:**

| Element | What to note |
|---------|-------------|
| `config()` block | `materialized`, `cluster_by`, `tags`? |
| CTE naming | `source_data` → `aggregated_data` → `final`? Other? |
| CTE spacing | Blank lines inside/between CTEs? |
| Surrogate key macro | `dbt_utils.generate_surrogate_key`? Custom macro? |
| Key naming | `<entity>_key`? `<entity>_id`? `<entity>_sk`? |
| Aggregation alignment | Aligned `as` aliases? |
| SQL keyword casing | Same as staging or different? |
| Final select | `select * from final`? Explicit columns? |

**For dimension tables:**

| Element | What to note |
|---------|-------------|
| Uses `SELECT DISTINCT`? | With `WHERE ... IS NOT NULL`? |
| Key naming | `<entity>_id`? `<entity>_key`? |
| SQL keyword casing | Same as facts or different? |

> See [references/fact-table-patterns.md](references/fact-table-patterns.md) and
> [references/dimension-table-patterns.md](references/dimension-table-patterns.md) for
> default scaffolding and detailed examples.

### 1.3 — Extract mart schema.yml pattern

**If existing mart schema.yml exists:** Read one and extract:

| Element | What to note |
|---------|-------------|
| Description style | Multi-line `>`? Inline string? |
| Grain statement | Included in description? |
| SK description format | Template pattern? |
| Test types used | `unique`, `not_null`, `accepted_values`, `relationships`, `dbt_expectations.*`? |
| Indentation style | 2-space? 4-space? |
| Model types present | `fct_*`, `dim_*`, `summary_*`? Others? |

### 1.4 — Build gold pattern registry

```
GOLD PATTERN REGISTRY
======================
Source: [INFERRED | DEFAULT SCAFFOLDING]

Marts schema:          <...>
Marts materialized:    <table | incremental | ...>
Model types:           <fct_, dim_, summary_ | ...>

Fact SQL:
  config_block:        <materialized+cluster_by | ...>
  cte_pattern:         <source_data→aggregated_data→final | ...>
  cte_spacing:         <spacious | compact>
  sk_macro:            <dbt_utils.generate_surrogate_key | custom | ...>
  key_naming:          <entity_key | entity_id | ...>
  keyword_case:        <lowercase | UPPER | ...>
  final_select:        <select * from final | explicit columns>

Dim SQL:
  uses_distinct:       <yes | no>
  null_filter:         <yes | no>
  key_naming:          <entity_id | entity_key | ...>
  keyword_case:        <lowercase | UPPER | ...>

Mart schema.yml:
  description_style:   <multiline > | inline>
  grain_in_desc:       <yes | no>
  sk_description:      <template | freetext>
  test_types:          <unique, not_null, accepted_values, ...>
  indentation:         <2-space | 4-space>
```

---

## Step 2 — Design the Gold Layer

Before writing code, plan each mart model:

### 2.1 — Determine what to build

| Model Type | When to Create | Key Questions |
|-----------|----------------|---------------|
| **Fact table** (`fct_*`) | Transactional / event data with metrics | What's the grain? What metrics are aggregated? |
| **Dimension table** (`dim_*`) | Distinct lookup entities | Which entity? Is it a flat or SCD? |
| **Summary table** (`summary_*`) | Pre-aggregated cross-cuts | What dimensions to group by? |

### 2.2 — Define the grain for each model

For each model, state explicitly:
> "One row per `<entity>` [per `<time_period>`] [per `<dimension>`]"

### 2.3 — Map columns from upstream

Use the column classifications from the bronze layer profiling (or re-profile):

| Column | Classification | Mart Role |
|--------|---------------|-----------|
| PK columns | PK | Input to surrogate key |
| Date columns | Date dimension | Clustering key + dimension |
| Low-cardinality VARCHAR | Categorical dimension | GROUP BY + accepted_values test |
| Numeric amounts | SUM metric | Aggregated measure |
| Numeric rates | AVG metric | Aggregated measure |

---

## Step 3 — Generate Fact Table

Create `models/marts/<SOURCE_NAME>/fct_<entity>.sql`:

Generate using the pattern from Step 1 (inferred or default):

```sql
{{
    config(
        materialized='table',
        cluster_by=['<date_column>']
    )
}}

with source_data as (
    select
        <col_1>,
        <col_2>,
        <col_n>
    from {{ ref('<UPSTREAM_MODEL>') }}
),

aggregated_data as (
    select
        <group_col_1>,
        <group_col_2>,
        sum(<metric_col>)   as <metric_alias>,
        avg(<metric_col_2>) as <avg_alias>,
        count(*)            as record_count
    from source_data
    group by <group_col_1>, <group_col_2>
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['<pk_cols>']) }} as <entity>_key,
        <group_col_1>,
        <group_col_2>,
        <metric_alias>,
        <avg_alias>,
        record_count
    from aggregated_data
)

select * from final
```

**Rules:**
- Match CTE names, keyword case, spacing from the pattern registry
- `config()` block: include `materialized` and `cluster_by` on the primary date column
- Surrogate key: use the project's SK macro with the grain columns as input
- Key naming: use `<entity>_key` or `<entity>_id` per the registry
- List ALL columns explicitly in the `final` CTE — no `SELECT *`
- Use `{{ ref() }}` for the upstream model — never hard-code schemas
- Align aggregation aliases if the project pattern does so

---

## Step 4 — Generate Dimension Table (if applicable)

Only create a dimension table if clear lookup entities exist (e.g., distinct categories,
customer types, geographic regions).

Create `models/marts/<SOURCE_NAME>/dim_<entity>.sql`:

```sql
with distinct_values as (
    select distinct
        <column>
    from {{ ref('<UPSTREAM_MODEL>') }}
    where <column> is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['<column>']) }} as <entity>_id,
    <column>
from distinct_values
```

**Rules:**
- Use `SELECT DISTINCT` with `WHERE ... IS NOT NULL`
- Key naming: `<entity>_id` (or match registry)
- Match keyword case from the registry (facts and dims may differ)

---

## Step 5 — Generate Mart Schema.yml

Create `models/marts/<SOURCE_NAME>/schema.yml`:

```yaml
version: 2

models:
  - name: fct_<entity>
    description: >
      Fact table for <entity>.
      Grain: one row per (<grain columns>) combination.
    columns:
      - name: <entity>_key
        description: "Surrogate primary key — hash of <grain columns>."
        tests:
          - unique
          - not_null
      - name: <date_col>
        description: "<description>"
        tests:
          - not_null
      - name: <categorical_col>
        description: "<description>"
        tests:
          - not_null
          - accepted_values:
              values: ['val1', 'val2', 'val3']
      - name: <metric_col>
        description: "<what this metric represents>"
        tests:
          - not_null

  - name: dim_<entity>
    description: "Dimension table for <entity>."
    columns:
      - name: <entity>_id
        description: "Surrogate primary key."
        tests:
          - unique
          - not_null
      - name: <column>
        description: "<description>"
        tests:
          - not_null
```

**Rules:**
- Match description style (multiline `>` or inline) from registry
- Include grain statement in fact description
- SK column: `unique` + `not_null` tests always
- Dimension columns: `not_null` on key dimensions
- Low-cardinality columns: `accepted_values` test (use profiled distinct values)
- Metric columns: `not_null` on critical metrics
- List ALL columns from the SQL output

---

## Step 6 — Build & Test Gold Layer

```bash
# Build just the mart models
dbt build --select fct_<entity> dim_<entity>

# Or build the full pipeline from source
dbt build --select "source:<SOURCE_NAME>+"
```

Report:
- Pass/fail count per model and test
- Row count for each mart model
- Any test failures (column, failing row count)
- Compilation errors
- Execution time

**If any test fails, diagnose and fix before proceeding.**

---

## Step 7 — Validate Against Gold Patterns

### 7.1 — Structural validation

| Check | Rule | Fix |
|-------|------|-----|
| Directory | `models/marts/<SOURCE_NAME>/` exists | Create it |
| Fact file naming | `fct_<entity>.sql` | Rename |
| Dim file naming | `dim_<entity>.sql` | Rename |
| `schema.yml` present | All models have entries | Add missing |
| No orphan SQL/YAML | 1:1 match between `.sql` and `schema.yml` | Add/remove |

### 7.2 — Fact SQL validation

| Check | Expected (from registry) |
|-------|-------------------------|
| `config()` block | Matches `config_block` (materialized + cluster_by) |
| CTE pattern | Matches `cte_pattern` from registry |
| CTE spacing | Matches `cte_spacing` from registry |
| Surrogate key | Uses `sk_macro` from registry |
| Key naming | Matches `key_naming` from registry |
| Keyword case | Matches `keyword_case` from registry |
| No `SELECT *` | All columns listed explicitly in final CTE |
| No hard-coded schemas | Uses `{{ ref() }}` only |
| `{{ ref() }}` targets exist | Referenced staging/intermediate model exists |

### 7.3 — Dimension SQL validation

| Check | Expected (from registry) |
|-------|-------------------------|
| `SELECT DISTINCT` | Matches `uses_distinct` from registry |
| `WHERE IS NOT NULL` | Matches `null_filter` from registry |
| Key naming | Matches dim `key_naming` from registry |
| No hard-coded schemas | Uses `{{ ref() }}` only |

### 7.4 — Schema.yml validation

| Check | Expected (from registry) |
|-------|-------------------------|
| Description style | Matches `description_style` from registry |
| Grain in description | Matches `grain_in_desc` from registry |
| SK description | Matches `sk_description` from registry |
| SK tests | `unique` + `not_null` always |
| Dimension tests | `not_null` on key dimensions |
| Low-cardinality tests | `accepted_values` on categorical columns |
| Metric tests | `not_null` on critical metrics |
| All columns listed | Every column from SQL output |

### 7.5 — Cross-file consistency

| Check | Rule |
|-------|------|
| Mart `ref()` targets exist | Referenced upstream models exist |
| Mart `schema.yml` columns match SQL output | All columns accounted for |
| No duplicate model names | Across all schema.yml in the project |
| Surrogate key inputs match grain | SK columns = grain-defining columns |

### 7.6 — Validation report

```
## Gold Layer Validation Report

| File | Check | Status | Detail |
|------|-------|--------|--------|
| fct_*.sql | config() | ✅ PASS | materialized='table', cluster_by set |
| fct_*.sql | CTE pattern | ✅ PASS | Matches registry pattern |
| fct_*.sql | Surrogate key | ✅ PASS | generate_surrogate_key used |
| fct_*.sql | No SELECT * | ✅ PASS | All columns explicit in final |
| dim_*.sql | SELECT DISTINCT | ✅ PASS | With IS NOT NULL filter |
| schema.yml | SK tests | ✅ PASS | unique + not_null on all keys |
| schema.yml | Grain statement | ⚠️ FIXED | Added grain to description |
| Cross-file | Column consistency | ✅ PASS | All columns match |

Total: 8 checks — 7 passed, 1 auto-fixed, 0 failed
```

---

## Step 8 — Gold Checklist

- [ ] Fact table has `config(materialized='table', cluster_by=[...])` (or project equivalent)
- [ ] Surrogate key uses project's SK macro
- [ ] Key naming matches project convention
- [ ] All columns listed explicitly — no `SELECT *` in final CTE
- [ ] All models use `{{ ref() }}` — no hard-coded schemas
- [ ] No `LIMIT` clause in any production model
- [ ] Every model in `schema.yml` with non-empty description
- [ ] Fact description includes grain statement
- [ ] PK column(s) have `unique` + `not_null` tests
- [ ] Low-cardinality columns have `accepted_values` tests
- [ ] Metric columns have `not_null` tests
- [ ] Dimension table uses `SELECT DISTINCT` with null filter (if applicable)
- [ ] `dbt build` passed with 0 test failures
- [ ] Validation report shows 0 failures

---

## Next Steps (Delegate to Other Skills)

| Action | Skill |
|--------|-------|
| Create Snowflake Semantic Views | `$snowflake-semantic-view-creator` or `$semantic-view` |
| Generate Cortex Analyst YAML | `$cortex-analyst-semantic-model` |
| Deploy a Snowflake Agent | `$cortex-agent` |
| Add unit tests | `$adding-dbt-unit-test` |
| Run full project quality audit | `$project-quality-audit` |
| Set up data quality monitoring | `$data-quality` |
| Visualize model lineage | `$creating-mermaid-dbt-dag` |
| Create a Streamlit dashboard | `$developing-with-streamlit` |

---

## Example Invocation

```
$onboard-gold-layer

Source name: datafeeds
Upstream model: stg_datafeeds__product_views_and_purchases
Entity: product_views
```
