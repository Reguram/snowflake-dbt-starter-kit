-- Summary mart: auto-generated aggregations from CDC_INPATIENT_BEDS_ALL
-- Dimensions: ISO3166_1, ISO3166_2, LAST_REPORTED_FLAG
-- Measures: INPATIENT_BEDS_OCCUPIED, INPATIENT_BEDS_LOWER_BOUND, INPATIENT_BEDS_UPPER_BOUND, INPATIENT_BEDS_IN_USE_PCT, INPATIENT_BEDS_IN_USE_PCT_LOWER_BOUND, INPATIENT_BEDS_IN_USE_PCT_UPPER_BOUND, TOTAL_INPATIENT_BEDS, TOTAL_INPATIENT_BEDS_LOWER_BOUND, TOTAL_INPATIENT_BEDS_UPPER_BOUND

with source as (
    select * from {{ ref('stg_covid19_data__cdc_inpatient_beds_all') }}
)

select
    iso3166_1,
    iso3166_2,
    last_reported_flag,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(inpatient_beds_occupied) as total_inpatient_beds_occupied,
    avg(inpatient_beds_occupied) as avg_inpatient_beds_occupied,
    min(inpatient_beds_occupied) as min_inpatient_beds_occupied,
    max(inpatient_beds_occupied) as max_inpatient_beds_occupied,
    sum(inpatient_beds_lower_bound) as total_inpatient_beds_lower_bound,
    avg(inpatient_beds_lower_bound) as avg_inpatient_beds_lower_bound,
    min(inpatient_beds_lower_bound) as min_inpatient_beds_lower_bound,
    max(inpatient_beds_lower_bound) as max_inpatient_beds_lower_bound,
    sum(inpatient_beds_upper_bound) as total_inpatient_beds_upper_bound,
    avg(inpatient_beds_upper_bound) as avg_inpatient_beds_upper_bound,
    min(inpatient_beds_upper_bound) as min_inpatient_beds_upper_bound,
    max(inpatient_beds_upper_bound) as max_inpatient_beds_upper_bound,
    sum(inpatient_beds_in_use_pct) as total_inpatient_beds_in_use_pct,
    avg(inpatient_beds_in_use_pct) as avg_inpatient_beds_in_use_pct,
    min(inpatient_beds_in_use_pct) as min_inpatient_beds_in_use_pct,
    max(inpatient_beds_in_use_pct) as max_inpatient_beds_in_use_pct,
    sum(inpatient_beds_in_use_pct_lower_bound) as total_inpatient_beds_in_use_pct_lower_bound,
    avg(inpatient_beds_in_use_pct_lower_bound) as avg_inpatient_beds_in_use_pct_lower_bound,
    min(inpatient_beds_in_use_pct_lower_bound) as min_inpatient_beds_in_use_pct_lower_bound,
    max(inpatient_beds_in_use_pct_lower_bound) as max_inpatient_beds_in_use_pct_lower_bound,
    sum(inpatient_beds_in_use_pct_upper_bound) as total_inpatient_beds_in_use_pct_upper_bound,
    avg(inpatient_beds_in_use_pct_upper_bound) as avg_inpatient_beds_in_use_pct_upper_bound,
    min(inpatient_beds_in_use_pct_upper_bound) as min_inpatient_beds_in_use_pct_upper_bound,
    max(inpatient_beds_in_use_pct_upper_bound) as max_inpatient_beds_in_use_pct_upper_bound,
    sum(total_inpatient_beds) as total_total_inpatient_beds,
    avg(total_inpatient_beds) as avg_total_inpatient_beds,
    min(total_inpatient_beds) as min_total_inpatient_beds,
    max(total_inpatient_beds) as max_total_inpatient_beds,
    sum(total_inpatient_beds_lower_bound) as total_total_inpatient_beds_lower_bound,
    avg(total_inpatient_beds_lower_bound) as avg_total_inpatient_beds_lower_bound,
    min(total_inpatient_beds_lower_bound) as min_total_inpatient_beds_lower_bound,
    max(total_inpatient_beds_lower_bound) as max_total_inpatient_beds_lower_bound,
    sum(total_inpatient_beds_upper_bound) as total_total_inpatient_beds_upper_bound,
    avg(total_inpatient_beds_upper_bound) as avg_total_inpatient_beds_upper_bound,
    min(total_inpatient_beds_upper_bound) as min_total_inpatient_beds_upper_bound,
    max(total_inpatient_beds_upper_bound) as max_total_inpatient_beds_upper_bound

from source
group by iso3166_1, iso3166_2, last_reported_flag, date_trunc('month', date), year(date)
