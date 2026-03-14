-- Summary mart: auto-generated aggregations from HDX_ACAPS
-- Dimensions: REGION, CATEGORY, MEASURE, TARGETED_POP_GROUP, NON_COMPLIANCE, SOURCE_TYPE, ISO3166_1, LOG_TYPE
-- Measures: count only

with source as (
    select * from {{ ref('stg_covid19_data__hdx_acaps') }}
)

select
    region,
    category,
    measure,
    targeted_pop_group,
    non_compliance,
    source_type,
    iso3166_1,
    log_type,
    date_trunc('month', date_implemented) as month_period,
    year(date_implemented) as year_period,
    count(*) as record_count

from source
group by region, category, measure, targeted_pop_group, non_compliance, source_type, iso3166_1, log_type, date_trunc('month', date_implemented), year(date_implemented)
