with source as (
    select * from {{ source('covid19_data', 'KFF_US_ICU_BEDS') }}
),

staged as (
    select
        country_region,
        iso3166_1,
        iso3166_2,
        note,
        state,
        hospitals,
        icu_beds,
        county,
        fips
    from source
)

select * from staged
