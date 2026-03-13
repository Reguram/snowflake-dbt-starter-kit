-- Summary mart: auto-generated aggregations from MALL_MARKETS_MONTHLY_TRANSACTION
-- Dimensions: WEBSITE_TYPE, DATA_SOURCE, MAKER, ITEM_NAME, MODEL, CONDITION, VOLUME, IS_SIM_FREE, NETWORK_RESTRICTION
-- Measures: PRICE, STOCK_PERIOD

with source as (
    select * from {{ ref('stg_japan_ecomm_data__mall_markets_monthly_transaction') }}
)

select
    website_type,
    data_source,
    maker,
    item_name,
    model,
    condition,
    volume,
    is_sim_free,
    network_restriction,
    date_trunc('month', sales_date) as month_period,
    year(sales_date) as year_period,
    count(*) as record_count,
    sum(price) as total_price,
    avg(price) as avg_price,
    min(price) as min_price,
    max(price) as max_price,
    sum(stock_period) as total_stock_period,
    avg(stock_period) as avg_stock_period,
    min(stock_period) as min_stock_period,
    max(stock_period) as max_stock_period

from source
group by website_type, data_source, maker, item_name, model, condition, volume, is_sim_free, network_restriction, date_trunc('month', sales_date), year(sales_date)
