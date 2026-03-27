CREATE OR REPLACE SEMANTIC VIEW DBT_DEV.SEMANTIC.SEM_JHU_COVID19
  TABLES (
    jhu AS DBT_DEV.DBT_MARTS.SUMMARY_JHU_COVID_19
  )
  DIMENSIONS (
    jhu.province_state AS province_state
      COMMENT = 'Province or state name',
    jhu.county AS county
      COMMENT = 'County name',
    jhu.fips AS fips
      COMMENT = 'FIPS geographic code',
    jhu.case_type AS case_type
      COMMENT = 'Type of COVID case (Confirmed, Deaths, etc.)',
    jhu.iso3166_1 AS iso3166_1
      COMMENT = 'ISO 3166-1 country code',
    jhu.iso3166_2 AS iso3166_2
      COMMENT = 'ISO 3166-2 state/region code',
    jhu.last_reported_flag AS last_reported_flag
      COMMENT = 'True if this is the most recent record for this location',
    jhu.month_period AS month_period
      COMMENT = 'Month period of the record',
    jhu.year_period AS year_period
      COMMENT = 'Year period of the record'
  )
  METRICS (
    jhu.total_cases AS SUM(total_cases)
      COMMENT = 'Total cumulative COVID cases',
    jhu.total_new_cases AS SUM(total_difference)
      COMMENT = 'Total new cases (difference from previous period)',
    jhu.avg_cases AS AVG(avg_cases)
      COMMENT = 'Average cases per reporting period',
    jhu.max_cases AS MAX(max_cases)
      COMMENT = 'Maximum cases in a single reporting period',
    jhu.total_records AS SUM(record_count)
      COMMENT = 'Total number of reporting records'
  )
  COMMENT = 'JHU COVID-19 summary — cumulative and incremental case counts by country, state, county, and case type';
