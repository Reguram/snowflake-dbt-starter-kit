-- Summary mart: auto-generated aggregations from NYC_HEALTH_TESTS
-- Dimensions: FIPS, COUNTRY_REGION, ISO3166_1, ISO3166_2
-- Measures: COVID_CASE_COUNT, TOTAL_COVID_TESTS, PERCENT_POSITIVE

with source as (
    select * from {{ ref('stg_covid19_data__nyc_health_tests') }}
)

select
    fips,
    country_region,
    iso3166_1,
    iso3166_2,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(covid_case_count) as total_covid_case_count,
    avg(covid_case_count) as avg_covid_case_count,
    min(covid_case_count) as min_covid_case_count,
    max(covid_case_count) as max_covid_case_count,
    sum(total_covid_tests) as total_total_covid_tests,
    avg(total_covid_tests) as avg_total_covid_tests,
    min(total_covid_tests) as min_total_covid_tests,
    max(total_covid_tests) as max_total_covid_tests,
    sum(percent_positive) as total_percent_positive,
    avg(percent_positive) as avg_percent_positive,
    min(percent_positive) as min_percent_positive,
    max(percent_positive) as max_percent_positive

from source
group by fips, country_region, iso3166_1, iso3166_2, date_trunc('month', date), year(date)
