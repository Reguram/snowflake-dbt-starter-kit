with source as (
    select * from {{ source('covid19_data', 'KFF_US_STATE_MITIGATIONS') }}
),

staged as (
    select
        country_region,
        province_state,
        status_of_reopening,
        stay_at_home_order,
        mandatory_quarantine_for_travelers,
        non_essential_business_closures,
        large_gatherings_ban,
        restaurant_limits,
        bar_closures,
        face_covering_requirement,
        primary_election_postponement,
        emergency_declaration,
        last_updated_date
    from source
)

select * from staged
