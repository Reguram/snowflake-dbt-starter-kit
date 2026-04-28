with source as (
    select * from {{ ref('stg_american_community_survey__tableau_acs_dp05_us_cities_capitals_largest') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['geo_id', 'year', 'variable_base']) }} as acs_capitals_id,
    year,
    state,
    city,
    geo_id,
    is_capital,
    dataset,
    subject,
    variable_base,
    label_category,
    label_value,
    label_concept,
    value_e  as estimate,
    value_pe as percent_estimate
from source
