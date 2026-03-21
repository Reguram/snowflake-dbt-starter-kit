CREATE OR REPLACE SEMANTIC VIEW DBT_DEV.SEMANTIC.SEM_SALES_ANALYSIS
  TABLES (
    sem_sales AS DBT_DEV.DBT_MARTS.SEM_SALES_ANALYSIS
  )
  DIMENSIONS (
    sem_sales.sales_date AS sales_date
      COMMENT = 'Sales date',
    sem_sales.item_category AS item_category
      COMMENT = 'Item category',
    sem_sales.sales_month AS DATE_TRUNC('month', sales_date)
      COMMENT = 'Sales month derived from sales_date',
    sem_sales.sales_quarter AS DATE_TRUNC('quarter', sales_date)
      COMMENT = 'Sales quarter derived from sales_date',
    sem_sales.sales_year AS EXTRACT(YEAR FROM sales_date)
      COMMENT = 'Sales year derived from sales_date'
  )
  METRICS (
    sem_sales.total_sales AS SUM(total_sales)
      COMMENT = 'Total sales',
    sem_sales.total_average_price AS AVG(average_price)
      COMMENT = 'Average price',
    sem_sales.total_transaction_count AS SUM(transaction_count)
      COMMENT = 'Transaction count'
  )
  COMMENT = 'Sales Analysis semantic view';