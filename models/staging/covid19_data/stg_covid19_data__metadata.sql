with source as (
    select * from {{ source('covid19_data', 'METADATA') }}
),

staged as (
    select
        table,
        description,
        column,
        type,
        nullable,
        comments,
        source
    from source
)

select * from staged
