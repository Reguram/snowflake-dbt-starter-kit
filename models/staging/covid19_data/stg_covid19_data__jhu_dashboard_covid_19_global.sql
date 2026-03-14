with source as (
    select * from {{ source('covid19_data', 'JHU_DASHBOARD_COVID_19_GLOBAL') }}
),

staged as (
    select
        country_region,
        province_state,
        county,
        fips,
        date,
        active,
        people_tested,
        confirmed,
        people_hospitalized,
        deaths,
        recovered,
        incident_rate,
        testing_rate,
        hospitalization_rate,
        mortality_rate,
        long,
        lat,
        iso3166_1,
        iso3166_2,
        last_update_date,
        last_reported_flag
    from source
)

select * from staged
