with source as (
    select * from {{ source('japan_ecomm_data', 'MALL_MARKETS_YEARLY_REPORT') }}
),

renamed as (
    select
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
        mom_change_in_gmv
    from source
)

select * from renamed
