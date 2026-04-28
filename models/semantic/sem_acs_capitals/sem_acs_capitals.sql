{{
  config(
    materialized = 'semantic_view',
    schema = 'SEMANTIC',
    tags = ['semantic', 'sem_acs_capitals'],
    post_hook = [
      "{{ publish_verified_queries() }}"
    ]
  )
}}

TABLES (
  caps AS {{ ref('summary_acs_capitals_and_largest_cities') }}
)
DIMENSIONS (
  caps.survey_year AS year
    COMMENT = 'ACS survey year',
  caps.state AS state
    COMMENT = 'US state name',
  caps.city AS city
    COMMENT = 'City name (state capital or largest city in the state)',
  caps.geo_id AS geo_id
    COMMENT = 'Census geographic identifier (FIPS code) for the city',
  caps.is_capital AS is_capital
    COMMENT = 'Whether the city is a state capital (Yes/No)',
  caps.subject AS subject
    COMMENT = 'ACS subject area',
  caps.variable_code AS variable_base
    COMMENT = 'ACS variable code (e.g. DP05_0001)',
  caps.label_category AS label_category
    COMMENT = 'Broad demographic category label (e.g. RACE, SEX AND AGE)',
  caps.label_value AS label_value
    COMMENT = 'Specific demographic label value (e.g. Total population, Male)',
  caps.label_concept AS label_concept
    COMMENT = 'Concept grouping for the label'
)
METRICS (
  caps.total_estimate AS SUM(estimate)
    COMMENT = 'Sum of ACS estimate values for the capital or largest city',
  caps.avg_percent_estimate AS AVG(percent_estimate)
    COMMENT = 'Average percent estimate for the capital or largest city'
)
COMMENT = 'ACS DP05 demographic estimates for US state capitals and largest cities. Use is_capital to compare capital vs non-capital largest cities.'

AI_SQL_GENERATION 'This view covers ACS DP05 demographic data for US state capitals and largest non-capital cities. Use is_capital = Yes to filter capital cities, is_capital = No for largest non-capital cities. Use state + city for city-level analysis. total_estimate sums ACS estimates; avg_percent_estimate averages percent estimates. Filter label_value = Total population for population totals, label_category = RACE for race breakdown. Group by survey_year for trends.'
