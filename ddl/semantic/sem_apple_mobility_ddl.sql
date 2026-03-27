CREATE OR REPLACE SEMANTIC VIEW DBT_DEV.SEMANTIC.SEM_APPLE_MOBILITY
  TABLES (
    apple AS DBT_DEV.DBT_MARTS.SUMMARY_APPLE_MOBILITY
  )
  DIMENSIONS (
    apple.province_state AS province_state
      COMMENT = 'Province or state name',
    apple.transportation_type AS transportation_type
      COMMENT = 'Type of transportation (driving, walking, transit)',
    apple.iso3166_1 AS iso3166_1
      COMMENT = 'ISO 3166-1 country code',
    apple.iso3166_2 AS iso3166_2
      COMMENT = 'ISO 3166-2 state/region code',
    apple.last_reported_flag AS last_reported_flag
      COMMENT = 'True if this is the most recent record for this location',
    apple.month_period AS month_period
      COMMENT = 'Month period of the mobility record',
    apple.year_period AS year_period
      COMMENT = 'Year period of the mobility record'
  )
  METRICS (
    apple.total_mobility_change AS SUM(total_difference)
      COMMENT = 'Total mobility change (% vs baseline, summed across periods)',
    apple.avg_mobility_change AS AVG(avg_difference)
      COMMENT = 'Average mobility change percentage vs baseline',
    apple.max_mobility_change AS MAX(max_difference)
      COMMENT = 'Maximum mobility change percentage vs baseline',
    apple.min_mobility_change AS MIN(min_difference)
      COMMENT = 'Minimum mobility change percentage vs baseline',
    apple.total_records AS SUM(record_count)
      COMMENT = 'Total number of reporting records'
  )
  COMMENT = 'Apple Maps mobility data — percentage change in routing requests by transportation type (driving, walking, transit) by region and month';
