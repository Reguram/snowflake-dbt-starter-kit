{{
    config(
        materialized='table',
        cluster_by=['sales_date']
    )
}}

with source_data as (

    select
        sales_date,
        maker,
        item_category,
        price
    from {{ ref('int_enriched_transactions') }}

),

aggregated_data as (

    select
        sales_date,
        maker,
        item_category,
        sum(price)   as total_sales,
        avg(price)   as average_price,
        count(*)     as transaction_count
    from source_data
    group by sales_date, maker, item_category

),

final as (

    select
        {{ dbt_utils.generate_surrogate_key(['sales_date', 'maker', 'item_category']) }} as sales_key,
        sales_date,
        maker,
        item_category,
        total_sales,
        average_price,
        transaction_count
    from aggregated_data

)

select * from final