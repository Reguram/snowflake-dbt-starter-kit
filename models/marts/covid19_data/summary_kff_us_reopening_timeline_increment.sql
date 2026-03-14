-- Summary mart: auto-generated aggregations from KFF_US_REOPENING_TIMELINE_INCREMENT
-- Dimensions: COUNTRY_REGION, PROVINCE_STATE, STATUS
-- Measures: count only

with source as (
    select * from {{ ref('stg_covid19_data__kff_us_reopening_timeline_increment') }}
)

select
    country_region,
    province_state,
    status,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count

from source
group by country_region, province_state, status, date_trunc('month', date), year(date)
