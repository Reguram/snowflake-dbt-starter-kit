with source as (
    select * from {{ source('covid19_data', 'VH_CAN_DETAILED') }}
),

staged as (
    select
        date,
        province_state,
        healthcare_region,
        cases,
        deaths,
        iso3166_1,
        iso3166_2,
        last_updated_date,
        last_reported_flag
    from source
)

select * from staged
