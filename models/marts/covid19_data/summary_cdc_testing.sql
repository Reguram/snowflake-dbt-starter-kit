-- Summary mart: auto-generated aggregations from CDC_TESTING
-- Dimensions: ISO3166_2
-- Measures: POSITIVE, NEGATIVE, INCONCLUSIVE

with source as (
    select * from {{ ref('stg_covid19_data__cdc_testing') }}
)

select
    iso3166_2,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(positive) as total_positive,
    avg(positive) as avg_positive,
    min(positive) as min_positive,
    max(positive) as max_positive,
    sum(negative) as total_negative,
    avg(negative) as avg_negative,
    min(negative) as min_negative,
    max(negative) as max_negative,
    sum(inconclusive) as total_inconclusive,
    avg(inconclusive) as avg_inconclusive,
    min(inconclusive) as min_inconclusive,
    max(inconclusive) as max_inconclusive

from source
group by iso3166_2, date_trunc('month', date), year(date)
