with source as (
    select * from {{ source('covid19_data', 'WHO_SITUATION_REPORTS') }}
),

staged as (
    select
        country,
        total_cases,
        cases_new,
        deaths,
        deaths_new,
        transmission_classification,
        days_since_last_reported_case,
        iso3166_1,
        country_region,
        date,
        situation_report_name,
        situation_report_url,
        last_update_date,
        last_reported_flag
    from source
)

select * from staged
