with source as (
    select * from {{ source('us_census_data', '2020_REDISTRICTING_METADATA_CBG_FIELD_DESCRIPTIONS') }}
),

staged as (
    select
        field_name,
        column_id,
        column_topic,
        column_universe
    from source
)

select * from staged
