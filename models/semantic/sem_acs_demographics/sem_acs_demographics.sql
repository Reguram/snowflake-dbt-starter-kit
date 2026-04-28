{{
  config(
    materialized = 'semantic_view',
    schema = 'SEMANTIC',
    tags = ['semantic', 'sem_acs_demographics'],
    post_hook = [
      "{{ publish_verified_queries() }}"
    ]
  )
}}

TABLES (
  demo AS {{ ref('fct_acs_demographics') }}
)
DIMENSIONS (
  demo.geography_level AS geography_level
    COMMENT = 'Geographic aggregation level: county or state',
  demo.survey_year AS year
    COMMENT = 'ACS survey year',
  demo.state AS state
    COMMENT = 'US state name',
  demo.county AS county
    COMMENT = 'County name (null for state-level rows)',
  demo.geo_id AS geo_id
    COMMENT = 'Census geographic identifier (FIPS code)',
  demo.subject AS subject
    COMMENT = 'ACS subject area (e.g. SEX AND AGE, RACE)',
  demo.variable_code AS variable_base
    COMMENT = 'ACS variable code (e.g. DP05_0001)',
  demo.label_category AS label_category
    COMMENT = 'Broad demographic category label',
  demo.label_value AS label_value
    COMMENT = 'Specific demographic label value',
  demo.label_concept AS label_concept
    COMMENT = 'Concept grouping for the label'
)
METRICS (
  demo.total_estimate AS SUM(estimate)
    COMMENT = 'Sum of ACS estimate values across selected geography and variables',
  demo.avg_percent_estimate AS AVG(percent_estimate)
    COMMENT = 'Average percent estimate across selected geography and variables'
)
COMMENT = 'ACS DP05 demographic estimates combining US county and state levels. Use geography_level to distinguish county vs state rows.'

AI_SQL_GENERATION 'This view combines county and state level ACS DP05 demographic data. Always filter or group by geography_level (county or state) to avoid mixing levels. Use state + county for county analysis, state only for state-level analysis. total_estimate sums ACS estimates; avg_percent_estimate averages percent estimates. Filter label_value = Total population for population totals, label_category = RACE for race breakdown. Group by survey_year for trends.'
