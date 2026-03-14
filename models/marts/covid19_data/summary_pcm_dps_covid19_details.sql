-- Summary mart: auto-generated aggregations from PCM_DPS_COVID19_DETAILS
-- Dimensions: PROVINCE_STATE, ISO3166_1, ISO3166_2, NOTE_EN, LAST_REPORTED_FLAG
-- Measures: HOSPITALIZED, INTENSIVE_CARE, TOTAL_HOSPITALIZED, HOME_ISOLATION, TOTAL_POSITIVE, NEW_POSITIVE, DISCHARGED_HEALED, DECEASED, TOTAL_CASES, TESTED, HOSPITALIZED_SINCE_PREV_DAY, INTENSIVE_CARE_SINCE_PREV_DAY, TOTAL_HOSPITALIZED_SINCE_PREV_DAY, HOME_ISOLATION_SINCE_PREV_DAY, TOTAL_POSITIVE_SINCE_PREV_DAY, DISCHARGED_HEALED_SINCE_PREV_DAY, DECEASED_SINCE_PREV_DAY, TOTAL_CASES_SINCE_PREV_DAY, TESTED_SINCE_PREV_DAY

with source as (
    select * from {{ ref('stg_covid19_data__pcm_dps_covid19_details') }}
)

select
    province_state,
    iso3166_1,
    iso3166_2,
    note_en,
    last_reported_flag,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(hospitalized) as total_hospitalized,
    avg(hospitalized) as avg_hospitalized,
    min(hospitalized) as min_hospitalized,
    max(hospitalized) as max_hospitalized,
    sum(intensive_care) as total_intensive_care,
    avg(intensive_care) as avg_intensive_care,
    min(intensive_care) as min_intensive_care,
    max(intensive_care) as max_intensive_care,
    sum(total_hospitalized) as total_total_hospitalized,
    avg(total_hospitalized) as avg_total_hospitalized,
    min(total_hospitalized) as min_total_hospitalized,
    max(total_hospitalized) as max_total_hospitalized,
    sum(home_isolation) as total_home_isolation,
    avg(home_isolation) as avg_home_isolation,
    min(home_isolation) as min_home_isolation,
    max(home_isolation) as max_home_isolation,
    sum(total_positive) as total_total_positive,
    avg(total_positive) as avg_total_positive,
    min(total_positive) as min_total_positive,
    max(total_positive) as max_total_positive,
    sum(new_positive) as total_new_positive,
    avg(new_positive) as avg_new_positive,
    min(new_positive) as min_new_positive,
    max(new_positive) as max_new_positive,
    sum(discharged_healed) as total_discharged_healed,
    avg(discharged_healed) as avg_discharged_healed,
    min(discharged_healed) as min_discharged_healed,
    max(discharged_healed) as max_discharged_healed,
    sum(deceased) as total_deceased,
    avg(deceased) as avg_deceased,
    min(deceased) as min_deceased,
    max(deceased) as max_deceased,
    sum(total_cases) as total_total_cases,
    avg(total_cases) as avg_total_cases,
    min(total_cases) as min_total_cases,
    max(total_cases) as max_total_cases,
    sum(tested) as total_tested,
    avg(tested) as avg_tested,
    min(tested) as min_tested,
    max(tested) as max_tested

from source
group by province_state, iso3166_1, iso3166_2, note_en, last_reported_flag, date_trunc('month', date), year(date)
