# Intermediate Model Patterns

## Purpose
Intermediate models apply business logic between staging (bronze) and marts (gold).
They are ONLY created when justified — not every pipeline needs a silver layer.

## Pattern Extraction Guide

When reading an existing `int_*.sql` file, extract these elements:

### File & Directory Conventions

| Element | Common Variants |
|---------|----------------|
| File naming | `int_<source>__<desc>.sql`, `int_<desc>.sql` |
| Directory | `models/intermediate/<source>/`, `models/intermediate/` (flat) |
| Schema.yml | Per-directory `schema.yml` or shared |

### SQL Structure Elements

| Element | Common Variants |
|---------|----------------|
| CTE naming | `source_data`→`enriched`, `staged`→`transformed`, `base`→`final` |
| SQL keyword case | `UPPER_CASE`, `lowercase` |
| `config()` | In-file `{{ config(materialized='view') }}`, managed by `dbt_project.yml` |
| CTE spacing | Blank lines between CTEs (spacious), no blanks (compact) |
| References | `{{ ref('stg_...') }}` to staging, `{{ source() }}` direct |

## Default Scaffolding

### Single-source intermediate
```sql
with staged as (
    select * from {{ ref('stg_<SOURCE_NAME>__<table>') }}
),

enriched as (
    select
        *,
        -- Business logic here
        case
            when amount > 1000 then 'large'
            when amount > 100 then 'medium'
            else 'small'
        end as order_size_category
    from staged
)

select * from enriched
```

### Multi-source join
```sql
with orders as (
    select * from {{ ref('stg_<SOURCE_NAME>__orders') }}
),

customers as (
    select * from {{ ref('stg_<SOURCE_NAME>__customers') }}
),

joined as (
    select
        orders.order_id,
        orders.order_date,
        orders.amount,
        customers.customer_name,
        customers.segment
    from orders
    left join customers
        on orders.customer_id = customers.customer_id
)

select * from joined
```

### Deduplication
```sql
with source_data as (
    select
        *,
        row_number() over (
            partition by <entity_id>
            order by <timestamp_col> desc
        ) as rn
    from {{ ref('stg_<SOURCE_NAME>__<table>') }}
)

select * from source_data
where rn = 1
```

### LATERAL FLATTEN (semi-structured)
```sql
with raw_data as (
    select * from {{ ref('stg_<SOURCE_NAME>__<table>') }}
),

flattened as (
    select
        raw_data.id,
        f.value:"key"::varchar as extracted_key,
        f.value:"value"::number as extracted_value
    from raw_data,
    lateral flatten(input => raw_data.variant_column) as f
)

select * from flattened
```

### Code-to-label mapping (CASE expression)

Use when a source column contains short codes (single letters, numeric codes, status flags)
that need to be translated to human-readable business labels. Common in retail, healthcare,
finance, and e-commerce datasets where storage-efficient codes are decoded for analytics.

**Generic template:**
```sql
with source_data as (
    select * from {{ ref('stg_<SOURCE_NAME>__<table>') }}
),

decoded as (
    select
        <pk_col>,
        -- ... other passthrough columns ...
        case <code_column>
            when '<code_1>' then '<label_1>'
            when '<code_2>' then '<label_2>'
            when '<code_3>' then '<label_3>'
            else '<default_label>'   -- e.g. 'Unknown', 'Other', null
        end as <decoded_column>
    from source_data
)

select * from decoded
```

**Example variants:**

| Domain | Source codes | Decoded labels |
|--------|-------------|----------------|
| Item condition (retail/e-commerce) | `'A'`, `'B'`, `'C'`, `'D'` | `'Excellent'`, `'Good'`, `'Fair'`, `'Poor'` |
| Order status | `'P'`, `'S'`, `'D'`, `'C'` | `'Pending'`, `'Shipped'`, `'Delivered'`, `'Cancelled'` |
| Severity / priority | `1`, `2`, `3`, `4` | `'Critical'`, `'High'`, `'Medium'`, `'Low'` |
| Customer segment | `'G'`, `'S'`, `'B'` | `'Gold'`, `'Silver'`, `'Bronze'` |
| Yes/No flags | `'Y'`, `'N'` | `true`, `false` (or `'Yes'`, `'No'`) |

**Concrete example — retail item condition:**
```sql
with source_data as (
    select * from {{ ref('stg_<SOURCE_NAME>__transactions') }}
),

decoded as (
    select
        listing_id,
        sales_date,
        item_name,
        case condition
            when 'A' then 'Excellent'
            when 'B' then 'Good'
            when 'C' then 'Fair'
            when 'D' then 'Poor'
            else 'Unknown'
        end as condition,
        cast(price as number(14,2)) as price
    from source_data
)

select * from decoded
```

**Rules:**
- Always include an `else` branch (typically `'Unknown'`, `'Other'`, or `null`) to handle
  new/unexpected codes without dropping rows.
- Keep the decoded column name the same as the source column when the meaning is unchanged
  (just translated), or rename to `<column>_label` / `<column>_desc` if both raw and decoded
  values must coexist.
- Add an `accepted_values` test on the decoded column in `schema.yml` listing all possible
  output labels (including the default).
- For mappings with **>10 codes**, prefer a **seed file** (CSV) joined as a lookup instead of
  a long CASE expression — easier to maintain and document.
- Document the source-of-truth for the code definitions in the model description (e.g.,
  vendor data dictionary link).

**Recommended `schema.yml` test:**
```yaml
- name: condition
  description: "Item condition decoded from source code (A/B/C/D → Excellent/Good/Fair/Poor)."
  tests:
    - not_null
    - accepted_values:
        values: ['Excellent', 'Good', 'Fair', 'Poor', 'Unknown']
```

### Window functions
```sql
with staged as (
    select * from {{ ref('stg_<SOURCE_NAME>__<table>') }}
),

with_running_totals as (
    select
        *,
        sum(amount) over (
            partition by customer_id
            order by order_date
            rows between unbounded preceding and current row
        ) as cumulative_amount,
        lag(order_date) over (
            partition by customer_id
            order by order_date
        ) as previous_order_date
    from staged
)

select * from with_running_totals
```

## Decision Matrix: Skip vs Create

| Scenario | Decision | Reason |
|----------|----------|--------|
| Single table, only rename columns | **SKIP** | Staging already does this |
| Single table, add 1-2 CASE columns | **SKIP** | Do in mart instead |
| Single table, heavy transformation (5+ derived cols) | **CREATE** | Too much logic for marts |
| Multiple tables need joining | **CREATE** | Can't join in staging |
| VARIANT columns need flattening | **CREATE** | Structural change |
| Source has duplicates | **CREATE** | Dedup before marts |
| Window functions needed | **CREATE** | Complex logic |
| Simple WHERE filter | **SKIP** | Filter in mart |
| Complex WHERE with business rules | **CREATE** | Business logic |

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|---------------|-----|
| Aggregation in intermediate | Wrong layer — aggregate in marts | Move GROUP BY to gold |
| 1:1 pass-through (no transformation) | Unnecessary layer — wasted compute | Delete and ref staging directly |
| Hard-coded filter values | Breaks across environments | Use `var()` or configurable values |
| Joining more than 4-5 tables | Too complex — split into multiple intermediates | Chain intermediates |
| Using `{{ source() }}` when staging exists | Skips bronze layer validation | Use `{{ ref('stg_...') }}` |
