with source as (
    select * from {{ source('american_community_survey', 'TABLEAU_ACS_DP05_US_COUNTIES') }}
),

staged as (
    select
        load_date,
        year,
        dataset,
        subject,
        variable_base,
        variable_e,
        variable_pe,
        params_for,
        params_in,
        geo_id,
        value_e,
        value_pe,
        state,
        county,
        label_dataset,
        label
    from source
)

select * from staged
