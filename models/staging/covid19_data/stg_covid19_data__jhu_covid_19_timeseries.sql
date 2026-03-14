with source as (
    select * from {{ source('covid19_data', 'JHU_COVID_19_TIMESERIES') }}
),

staged as (
    select
        country_region,
        province_state,
        county,
        fips,
        lat,
        long,
        iso3166_1,
        iso3166_2,
        date,
        cases,
        case_type,
        last_update_date,
        last_reported_flag,
        difference
    from source
)

select * from staged
