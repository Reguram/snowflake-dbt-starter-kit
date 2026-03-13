-- Summary mart: auto-generated aggregations from 2019_CBG_GEOMETRY_WKT
-- Dimensions: COUNTY_FIPS, BLOCK_GROUP, STATE, COUNTY, MTFCC
-- Measures: count only

with source as (
    select * from {{ ref('stg_us_census_data__2019_cbg_geometry_wkt') }}
)

select
    county_fips,
    block_group,
    state,
    county,
    mtfcc,
    count(*) as record_count

from source
group by county_fips, block_group, state, county, mtfcc
