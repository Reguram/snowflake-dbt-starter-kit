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

Every staging model is authored as a **trio** of sibling files under
`models/staging/<source>/`:

- `stg_<source>__<table>.sql` — generated SQL (1:1 transform of the source)
- `stg_<source>__<table>.yml` *(or merged into a directory `schema.yml`)* — schema/tests/docs
- `stg_<source>__<table>.md` — **transformation spec, source of truth for column-level transforms**

**The `.md` spec drives the `.sql`.** Authoring rules:

1. List **only columns that need a transformation** in the *Transformations*
   table. Each row carries an *Output column*, *Type*, *Source column(s)*,
   and a **natural-language description** of the transform
   (e.g. *"safely cast to a date"*, *"trim whitespace"*,
   *"total sales divided by total volume"*). The agent translates the
   description into a Snowflake SQL expression and records it in the
   *Resolved SQL* column of the spec.
2. **Any column not mentioned is moved as-is** — emitted as
   `"SOURCE_COL" as source_col` with no logic.
3. **Excluded columns are called out explicitly** under *Excluded columns*.
4. No business logic in the `.md` — bronze is 1:1; joins / aggregates /
   `ref()` belong in intermediate or marts.

See [.agents/skills/onboard-bronze-layer/references/transformations-md-template.md](../../.agents/skills/onboard-bronze-layer/references/transformations-md-template.md)
for the canonical template, and `$onboard-bronze-layer` for the full flow.

Workflow:

1. Identify the source name and table name.
2. Author or scaffold `stg_<source>__<table>.md` from the EDA profile —
   pre-fill safe casts as natural-language descriptions
   (e.g. *"safely cast to a date"*), list red-flagged columns under
   *Excluded columns*, leave everything else implicitly as-is.
3. Generate `stg_<source>__<table>.sql` mechanically from the `.md` plan:
   - For each *Transformations* row, resolve the natural-language
     *Description* into a Snowflake SQL expression and write it back into
     the *Resolved SQL* column of the spec.
   - CTE `source` selecting from `{{ source(...) }}`.
   - CTE `staged` containing one line per kept column, sourced from the
     plan (resolved expression, or `"SRC" as snake`).
   - Final `select * from staged`.
4. Add the `schema.yml` entry — column set must match the SQL output:
   - Description.
   - Primary key with `unique` + `not_null` tests.
   - Foreign keys with `relationships` tests.
   - Categorical columns with `accepted_values`.
5. **Validate consistency**: every Transformations row produced an output
   column; every Excluded column is absent from SQL and YAML; every other
   source column appears renamed-only.

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

### Example Prompt → Output (Intermediate: code-to-label decoding)
**Prompt**: "Add an intermediate model that decodes the `CONDITION` code into a readable label"

**Output** (generic pattern — applies to any short-code → business-label translation):
```sql
-- models/intermediate/<source>/int_<source>__<table>_decoded.sql
with source_data as (
    select * from {{ ref('stg_<source>__<table>') }}
),
decoded as (
    select
        <pk_col>,
        -- pass-through columns ...
        case <code_column>
            when '<code_1>' then '<label_1>'
            when '<code_2>' then '<label_2>'
            when '<code_3>' then '<label_3>'
            else 'Unknown'   -- always include a default branch
        end as <decoded_column>
    from source_data
)
select * from decoded
```

**Concrete example** (retail item condition `A`/`B`/`C`/`D` → readable grade):
```sql
case condition
    when 'A' then 'Excellent'
    when 'B' then 'Good'
    when 'C' then 'Fair'
    when 'D' then 'Poor'
    else 'Unknown'
end as condition
```

**Common variants of the same pattern:**
| Source codes | Decoded labels | Domain |
|--------------|---------------|--------|
| `'A'`, `'B'`, `'C'`, `'D'` | `'Excellent'`, `'Good'`, `'Fair'`, `'Poor'` | Item condition / grade |
| `'P'`, `'S'`, `'D'`, `'C'` | `'Pending'`, `'Shipped'`, `'Delivered'`, `'Cancelled'` | Order status |
| `1`, `2`, `3`, `4` | `'Critical'`, `'High'`, `'Medium'`, `'Low'` | Severity / priority |
| `'G'`, `'S'`, `'B'` | `'Gold'`, `'Silver'`, `'Bronze'` | Customer tier |
| `'Y'`, `'N'` | `true`, `false` | Boolean flags |

**Always pair with this `schema.yml` test** so unexpected codes are caught:
```yaml
- name: <decoded_column>
  description: "<col> decoded from source code (<code_1>/<code_2>/... → <label_1>/<label_2>/...)."
  tests:
    - not_null
    - accepted_values:
        values: ['<label_1>', '<label_2>', '<label_3>', 'Unknown']
```

**When to escalate to a seed file:** if the mapping has **more than ~10 codes**, replace the
inline `CASE` with a `seeds/<name>_lookup.csv` joined via `{{ ref() }}` — easier to version,
review, and document.

> Full pattern reference: see `onboard-silver-layer/references/intermediate-patterns.md`
> → "Code-to-label mapping (CASE expression)".
