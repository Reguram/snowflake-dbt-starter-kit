with source as (
    select * from {{ source('covid19_data', 'HUM_RESTRICTIONS_AIRLINE') }}
),

staged as (
    select
        country,
        iso3166_1,
        long,
        lat,
        published,
        sources,
        airline,
        restriction_text,
        last_update_date
    from source
)

select * from staged
