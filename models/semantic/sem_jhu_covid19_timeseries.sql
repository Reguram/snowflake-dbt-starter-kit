{{ config(enabled=false) }}
{#
  ======================================================================
  Semantic View: SEM_JHU_COVID19_TIMESERIES
  ======================================================================
  This model is DISABLED (enabled: false in dbt_project.yml).
  It does NOT run during `dbt build`.

  The Snowflake Semantic View DDL is maintained in:
    ddl/semantic/sem_jhu_covid19_timeseries_ddl.sql

  To execute the DDL, run it directly in Snowflake:
    USE ROLE ACCOUNTADMIN;
    -- then paste/execute the DDL from ddl/semantic/sem_jhu_covid19_timeseries_ddl.sql

  The DDL references SUMMARY_JHU_COVID_19_TIMESERIES (in DBT_MARTS) directly.

  Original base SELECT (kept for reference):
  --------------------------------------------------------------------------
  with base as (
      select * from {{ ref('summary_jhu_covid_19_timeseries') }}
  )
  select
      province_state, county, fips, iso3166_1, iso3166_2,
      case_type, last_reported_flag, month_period, year_period,
      total_cases, total_difference, avg_cases, max_cases, record_count
  from base
  --------------------------------------------------------------------------
#}

-- This model is disabled. See comment block above for details.
select 1 as _placeholder
