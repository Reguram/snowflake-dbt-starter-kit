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

### Multi-source union (combine same-grain feeds)

Use when stacking multiple staging models that share the same grain — e.g. region-
partitioned tables (`orders_na`, `orders_eu`), monthly snapshots, or feeds from
multiple source systems. Each branch is aligned to a common schema in its own CTE
**before** the `UNION ALL`. A `source_system` discriminator column is added so the
origin of each row is recoverable downstream.

```sql
with na_raw as (
    select * from {{ ref('stg_<SOURCE_NAME>__orders_na') }}
),

eu_raw as (
    select * from {{ ref('stg_<SOURCE_NAME>__orders_eu') }}
),

na_aligned as (
    select
        order_id::varchar             as order_id,
        customer_id::varchar          as customer_id,
        amount::number(18,4)          as amount,
        order_date::timestamp_ntz     as order_event_at,
        cast(null as varchar)         as eu_vat_id,   -- column missing in NA
        'na'                          as source_system
    from na_raw
),

eu_aligned as (
    select
        order_id::varchar             as order_id,
        customer_id::varchar          as customer_id,
        amount::number(18,4)          as amount,
        order_event_ts::timestamp_ntz as order_event_at,
        eu_vat_id::varchar            as eu_vat_id,
        'eu'                          as source_system
    from eu_raw
)

select * from na_aligned
union all
select * from eu_aligned
```

**Rules:**
- Use `union all` by default — it preserves row counts and is far cheaper than `union`
  (which sorts + dedupes the entire result).
- Only use `union` (without `all`) when the user explicitly asks to deduplicate identical
  rows that may legitimately appear in multiple branches.
- Every branch must `select` the **same column names, in the same order, with the same
  types**. Snowflake will raise a `Numeric value '...' is not recognized` or implicit-
  conversion error otherwise.
- Use `cast(null as <type>) as <col>` for columns that exist in only some branches.
- Add a `source_system` (or similarly-named) discriminator column per branch.
- Build the cross-branch type-alignment matrix from each input's EDA report
  (see Step 2.5.2 of the skill). Cast on the side(s) that don't already match the
  chosen common target type.

### Cleansing pipeline (TRIM / NULL-IF / COALESCE)

Use when a source has dirty string values, sentinel placeholders (`'N/A'`, `'NULL'`,
empty strings) or whitespace that needs normalising before downstream joins.

```sql
with raw as (
    select * from {{ ref('stg_<SOURCE_NAME>__<table>') }}
),

cleansed as (
    select
        <pk_col>,
        trim(email)                                       as email,
        upper(trim(country_code))                         as country_code,
        nullif(trim(status), '')                          as status,
        nullif(trim(status), 'N/A')                       as status_v2,
        coalesce(nullif(trim(segment), ''), 'unknown')    as segment
    from raw
)

select * from cleansed
```

**Rules:**
- Apply cleansing **before** joins so join keys are already normalised.
- Combine `trim` + `nullif` on the same column when the source mixes whitespace +
  sentinels.
- Use `coalesce(nullif(trim(...), ''), '<default>')` to emit a known fallback rather
  than `NULL`.
- Promote EDA red flags (high-null columns with whitespace, suspected sentinel values)
  into automatic cleansing rules — surface them to the user before generating SQL.

### EDA-driven type conversion

Use when the EDA report shows a column is stored in the wrong type (e.g. amount as
`VARCHAR`, dates as `VARCHAR(10)`, booleans as `'Y'/'N'`) and the bronze skill kept
the raw type because the cast was unsafe at staging time.

```sql
with raw as (
    select * from {{ ref('stg_<SOURCE_NAME>__<table>') }}
),

typed as (
    select
        <pk_col>,
        try_to_number(amount_str, 14, 2)         as amount,
        try_to_date(order_date_str, 'YYYY-MM-DD') as order_date,
        try_to_timestamp(event_ts_str)           as event_at,
        case upper(trim(active_flag))
            when 'Y'    then true
            when 'TRUE' then true
            when '1'    then true
            when 'N'    then false
            when 'FALSE' then false
            when '0'    then false
        end                                       as is_active,
        f.value:"id"::number                      as nested_id,
        f.value:"label"::varchar                  as nested_label
    from raw,
    lateral flatten(input => raw.payload_variant) as f
)

select * from typed
```

**Rules:**
- Always prefer `TRY_TO_*` over `TO_*` so a single bad row does not fail the whole load.
- Never cast a column that the EDA already shows in the correct type — that's wasted
  compute and obscures lineage.
- For boolean codings, build the `case` from the actual distinct values in the EDA
  distribution section (don't assume `'Y'/'N'`).
- For `VARIANT` flattening, do it in the same `typed` CTE only when the flatten produces
  scalar columns; otherwise keep a separate `flattened` CTE.
- Keep all type-cast logic in **one** `typed` CTE — never sprinkle casts across CTEs,
  it makes the type contract hard to read.

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
