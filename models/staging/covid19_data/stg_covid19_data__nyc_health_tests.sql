with source as (
    select * from {{ source('covid19_data', 'NYC_HEALTH_TESTS') }}
),

staged as (
    select
        modified_zcta,
        covid_case_count,
        total_covid_tests,
        percent_positive,
        date,
        fips,
        country_region,
        iso3166_1,
        iso3166_2,
        last_updated_date,
        last_reported_date
    from source
)

select * from staged
