# Change Request — 2026-05-06
**From:** Aaron Patel (Marketing Analytics)
**Models impacted:** `fct_sales`, `summary_mall_markets_monthly_transaction`
**Source:** `japan_ecomm_data`

Sample change request for demoing the spec-driven-model-sync skill.

## fct_sales

- Rename `transaction_count` to `order_count`.
- Add a new column `revenue_per_order` defined as `total_sales` divided by
  `transaction_count` (null-safe — null when count is 0).
- Add `accepted_values` test on `item_category` for
  `['electronics', 'apparel', 'home', 'beauty', 'other']`.
- Update description of `fct_sales.maker` to "Brand or manufacturer of the
  item sold."

## summary_mall_markets_monthly_transaction

- Add a `not_null` test on `month_start_date`.
- Drop column `legacy_channel_code` — no longer populated upstream.
