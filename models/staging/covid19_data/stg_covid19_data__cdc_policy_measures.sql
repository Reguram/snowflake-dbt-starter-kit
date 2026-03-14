with source as (
    select * from {{ source('covid19_data', 'CDC_POLICY_MEASURES') }}
),

staged as (
    select
        state_id,
        county,
        fips_code,
        policy_level,
        date,
        policy_type,
        start_stop,
        comments,
        source,
        total_phase,
        iso3166_1,
        iso3166_2,
        last_update_date,
        last_reported_flag
    from source
)

select * from staged
