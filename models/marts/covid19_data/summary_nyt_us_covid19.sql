-- Summary mart: auto-generated aggregations from NYT_US_COVID19
-- Dimensions: COUNTY, STATE, FIPS, ISO3166_1, ISO3166_2, LAST_REPORTED_FLAG
-- Measures: CASES, DEATHS, CASES_SINCE_PREV_DAY, DEATHS_SINCE_PREV_DAY

with source as (
    select * from {{ ref('stg_covid19_data__nyt_us_covid19') }}
)

select
    county,
    state,
    fips,
    iso3166_1,
    iso3166_2,
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
    max(deaths_since_prev_day) as max_deaths_since_prev_day

from source
group by county, state, fips, iso3166_1, iso3166_2, last_reported_flag, date_trunc('month', date), year(date)
