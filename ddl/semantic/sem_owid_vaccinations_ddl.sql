CREATE OR REPLACE SEMANTIC VIEW DBT_DEV.SEMANTIC.SEM_OWID_VACCINATIONS
  TABLES (
    vax AS DBT_DEV.DBT_MARTS.SUMMARY_OWID_VACCINATIONS
  )
  DIMENSIONS (
    vax.country_region AS country_region
      COMMENT = 'Country or region name',
    vax.iso3166_1 AS iso3166_1
      COMMENT = 'ISO 3166-1 country code',
    vax.vaccines AS vaccines
      COMMENT = 'Vaccine brands used in the country',
    vax.last_reported_flag AS last_reported_flag
      COMMENT = 'True if this is the most recent record for this country',
    vax.month_period AS month_period
      COMMENT = 'Month period of the vaccination record',
    vax.year_period AS year_period
      COMMENT = 'Year period of the vaccination record'
  )
  METRICS (
    vax.total_vaccinations AS SUM(total_total_vaccinations)
      COMMENT = 'Total number of vaccine doses administered',
    vax.total_people_vaccinated AS SUM(total_people_vaccinated)
      COMMENT = 'Total number of people who received at least one dose',
    vax.total_people_fully_vaccinated AS SUM(total_people_fully_vaccinated)
      COMMENT = 'Total number of people fully vaccinated',
    vax.total_daily_vaccinations AS SUM(total_daily_vaccinations)
      COMMENT = 'Total daily vaccination doses administered',
    vax.avg_vaccinations_per_hundred AS AVG(avg_total_vaccinations_per_hundred)
      COMMENT = 'Average total vaccinations per 100 people',
    vax.avg_people_vaccinated_per_hundred AS AVG(avg_people_vaccinated_per_hundred)
      COMMENT = 'Average people vaccinated per 100 people',
    vax.avg_fully_vaccinated_per_hundred AS AVG(avg_people_fully_vaccinated_per_hundred)
      COMMENT = 'Average people fully vaccinated per 100 people',
    vax.avg_daily_vaccinations_per_million AS AVG(avg_daily_vaccinations_per_million)
      COMMENT = 'Average daily vaccinations per 1 million people',
    vax.total_records AS SUM(record_count)
      COMMENT = 'Total number of reporting records'
  )
  COMMENT = 'Our World in Data (OWID) global COVID-19 vaccination data — doses administered, people vaccinated, and per-capita rates by country and month';
