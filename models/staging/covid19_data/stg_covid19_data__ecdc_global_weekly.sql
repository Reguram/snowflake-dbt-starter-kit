with source as (
    select * from {{ source('covid19_data', 'ECDC_GLOBAL_WEEKLY') }}
),

staged as (
    select
        country_region,
        continentexp,
        iso3166_1,
        cases_weekly,
        deaths_weekly,
        cases_since_prev_week,
        deaths_since_prev_week,
        population,
        date,
        last_update_date,
        last_reported_flag
    from source
)

select * from staged
