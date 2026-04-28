# Fact Table Patterns

## Purpose
Fact tables are the core of the gold layer — they contain transactional/event data
with aggregated metrics at a defined grain.

## Pattern Extraction Guide

When reading an existing `fct_*.sql` file, extract these elements:

| Element | Common Variants |
|---------|----------------|
| `config()` contents | `materialized='table'`, `cluster_by=['date_col']`, `tags` |
| CTE naming | `source_data → aggregated_data → final`, `base → measures → output` |
| CTE spacing | Spacious (blank lines between), compact (no blanks) |
| SK macro | `dbt_utils.generate_surrogate_key`, custom `generate_sk` |
| Key naming | `<entity>_key`, `<entity>_id`, `<entity>_sk` |
| Keyword case | `select`, `SELECT`, `Select` |
| Final SELECT | `select * from final`, explicit column list |
| Aggregation alignment | Aligned `as` aliases, unaligned |

## Default Scaffolding Templates

### Simple fact table (single source, aggregation)
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
    from {{ ref('<upstream_model>') }}
),

aggregated_data as (
    select
        <group_col_1>,
        <group_col_2>,
        sum(<metric_col_1>) as total_<metric>,
        avg(<metric_col_2>) as avg_<metric>,
        count(*)            as record_count
    from source_data
    group by <group_col_1>, <group_col_2>
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['<pk_col_1>', '<pk_col_2>']) }} as <entity>_key,
        <group_col_1>,
        <group_col_2>,
        total_<metric>,
        avg_<metric>,
        record_count
    from aggregated_data
)

select * from final
```

### Fact table without aggregation (transactional grain)
```sql
{{
    config(
        materialized='table',
        cluster_by=['<date_column>']
    )
}}

with source_data as (
    select * from {{ ref('<upstream_model>') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['<pk_col>']) }} as <entity>_key,
        <date_col>,
        <dim_col_1>,
        <dim_col_2>,
        <metric_col_1>,
        <metric_col_2>
    from source_data
)

select * from final
```

### Multi-source fact table (from intermediate)
```sql
{{
    config(
        materialized='table',
        cluster_by=['<date_column>']
    )
}}

with enriched as (
    select * from {{ ref('int_<source>__<description>') }}
),

aggregated as (
    select
        <group_col_1>,
        <group_col_2>,
        sum(<metric>) as total_<metric>,
        count(distinct <entity_id>) as distinct_<entity>_count
    from enriched
    group by <group_col_1>, <group_col_2>
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['<pk_cols>']) }} as <entity>_key,
        *
    from aggregated
)

select * from final
```

### Summary / pre-aggregated table
```sql
{{
    config(
        materialized='table',
        cluster_by=['<date_column>']
    )
}}

with source_data as (
    select * from {{ ref('<upstream_fact_or_staging>') }}
),

summary as (
    select
        <time_dimension>,
        <category_dimension>,
        sum(<metric_1>) as total_<metric_1>,
        avg(<metric_2>) as avg_<metric_2>,
        count(*)        as record_count,
        count(distinct <entity_id>) as unique_<entity>_count
    from source_data
    group by <time_dimension>, <category_dimension>
)

select * from summary
```

## Clustering Key Selection

| Column Type | Priority | Example |
|------------|----------|---------|
| Date/timestamp used in WHERE | **Highest** | `order_date`, `created_at` |
| High-cardinality FK used in JOIN | **High** | `customer_id`, `product_id` |
| Low-cardinality used in filters | **Medium** | `region`, `status` |
| Rarely filtered | **Skip** | `description`, `notes` |

```sql
-- Single key
{{ config(cluster_by=['order_date']) }}

-- Multiple keys (up to 3-4 for Snowflake)
{{ config(cluster_by=['order_date', 'region']) }}
```

## Surrogate Key Patterns

```sql
-- Using dbt_utils (most common)
{{ dbt_utils.generate_surrogate_key(['col1', 'col2']) }} as entity_key

-- Custom macro (if project has one)
{{ generate_sk('col1', 'col2') }} as entity_key
```

**Input columns for the surrogate key should be the grain-defining columns** —
the columns that make each row unique.

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|---------------|-----|
| `SELECT *` in final CTE | Breaks contract — columns may change upstream | List all columns |
| No `config()` block | Uses project default (may be `view`) | Add explicit `table` materialization |
| No `cluster_by` | Large tables scan inefficiently | Add date/filter column |
| SK from non-grain columns | Key won't be unique | Use only grain columns |
| Hard-coded schema/database | Breaks across environments | Use `{{ ref() }}` |
| Aggregation + window in same CTE | Hard to debug, often wrong results | Split into separate CTEs |
| `LIMIT` clause | Truncates production data | Remove |
