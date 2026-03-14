with source as (
    select * from {{ source('covid19_data', 'HUM_RESTRICTIONS_COUNTRY') }}
),

staged as (
    select
        country,
        iso3166_1,
        long,
        lat,
        published,
        sources,
        restriction_text,
        info_date,
        quarantine_text,
        last_update_date
    from source
)

select * from staged
