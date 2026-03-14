-- Summary mart: auto-generated aggregations from CDC_POLICY_MEASURES
-- Dimensions: POLICY_LEVEL, POLICY_TYPE, START_STOP, SOURCE, ISO3166_1, ISO3166_2, LAST_REPORTED_FLAG
-- Measures: FIPS_CODE, TOTAL_PHASE

with source as (
    select * from {{ ref('stg_covid19_data__cdc_policy_measures') }}
)

select
    policy_level,
    policy_type,
    start_stop,
    source,
    iso3166_1,
    iso3166_2,
    last_reported_flag,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(fips_code) as total_fips_code,
    avg(fips_code) as avg_fips_code,
    min(fips_code) as min_fips_code,
    max(fips_code) as max_fips_code,
    sum(total_phase) as total_total_phase,
    avg(total_phase) as avg_total_phase,
    min(total_phase) as min_total_phase,
    max(total_phase) as max_total_phase

from source
group by policy_level, policy_type, start_stop, source, iso3166_1, iso3166_2, last_reported_flag, date_trunc('month', date), year(date)
