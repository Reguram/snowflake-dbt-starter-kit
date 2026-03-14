with source as (
    select * from {{ source('covid19_data', 'ECDC_GLOBAL') }}
),

staged as (
    select
        country_region,
        continentexp,
        iso3166_1,
        cases,
        deaths,
        cases_since_prev_day,
        deaths_since_prev_day,
        population,
        date,
        last_update_date,
        last_reported_flag
    from source
)

select * from staged
