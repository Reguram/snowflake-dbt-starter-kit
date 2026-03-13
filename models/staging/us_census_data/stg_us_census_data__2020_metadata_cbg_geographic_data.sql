with source as (
    select * from {{ source('us_census_data', '2020_METADATA_CBG_GEOGRAPHIC_DATA') }}
),

staged as (
    select
        census_block_group,
        amount_land,
        amount_water,
        latitude,
        longitude
    from source
)

select * from staged
