-- Summary mart: auto-generated aggregations from KFF_US_POLICY_ACTIONS
-- Dimensions: PROVINCE_STATE, WAIVE_COST_SHARING_FOR_COVID_19_TREATMENT, FREE_COST_VACCINE_WHEN_AVAILABLE, STATE_REQUIRES_WAIVER_OF_PRIOR_AUTHORIZATION_REQUIREMENTS, EARLY_PRESCRIPTION_REFILLS, MARKETPLACE_SPECIAL_ENROLLMENT_PERIOD, SECTION_1135_WAIVER, PAID_SICK_LEAVE, PREMIUM_PAYMENT_GRACE_PERIOD, NOTES
-- Measures: count only

with source as (
    select * from {{ ref('stg_covid19_data__kff_us_policy_actions') }}
)

select
    province_state,
    waive_cost_sharing_for_covid_19_treatment,
    free_cost_vaccine_when_available,
    state_requires_waiver_of_prior_authorization_requirements,
    early_prescription_refills,
    marketplace_special_enrollment_period,
    section_1135_waiver,
    paid_sick_leave,
    premium_payment_grace_period,
    notes,
    date_trunc('month', last_updated_date) as month_period,
    year(last_updated_date) as year_period,
    count(*) as record_count

from source
group by province_state, waive_cost_sharing_for_covid_19_treatment, free_cost_vaccine_when_available, state_requires_waiver_of_prior_authorization_requirements, early_prescription_refills, marketplace_special_enrollment_period, section_1135_waiver, paid_sick_leave, premium_payment_grace_period, notes, date_trunc('month', last_updated_date), year(last_updated_date)
