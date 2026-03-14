with source as (
    select * from {{ source('covid19_data', 'CDC_INPATIENT_BEDS_ALL') }}
),

staged as (
    select
        state,
        date,
        inpatient_beds_occupied,
        inpatient_beds_lower_bound,
        inpatient_beds_upper_bound,
        inpatient_beds_in_use_pct,
        inpatient_beds_in_use_pct_lower_bound,
        inpatient_beds_in_use_pct_upper_bound,
        total_inpatient_beds,
        total_inpatient_beds_lower_bound,
        total_inpatient_beds_upper_bound,
        iso3166_1,
        iso3166_2,
        last_reported_flag
    from source
)

select * from staged
