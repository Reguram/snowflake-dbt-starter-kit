# Task 6: Add Data Quality Tests

## Prompt
Add comprehensive data quality tests to the `fct_orders` model:

1. **Schema tests** (in schema.yml):
   - Primary key: unique + not_null on order_id
   - Foreign key: customer_key references dim_customers
   - Accepted values: order_status in ['F', 'O', 'P']
   - Range check: net_revenue between 0 and 10,000,000
   - Not null: order_date, net_revenue, total_quantity

2. **Custom singular tests** (in tests/):
   - `assert_no_future_orders.sql`: No orders with order_date > current_date
   - `assert_ship_after_order.sql`: first_ship_date >= order_date
   - `assert_revenue_consistency.sql`: net_revenue ≈ gross_revenue * (1 - avg_discount) within 1%

3. **Source freshness** (in _sources.yml):
   - Warning if source data older than 24 hours
   - Error if older than 48 hours

## Expected Output
- Updated `models/marts/schema.yml`
- 3 custom test files in `tests/`
- Updated `models/staging/_sources.yml` with freshness

## Evaluation Dimensions
- Code Review (testing knowledge)
- dbt Model Generation
- Context Awareness

## Scoring Notes
- 5 pts: All tests correct, proper dbt syntax, freshness configured
- 4 pts: Most tests correct, minor syntax issues
- 3 pts: Basic tests present but missing custom tests or freshness
- 2 pts: Incorrect test syntax or wrong model references
- 1 pts: Does not produce valid dbt test definitions
