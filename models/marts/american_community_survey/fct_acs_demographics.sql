with counties as (
    select
        year,
        state,
        county,
        geo_id,
        dataset,
        subject,
        variable_base,
        label_category,
        label_value,
        label_concept,
        value_e,
        value_pe
    from {{ ref('stg_american_community_survey__tableau_acs_dp05_us_counties_future') }}
),

states as (
    select
        year,
        state,
        null as county,
        geo_id,
        dataset,
        subject,
        variable_base,
        label_category,
        label_value,
        label_concept,
        value_e,
        value_pe
    from {{ ref('stg_american_community_survey__tableau_acs_dp05_us_states_future') }}
),

combined as (
    select 'county' as geography_level, * from counties
    union all
    select 'state' as geography_level, * from states
)

select
    {{ dbt_utils.generate_surrogate_key(['geo_id', 'year', 'variable_base']) }} as acs_demographics_id,
    geography_level,
    year,
    state,
    county,
    geo_id,
    dataset,
    subject,
    variable_base,
    label_category,
    label_value,
    label_concept,
    value_e          as estimate,
    value_pe         as percent_estimate
from combined
