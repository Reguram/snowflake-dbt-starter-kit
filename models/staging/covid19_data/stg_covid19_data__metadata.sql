with source as (
    select * from {{ source('covid19_data', 'METADATA') }}
),

staged as (
    select
        "TABLE" as table_name,
        description,
        "COLUMN" as column_name,
        "TYPE" as data_type,
        nullable,
        comments,
        "SOURCE" as data_source
    from source
)

select * from staged
