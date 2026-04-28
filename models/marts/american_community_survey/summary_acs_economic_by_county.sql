with source as (
    select * from {{ ref('stg_american_community_survey__tableau_acs_dp03_us_counties_future') }}
),

summary as (
    select
        year,
        state,
        county,
        geo_id,
        subject,
        label_category,
        sum(value_e)  as total_estimate,
        sum(value_pe) as total_percent_estimate,
        count(distinct variable_base) as variable_count
    from source
    group by 1, 2, 3, 4, 5, 6
)

select
    {{ dbt_utils.generate_surrogate_key(['geo_id', 'year', 'subject', 'label_category']) }} as summary_id,
    year,
    state,
    county,
    geo_id,
    subject,
    label_category,
    total_estimate,
    total_percent_estimate,
    variable_count
from summary
