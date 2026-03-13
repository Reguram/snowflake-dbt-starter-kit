-- Fact table: auto-generated from MALL_MARKETS_MONTHLY_TRANSACTION
with source as (
    select * from {{ ref('stg_japan_ecomm_data__mall_markets_monthly_transaction') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['listing_id']) }} as "mall_markets_monthly_transaction_id",
    listing_id,
    website_type,
    data_source,
    sales_date,
    maker,
    item_name,
    model,
    release_date,
    condition,
    volume,
    is_sim_free,
    network_restriction,
    price,
    stock_period,
    date_trunc('month', data_source) as data_source_month,
    year(data_source) as data_source_year

from source
