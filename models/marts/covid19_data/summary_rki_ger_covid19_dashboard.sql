-- Summary mart: auto-generated aggregations from RKI_GER_COVID19_DASHBOARD
-- Dimensions: COUNTY, STATE_ID, STATE, DISTRICT_TYPE, ISO3166_1, ISO3166_2, LAST_REPORTED_FLAG
-- Measures: POPULATION, DEATH_RATE, CASES, DEATHS, CASES_PER_100K, CASES_PER_POPULATION, CASES7_PER_100K

with source as (
    select * from {{ ref('stg_covid19_data__rki_ger_covid19_dashboard') }}
)

select
    county,
    state_id,
    state,
    district_type,
    iso3166_1,
    iso3166_2,
    last_reported_flag,
    date_trunc('month', last_update) as month_period,
    year(last_update) as year_period,
    count(*) as record_count,
    sum(population) as total_population,
    avg(population) as avg_population,
    min(population) as min_population,
    max(population) as max_population,
    sum(death_rate) as total_death_rate,
    avg(death_rate) as avg_death_rate,
    min(death_rate) as min_death_rate,
    max(death_rate) as max_death_rate,
    sum(cases) as total_cases,
    avg(cases) as avg_cases,
    min(cases) as min_cases,
    max(cases) as max_cases,
    sum(deaths) as total_deaths,
    avg(deaths) as avg_deaths,
    min(deaths) as min_deaths,
    max(deaths) as max_deaths,
    sum(cases_per_100k) as total_cases_per_100k,
    avg(cases_per_100k) as avg_cases_per_100k,
    min(cases_per_100k) as min_cases_per_100k,
    max(cases_per_100k) as max_cases_per_100k,
    sum(cases_per_population) as total_cases_per_population,
    avg(cases_per_population) as avg_cases_per_population,
    min(cases_per_population) as min_cases_per_population,
    max(cases_per_population) as max_cases_per_population,
    sum(cases7_per_100k) as total_cases7_per_100k,
    avg(cases7_per_100k) as avg_cases7_per_100k,
    min(cases7_per_100k) as min_cases7_per_100k,
    max(cases7_per_100k) as max_cases7_per_100k

from source
group by county, state_id, state, district_type, iso3166_1, iso3166_2, last_reported_flag, date_trunc('month', last_update), year(last_update)
