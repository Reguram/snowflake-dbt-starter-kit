-- Summary mart: auto-generated aggregations from ECDC_GLOBAL_WEEKLY
-- Dimensions: CONTINENTEXP, ISO3166_1, LAST_REPORTED_FLAG
-- Measures: CASES_WEEKLY, DEATHS_WEEKLY, CASES_SINCE_PREV_WEEK, DEATHS_SINCE_PREV_WEEK, POPULATION

with source as (
    select * from {{ ref('stg_covid19_data__ecdc_global_weekly') }}
)

select
    continentexp,
    iso3166_1,
    last_reported_flag,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(cases_weekly) as total_cases_weekly,
    avg(cases_weekly) as avg_cases_weekly,
    min(cases_weekly) as min_cases_weekly,
    max(cases_weekly) as max_cases_weekly,
    sum(deaths_weekly) as total_deaths_weekly,
    avg(deaths_weekly) as avg_deaths_weekly,
    min(deaths_weekly) as min_deaths_weekly,
    max(deaths_weekly) as max_deaths_weekly,
    sum(cases_since_prev_week) as total_cases_since_prev_week,
    avg(cases_since_prev_week) as avg_cases_since_prev_week,
    min(cases_since_prev_week) as min_cases_since_prev_week,
    max(cases_since_prev_week) as max_cases_since_prev_week,
    sum(deaths_since_prev_week) as total_deaths_since_prev_week,
    avg(deaths_since_prev_week) as avg_deaths_since_prev_week,
    min(deaths_since_prev_week) as min_deaths_since_prev_week,
    max(deaths_since_prev_week) as max_deaths_since_prev_week,
    sum(population) as total_population,
    avg(population) as avg_population,
    min(population) as min_population,
    max(population) as max_population

from source
group by continentexp, iso3166_1, last_reported_flag, date_trunc('month', date), year(date)
