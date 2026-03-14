with source as (
    select * from {{ source('covid19_data', 'JHU_COVID_19') }}
),

staged as (
    select
        country_region,
        province_state,
        county,
        fips,
        date,
        case_type,
        cases,
        long,
        lat,
        iso3166_1,
        iso3166_2,
        difference,
        last_updated_date,
        last_reported_flag
    from source
)

select * from staged
