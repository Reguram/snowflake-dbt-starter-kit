with source as (
    select * from {{ source('covid19_data', 'WHO_DAILY_REPORT') }}
),

staged as (
    select
        country_region,
        cases_total,
        cases_total_per_100000,
        cases,
        deaths_total,
        deaths_total_per_100000,
        deaths,
        transmission_classification,
        date,
        iso3166_1
    from source
)

select * from staged
