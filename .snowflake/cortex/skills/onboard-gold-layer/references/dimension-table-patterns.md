# Dimension Table Patterns

## Purpose
Dimension tables provide lookup/reference data for fact tables — distinct entities
like customers, products, regions, categories, or statuses.

## Pattern Extraction Guide

When reading an existing `dim_*.sql` file, extract:

| Element | Common Variants |
|---------|----------------|
| Uses `SELECT DISTINCT` | Yes (most common), No (when already unique) |
| `WHERE IS NOT NULL` filter | Yes (filter null keys), No |
| Key naming | `<entity>_id`, `<entity>_key`, `<entity>_sk` |
| SK macro | `dbt_utils.generate_surrogate_key`, custom, or none |
| Keyword case | Same as facts, or different |
| `config()` block | `table` (explicit), managed by `dbt_project.yml` |

## Default Scaffolding Templates

### Simple distinct dimension (single column)
```sql
with distinct_values as (
    select distinct
        <column>
    from {{ ref('<upstream_model>') }}
    where <column> is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['<column>']) }} as <entity>_id,
    <column>
from distinct_values
```

### Multi-column dimension (composite entity)
```sql
with source_data as (
    select * from {{ ref('<upstream_model>') }}
),

distinct_entities as (
    select distinct
        <entity_id>,
        <attribute_1>,
        <attribute_2>,
        <attribute_3>
    from source_data
    where <entity_id> is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['<entity_id>']) }} as <entity>_key,
    <entity_id>,
    <attribute_1>,
    <attribute_2>,
    <attribute_3>
from distinct_entities
```

### Dimension from multiple sources (joined)
```sql
with primary_source as (
    select * from {{ ref('<staging_model_1>') }}
),

secondary_source as (
    select * from {{ ref('<staging_model_2>') }}
),

combined as (
    select
        primary_source.<entity_id>,
        primary_source.<attribute_1>,
        secondary_source.<attribute_2>
    from primary_source
    left join secondary_source
        on primary_source.<entity_id> = secondary_source.<entity_id>
),

distinct_entities as (
    select distinct * from combined
    where <entity_id> is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['<entity_id>']) }} as <entity>_key,
    *
from distinct_entities
```

### Date dimension (generated)
```sql
with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2020-01-01' as date)",
        end_date="cast(current_date() as date)"
    ) }}
),

final as (
    select
        cast(date_day as date)              as date_key,
        date_day                            as full_date,
        extract(year from date_day)         as year,
        extract(month from date_day)        as month,
        extract(day from date_day)          as day_of_month,
        extract(dayofweek from date_day)    as day_of_week,
        extract(quarter from date_day)      as quarter,
        to_char(date_day, 'YYYY-MM')        as year_month,
        case
            when extract(dayofweek from date_day) in (0, 6) then true
            else false
        end as is_weekend
    from date_spine
)

select * from final
```

### Static / seed-based dimension
```sql
-- When dimension data comes from a seed CSV
select
    {{ dbt_utils.generate_surrogate_key(['<code>']) }} as <entity>_id,
    <code>,
    <label>,
    <category>
from {{ ref('<seed_name>') }}
```

## When to Create a Dimension

| Scenario | Create Dim? | Reason |
|----------|------------|--------|
| Column has < 50 distinct values in a large fact table | **Yes** | Reduces fact table width |
| Column represents a business entity (customer, product) | **Yes** | Natural dimension |
| Column is a code that maps to a label | **Yes** | Lookup table |
| Column already has unique rows in staging | **Maybe** | Only if it simplifies downstream queries |
| Column is a free-text field | **No** | Too many distinct values |
| Column is a numeric metric | **No** | Belongs in fact table |

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|---------------|-----|
| Dimension without `WHERE IS NOT NULL` | Creates null-key rows | Add filter |
| Dimension without `SELECT DISTINCT` | May have duplicate rows | Add distinct |
| Dimension with aggregation | Wrong model type — should be fact or summary | Move to fact |
| Dimension with many numeric columns | Should be a fact table | Reclassify |
| No surrogate key | Missing stable PK | Add SK via macro |
| Natural key as PK without testing | May not be unique | Add unique + not_null tests |
