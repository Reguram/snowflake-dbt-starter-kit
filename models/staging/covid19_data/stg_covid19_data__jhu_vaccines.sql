with source as (
    select * from {{ source('covid19_data', 'JHU_VACCINES') }}
),

staged as (
    select
        date,
        province_state,
        fips,
        doses_alloc_total,
        doses_alloc_moderna,
        doses_alloc_pfizer,
        doses_alloc_johnson_and_johnson,
        doses_alloc_unassigned,
        doses_alloc_unknown,
        doses_shipped_total,
        doses_shipped_moderna,
        doses_shipped_pfizer,
        doses_shipped_johnson_and_johnson,
        doses_shipped_unassigned,
        doses_shipped_unknown,
        doses_admin_total,
        doses_admin_moderna,
        doses_admin_pfizer,
        doses_admin_johnson_and_johnson,
        doses_admin_unassigned,
        doses_admin_unknown,
        people_total,
        people_total_2nd_dose,
        country_region,
        last_update_date,
        last_reported_flag,
        stabbr
    from source
)

select * from staged
