---
description: "Analyze a dbt model and suggest comprehensive tests (schema, unit, custom)"
---
# Suggest Tests

Analyze the currently open dbt model and suggest comprehensive tests.

## What to do:
1. Read the model's SQL to understand columns, joins, and business logic
2. Read existing schema.yml tests (if any)
3. Suggest missing tests:
   - **Primary key**: `unique` + `not_null` on the primary key column
   - **Foreign keys**: `relationships` tests for all FK columns
   - **Categoricals**: `accepted_values` for status/type/segment columns
   - **Ranges**: `dbt_expectations.expect_column_values_to_be_between` for numeric columns
   - **Not null**: For all required business columns
4. Suggest **unit tests** for complex SQL logic (window functions, case statements, date math)
5. Suggest **custom singular tests** for business rules that can't be expressed as schema tests
6. Generate the YAML for all suggested tests

Follow the patterns in the `data-quality` and `adding-dbt-unit-test` skills.
