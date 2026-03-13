with source as (
    select * from {{ source('japan_ecomm_data', 'MALL_MARKETS_MONTHLY_TRANSACTION') }}
),

renamed as (
    select
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
        stock_period
    from source
)

select * from renamed
