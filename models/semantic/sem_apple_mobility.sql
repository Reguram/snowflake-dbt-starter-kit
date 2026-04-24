{{ config(enabled=false) }}
{#
  ======================================================================
  Semantic View: SEM_APPLE_MOBILITY
  ======================================================================
  This model is DISABLED (enabled: false in dbt_project.yml).
  It does NOT run during `dbt build`.

  The Snowflake Semantic View DDL is maintained in:
    ddl/semantic/sem_apple_mobility_ddl.sql

  To execute the DDL, run it directly in Snowflake:
    USE ROLE ACCOUNTADMIN;
    -- then paste/execute the DDL from ddl/semantic/sem_apple_mobility_ddl.sql

  The DDL references SUMMARY_APPLE_MOBILITY (in DBT_MARTS) directly.

  Original base SELECT (kept for reference):
  --------------------------------------------------------------------------
  with base as (
      select * from {{ ref('summary_apple_mobility') }}
  )
  select
      province_state, transportation_type, iso3166_1, iso3166_2,
      last_reported_flag, month_period, year_period,
      total_difference, avg_difference, max_difference, min_difference,
      record_count
  from base
  --------------------------------------------------------------------------
#}

-- This model is disabled. See comment block above for details.
select 1 as _placeholder
