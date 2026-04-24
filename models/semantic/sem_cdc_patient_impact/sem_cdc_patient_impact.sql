{{
  config(
    materialized = 'semantic_view',
    schema = 'SEMANTIC',
    tags = ['semantic', 'sem_cdc_patient_impact'],
    post_hook = [
      "{{ publish_verified_queries() }}"
    ]
  )
}}

TABLES (
  cdc AS {{ ref('fct_cdc_reported_patient_impact') }}
)
DIMENSIONS (
  cdc.state AS state
    COMMENT = 'US state abbreviation',
  cdc.iso3166_1 AS iso3166_1
    COMMENT = 'ISO 3166-1 country code',
  cdc.iso3166_2 AS iso3166_2
    COMMENT = 'ISO 3166-2 state/region code',
  cdc.report_date AS "DATE"
    COMMENT = 'Date of the report',
  cdc.report_month AS date_month
    COMMENT = 'Report month derived from date',
  cdc.report_year AS date_year
    COMMENT = 'Report year derived from date'
)
METRICS (
  cdc.total_inpatient_beds AS SUM(inpatient_beds)
    COMMENT = 'Total staffed inpatient beds',
  cdc.total_inpatient_beds_used_covid AS SUM(inpatient_beds_used_covid)
    COMMENT = 'Total inpatient beds occupied by COVID patients',
  cdc.total_adult_covid_hospitalized AS SUM(total_adult_patients_hospitalized_confirmed_covid)
    COMMENT = 'Total adult patients hospitalized with confirmed COVID',
  cdc.total_staffed_icu_beds AS SUM(total_staffed_adult_icu_beds)
    COMMENT = 'Total staffed adult ICU beds',
  cdc.total_icu_covid_patients AS SUM(staffed_icu_adult_patients_confirmed_covid)
    COMMENT = 'Total ICU patients with confirmed COVID',
  cdc.avg_inpatient_bed_utilization AS AVG(inpatient_beds_utilization)
    COMMENT = 'Average inpatient bed utilization rate',
  cdc.avg_adult_icu_bed_covid_utilization AS AVG(adult_icu_bed_covid_utilization)
    COMMENT = 'Average adult ICU bed COVID utilization rate'
)
COMMENT = 'CDC hospital patient impact — inpatient beds, ICU, staffing, and COVID admissions by US state and date'

-- AI_SQL_GENERATION
-- When users ask about "hospital capacity", "COVID hospitalizations", "ICU beds", or "patient impact", query this semantic view.
-- inpatient_beds is the total staffed inpatient bed count.
-- inpatient_beds_used_covid tracks beds occupied specifically by COVID patients.
-- For state-level analysis, group by state.
-- For time-based trends, group by report_date or report_month.
