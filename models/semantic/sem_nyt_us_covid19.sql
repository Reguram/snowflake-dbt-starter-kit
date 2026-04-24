{{ config(enabled=false) }}
{#
  ======================================================================
  Semantic View: SEM_NYT_US_COVID19
  ======================================================================
  This model is DISABLED (enabled: false in dbt_project.yml).
  It does NOT run during `dbt build`.

  The Snowflake Semantic View DDL is maintained in:
    ddl/semantic/sem_nyt_us_covid19_ddl.sql

  To execute the DDL, run it directly in Snowflake:
    USE ROLE ACCOUNTADMIN;
    -- then paste/execute the DDL from ddl/semantic/sem_nyt_us_covid19_ddl.sql

  The DDL references SUMMARY_NYT_US_COVID19 (in DBT_MARTS) directly.

  Original base SELECT (kept for reference):
  --------------------------------------------------------------------------
  with base as (
      select * from {{ ref('summary_nyt_us_covid19') }}
  )
  select
      state, county, fips, iso3166_1, iso3166_2, last_reported_flag,
      month_period, year_period, total_cases, total_deaths,
      total_cases_since_prev_day, total_deaths_since_prev_day,
      avg_cases, avg_deaths, record_count
  from base
  --------------------------------------------------------------------------
#}

-- This model is disabled. See comment block above for details.
select 1 as _placeholder
