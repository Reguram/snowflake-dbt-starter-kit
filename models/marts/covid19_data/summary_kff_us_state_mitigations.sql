-- Summary mart: auto-generated aggregations from KFF_US_STATE_MITIGATIONS
-- Dimensions: PROVINCE_STATE, STATUS_OF_REOPENING, STAY_AT_HOME_ORDER, MANDATORY_QUARANTINE_FOR_TRAVELERS, NON_ESSENTIAL_BUSINESS_CLOSURES, LARGE_GATHERINGS_BAN, RESTAURANT_LIMITS, BAR_CLOSURES, FACE_COVERING_REQUIREMENT, PRIMARY_ELECTION_POSTPONEMENT, EMERGENCY_DECLARATION
-- Measures: count only

with source as (
    select * from {{ ref('stg_covid19_data__kff_us_state_mitigations') }}
)

select
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
    date_trunc('month', last_updated_date) as month_period,
    year(last_updated_date) as year_period,
    count(*) as record_count

from source
group by province_state, status_of_reopening, stay_at_home_order, mandatory_quarantine_for_travelers, non_essential_business_closures, large_gatherings_ban, restaurant_limits, bar_closures, face_covering_requirement, primary_election_postponement, emergency_declaration, date_trunc('month', last_updated_date), year(last_updated_date)
