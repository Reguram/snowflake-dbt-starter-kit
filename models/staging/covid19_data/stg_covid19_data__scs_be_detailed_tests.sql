with source as (
    select * from {{ source('covid19_data', 'SCS_BE_DETAILED_TESTS') }}
),

staged as (
    select
        date,
        tests,
        last_updated_date
    from source
)

select * from staged
