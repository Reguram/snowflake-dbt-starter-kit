with source as (
    select * from {{ source('covid19_data', 'CDC_INPATIENT_BEDS_ICU_ALL') }}
),

staged as (
    select
        state,
        date,
        staffed_adult_icu_beds_occupied,
        staffed_adult_icu_beds_occupied_lower_bound,
        staffed_adult_icu_beds_occupied_upper_bound,
        staffed_adult_icu_beds_occupied_pct,
        staffed_adult_icu_beds_occupied_pct_lower_bound,
        staffed_adult_icu_beds_occupied_pct_upper_bound,
        total_staffed_icu_beds,
        total_staffed_icu_beds_lower_bound,
        total_staffed_icu_beds_upper_bound,
        iso3166_1,
        iso3166_2,
        last_reported_flag
    from source
)

select * from staged
