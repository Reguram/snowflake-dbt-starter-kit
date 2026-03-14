-- Summary mart: auto-generated aggregations from JHU_COVID_19_TIMESERIES
-- Dimensions: PROVINCE_STATE, COUNTY, FIPS, ISO3166_1, ISO3166_2, CASE_TYPE, LAST_REPORTED_FLAG
-- Measures: LAT, LONG, CASES, DIFFERENCE

with source as (
    select * from {{ ref('stg_covid19_data__jhu_covid_19_timeseries') }}
)

select
    province_state,
    county,
    fips,
    iso3166_1,
    iso3166_2,
    case_type,
    last_reported_flag,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(lat) as total_lat,
    avg(lat) as avg_lat,
    min(lat) as min_lat,
    max(lat) as max_lat,
    sum(long) as total_long,
    avg(long) as avg_long,
    min(long) as min_long,
    max(long) as max_long,
    sum(cases) as total_cases,
    avg(cases) as avg_cases,
    min(cases) as min_cases,
    max(cases) as max_cases,
    sum(difference) as total_difference,
    avg(difference) as avg_difference,
    min(difference) as min_difference,
    max(difference) as max_difference

from source
group by province_state, county, fips, iso3166_1, iso3166_2, case_type, last_reported_flag, date_trunc('month', date), year(date)
