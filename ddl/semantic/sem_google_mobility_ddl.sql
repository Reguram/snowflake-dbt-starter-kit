CREATE OR REPLACE SEMANTIC VIEW DBT_DEV.SEMANTIC.SEM_GOOGLE_MOBILITY
  TABLES (
    mobility AS DBT_DEV.DBT_MARTS.SUMMARY_GOOG_GLOBAL_MOBILITY_REPORT
  )
  DIMENSIONS (
    mobility.province_state AS province_state
      COMMENT = 'Province or state name',
    mobility.iso_3166_1 AS iso_3166_1
      COMMENT = 'ISO 3166-1 country code',
    mobility.iso_3166_2 AS iso_3166_2
      COMMENT = 'ISO 3166-2 state/region code',
    mobility.sub_region_2 AS sub_region_2
      COMMENT = 'Sub-region level 2 (e.g., county)',
    mobility.last_reported_flag AS last_reported_flag
      COMMENT = 'True if this is the most recent record for this region',
    mobility.month_period AS month_period
      COMMENT = 'Month period of the mobility record',
    mobility.year_period AS year_period
      COMMENT = 'Year period of the mobility record'
  )
  METRICS (
    mobility.avg_grocery_pharmacy_change AS AVG(avg_grocery_and_pharmacy_change_perc)
      COMMENT = 'Average % change in visits to grocery stores and pharmacies vs baseline',
    mobility.avg_parks_change AS AVG(avg_parks_change_perc)
      COMMENT = 'Average % change in visits to parks vs baseline',
    mobility.avg_residential_change AS AVG(avg_residential_change_perc)
      COMMENT = 'Average % change in time spent at residential locations vs baseline',
    mobility.avg_retail_recreation_change AS AVG(avg_retail_and_recreation_change_perc)
      COMMENT = 'Average % change in visits to retail and recreation vs baseline',
    mobility.avg_transit_stations_change AS AVG(avg_transit_stations_change_perc)
      COMMENT = 'Average % change in visits to transit stations vs baseline',
    mobility.avg_workplaces_change AS AVG(avg_workplaces_change_perc)
      COMMENT = 'Average % change in visits to workplaces vs baseline',
    mobility.total_records AS SUM(record_count)
      COMMENT = 'Total number of reporting records'
  )
  COMMENT = 'Google global mobility report — percentage change in visits to places by category (retail, parks, transit, workplaces, residential) by region and month';
