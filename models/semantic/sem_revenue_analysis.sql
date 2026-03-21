{{ config(materialized='view', schema='DBT_MARTS') }}

with sales as (

    select
        sales_date,
        maker,
        item_category,
        total_sales,
        average_price,
        transaction_count
    from {{ ref('fct_sales') }}

)

select
    sales_date,
    date_trunc('month', sales_date) as sales_month,
    date_trunc('quarter', sales_date) as sales_quarter,
    extract(year from sales_date) as sales_year,
    maker,
    item_category,
    total_sales,
    average_price,
    transaction_count
from sales