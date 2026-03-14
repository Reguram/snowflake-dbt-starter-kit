-- Summary mart: auto-generated aggregations from WHO_SITUATION_REPORTS
-- Dimensions: TRANSMISSION_CLASSIFICATION, ISO3166_1, COUNTRY_REGION, SITUATION_REPORT_NAME, SITUATION_REPORT_URL, LAST_REPORTED_FLAG
-- Measures: TOTAL_CASES, CASES_NEW, DEATHS, DEATHS_NEW, DAYS_SINCE_LAST_REPORTED_CASE

with source as (
    select * from {{ ref('stg_covid19_data__who_situation_reports') }}
)

select
    transmission_classification,
    iso3166_1,
    country_region,
    situation_report_name,
    situation_report_url,
    last_reported_flag,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(total_cases) as total_total_cases,
    avg(total_cases) as avg_total_cases,
    min(total_cases) as min_total_cases,
    max(total_cases) as max_total_cases,
    sum(cases_new) as total_cases_new,
    avg(cases_new) as avg_cases_new,
    min(cases_new) as min_cases_new,
    max(cases_new) as max_cases_new,
    sum(deaths) as total_deaths,
    avg(deaths) as avg_deaths,
    min(deaths) as min_deaths,
    max(deaths) as max_deaths,
    sum(deaths_new) as total_deaths_new,
    avg(deaths_new) as avg_deaths_new,
    min(deaths_new) as min_deaths_new,
    max(deaths_new) as max_deaths_new,
    sum(days_since_last_reported_case) as total_days_since_last_reported_case,
    avg(days_since_last_reported_case) as avg_days_since_last_reported_case,
    min(days_since_last_reported_case) as min_days_since_last_reported_case,
    max(days_since_last_reported_case) as max_days_since_last_reported_case

from source
group by transmission_classification, iso3166_1, country_region, situation_report_name, situation_report_url, last_reported_flag, date_trunc('month', date), year(date)
