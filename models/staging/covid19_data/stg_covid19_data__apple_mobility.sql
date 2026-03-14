with source as (
    select * from {{ source('covid19_data', 'APPLE_MOBILITY') }}
),

staged as (
    select
        country_region,
        province_state,
        date,
        transportation_type,
        difference,
        iso3166_1,
        iso3166_2,
        last_updated_date,
        last_reported_flag
    from source
)

select * from staged
