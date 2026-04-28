# Mart Schema.yml Patterns

## Purpose
Every mart model MUST have a `schema.yml` entry with descriptions and tests.
This reference shows patterns for fact, dimension, and summary models.

## Pattern Extraction Guide

When reading an existing mart `schema.yml`, extract:

| Element | Common Variants |
|---------|----------------|
| Description style | Multi-line `>`, inline string `"..."` |
| Grain statement | Included in description, separate `meta.grain` |
| SK description | Template: `"Surrogate PK — hash of X, Y"`, freetext |
| Test types | `unique`, `not_null`, `accepted_values`, `relationships`, `dbt_expectations.*` |
| Indentation | 2-space, 4-space |

## Default Scaffolding

### Fact table schema
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
        description: "<what this date represents>"
        tests:
          - not_null
      - name: <categorical_col>
        description: "<what this column represents>"
        tests:
          - not_null
          - accepted_values:
              values: ['val1', 'val2', 'val3']
      - name: <metric_col>
        description: "<what this metric represents (unit, aggregation type)>"
        tests:
          - not_null
      - name: record_count
        description: "Number of source records aggregated into this row."
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 1
```

### Dimension table schema
```yaml
  - name: dim_<entity>
    description: "Distinct <entity> values from the source data."
    columns:
      - name: <entity>_id
        description: "Surrogate primary key."
        tests:
          - unique
          - not_null
      - name: <entity_column>
        description: "<what this column represents>"
        tests:
          - unique
          - not_null
```

### Summary table schema
```yaml
  - name: summary_<table_name>
    description: >
      Pre-aggregated summary of <what>.
      Grain: one row per (<dimension_1>, <dimension_2>).
    columns:
      - name: <dimension_1>
        description: "<description>"
        tests:
          - not_null
      - name: <dimension_2>
        description: "<description>"
        tests:
          - not_null
      - name: total_<metric>
        description: "Sum of <metric> across all records in this group."
      - name: unique_<entity>_count
        description: "Count of distinct <entity> values in this group."
```

## Test Selection Guide

| Column Type | Required Tests | Optional Tests |
|-------------|---------------|----------------|
| Surrogate key (PK) | `unique`, `not_null` | — |
| Natural key (candidate PK) | `unique`, `not_null` | — |
| Foreign key | `not_null` | `relationships` (if target dim exists) |
| Date/timestamp | `not_null` | `dbt_expectations.expect_column_values_to_be_between` |
| Low-cardinality categorical | `not_null` | `accepted_values` |
| High-cardinality categorical | — | `not_null` (if required) |
| Numeric metric | `not_null` (if non-nullable) | `dbt_expectations.expect_column_values_to_be_between` |
| Free text | — | — |
| Boolean | — | `accepted_values: [true, false]` |
| Count metric | `not_null` | `dbt_expectations.expect_column_values_to_be_between: {min_value: 0}` |

## Relationships Test Pattern

When a fact table has a foreign key to a dimension table:

```yaml
      - name: customer_id
        description: "FK to dim_customers."
        tests:
          - not_null
          - relationships:
              to: ref('dim_customers')
              field: customer_id
```

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|---------------|-----|
| Empty description | Fails quality audit | Add meaningful description |
| Missing PK tests | Data quality unknown | Add `unique` + `not_null` |
| Every column has `not_null` | Over-testing — noisy failures | Only test columns that must be non-null |
| No `accepted_values` on categoricals | Won't catch unexpected values | Add for < 20 distinct values |
| Description says "TODO" or placeholder | Not helpful | Write actual description |
| Grain not stated | Others can't understand the model | Add grain to fact description |
| Duplicate test on same column | Redundant | Remove duplicate |
