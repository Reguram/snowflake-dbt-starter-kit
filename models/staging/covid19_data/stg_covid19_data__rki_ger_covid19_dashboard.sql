with source as (
    select * from {{ source('covid19_data', 'RKI_GER_COVID19_DASHBOARD') }}
),

staged as (
    select
        district_id,
        county,
        state_id,
        state,
        district_type,
        population,
        death_rate,
        cases,
        deaths,
        cases_per_100k,
        cases_per_population,
        cases7_per_100k,
        last_update,
        iso3166_1,
        iso3166_2,
        last_update_date,
        last_reported_flag
    from source
)

select * from staged
