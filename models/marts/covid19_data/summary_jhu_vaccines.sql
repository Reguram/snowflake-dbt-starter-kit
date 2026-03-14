-- Summary mart: auto-generated aggregations from JHU_VACCINES
-- Dimensions: PROVINCE_STATE, COUNTRY_REGION, LAST_REPORTED_FLAG, STABBR
-- Measures: FIPS, DOSES_ALLOC_TOTAL, DOSES_ALLOC_MODERNA, DOSES_ALLOC_PFIZER, DOSES_ALLOC_JOHNSON_AND_JOHNSON, DOSES_ALLOC_UNASSIGNED, DOSES_ALLOC_UNKNOWN, DOSES_SHIPPED_TOTAL, DOSES_SHIPPED_MODERNA, DOSES_SHIPPED_PFIZER, DOSES_SHIPPED_JOHNSON_AND_JOHNSON, DOSES_SHIPPED_UNASSIGNED, DOSES_SHIPPED_UNKNOWN, DOSES_ADMIN_TOTAL, DOSES_ADMIN_MODERNA, DOSES_ADMIN_PFIZER, DOSES_ADMIN_JOHNSON_AND_JOHNSON, DOSES_ADMIN_UNASSIGNED, DOSES_ADMIN_UNKNOWN, PEOPLE_TOTAL, PEOPLE_TOTAL_2ND_DOSE

with source as (
    select * from {{ ref('stg_covid19_data__jhu_vaccines') }}
)

select
    province_state,
    country_region,
    last_reported_flag,
    stabbr,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(fips) as total_fips,
    avg(fips) as avg_fips,
    min(fips) as min_fips,
    max(fips) as max_fips,
    sum(doses_alloc_total) as total_doses_alloc_total,
    avg(doses_alloc_total) as avg_doses_alloc_total,
    min(doses_alloc_total) as min_doses_alloc_total,
    max(doses_alloc_total) as max_doses_alloc_total,
    sum(doses_alloc_moderna) as total_doses_alloc_moderna,
    avg(doses_alloc_moderna) as avg_doses_alloc_moderna,
    min(doses_alloc_moderna) as min_doses_alloc_moderna,
    max(doses_alloc_moderna) as max_doses_alloc_moderna,
    sum(doses_alloc_pfizer) as total_doses_alloc_pfizer,
    avg(doses_alloc_pfizer) as avg_doses_alloc_pfizer,
    min(doses_alloc_pfizer) as min_doses_alloc_pfizer,
    max(doses_alloc_pfizer) as max_doses_alloc_pfizer,
    sum(doses_alloc_johnson_and_johnson) as total_doses_alloc_johnson_and_johnson,
    avg(doses_alloc_johnson_and_johnson) as avg_doses_alloc_johnson_and_johnson,
    min(doses_alloc_johnson_and_johnson) as min_doses_alloc_johnson_and_johnson,
    max(doses_alloc_johnson_and_johnson) as max_doses_alloc_johnson_and_johnson,
    sum(doses_alloc_unassigned) as total_doses_alloc_unassigned,
    avg(doses_alloc_unassigned) as avg_doses_alloc_unassigned,
    min(doses_alloc_unassigned) as min_doses_alloc_unassigned,
    max(doses_alloc_unassigned) as max_doses_alloc_unassigned,
    sum(doses_alloc_unknown) as total_doses_alloc_unknown,
    avg(doses_alloc_unknown) as avg_doses_alloc_unknown,
    min(doses_alloc_unknown) as min_doses_alloc_unknown,
    max(doses_alloc_unknown) as max_doses_alloc_unknown,
    sum(doses_shipped_total) as total_doses_shipped_total,
    avg(doses_shipped_total) as avg_doses_shipped_total,
    min(doses_shipped_total) as min_doses_shipped_total,
    max(doses_shipped_total) as max_doses_shipped_total,
    sum(doses_shipped_moderna) as total_doses_shipped_moderna,
    avg(doses_shipped_moderna) as avg_doses_shipped_moderna,
    min(doses_shipped_moderna) as min_doses_shipped_moderna,
    max(doses_shipped_moderna) as max_doses_shipped_moderna,
    sum(doses_shipped_pfizer) as total_doses_shipped_pfizer,
    avg(doses_shipped_pfizer) as avg_doses_shipped_pfizer,
    min(doses_shipped_pfizer) as min_doses_shipped_pfizer,
    max(doses_shipped_pfizer) as max_doses_shipped_pfizer

from source
group by province_state, country_region, last_reported_flag, stabbr, date_trunc('month', date), year(date)
