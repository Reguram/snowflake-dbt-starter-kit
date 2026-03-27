{#
  ======================================================================
  Semantic View: SEM_REVENUE_ANALYSIS
  ======================================================================
  This model is DISABLED (enabled: false in dbt_project.yml).
  It does NOT run during `dbt build`.

  The Snowflake Semantic View DDL should be maintained in:
    ddl/semantic/sem_revenue_analysis_ddl.sql

  To generate DDL, use the macro:
    dbt run-operation generate_semantic_view_ddl --args '{"model_name": "sem_revenue_analysis"}'

  The DDL references fct_sales (in DBT_MARTS) directly — no intermediate
  base view is needed.

  Original base SELECT (kept for reference):
  --------------------------------------------------------------------------
  with sales as (
      select
          sales_date, maker, item_category,
          total_sales, average_price, transaction_count
      from {{ ref('fct_sales') }}
  )
  select
      sales_date,
      date_trunc('month', sales_date) as sales_month,
      date_trunc('quarter', sales_date) as sales_quarter,
      extract(year from sales_date) as sales_year,
      maker, item_category,
      total_sales, average_price, transaction_count
  from sales
  --------------------------------------------------------------------------
#}

-- This model is disabled. See comment block above for details.
select 1 as _placeholder