{{
  config(
    materialized = 'semantic_view',
    schema = 'SEMANTIC',
    tags = ['semantic', 'sem_revenue_analysis'],
    post_hook = [
      "{{ publish_verified_queries() }}"
    ]
  )
}}

TABLES (
  sales AS {{ ref('fct_sales') }}
)
DIMENSIONS (
  sales.sales_date AS sales_date
    COMMENT = 'Date of sales activity',
  sales.maker AS maker
    COMMENT = 'Manufacturer or brand of the item sold',
  sales.item_category AS item_category
    COMMENT = 'Product category (Smartphone or Other)'
)
METRICS (
  sales.total_revenue AS SUM(total_sales)
    COMMENT = 'Total sales revenue',
  sales.total_transactions AS SUM(transaction_count)
    COMMENT = 'Total number of transactions',
  sales.avg_price AS AVG(average_price)
    COMMENT = 'Average item price'
)
COMMENT = 'Revenue analysis by maker, category, and time for Cortex Analyst'

AI_SQL_GENERATION $$
When users ask about "revenue", "sales", or "transactions", query this semantic view.
total_sales is the primary revenue metric — always use SUM aggregation.
For time-based queries, group by sales_date.
maker represents the manufacturer or brand.
item_category is either "Smartphone" or "Other".
$$
