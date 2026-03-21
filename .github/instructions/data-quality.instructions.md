---
applyTo: "models/**/schema.yml,models/**/_sources.yml,tests/**"
description: "Data quality testing patterns — schema tests (unique, not_null, relationships, accepted_values), custom singular tests, and source freshness. Auto-activates when editing schema.yml, sources, or test files."
---

# Skill: Data Quality Checks

## When to Use
Use this skill when asked to check data quality, add tests, or validate dbt models.

## Test Types

### Schema Tests (in schema.yml)
| Test | Use Case | Example |
|------|----------|---------|
| `unique` | Primary keys | Every model's PK |
| `not_null` | Required fields | PKs, FKs, dates |
| `relationships` | Foreign keys | FK → PK in parent |
| `accepted_values` | Enums | status, segment |
| `dbt_expectations.expect_column_values_to_be_between` | Ranges | quantity 0-100 |
| `dbt_expectations.expect_column_to_exist` | Schema drift | Critical columns |

### Custom Singular Tests (in tests/)
- **Row count thresholds**: Ensure tables have minimum expected records
- **Revenue positivity**: Fulfilled orders should have positive revenue
- **Referential integrity**: Custom cross-model validation
- **Business rule validation**: Domain-specific assertions

### Freshness Checks (in _sources.yml)
```yaml
sources:
  - name: tpch
    loaded_at_field: _loaded_at
    freshness:
      warn_after: {count: 24, period: hour}
      error_after: {count: 48, period: hour}
```

## Implementation Pattern

### Adding Tests to Existing Model
1. Open `models/<layer>/schema.yml`
2. Find or add the model entry
3. Add column-level tests:
```yaml
columns:
  - name: order_key
    tests:
      - unique
      - not_null
  - name: customer_key
    tests:
      - not_null
      - relationships:
          to: ref('dim_customers')
          field: customer_key
```

### Creating Custom Test
Create `tests/assert_<description>.sql`:
```sql
-- Returns rows that FAIL the assertion
select *
from {{ ref('model_name') }}
where <condition_that_should_never_be_true>
```

## Unit Testing (dbt Unit Tests)
Unit tests mock upstream inputs and validate expected outputs — ideal for complex SQL logic.

### When to Use Unit Tests
- Complex SQL: regex, date math, window functions, complex joins
- Bug fix verification: prove the fix works with a regression test
- Edge cases: NULLs, empty strings, boundary dates
- High-criticality models: revenue, compliance, financial reporting
- Before refactoring: lock in current behavior

### Unit Test Structure
Define in any YAML file within your model paths:
```yaml
unit_tests:
  - name: test_order_status_logic
    description: "Verify status derivation for different scenarios"
    model: fct_orders
    given:
      - input: ref('stg_tpch__orders')
        rows:
          - {order_key: 1, order_status: "F", total_price: 100.00}
          - {order_key: 2, order_status: "O", total_price: 0.00}
          - {order_key: 3, order_status: "P", total_price: 50.00}
    expect:
      rows:
        - {order_key: 1, is_fulfilled: true, has_revenue: true}
        - {order_key: 2, is_fulfilled: false, has_revenue: false}
        - {order_key: 3, is_fulfilled: false, has_revenue: true}
```

### TDD Workflow
1. Choose the model to test
2. Use `dbt show --select upstream_model --limit 5` to preview upstream data shapes
3. Mock representative + edge-case inputs in `given`
4. Define expected outputs in `expect`
5. Run: `dbt build --select model_name` (runs unit tests + materializes + data tests)
6. Or run unit tests only: `dbt test --select "model_name,test_type:unit"`

### Unit Test Tips
- Use `dict` format (YAML) by default — most readable
- Only include columns relevant to your test logic (others default to NULL)
- For ephemeral model dependencies, use `sql` format (requires ALL columns)
- Exclude from production: `dbt build --exclude-resource-type unit_test`
- Fixture CSV files go in `tests/fixtures/` — reference via `fixture: fixture_name`

## Running Tests
- All tests: `dbt test`
- Specific model: `dbt test --select fct_orders`
- By tag: `dbt test --select tag:marts`
- Just sources: `dbt test --select source:tpch`
- Unit tests only: `dbt test --select "model_name,test_type:unit"`
- Prefer `dbt build --select model` over separate `dbt run` + `dbt test`
