---
applyTo: "models/**/*.sql,models/**/*.yml"
description: "dbt model generation patterns for staging, intermediate, and mart layers. Includes DRY principles, planning workflow, and dbt show validation. Auto-activates when editing SQL model files or YAML configs."
---

# Skill: dbt Model Generation

## When to Use
Use this skill when asked to create, scaffold, modify, or generate a dbt model. Also activates when editing any model SQL or YAML to provide context-aware guidance.

## Planning Workflow (Do This First)
Before creating or modifying ANY model:
1. **Check if logic already exists** — search existing models before adding a new one. Prefer adding a column to an existing intermediate model over creating a new model
2. **Read YAML docs** — always read schema.yml for upstream models before modifying them
3. **Ask "why a new model?"** — only create a new model if the logic serves a distinct analytical purpose. Extending existing models keeps the DAG clean
4. **Preview input data** — use `dbt show --select upstream_model --limit 10` to understand the shape of upstream data before writing SQL
5. **Plan CTEs** — sketch out the CTE chain before writing SQL

## DRY Principles
- Before adding a new column or calculation, check if it already exists in an intermediate or staging model
- Prefer reusing existing intermediate models over duplicating logic
- Use `{{ ref() }}` to build on existing work — never copy SQL from another model
- If the same transformation appears in 2+ places, extract it to an intermediate model

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

## Validation with `dbt show`
After writing or modifying any model, **always validate** with `dbt show`:

```bash
# Preview model output (use --limit to control cost)
dbt show --select my_model --limit 10

# Profile key columns — check for NULLs, duplicates, ranges
dbt show --inline "select count(*), count(distinct pk_col), count(*) - count(pk_col) as nulls from {{ ref('my_model') }}" --limit 1

# Preview upstream data before writing joins
dbt show --select upstream_model --limit 5
```

**Common validation checks:**
- Row count matches expectations
- Primary key is unique (count = count distinct)
- No unexpected NULLs in required columns
- Join fanout hasn't occurred (row count didn't explode)
- Aggregations produce sensible values (min/max/avg)

## Common Mistakes to Avoid
| Mistake | Why It's Wrong | Do This Instead |
|---------|---------------|-----------------|
| One-shotting without validation | Misconfigured joins go undetected | Use `dbt show` after every CTE |
| Assuming schema knowledge | Column names/types may differ | Read schema.yml + `dbt show` upstream first |
| Creating unnecessary models | Bloats DAG, duplicates logic | Check if existing model can be extended |
| Hardcoding table names | Breaks across environments | Always use `{{ ref() }}` or `{{ source() }}` |
| Running full `dbt build` to test | Expensive and slow | Use `dbt show --select model` for quick feedback |

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
