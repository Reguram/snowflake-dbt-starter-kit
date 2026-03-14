with source as (
    select * from {{ source('covid19_data', 'IHME_COVID_19') }}
),

staged as (
    select
        date,
        allbed_mean,
        allbed_lower,
        allbed_upper,
        icubed_mean,
        icubed_lower,
        icubed_upper,
        invven_mean,
        invven_lower,
        invven_upper,
        deaths_mean,
        deaths_lower,
        deaths_upper,
        admis_mean,
        admis_lower,
        admis_upper,
        newicu_mean,
        newicu_lower,
        newicu_upper,
        totdea_mean,
        totdea_lower,
        totdea_upper,
        bedover_mean,
        bedover_lower,
        bedover_upper,
        icuover_mean,
        icuover_lower,
        icuover_upper,
        last_updated_date,
        last_reported_flag,
        country_region,
        iso_3166_1,
        iso_3166_2,
        province_state
    from source
)

select * from staged
