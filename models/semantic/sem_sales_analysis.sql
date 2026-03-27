{#
  ======================================================================
  Semantic View: SEM_SALES_ANALYSIS
  ======================================================================
  This model is DISABLED (enabled: false in dbt_project.yml).
  It does NOT run during `dbt build`.

  The Snowflake Semantic View DDL is maintained in:
    ddl/semantic/sem_sales_analysis_ddl.sql

  To execute the DDL, run it directly in Snowflake:
    USE ROLE <your_role>;
    -- then paste/execute the DDL from ddl/semantic/sem_sales_analysis_ddl.sql

  The DDL references fct_sales (in DBT_MARTS) directly — no intermediate
  base view is needed.

  Original base SELECT (kept for reference):
  --------------------------------------------------------------------------
  with base as (
      select * from {{ ref('fct_sales') }}
  )
  select
      sales_date,
      item_category,
      date_trunc('month', sales_date) as sales_month,
      date_trunc('quarter', sales_date) as sales_quarter,
      extract(year from sales_date) as sales_year,
      total_sales,
      average_price,
      transaction_count
  from base
  --------------------------------------------------------------------------
#}

-- This model is disabled. See comment block above for details.
select 1 as _placeholder
