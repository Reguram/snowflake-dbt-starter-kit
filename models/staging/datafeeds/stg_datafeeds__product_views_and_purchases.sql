with source as (
    select * from {{ source('datafeeds', 'PRODUCT_VIEWS_AND_PURCHASES') }}
),

deduplicated as (
    select
        *
    from source
    qualify row_number() over (
        partition by site, country, year, month, product
        order by estimated_views desc
    ) = 1
),

staged as (
    select
        {{ dbt_utils.generate_surrogate_key(['site', 'country', 'year', 'month', 'product']) }} as product_views_key,
        site,
        country as country_code,
        year as year_number,
        month as month_number,
        product as product_id,
        title as product_title,
        brand,
        main_category,
        sub_category,
        estimated_views,
        estimated_purchases
    from deduplicated
)

select * from staged
