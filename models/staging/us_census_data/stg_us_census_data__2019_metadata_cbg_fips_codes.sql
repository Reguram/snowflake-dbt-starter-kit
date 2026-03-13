with source as (
    select * from {{ source('us_census_data', '2019_METADATA_CBG_FIPS_CODES') }}
),

staged as (
    select
        state,
        state_fips,
        county_fips,
        county,
        class_code
    from source
)

select * from staged
