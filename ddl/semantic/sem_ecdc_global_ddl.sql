CREATE OR REPLACE SEMANTIC VIEW DBT_DEV.SEMANTIC.SEM_ECDC_GLOBAL
  TABLES (
    ecdc AS DBT_DEV.DBT_MARTS.SUMMARY_ECDC_GLOBAL
  )
  DIMENSIONS (
    ecdc.continentexp AS continentexp
      COMMENT = 'Continent name',
    ecdc.iso3166_1 AS iso3166_1
      COMMENT = 'ISO 3166-1 country code',
    ecdc.last_reported_flag AS last_reported_flag
      COMMENT = 'True if this is the most recent record for this country',
    ecdc.month_period AS month_period
      COMMENT = 'Month period of the record',
    ecdc.year_period AS year_period
      COMMENT = 'Year period of the record'
  )
  METRICS (
    ecdc.total_cases AS SUM(total_cases)
      COMMENT = 'Total cumulative COVID cases',
    ecdc.total_deaths AS SUM(total_deaths)
      COMMENT = 'Total cumulative COVID deaths',
    ecdc.total_new_cases AS SUM(total_cases_since_prev_day)
      COMMENT = 'Total new COVID cases since previous day/period',
    ecdc.total_new_deaths AS SUM(total_deaths_since_prev_day)
      COMMENT = 'Total new COVID deaths since previous day/period',
    ecdc.avg_cases_per_period AS AVG(avg_cases)
      COMMENT = 'Average cases per reporting period',
    ecdc.avg_deaths_per_period AS AVG(avg_deaths)
      COMMENT = 'Average deaths per reporting period',
    ecdc.avg_population AS AVG(avg_population)
      COMMENT = 'Average population of reporting countries',
    ecdc.total_records AS SUM(record_count)
      COMMENT = 'Total number of reporting records'
  )
  COMMENT = 'ECDC global COVID-19 data — cumulative and daily cases, deaths, and population by country and continent';
