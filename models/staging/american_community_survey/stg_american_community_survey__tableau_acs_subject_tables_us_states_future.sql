with source as (
    select * from {{ source('american_community_survey', 'TABLEAU_ACS_SUBJECT_TABLES_US_STATES_FUTURE') }}
),

staged as (
    select
        load_date,
        year,
        dataset,
        subject,
        variable_base,
        geo_id,
        value_e,
        value_pe,
        state,
        county,
        label_category,
        label_value,
        label_concept
    from source
)

select * from staged
