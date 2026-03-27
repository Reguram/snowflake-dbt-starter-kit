CREATE OR REPLACE SEMANTIC VIEW DBT_DEV.SEMANTIC.SEM_PRODUCT_PERFORMANCE
  TABLES (
    product AS DBT_DEV.DBT_MARTS.FCT_PRODUCT_PERFORMANCE
  )
  DIMENSIONS (
    product.site AS site
      COMMENT = 'E-commerce site name',
    product.site_segment AS site_segment
      COMMENT = 'Segment of the site (e.g., domestic, international)',
    product.brand AS brand
      COMMENT = 'Product brand',
    product.main_category AS main_category
      COMMENT = 'Primary product category',
    product.sub_category AS sub_category
      COMMENT = 'Secondary product sub-category',
    product.period_date AS period_date
      COMMENT = 'Date of the performance record',
    product.period_month AS DATE_TRUNC('month', period_date)
      COMMENT = 'Month derived from period_date',
    product.period_year AS EXTRACT(YEAR FROM period_date)
      COMMENT = 'Year derived from period_date'
  )
  METRICS (
    product.total_views AS SUM(total_views)
      COMMENT = 'Total number of product page views',
    product.total_purchases AS SUM(total_purchases)
      COMMENT = 'Total number of purchases',
    product.avg_conversion_rate AS AVG(conversion_rate)
      COMMENT = 'Average conversion rate (purchases / views)',
    product.max_conversion_rate AS MAX(conversion_rate)
      COMMENT = 'Maximum conversion rate achieved',
    product.min_conversion_rate AS MIN(conversion_rate)
      COMMENT = 'Minimum conversion rate recorded'
  )
  COMMENT = 'E-commerce product performance — views, purchases, and conversion rates by site, brand, category, and time period';
