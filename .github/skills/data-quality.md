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

## Running Tests
- All tests: `dbt test`
- Specific model: `dbt test --select fct_orders`
- By tag: `dbt test --select tag:marts`
- Just sources: `dbt test --select source:tpch`
