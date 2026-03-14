with source as (
    select * from {{ source('covid19_data', 'KFF_US_REOPENING_TIMELINE_INCREMENT') }}
),

staged as (
    select
        date,
        country_region,
        province_state,
        status
    from source
)

select * from staged
