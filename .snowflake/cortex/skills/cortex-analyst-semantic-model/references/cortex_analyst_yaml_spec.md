# Cortex Analyst YAML Semantic Model Specification

> Reference: [Snowflake Documentation — Cortex Analyst Semantic Model Spec](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/semantic-model-spec)

## Top-Level Structure

```yaml
name: <string>                # Required. Unique name for the semantic model.
description: <string>         # Optional. Description of the model.
tables: [<table>]             # Required. List of logical table definitions.
relationships: [<rel>]        # Optional. Join definitions between tables.
verified_queries: [<vq>]      # Optional. Tested SQL queries for accuracy.
custom_instructions: <string> # Optional. Text-to-SQL instructions.
```

## Table Definition

```yaml
- name: <string>              # Required. Logical table name.
  description: <string>       # Optional. Multi-line description.
  base_table:                 # Required. Physical Snowflake table reference.
    database: <string>        # e.g., DBT_DEV
    schema: <string>          # Where the TABLE lives (e.g., DBT_MARTS), NOT the stage schema
    table: <string>           # e.g., FCT_SALES
  dimensions: [<dim>]         # Optional. Categorical/entity columns.
  time_dimensions: [<td>]     # Optional. Date/timestamp columns.
  facts: [<fact>]             # Optional. Numeric/aggregatable columns.
  primary_key:                # Optional. Uniqueness constraint.
    columns: [<string>]
```

## Dimension

```yaml
- name: <string>              # Required. Column name (UPPER_CASE).
  synonyms: [<string>]        # Optional. NL synonyms for the column.
  description: <string>       # Required. What this column represents.
  expr: <string>              # Required. SQL expression (usually column name).
  data_type: <string>         # Required. Snowflake data type.
  sample_values: [<string>]   # Optional. Example values from actual data.
```

## Time Dimension

Same as Dimension, but specifically for DATE/TIMESTAMP columns. Cortex Analyst uses these for time-based queries (trends, periods, date filters).

## Fact

```yaml
- name: <string>              # Required. Column name (UPPER_CASE).
  synonyms: [<string>]        # Optional. NL synonyms.
  description: <string>       # Required. What this metric measures.
  expr: <string>              # Required. SQL expression.
  data_type: <string>         # Required. Snowflake data type (NUMBER, FLOAT, etc.).
  default_aggregation: <agg>  # Optional. Default: sum. One of: sum, avg, count, min, max.
  sample_values: [<string>]   # Optional. Example values.
```

## Primary Key

```yaml
primary_key:
  columns:                    # Required. List of dimension columns that uniquely identify rows.
    - <column_name>
```

## Relationships

Defines join logic between logical tables. Required for multi-table semantic models.

```yaml
relationships:
  - name: <string>            # Required. Unique relationship identifier.
    left_table: <string>      # Required. Logical table name (many side for many_to_one).
    right_table: <string>     # Required. Logical table name (one side for many_to_one).
    relationship_columns:     # Required. Join column pairs.
      - left_column: <string>
        right_column: <string>
    join_type: <string>       # Required. "left_outer" or "inner".
    relationship_type: <string> # Required. "many_to_one" or "one_to_one".
```

## Verified Queries

Pre-validated SQL queries that demonstrate correct analytical patterns. Cortex Analyst uses these to improve accuracy.

```yaml
verified_queries:
  - name: <string>            # Required. Unique query identifier.
    question: <string>        # Required. Natural language question.
    use_as_onboarding_question: <bool> # Optional. Show in initial suggestions.
    sql: <string>             # Required. Complete, tested SQL query.
    verified_by: <string>     # Optional. Who verified this query.
    verified_at: <int>        # Optional. Unix timestamp of verification.
```

## Custom Instructions

Free-text instructions to guide text-to-SQL generation. Include domain-specific rules, column usage patterns, and edge cases.

```yaml
custom_instructions: |
  When asked about 'revenue', use SUM(TOTAL_SALES).
  For 'high' and 'low' prices, use 'all-day_high' and 'all-day_low' variables.
  String comparisons are case-insensitive — convert to uppercase.
  For 'most recent' queries, use ORDER BY DATE DESC LIMIT 1.
```

## Best Practices

1. **Descriptions are critical** — Cortex Analyst uses them to understand semantics
2. **Synonyms improve NL matching** — include domain jargon, abbreviations, and alternative names
3. **Sample values help disambiguation** — Cortex Analyst uses them to infer data patterns
4. **Verified queries set accuracy baseline** — test every query before including
5. **Custom instructions reduce errors** — document non-obvious column usage rules
6. **One YAML per analytical domain** — don't combine unrelated tables in one model
7. **Fully qualified table names** — always use `database.schema.table` in SQL
8. **Primary keys matter** — they help Cortex Analyst understand table grain
