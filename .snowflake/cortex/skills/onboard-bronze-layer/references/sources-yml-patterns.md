# `_sources.yml` Pattern Reference

## Purpose
The `_sources.yml` file declares raw Snowflake tables as dbt sources — enabling `{{ source() }}`
references, lineage tracking, and freshness checks. One file per source directory.

## Pattern Extraction Guide

When reading an existing `_sources.yml`, extract these elements:

### Structure Elements

| Element | Common Variants | Notes |
|---------|----------------|-------|
| Source `name` | `snake_case` (most common), `camelCase`, `PascalCase` | Must match directory name |
| `description` | Template: `"Raw source from DB.SCHEMA"`, Free text | Note exact wording |
| `database` | Hard-coded `"MY_DB"`, Dynamic `"{{ var('source_db') }}"` | Note quoting style |
| `schema` | Hard-coded `"MY_SCHEMA"`, Dynamic `"{{ var('source_schema') }}"` | Note quoting style |
| `quoting.identifier` | `true` (Snowflake standard), `false`, absent | Snowflake needs `true` for mixed-case |
| `quoting.database` | `true`, absent | Less common |
| `quoting.schema` | `true`, absent | Less common |

### Table Elements

| Element | Common Variants | Notes |
|---------|----------------|-------|
| Table `name` | `UPPER_CASE` (Snowflake default), `lowercase` | Must match actual Snowflake table |
| Table `description` | Template: `"Raw <table> table (~N rows)"`, Free text | Note format |
| `loaded_at_field` | Column name for freshness checks | Optional |
| `freshness.warn_after` | `{count: 24, period: hour}` | Optional |

### Column Elements

| Element | Common Variants | Notes |
|---------|----------------|-------|
| Column `name` | `UPPER_CASE` (raw Snowflake), `snake_case` | Must match actual source columns |
| Column `description` | Empty `""`, Populated text | Note which approach |
| PK column tests | `unique` + `not_null` (standard) | Some projects add `dbt_expectations` |
| Non-PK tests | None (most common), `not_null` on required fields | Note project convention |
| `accepted_values` | On low-cardinality columns | Some projects add in staging, others in sources |

## Default Scaffolding

Use this template when no existing `_sources.yml` exists in the project:

```yaml
version: 2

sources:
  - name: <SOURCE_NAME>
    description: "Raw source from <SOURCE_DATABASE>.<SOURCE_SCHEMA>"
    database: "<SOURCE_DATABASE>"
    schema: "<SOURCE_SCHEMA>"
    quoting:
      identifier: true
    tables:
      - name: <SOURCE_TABLE>
        description: "Raw <table_lower> table (~<row_count> rows)"
        columns:
          - name: <PK_COLUMN>
            description: ""
            tests:
              - unique
              - not_null
          - name: <OTHER_COLUMN>
            description: ""
```

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|---------------|-----|
| Hard-coded `database.schema.table` in SQL | Breaks portability across environments | Use `{{ source() }}` |
| Missing `quoting.identifier: true` | Snowflake may not find mixed-case columns | Add quoting block |
| Tests on every column in sources | Over-testing at wrong layer — test in staging/marts | Only PK tests in sources |
| `SELECT *` reference instead of `{{ source() }}` | No lineage tracking | Use `{{ source() }}` |
| Duplicate source names across directories | dbt compilation error | Unique names per source |
