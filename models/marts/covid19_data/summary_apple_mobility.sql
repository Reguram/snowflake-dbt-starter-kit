-- Summary mart: auto-generated aggregations from APPLE_MOBILITY
-- Dimensions: PROVINCE_STATE, TRANSPORTATION_TYPE, ISO3166_1, ISO3166_2, LAST_REPORTED_FLAG
-- Measures: DIFFERENCE

with source as (
    select * from {{ ref('stg_covid19_data__apple_mobility') }}
)

select
    province_state,
    transportation_type,
    iso3166_1,
    iso3166_2,
    last_reported_flag,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(difference) as total_difference,
    avg(difference) as avg_difference,
    min(difference) as min_difference,
    max(difference) as max_difference

from source
group by province_state, transportation_type, iso3166_1, iso3166_2, last_reported_flag, date_trunc('month', date), year(date)
