{{
  config(
    materialized = 'semantic_view',
    schema = 'SEMANTIC',
    tags = ['semantic', 'sem_acs_cities'],
    post_hook = [
      "{{ publish_verified_queries() }}"
    ]
  )
}}

TABLES (
  cities AS {{ ref('fct_acs_cities') }}
)
DIMENSIONS (
  cities.survey_year AS year
    COMMENT = 'ACS survey year (e.g. 2015, 2019, 2022)',
  cities.state AS state
    COMMENT = 'US state name (e.g. Texas, California)',
  cities.county AS county
    COMMENT = 'County name within the state',
  cities.city_or_place AS city_or_place
    COMMENT = 'City, town, village, or census-designated place name',
  cities.geo_id AS geo_id
    COMMENT = 'Census geographic identifier (FIPS code) for the place',
  cities.subject AS subject
    COMMENT = 'ACS subject area (e.g. SEX AND AGE, RACE, HOUSING)',
  cities.variable_code AS variable_base
    COMMENT = 'ACS variable code (e.g. DP05_0001)',
  cities.label_category AS label_category
    COMMENT = 'Broad demographic category label (e.g. SEX AND AGE, RACE)',
  cities.label_value AS label_value
    COMMENT = 'Specific demographic label value (e.g. Total population, Male)',
  cities.label_concept AS label_concept
    COMMENT = 'Concept grouping for the label (e.g. RACE, SEX AND AGE)',
  cities.latitude AS lat
    COMMENT = 'Latitude coordinate of the city/place',
  cities.longitude AS long
    COMMENT = 'Longitude coordinate of the city/place'
)
METRICS (
  cities.total_estimate AS SUM(estimate)
    COMMENT = 'Sum of ACS estimate values across selected variables and geography',
  cities.avg_percent_estimate AS AVG(percent_estimate)
    COMMENT = 'Average percent estimate across selected variables and geography'
)
COMMENT = 'ACS DP05 demographic and housing estimates for US cities and places with geolocation. One row per city/variable/year combination.'

AI_SQL_GENERATION 'This view covers city-level ACS DP05 demographic data. Use city_or_place to filter by city, state for state-level grouping, label_category and label_value for demographic topics (RACE, SEX AND AGE, HOUSING). total_estimate sums ACS estimates; avg_percent_estimate averages percent estimates. For population totals filter label_value = Total population. Use latitude/longitude for geographic mapping. Group by survey_year for time trends.'
