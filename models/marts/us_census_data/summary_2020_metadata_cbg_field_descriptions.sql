-- Summary mart: auto-generated aggregations from 2020_METADATA_CBG_FIELD_DESCRIPTIONS
-- Dimensions: TABLE_NUMBER, TABLE_TITLE, TABLE_TOPICS, TABLE_UNIVERSE, FIELD_LEVEL_1, FIELD_LEVEL_2, FIELD_LEVEL_3, FIELD_LEVEL_4, FIELD_LEVEL_5, FIELD_LEVEL_6, FIELD_LEVEL_7, FIELD_LEVEL_8, FIELD_LEVELl_9, FIELD_LEVEL_10
-- Measures: count only

with source as (
    select * from {{ ref('stg_us_census_data__2020_metadata_cbg_field_descriptions') }}
)

select
    table_number,
    table_title,
    table_topics,
    table_universe,
    field_level_1,
    field_level_2,
    field_level_3,
    field_level_4,
    field_level_5,
    field_level_6,
    field_level_7,
    field_level_8,
    "FIELD_LEVELl_9",
    field_level_10,
    count(*) as record_count

from source
group by table_number, table_title, table_topics, table_universe, field_level_1, field_level_2, field_level_3, field_level_4, field_level_5, field_level_6, field_level_7, field_level_8, "FIELD_LEVELl_9", field_level_10
