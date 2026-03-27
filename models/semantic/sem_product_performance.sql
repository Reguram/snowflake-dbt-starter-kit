{#
  ======================================================================
  Semantic View: SEM_PRODUCT_PERFORMANCE
  ======================================================================
  This model is DISABLED (enabled: false in dbt_project.yml).
  It does NOT run during `dbt build`.

  The Snowflake Semantic View DDL is maintained in:
    ddl/semantic/sem_product_performance_ddl.sql

  To execute the DDL, run it directly in Snowflake:
    USE ROLE ACCOUNTADMIN;
    -- then paste/execute the DDL from ddl/semantic/sem_product_performance_ddl.sql

  The DDL references FCT_PRODUCT_PERFORMANCE (in DBT_MARTS) directly.

  Original base SELECT (kept for reference):
  --------------------------------------------------------------------------
  with base as (
      select * from {{ ref('fct_product_performance') }}
  )
  select
      site, site_segment, brand, main_category, sub_category,
      period_date,
      date_trunc('month', period_date) as period_month,
      extract(year from period_date) as period_year,
      total_views, total_purchases, conversion_rate
  from base
  --------------------------------------------------------------------------
#}

-- This model is disabled. See comment block above for details.
select 1 as _placeholder
