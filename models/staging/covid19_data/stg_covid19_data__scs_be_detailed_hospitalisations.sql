with source as (
    select * from {{ source('covid19_data', 'SCS_BE_DETAILED_HOSPITALISATIONS') }}
),

staged as (
    select
        province,
        region,
        date,
        nr_reporting,
        total_in,
        total_in_icu,
        total_in_resp,
        total_in_ecmo,
        new_in,
        new_out,
        iso3166_1,
        iso3166_2,
        iso3166_3,
        last_updated_date
    from source
)

select * from staged
