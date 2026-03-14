with source as (
    select * from {{ source('covid19_data', 'KFF_HCP_CAPACITY') }}
),

staged as (
    select
        country_region,
        province_state,
        total_hospital_beds,
        hospital_beds_per_1000_population,
        total_chcs,
        chc_service_delivery_sites
    from source
)

select * from staged
