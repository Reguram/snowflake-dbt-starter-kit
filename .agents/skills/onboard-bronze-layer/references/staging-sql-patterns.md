# Staging SQL Pattern Reference

## Purpose
Staging models are 1:1 with raw source tables. They rename columns, cast types,
and make data accessible via `{{ ref() }}` for downstream models. No business logic.

## Pattern Extraction Guide

When reading an existing `stg_*.sql` file, extract these elements:

### CTE Structure

| Element | Common Variants | Notes |
|---------|----------------|-------|
| First CTE name | `source` (most common), `src`, `raw`, `base` | The source-reading CTE |
| First CTE body | `select * from {{ source() }}` (most common) | Some list columns explicitly |
| Transform CTE name | `staged` (most common), `renamed`, `cleaned`, `final` | The column-renaming CTE |
| Final select | `select * from staged` (most common), explicit column list | Note which approach |
| Number of CTEs | 2 (standard), 3+ (if type casting or dedup needed) | Note CTE count |

### SQL Style

| Element | Common Variants | Notes |
|---------|----------------|-------|
| Keyword casing | `lowercase` (dbt convention), `UPPER_CASE` (SQL tradition) | Note consistency |
| Indentation | 4-space (most common), 2-space, tabs | Note exact spacing |
| Column indentation | 8-space (nested in CTE), 4-space | Count spaces before column names |
| Trailing commas | Yes (modern dbt style), No (traditional SQL) | Note which |
| Blank lines between CTEs | Yes (spacious), No (compact) | Note spacing |
| CTE comma placement | Leading `, cte_name as (` vs trailing `) , cte_name as (` | Note style |

### Column Handling

| Element | Common Variants | Notes |
|---------|----------------|-------|
| Column renaming | `"SOURCE_COL" as snake_col` (explicit), `lower()` function | Note approach |
| Type casting | `TRY_TO_DATE()` (safe), `CAST()` (strict), `::type` (shorthand) | Note which |
| Column ordering | Alphabetical, logical grouping, source order | Note convention |
| Surrogate key | `{{ dbt_utils.generate_surrogate_key() }}`, custom macro, none | Note if present |
| `config()` block | In-file `{{ config() }}`, managed by `dbt_project.yml` | Important distinction |

## Default Scaffolding

Use this template when no existing staging SQL exists in the project:

```sql
with source as (
    select * from {{ source('<SOURCE_NAME>', '<SOURCE_TABLE>') }}
),

staged as (
    select
        <col_1_snake>,
        <col_2_snake>,
        <col_n_snake>
    from source
)

select * from staged
```

## Column Renaming Examples

```sql
-- Standard rename (UPPER_CASE source → snake_case)
"ORDER_ID" as order_id,
"CUSTOMER_NAME" as customer_name,
"ORDER_DATE" as order_date,

-- With type casting
TRY_TO_DATE("ORDER_DATE") as order_date,
TRY_TO_NUMBER("QUANTITY") as quantity,
TRIM("CUSTOMER_NAME") as customer_name,

-- Surrogate key (when no natural PK exists)
{{ dbt_utils.generate_surrogate_key(['"COL1"', '"COL2"']) }} as row_key,
```

## Staging Schema.yml Pattern

### Extraction Guide

| Element | Common Variants | Notes |
|---------|----------------|-------|
| Description format | Template: `"Staged <table> from <source>"`, Free text | Note wording |
| Column names | snake_case (matching SQL output) | Must match exactly |
| Column descriptions | Empty `""` (initial), Populated | Note approach |
| PK tests | `unique` + `not_null` (standard) | Note test types |
| Non-PK tests | None (most common at staging), `not_null` on required | Note convention |
| Indentation | 2-space (YAML standard), 4-space | Note spacing |

### Default Scaffolding

```yaml
version: 2

models:
  - name: stg_<SOURCE_NAME>__<table_lower>
    description: "Staged <table_lower> from <SOURCE_NAME> — renamed columns, 1:1 with source"
    columns:
      - name: <pk_col_lower>
        description: ""
        tests:
          - unique
          - not_null
      - name: <other_col_lower>
        description: ""
```

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|---------------|-----|
| `SELECT *` in transform CTE | No explicit column control, breaks on source changes | List all columns |
| Business logic in staging | Wrong layer — staging is 1:1 with source | Move to intermediate |
| Hard-coded `config()` when `dbt_project.yml` manages it | Conflicting materialization settings | Match project convention |
| Missing double underscore | dbt naming convention: `stg_<source>__<table>` | Use `__` separator |
| Aggregation in staging | Wrong layer — staging is row-level | Move to intermediate or marts |
