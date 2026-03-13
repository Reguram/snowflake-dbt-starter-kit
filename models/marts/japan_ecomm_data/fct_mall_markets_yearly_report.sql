-- Fact table: auto-generated from MALL_MARKETS_YEARLY_REPORT
with source as (
    select * from {{ ref('stg_japan_ecomm_data__mall_markets_yearly_report') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['month']) }} as mall_markets_yearly_report_id,
    month,
    website_type,
    data_source,
    maker,
    item_name,
    model,
    release_date,
    condition,
    volume,
    sum_price,
    mom_change_in_listing_count,
    transaction_ount,
    mom_change_in_transaction_count,
    listing_count,
    mom_change_in_gmv,
    date_trunc('month', month) as month_month,
    year(month) as month_year

from source
