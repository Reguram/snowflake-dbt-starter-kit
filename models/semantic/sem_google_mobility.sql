{{ config(enabled=false) }}
{#
  ======================================================================
  Semantic View: SEM_GOOGLE_MOBILITY
  ======================================================================
  This model is DISABLED (enabled: false in dbt_project.yml).
  It does NOT run during `dbt build`.

  The Snowflake Semantic View DDL is maintained in:
    ddl/semantic/sem_google_mobility_ddl.sql

  To execute the DDL, run it directly in Snowflake:
    USE ROLE ACCOUNTADMIN;
    -- then paste/execute the DDL from ddl/semantic/sem_google_mobility_ddl.sql

  The DDL references SUMMARY_GOOG_GLOBAL_MOBILITY_REPORT (in DBT_MARTS) directly.

  Original base SELECT (kept for reference):
  --------------------------------------------------------------------------
  with base as (
      select * from {{ ref('summary_goog_global_mobility_report') }}
  )
  select
      province_state, iso_3166_1, iso_3166_2, sub_region_2,
      last_reported_flag, month_period, year_period,
      avg_grocery_and_pharmacy_change_perc, avg_parks_change_perc,
      avg_residential_change_perc, avg_retail_and_recreation_change_perc,
      avg_transit_stations_change_perc, avg_workplaces_change_perc, record_count
  from base
  --------------------------------------------------------------------------
#}

-- This model is disabled. See comment block above for details.
select 1 as _placeholder
