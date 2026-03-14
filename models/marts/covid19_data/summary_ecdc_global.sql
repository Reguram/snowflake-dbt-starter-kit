-- Summary mart: auto-generated aggregations from ECDC_GLOBAL
-- Dimensions: CONTINENTEXP, ISO3166_1, LAST_REPORTED_FLAG
-- Measures: CASES, DEATHS, CASES_SINCE_PREV_DAY, DEATHS_SINCE_PREV_DAY, POPULATION

with source as (
    select * from {{ ref('stg_covid19_data__ecdc_global') }}
)

select
    continentexp,
    iso3166_1,
    last_reported_flag,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(cases) as total_cases,
    avg(cases) as avg_cases,
    min(cases) as min_cases,
    max(cases) as max_cases,
    sum(deaths) as total_deaths,
    avg(deaths) as avg_deaths,
    min(deaths) as min_deaths,
    max(deaths) as max_deaths,
    sum(cases_since_prev_day) as total_cases_since_prev_day,
    avg(cases_since_prev_day) as avg_cases_since_prev_day,
    min(cases_since_prev_day) as min_cases_since_prev_day,
    max(cases_since_prev_day) as max_cases_since_prev_day,
    sum(deaths_since_prev_day) as total_deaths_since_prev_day,
    avg(deaths_since_prev_day) as avg_deaths_since_prev_day,
    min(deaths_since_prev_day) as min_deaths_since_prev_day,
    max(deaths_since_prev_day) as max_deaths_since_prev_day,
    sum(population) as total_population,
    avg(population) as avg_population,
    min(population) as min_population,
    max(population) as max_population

from source
group by continentexp, iso3166_1, last_reported_flag, date_trunc('month', date), year(date)
