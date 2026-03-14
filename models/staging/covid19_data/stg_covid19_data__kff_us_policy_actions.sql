with source as (
    select * from {{ source('covid19_data', 'KFF_US_POLICY_ACTIONS') }}
),

staged as (
    select
        country_region,
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
        last_updated_date
    from source
)

select * from staged
