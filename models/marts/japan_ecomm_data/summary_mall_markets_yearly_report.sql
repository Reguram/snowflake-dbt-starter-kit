-- Summary mart: auto-generated aggregations from MALL_MARKETS_YEARLY_REPORT
-- Dimensions: WEBSITE_TYPE, DATA_SOURCE, MAKER, ITEM_NAME, MODEL, CONDITION, VOLUME
-- Measures: SUM_PRICE, MOM_CHANGE_IN_LISTING_COUNT, TRANSACTION_OUNT, MOM_CHANGE_IN_TRANSACTION_COUNT, LISTING_COUNT, MOM_CHANGE_IN_GMV

with source as (
    select * from {{ ref('stg_japan_ecomm_data__mall_markets_yearly_report') }}
)

select
    website_type,
    data_source,
    maker,
    item_name,
    model,
    condition,
    volume,
    date_trunc('month', month) as month_period,
    year(month) as year_period,
    count(*) as record_count,
    sum(sum_price) as total_sum_price,
    avg(sum_price) as avg_sum_price,
    min(sum_price) as min_sum_price,
    max(sum_price) as max_sum_price,
    sum(mom_change_in_listing_count) as total_mom_change_in_listing_count,
    avg(mom_change_in_listing_count) as avg_mom_change_in_listing_count,
    min(mom_change_in_listing_count) as min_mom_change_in_listing_count,
    max(mom_change_in_listing_count) as max_mom_change_in_listing_count,
    sum(transaction_ount) as total_transaction_ount,
    avg(transaction_ount) as avg_transaction_ount,
    min(transaction_ount) as min_transaction_ount,
    max(transaction_ount) as max_transaction_ount,
    sum(mom_change_in_transaction_count) as total_mom_change_in_transaction_count,
    avg(mom_change_in_transaction_count) as avg_mom_change_in_transaction_count,
    min(mom_change_in_transaction_count) as min_mom_change_in_transaction_count,
    max(mom_change_in_transaction_count) as max_mom_change_in_transaction_count,
    sum(listing_count) as total_listing_count,
    avg(listing_count) as avg_listing_count,
    min(listing_count) as min_listing_count,
    max(listing_count) as max_listing_count,
    sum(mom_change_in_gmv) as total_mom_change_in_gmv,
    avg(mom_change_in_gmv) as avg_mom_change_in_gmv,
    min(mom_change_in_gmv) as min_mom_change_in_gmv,
    max(mom_change_in_gmv) as max_mom_change_in_gmv

from source
group by website_type, data_source, maker, item_name, model, condition, volume, date_trunc('month', month), year(month)
