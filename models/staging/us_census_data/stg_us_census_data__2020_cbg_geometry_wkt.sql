with source as (
    select * from {{ source('us_census_data', '2020_CBG_GEOMETRY_WKT') }}
),

staged as (
    select
        state_fips,
        county_fips,
        tract_code,
        block_group,
        census_block_group,
        state,
        county,
        mtfcc,
        geometry
    from source
)

select * from staged
