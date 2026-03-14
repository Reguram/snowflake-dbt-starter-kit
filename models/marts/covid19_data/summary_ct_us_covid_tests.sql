-- Summary mart: auto-generated aggregations from CT_US_COVID_TESTS
-- Dimensions: PROVINCE_STATE, ISO3166_1, ISO3166_2, LAST_REPORTED_FLAG
-- Measures: POSITIVE, POSITIVE_SINCE_PREVIOUS_DAY, NEGATIVE, NEGATIVE_SINCE_PREVIOUS_DAY, PENDING, PENDING_SINCE_PREVIOUS_DAY, DEATH, DEATH_SINCE_PREVIOUS_DAY, HOSPITALIZED, HOSPITALIZED_SINCE_PREVIOUS_DAY, TOTAL, TOTAL_SINCE_PREVIOUS_DAY, HOSPITALIZEDCURRENTLY, HOSPITALIZEDCURRENTLYINCREASE, HOSPITALIZEDCUMULATIVE, HOSPITALIZEDCUMULATIVEINCREASE, INICUCURRENTLY, INICUCURRENTLYINCREASE, INICUCUMULATIVE, INICUCUMULATIVEINCREASE, ONVENTILATORCURRENTLY, ONVENTILATORCURRENTLYINCREASE, ONVENTILATORCUMULATIVE, ONVENTILATORCUMULATIVEINCREASE

with source as (
    select * from {{ ref('stg_covid19_data__ct_us_covid_tests') }}
)

select
    province_state,
    iso3166_1,
    iso3166_2,
    last_reported_flag,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(positive) as total_positive,
    avg(positive) as avg_positive,
    min(positive) as min_positive,
    max(positive) as max_positive,
    sum(positive_since_previous_day) as total_positive_since_previous_day,
    avg(positive_since_previous_day) as avg_positive_since_previous_day,
    min(positive_since_previous_day) as min_positive_since_previous_day,
    max(positive_since_previous_day) as max_positive_since_previous_day,
    sum(negative) as total_negative,
    avg(negative) as avg_negative,
    min(negative) as min_negative,
    max(negative) as max_negative,
    sum(negative_since_previous_day) as total_negative_since_previous_day,
    avg(negative_since_previous_day) as avg_negative_since_previous_day,
    min(negative_since_previous_day) as min_negative_since_previous_day,
    max(negative_since_previous_day) as max_negative_since_previous_day,
    sum(pending) as total_pending,
    avg(pending) as avg_pending,
    min(pending) as min_pending,
    max(pending) as max_pending,
    sum(pending_since_previous_day) as total_pending_since_previous_day,
    avg(pending_since_previous_day) as avg_pending_since_previous_day,
    min(pending_since_previous_day) as min_pending_since_previous_day,
    max(pending_since_previous_day) as max_pending_since_previous_day,
    sum(death) as total_death,
    avg(death) as avg_death,
    min(death) as min_death,
    max(death) as max_death,
    sum(death_since_previous_day) as total_death_since_previous_day,
    avg(death_since_previous_day) as avg_death_since_previous_day,
    min(death_since_previous_day) as min_death_since_previous_day,
    max(death_since_previous_day) as max_death_since_previous_day,
    sum(hospitalized) as total_hospitalized,
    avg(hospitalized) as avg_hospitalized,
    min(hospitalized) as min_hospitalized,
    max(hospitalized) as max_hospitalized,
    sum(hospitalized_since_previous_day) as total_hospitalized_since_previous_day,
    avg(hospitalized_since_previous_day) as avg_hospitalized_since_previous_day,
    min(hospitalized_since_previous_day) as min_hospitalized_since_previous_day,
    max(hospitalized_since_previous_day) as max_hospitalized_since_previous_day

from source
group by province_state, iso3166_1, iso3166_2, last_reported_flag, date_trunc('month', date), year(date)
