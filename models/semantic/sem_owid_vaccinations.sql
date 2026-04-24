{{ config(enabled=false) }}
{#
  ======================================================================
  Semantic View: SEM_OWID_VACCINATIONS
  ======================================================================
  This model is DISABLED (enabled: false in dbt_project.yml).
  It does NOT run during `dbt build`.

  The Snowflake Semantic View DDL is maintained in:
    ddl/semantic/sem_owid_vaccinations_ddl.sql

  To execute the DDL, run it directly in Snowflake:
    USE ROLE ACCOUNTADMIN;
    -- then paste/execute the DDL from ddl/semantic/sem_owid_vaccinations_ddl.sql

  The DDL references SUMMARY_OWID_VACCINATIONS (in DBT_MARTS) directly.

  Original base SELECT (kept for reference):
  --------------------------------------------------------------------------
  with base as (
      select * from {{ ref('summary_owid_vaccinations') }}
  )
  select
      country_region, iso3166_1, vaccines, last_reported_flag,
      month_period, year_period,
      total_total_vaccinations, total_people_vaccinated,
      total_people_fully_vaccinated, total_daily_vaccinations,
      avg_total_vaccinations_per_hundred, avg_people_vaccinated_per_hundred,
      avg_people_fully_vaccinated_per_hundred, avg_daily_vaccinations_per_million,
      record_count
  from base
  --------------------------------------------------------------------------
#}

-- This model is disabled. See comment block above for details.
select 1 as _placeholder
