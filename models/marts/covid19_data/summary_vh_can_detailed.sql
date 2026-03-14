-- Summary mart: auto-generated aggregations from VH_CAN_DETAILED
-- Dimensions: PROVINCE_STATE, HEALTHCARE_REGION, ISO3166_1, ISO3166_2, LAST_REPORTED_FLAG
-- Measures: CASES, DEATHS

with source as (
    select * from {{ ref('stg_covid19_data__vh_can_detailed') }}
)

select
    province_state,
    healthcare_region,
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
    max(deaths) as max_deaths

from source
group by province_state, healthcare_region, iso3166_1, iso3166_2, last_reported_flag, date_trunc('month', date), year(date)
