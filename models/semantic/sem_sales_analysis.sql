-- models/semantic/sem_sales_analysis.sql
{{ config(materialized='view', schema='DBT_MARTS') }}

with base as (
    select * from {{ ref('fct_sales') }}
)

select
    -- Dimensions
    sales_date,
    item_category,
    -- Derived time dimensions
    date_trunc('month', sales_date) as sales_month,
    date_trunc('quarter', sales_date) as sales_quarter,
    extract(year from sales_date) as sales_year,

    -- Metrics (raw columns for aggregation in Semantic View)
    total_sales,
    average_price,
    transaction_count

from base
