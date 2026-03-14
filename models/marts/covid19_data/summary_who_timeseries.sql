-- Summary mart: auto-generated aggregations from WHO_TIMESERIES
-- Dimensions: TRANSMISSION_CLASSIFICATION, ISO3166_1
-- Measures: CASES_TOTAL, CASES_TOTAL_PER_100000, CASES, DEATHS_TOTAL, DEATHS_TOTAL_PER_100000, DEATHS

with source as (
    select * from {{ ref('stg_covid19_data__who_timeseries') }}
)

select
    transmission_classification,
    iso3166_1,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(cases_total) as total_cases_total,
    avg(cases_total) as avg_cases_total,
    min(cases_total) as min_cases_total,
    max(cases_total) as max_cases_total,
    sum(cases_total_per_100000) as total_cases_total_per_100000,
    avg(cases_total_per_100000) as avg_cases_total_per_100000,
    min(cases_total_per_100000) as min_cases_total_per_100000,
    max(cases_total_per_100000) as max_cases_total_per_100000,
    sum(cases) as total_cases,
    avg(cases) as avg_cases,
    min(cases) as min_cases,
    max(cases) as max_cases,
    sum(deaths_total) as total_deaths_total,
    avg(deaths_total) as avg_deaths_total,
    min(deaths_total) as min_deaths_total,
    max(deaths_total) as max_deaths_total,
    sum(deaths_total_per_100000) as total_deaths_total_per_100000,
    avg(deaths_total_per_100000) as avg_deaths_total_per_100000,
    min(deaths_total_per_100000) as min_deaths_total_per_100000,
    max(deaths_total_per_100000) as max_deaths_total_per_100000,
    sum(deaths) as total_deaths,
    avg(deaths) as avg_deaths,
    min(deaths) as min_deaths,
    max(deaths) as max_deaths

from source
group by transmission_classification, iso3166_1, date_trunc('month', date), year(date)
