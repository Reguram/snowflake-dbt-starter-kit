with source as (
    select * from {{ source('covid19_data', 'PCM_DPS_COVID19_DETAILS') }}
),

staged as (
    select
        country_region,
        province_state,
        date,
        hospitalized,
        intensive_care,
        total_hospitalized,
        home_isolation,
        total_positive,
        new_positive,
        discharged_healed,
        deceased,
        total_cases,
        tested,
        hospitalized_since_prev_day,
        intensive_care_since_prev_day,
        total_hospitalized_since_prev_day,
        home_isolation_since_prev_day,
        total_positive_since_prev_day,
        discharged_healed_since_prev_day,
        deceased_since_prev_day,
        total_cases_since_prev_day,
        tested_since_prev_day,
        iso3166_1,
        iso3166_2,
        note_it,
        note_en,
        last_update_date,
        last_reported_flag
    from source
)

select * from staged
