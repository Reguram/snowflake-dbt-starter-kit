with source as (
    select * from {{ source('covid19_data', 'DEMOGRAPHICS') }}
),

staged as (
    select
        iso3166_1,
        iso3166_2,
        fips,
        latitude,
        longitude,
        state,
        county,
        total_population,
        total_male_population,
        total_female_population
    from source
)

select * from staged
