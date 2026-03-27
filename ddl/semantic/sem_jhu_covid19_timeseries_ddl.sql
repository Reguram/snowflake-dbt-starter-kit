CREATE OR REPLACE SEMANTIC VIEW DBT_DEV.SEMANTIC.SEM_JHU_COVID19_TIMESERIES
  TABLES (
    jhu_ts AS DBT_DEV.DBT_MARTS.SUMMARY_JHU_COVID_19_TIMESERIES
  )
  DIMENSIONS (
    jhu_ts.province_state AS province_state
      COMMENT = 'Province or state name',
    jhu_ts.county AS county
      COMMENT = 'County name',
    jhu_ts.fips AS fips
      COMMENT = 'FIPS geographic code',
    jhu_ts.iso3166_1 AS iso3166_1
      COMMENT = 'ISO 3166-1 country code',
    jhu_ts.iso3166_2 AS iso3166_2
      COMMENT = 'ISO 3166-2 state/region code',
    jhu_ts.case_type AS case_type
      COMMENT = 'Type of COVID case (Confirmed, Deaths, etc.)',
    jhu_ts.last_reported_flag AS last_reported_flag
      COMMENT = 'True if this is the most recent record for this location',
    jhu_ts.month_period AS month_period
      COMMENT = 'Month period of the record',
    jhu_ts.year_period AS year_period
      COMMENT = 'Year period of the record'
  )
  METRICS (
    jhu_ts.total_cases AS SUM(total_cases)
      COMMENT = 'Total cumulative COVID cases',
    jhu_ts.total_new_cases AS SUM(total_difference)
      COMMENT = 'Total new cases (difference from previous period)',
    jhu_ts.avg_cases AS AVG(avg_cases)
      COMMENT = 'Average cases per period',
    jhu_ts.max_cases AS MAX(max_cases)
      COMMENT = 'Maximum cases recorded in a single period',
    jhu_ts.total_records AS SUM(record_count)
      COMMENT = 'Total number of reporting records'
  )
  COMMENT = 'JHU COVID-19 timeseries — cumulative and incremental case counts by country, state, county, and case type over time';
