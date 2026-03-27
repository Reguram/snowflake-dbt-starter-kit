CREATE OR REPLACE SEMANTIC VIEW DBT_DEV.SEMANTIC.SEM_NYT_US_COVID19
  TABLES (
    nyt AS DBT_DEV.DBT_MARTS.SUMMARY_NYT_US_COVID19
  )
  DIMENSIONS (
    nyt.state AS state
      COMMENT = 'US state name',
    nyt.county AS county
      COMMENT = 'US county name',
    nyt.fips AS fips
      COMMENT = 'FIPS geographic code',
    nyt.iso3166_1 AS iso3166_1
      COMMENT = 'ISO 3166-1 country code',
    nyt.iso3166_2 AS iso3166_2
      COMMENT = 'ISO 3166-2 state code',
    nyt.last_reported_flag AS last_reported_flag
      COMMENT = 'True if this is the most recent record for this location',
    nyt.month_period AS month_period
      COMMENT = 'Month period of the record',
    nyt.year_period AS year_period
      COMMENT = 'Year period of the record'
  )
  METRICS (
    nyt.total_cases AS SUM(total_cases)
      COMMENT = 'Total cumulative COVID cases',
    nyt.total_deaths AS SUM(total_deaths)
      COMMENT = 'Total cumulative COVID deaths',
    nyt.total_new_cases AS SUM(total_cases_since_prev_day)
      COMMENT = 'Total new COVID cases since previous reporting period',
    nyt.total_new_deaths AS SUM(total_deaths_since_prev_day)
      COMMENT = 'Total new COVID deaths since previous reporting period',
    nyt.avg_cases AS AVG(avg_cases)
      COMMENT = 'Average cases per reporting period',
    nyt.avg_deaths AS AVG(avg_deaths)
      COMMENT = 'Average deaths per reporting period',
    nyt.total_records AS SUM(record_count)
      COMMENT = 'Total number of reporting records'
  )
  COMMENT = 'New York Times US COVID-19 data — cumulative and incremental cases and deaths by US state and county over time';
