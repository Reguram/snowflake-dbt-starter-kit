with source as (
    select * from {{ source('covid19_data', 'PCM_DPS_COVID19') }}
),

staged as (
    select
        country_region,
        province_state,
        date,
        case_type,
        cases,
        long,
        lat,
        difference,
        iso3166_1,
        iso3166_2,
        last_updated_date,
        last_reported_flag
    from source
)

select * from staged
