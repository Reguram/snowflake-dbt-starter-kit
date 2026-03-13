# Task 8: End-to-End — New Source to Dashboard

## Prompt
A new data source `RAW.PAYMENTS` has been added with these columns:
- PAYMENT_ID (INT, PK)
- ORDER_ID (INT, FK to ORDERS)
- PAYMENT_METHOD (VARCHAR: 'credit_card', 'bank_transfer', 'coupon')
- AMOUNT (DECIMAL(12,2))
- PAYMENT_DATE (DATE)
- STATUS (VARCHAR: 'success', 'failed', 'pending')

Build the complete end-to-end pipeline:

1. **Source definition**: Add to `_sources.yml`
2. **Staging model**: `stg_raw__payments`
3. **Intermediate model**: `int_orders_with_payments` joining orders + payments
4. **Mart update**: Add payment fields to `fct_orders`
5. **Semantic view update**: Add payment metrics to `sem_revenue_analysis`
6. **Tests**: Full test coverage for all new models
7. **Streamlit update**: Add payment breakdown panel to the dashboard

## Expected Output
- 5+ new/updated SQL files
- Updated schema.yml entries
- Updated Streamlit app code
- All models should reference each other correctly via {{ ref() }}

## Evaluation Dimensions
- dbt Model Generation (primary)
- Semantic View Creation
- Streamlit App Scaffolding
- Context Awareness
- Iteration Speed

## Scoring Notes
- 5 pts: Complete pipeline, all refs correct, tests defined, Streamlit works, semantic view updated
- 4 pts: Pipeline works but missing one component (e.g., no Streamlit update)
- 3 pts: Core models correct but missing tests or semantic view
- 2 pts: Models exist but don't chain correctly
- 1 pts: Incomplete, multiple missing pieces, won't compile
