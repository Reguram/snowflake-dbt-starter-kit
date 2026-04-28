with cities as (
    select
        year,
        state,
        county,
        place  as city_or_place,
        geo_id,
        dataset,
        subject,
        variable_base,
        label_category,
        label_value,
        label_concept,
        value_e,
        value_pe,
        lat,
        long
    from {{ ref('stg_american_community_survey__tableau_acs_dp05_us_cities_future') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['geo_id', 'year', 'variable_base']) }} as acs_city_id,
    year,
    state,
    county,
    city_or_place,
    geo_id,
    dataset,
    subject,
    variable_base,
    label_category,
    label_value,
    label_concept,
    value_e          as estimate,
    value_pe         as percent_estimate,
    lat,
    long
from cities
