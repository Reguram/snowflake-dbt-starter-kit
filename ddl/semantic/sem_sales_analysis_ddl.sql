-- References fct_sales directly (no intermediate sem_* base view needed)
CREATE OR REPLACE SEMANTIC VIEW DBT_DEV.SEMANTIC.SEM_SALES_ANALYSIS
  TABLES (
    sales AS DBT_DEV.DBT_MARTS.FCT_SALES
  )
  DIMENSIONS (
    sales.sales_date AS sales_date
      COMMENT = 'Sales date',
    sales.item_category AS item_category
      COMMENT = 'Item category',
    sales.maker AS maker
      COMMENT = 'Manufacturer or brand',
    sales.sales_month AS DATE_TRUNC('month', sales_date)
      COMMENT = 'Sales month derived from sales_date',
    sales.sales_quarter AS DATE_TRUNC('quarter', sales_date)
      COMMENT = 'Sales quarter derived from sales_date',
    sales.sales_year AS EXTRACT(YEAR FROM sales_date)
      COMMENT = 'Sales year derived from sales_date'
  )
  METRICS (
    sales.total_sales AS SUM(total_sales)
      COMMENT = 'Total sales',
    sales.total_average_price AS AVG(average_price)
      COMMENT = 'Average price',
    sales.total_transaction_count AS SUM(transaction_count)
      COMMENT = 'Transaction count'
  )
  COMMENT = 'Sales Analysis semantic view';