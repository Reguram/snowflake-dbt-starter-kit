-- Summary mart: auto-generated aggregations from SCS_BE_DETAILED_PROVINCE_CASE_COUNTS
-- Dimensions: REGION, SEX, AGEGROUP, ISO3166_1, ISO3166_2, ISO3166_3
-- Measures: NEW_CASES, TOTAL_CASES

with source as (
    select * from {{ ref('stg_covid19_data__scs_be_detailed_province_case_counts') }}
)

select
    region,
    sex,
    agegroup,
    iso3166_1,
    iso3166_2,
    iso3166_3,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(new_cases) as total_new_cases,
    avg(new_cases) as avg_new_cases,
    min(new_cases) as min_new_cases,
    max(new_cases) as max_new_cases,
    sum(total_cases) as total_total_cases,
    avg(total_cases) as avg_total_cases,
    min(total_cases) as min_total_cases,
    max(total_cases) as max_total_cases

from source
group by region, sex, agegroup, iso3166_1, iso3166_2, iso3166_3, date_trunc('month', date), year(date)
