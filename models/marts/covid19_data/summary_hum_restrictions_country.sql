-- Summary mart: auto-generated aggregations from HUM_RESTRICTIONS_COUNTRY
-- Dimensions: ISO3166_1, SOURCES, RESTRICTION_TEXT, QUARANTINE_TEXT
-- Measures: LONG, LAT

with source as (
    select * from {{ ref('stg_covid19_data__hum_restrictions_country') }}
)

select
    iso3166_1,
    sources,
    restriction_text,
    quarantine_text,
    date_trunc('month', published) as month_period,
    year(published) as year_period,
    count(*) as record_count,
    sum(long) as total_long,
    avg(long) as avg_long,
    min(long) as min_long,
    max(long) as max_long,
    sum(lat) as total_lat,
    avg(lat) as avg_lat,
    min(lat) as min_lat,
    max(lat) as max_lat

from source
group by iso3166_1, sources, restriction_text, quarantine_text, date_trunc('month', published), year(published)
