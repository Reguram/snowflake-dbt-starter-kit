with source as (
    select * from {{ source('us_census_data', '2019_TOTAL_RENTAL_GEO') }}
),

staged as (
    select
        census_block_group,
        "Total: Renter-occupied housing units",
        latitude,
        longitude
    from source
)

select * from staged
