-- Summary mart: auto-generated aggregations from 2020_REDISTRICTING_METADATA_CBG_FIELD_DESCRIPTIONS
-- Dimensions: FIELD_NAME, COLUMN_TOPIC, COLUMN_UNIVERSE
-- Measures: count only

with source as (
    select * from {{ ref('stg_us_census_data__2020_redistricting_metadata_cbg_field_descriptions') }}
)

select
    field_name,
    column_topic,
    column_universe,
    count(*) as record_count

from source
group by field_name, column_topic, column_universe
