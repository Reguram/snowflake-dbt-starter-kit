{{
  config(
    materialized = 'semantic_view',
    schema = 'SEMANTIC',
    tags = ['semantic', 'sem_acs_housing_by_county'],
    post_hook = [
      "{{ publish_verified_queries() }}"
    ]
  )
}}

TABLES (
  housing AS {{ ref('summary_acs_housing_by_county') }}
)
DIMENSIONS (
  housing.survey_year AS year
    COMMENT = 'ACS survey year',
  housing.state AS state
    COMMENT = 'US state name',
  housing.county AS county
    COMMENT = 'County name',
  housing.geo_id AS geo_id
    COMMENT = 'Census geographic identifier (FIPS code) for the county',
  housing.subject AS subject
    COMMENT = 'ACS housing subject area (e.g. HOUSING OCCUPANCY, HOUSING TENURE)',
  housing.label_category AS label_category
    COMMENT = 'Housing category label (e.g. HOUSING OCCUPANCY, UNITS IN STRUCTURE)'
)
METRICS (
  housing.total_housing_estimate AS SUM(total_estimate)
    COMMENT = 'Sum of ACS housing characteristic estimates for the grouping',
  housing.avg_housing_percent_estimate AS AVG(total_percent_estimate)
    COMMENT = 'Average percent estimate for the housing characteristic grouping',
  housing.total_variable_count AS SUM(variable_count)
    COMMENT = 'Total number of distinct ACS housing variables in the grouping'
)
COMMENT = 'ACS DP04 selected housing characteristics aggregated by US county, year, subject, and label category. Covers occupancy, tenure, structure type, value, and rent data.'

AI_SQL_GENERATION 'This view contains ACS DP04 housing data summarized at the county level. total_housing_estimate sums housing estimates; avg_housing_percent_estimate averages percent estimates. Use subject to filter by topic such as HOUSING OCCUPANCY, HOUSING TENURE, or GROSS RENT. Use state + county for county analysis, state only for state comparisons. Group by survey_year for trends. variable_count indicates distinct ACS variables in the row.'
