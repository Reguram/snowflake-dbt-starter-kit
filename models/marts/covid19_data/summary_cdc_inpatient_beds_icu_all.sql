-- Summary mart: auto-generated aggregations from CDC_INPATIENT_BEDS_ICU_ALL
-- Dimensions: ISO3166_1, ISO3166_2, LAST_REPORTED_FLAG
-- Measures: STAFFED_ADULT_ICU_BEDS_OCCUPIED, STAFFED_ADULT_ICU_BEDS_OCCUPIED_LOWER_BOUND, STAFFED_ADULT_ICU_BEDS_OCCUPIED_UPPER_BOUND, STAFFED_ADULT_ICU_BEDS_OCCUPIED_PCT, STAFFED_ADULT_ICU_BEDS_OCCUPIED_PCT_LOWER_BOUND, STAFFED_ADULT_ICU_BEDS_OCCUPIED_PCT_UPPER_BOUND, TOTAL_STAFFED_ICU_BEDS, TOTAL_STAFFED_ICU_BEDS_LOWER_BOUND, TOTAL_STAFFED_ICU_BEDS_UPPER_BOUND

with source as (
    select * from {{ ref('stg_covid19_data__cdc_inpatient_beds_icu_all') }}
)

select
    iso3166_1,
    iso3166_2,
    last_reported_flag,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(staffed_adult_icu_beds_occupied) as total_staffed_adult_icu_beds_occupied,
    avg(staffed_adult_icu_beds_occupied) as avg_staffed_adult_icu_beds_occupied,
    min(staffed_adult_icu_beds_occupied) as min_staffed_adult_icu_beds_occupied,
    max(staffed_adult_icu_beds_occupied) as max_staffed_adult_icu_beds_occupied,
    sum(staffed_adult_icu_beds_occupied_lower_bound) as total_staffed_adult_icu_beds_occupied_lower_bound,
    avg(staffed_adult_icu_beds_occupied_lower_bound) as avg_staffed_adult_icu_beds_occupied_lower_bound,
    min(staffed_adult_icu_beds_occupied_lower_bound) as min_staffed_adult_icu_beds_occupied_lower_bound,
    max(staffed_adult_icu_beds_occupied_lower_bound) as max_staffed_adult_icu_beds_occupied_lower_bound,
    sum(staffed_adult_icu_beds_occupied_upper_bound) as total_staffed_adult_icu_beds_occupied_upper_bound,
    avg(staffed_adult_icu_beds_occupied_upper_bound) as avg_staffed_adult_icu_beds_occupied_upper_bound,
    min(staffed_adult_icu_beds_occupied_upper_bound) as min_staffed_adult_icu_beds_occupied_upper_bound,
    max(staffed_adult_icu_beds_occupied_upper_bound) as max_staffed_adult_icu_beds_occupied_upper_bound,
    sum(staffed_adult_icu_beds_occupied_pct) as total_staffed_adult_icu_beds_occupied_pct,
    avg(staffed_adult_icu_beds_occupied_pct) as avg_staffed_adult_icu_beds_occupied_pct,
    min(staffed_adult_icu_beds_occupied_pct) as min_staffed_adult_icu_beds_occupied_pct,
    max(staffed_adult_icu_beds_occupied_pct) as max_staffed_adult_icu_beds_occupied_pct,
    sum(staffed_adult_icu_beds_occupied_pct_lower_bound) as total_staffed_adult_icu_beds_occupied_pct_lower_bound,
    avg(staffed_adult_icu_beds_occupied_pct_lower_bound) as avg_staffed_adult_icu_beds_occupied_pct_lower_bound,
    min(staffed_adult_icu_beds_occupied_pct_lower_bound) as min_staffed_adult_icu_beds_occupied_pct_lower_bound,
    max(staffed_adult_icu_beds_occupied_pct_lower_bound) as max_staffed_adult_icu_beds_occupied_pct_lower_bound,
    sum(staffed_adult_icu_beds_occupied_pct_upper_bound) as total_staffed_adult_icu_beds_occupied_pct_upper_bound,
    avg(staffed_adult_icu_beds_occupied_pct_upper_bound) as avg_staffed_adult_icu_beds_occupied_pct_upper_bound,
    min(staffed_adult_icu_beds_occupied_pct_upper_bound) as min_staffed_adult_icu_beds_occupied_pct_upper_bound,
    max(staffed_adult_icu_beds_occupied_pct_upper_bound) as max_staffed_adult_icu_beds_occupied_pct_upper_bound,
    sum(total_staffed_icu_beds) as total_total_staffed_icu_beds,
    avg(total_staffed_icu_beds) as avg_total_staffed_icu_beds,
    min(total_staffed_icu_beds) as min_total_staffed_icu_beds,
    max(total_staffed_icu_beds) as max_total_staffed_icu_beds,
    sum(total_staffed_icu_beds_lower_bound) as total_total_staffed_icu_beds_lower_bound,
    avg(total_staffed_icu_beds_lower_bound) as avg_total_staffed_icu_beds_lower_bound,
    min(total_staffed_icu_beds_lower_bound) as min_total_staffed_icu_beds_lower_bound,
    max(total_staffed_icu_beds_lower_bound) as max_total_staffed_icu_beds_lower_bound,
    sum(total_staffed_icu_beds_upper_bound) as total_total_staffed_icu_beds_upper_bound,
    avg(total_staffed_icu_beds_upper_bound) as avg_total_staffed_icu_beds_upper_bound,
    min(total_staffed_icu_beds_upper_bound) as min_total_staffed_icu_beds_upper_bound,
    max(total_staffed_icu_beds_upper_bound) as max_total_staffed_icu_beds_upper_bound

from source
group by iso3166_1, iso3166_2, last_reported_flag, date_trunc('month', date), year(date)
