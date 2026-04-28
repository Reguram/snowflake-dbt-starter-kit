{{
  config(
    materialized = 'semantic_view',
    schema = 'SEMANTIC',
    tags = ['semantic', 'sem_acs_economic_by_county'],
    post_hook = [
      "{{ publish_verified_queries() }}"
    ]
  )
}}

TABLES (
  econ AS {{ ref('summary_acs_economic_by_county') }}
)
DIMENSIONS (
  econ.survey_year AS year
    COMMENT = 'ACS survey year',
  econ.state AS state
    COMMENT = 'US state name',
  econ.county AS county
    COMMENT = 'County name',
  econ.geo_id AS geo_id
    COMMENT = 'Census geographic identifier (FIPS code) for the county',
  econ.subject AS subject
    COMMENT = 'ACS economic subject area (e.g. EMPLOYMENT STATUS, INCOME AND BENEFITS)',
  econ.label_category AS label_category
    COMMENT = 'Economic category label (e.g. EMPLOYMENT STATUS, COMMUTING TO WORK)'
)
METRICS (
  econ.total_economic_estimate AS SUM(total_estimate)
    COMMENT = 'Sum of ACS economic characteristic estimates for the grouping',
  econ.avg_economic_percent_estimate AS AVG(total_percent_estimate)
    COMMENT = 'Average percent estimate for the economic characteristic grouping',
  econ.total_variable_count AS SUM(variable_count)
    COMMENT = 'Total number of distinct ACS economic variables in the grouping'
)
COMMENT = 'ACS DP03 selected economic characteristics aggregated by US county, year, subject, and label category. Covers employment, income, commuting, and poverty data.'

AI_SQL_GENERATION 'This view contains ACS DP03 economic data summarized at the county level. total_economic_estimate sums economic estimates; avg_economic_percent_estimate averages percent estimates. Use subject to filter by topic such as EMPLOYMENT STATUS, INCOME AND BENEFITS, or POVERTY. Use state + county for county analysis, state only for state comparisons. Group by survey_year for trends. variable_count indicates distinct ACS variables in the row.'
