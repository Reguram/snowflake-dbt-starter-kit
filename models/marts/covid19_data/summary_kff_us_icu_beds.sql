-- Summary mart: auto-generated aggregations from KFF_US_ICU_BEDS
-- Dimensions: ISO3166_1, ISO3166_2, NOTE, STATE
-- Measures: HOSPITALS, ICU_BEDS

with source as (
    select * from {{ ref('stg_covid19_data__kff_us_icu_beds') }}
)

select
    iso3166_1,
    iso3166_2,
    note,
    state,
    count(*) as record_count,
    sum(hospitals) as total_hospitals,
    avg(hospitals) as avg_hospitals,
    min(hospitals) as min_hospitals,
    max(hospitals) as max_hospitals,
    sum(icu_beds) as total_icu_beds,
    avg(icu_beds) as avg_icu_beds,
    min(icu_beds) as min_icu_beds,
    max(icu_beds) as max_icu_beds

from source
group by iso3166_1, iso3166_2, note, state
