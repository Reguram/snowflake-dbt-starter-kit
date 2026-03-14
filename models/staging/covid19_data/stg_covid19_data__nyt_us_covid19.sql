with source as (
    select * from {{ source('covid19_data', 'NYT_US_COVID19') }}
),

staged as (
    select
        date,
        county,
        state,
        fips,
        cases,
        deaths,
        iso3166_1,
        iso3166_2,
        cases_since_prev_day,
        deaths_since_prev_day,
        last_update_date,
        last_reported_flag
    from source
)

select * from staged
