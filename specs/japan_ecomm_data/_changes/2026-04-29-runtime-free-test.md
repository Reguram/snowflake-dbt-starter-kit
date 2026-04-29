# Change Request — 2026-04-29
**From:** Jane Doe (BA)
**Models impacted:** `fct_sales`
**Source:** `japan_ecomm_data`

This is a real-time test of the runtime-free spec-driven-model-sync skill.

## fct_sales

- In `fct_sales`, rename `average_price` to `avg_unit_price`.
- Change description of `fct_sales.sales_date` to "Date the sale occurred (UTC)."
- Add test unique to `fct_sales.sales_key`.
