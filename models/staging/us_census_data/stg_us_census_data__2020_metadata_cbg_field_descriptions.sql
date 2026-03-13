with source as (
    select * from {{ source('us_census_data', '2020_METADATA_CBG_FIELD_DESCRIPTIONS') }}
),

staged as (
    select
        table_id,
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
        field_level_10
    from source
)

select * from staged
