with source as (
    select * from {{ source('covid19_data', 'SCS_BE_DETAILED_PROVINCE_CASE_COUNTS') }}
),

staged as (
    select
        province,
        region,
        sex,
        agegroup,
        date,
        iso3166_1,
        iso3166_2,
        iso3166_3,
        new_cases,
        total_cases,
        last_updated_date
    from source
)

select * from staged
