with source as (
    select * from {{ source('covid19_data', 'HS_BULK_DATA') }}
),

staged as (
    select
        long,
        lat,
        healthcare_provider_type,
        name,
        operator,
        beds,
        staff_medical,
        staff_nursing
    from source
)

select * from staged
