---
applyTo: "models/**/*.sql"
description: "dbt model generation patterns for staging, intermediate, and mart layers. Auto-activates when editing SQL model files."
---

# Skill: dbt Model Generation

## When to Use
Use this skill when asked to create, scaffold, or generate a new dbt model from a source table.

## Instructions

### Staging Model Generation
1. Identify the source name and table name
2. Generate `stg_<source>__<table>.sql` with:
   - CTE `source` selecting from `{{ source(...) }}`
   - CTE `renamed` mapping all columns to snake_case
   - Final `select * from renamed`
3. Add schema.yml entry with:
   - Description
   - Primary key with `unique` + `not_null` tests
   - Foreign keys with `relationships` tests
   - Categorical columns with `accepted_values`

### Intermediate Model Generation
1. Name as `int_<description>.sql`
2. Use CTEs joining staged models via `{{ ref() }}`
3. Materialize as `ephemeral` (default) or `view` for debugging
4. Add aggregations, business logic, type casting

### Mart Model Generation
1. Fact tables: `fct_<entity>.sql` — one row per business event
   - Include surrogate key: `{{ dbt_utils.generate_surrogate_key(['natural_key']) }}`
   - Include date parts for analysis: `date_trunc('month', ...)`, `year(...)`
2. Dimension tables: `dim_<entity>.sql` — one row per entity with attributes
   - Include calculated segments/tiers
   - Include foreign key references
3. Always define schema.yml with full test coverage

### Example Prompt → Output
**Prompt**: "Generate a staging model for the SUPPLIER table"

**Output**:
```sql
-- models/staging/stg_tpch__supplier.sql
with source as (
    select * from {{ source('tpch', 'SUPPLIER') }}
),
renamed as (
    select
        s_suppkey   as supplier_key,
        s_name      as supplier_name,
        s_address   as address,
        s_nationkey as nation_key,
        s_phone     as phone,
        s_acctbal   as account_balance,
        s_comment   as comment
    from source
)
select * from renamed
```
