with source as (
    select * from {{ source('covid19_data', 'SCS_BE_DETAILED_MORTALITY') }}
),

staged as (
    select
        region,
        sex,
        agegroup,
        date,
        deaths,
        iso3166_1,
        iso3166_2,
        last_updated_date
    from source
)

select * from staged
