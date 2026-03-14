with source as (
    select * from {{ source('covid19_data', 'CDC_TESTING') }}
),

staged as (
    select
        iso3166_1,
        iso3166_2,
        date,
        positive,
        negative,
        inconclusive
    from source
)

select * from staged
