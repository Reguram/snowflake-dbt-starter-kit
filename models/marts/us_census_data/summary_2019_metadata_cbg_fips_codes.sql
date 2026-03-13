-- Summary mart: auto-generated aggregations from 2019_METADATA_CBG_FIPS_CODES
-- Dimensions: STATE_FIPS, COUNTY_FIPS, CLASS_CODE
-- Measures: count only

with source as (
    select * from {{ ref('stg_us_census_data__2019_metadata_cbg_fips_codes') }}
)

select
    state_fips,
    county_fips,
    class_code,
    count(*) as record_count

from source
group by state_fips, county_fips, class_code
