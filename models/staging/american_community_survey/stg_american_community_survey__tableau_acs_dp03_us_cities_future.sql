with source as (
    select * from {{ source('american_community_survey', 'TABLEAU_ACS_DP03_US_CITIES_FUTURE') }}
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
        place,
        label_category,
        lat,
        long,
        label_value,
        label_concept
    from source
)

select * from staged
