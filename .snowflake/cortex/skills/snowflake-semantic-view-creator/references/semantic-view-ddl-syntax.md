# Snowflake Semantic View DDL Syntax

## CREATE SEMANTIC VIEW

```sql
CREATE [ OR REPLACE ] SEMANTIC VIEW [ IF NOT EXISTS ] <database>.<schema>.<name>
  TABLES (
    <table_alias> AS <fully_qualified_table_name>
      [ PRIMARY KEY ( <pk_column> [, ...] ) ]
      [ COMMENT = '<table_description>' ]
    [, ...]
  )
  [ RELATIONSHIPS (
    <relationship_name> AS
      <table_alias> ( <fk_column> ) REFERENCES <ref_table_alias> [ ( <pk_column> ) ]
    [, ...]
  ) ]
  [ FACTS (
    <table_alias>.<fact_name> AS <sql_expression>
      [ COMMENT = '<description>' ]
    [, ...]
  ) ]
  [ DIMENSIONS (
    <table_alias>.<dimension_name> AS <sql_expression>
      [ COMMENT = '<description>' ]
    [, ...]
  ) ]
  [ METRICS (
    <table_alias>.<metric_name> AS <aggregation>(<expression>)
      [ COMMENT = '<description>' ]
    [, ...]
  ) ]
  [ COMMENT = '<semantic_view_description>' ]
  [ AI_SQL_GENERATION '<instructions>' ]
  [ AI_QUESTION_CATEGORIZATION '<instructions>' ];
```

## Parameters

| Parameter | Description |
|-----------|-------------|
| `<database>.<schema>.<name>` | Fully qualified name of the semantic view |
| `TABLES` | Logical tables referenced by the semantic view |
| `RELATIONSHIPS` | Foreign key relationships between logical tables |
| `FACTS` | Computed columns used in dimension/metric expressions |
| `DIMENSIONS` | Columns for filtering/grouping, prefixed with table alias |
| `METRICS` | Aggregation expressions, prefixed with table alias |
| `COMMENT` | Description used by Cortex Analyst for NL understanding |
| `AI_SQL_GENERATION` | Custom instructions for Cortex Analyst SQL generation |
| `AI_QUESTION_CATEGORIZATION` | Custom instructions for question classification |

## Aggregation Types

| Type | Example | Use Case |
|------|---------|----------|
| `SUM` | `SUM(total_price)` | Revenue, quantity, amounts |
| `COUNT` | `COUNT(order_key)` | Row counts, entity counts |
| `AVG` | `AVG(unit_price)` | Averages, rates |
| `MIN` | `MIN(order_date)` | First occurrence, minimums |
| `MAX` | `MAX(order_date)` | Last occurrence, maximums |

## Example

```sql
CREATE OR REPLACE SEMANTIC VIEW DBT_DEV.SEMANTIC.SEM_SALES_ANALYSIS
  TABLES (
    sem_sales AS DBT_DEV.SEMANTIC.SEM_SALES_ANALYSIS
  )
  DIMENSIONS (
    sem_sales.sales_date AS sales_date
      COMMENT = 'Date of sales activity',
    sem_sales.item_category AS item_category
      COMMENT = 'Product category'
  )
  METRICS (
    sem_sales.total_sales AS SUM(total_sales)
      COMMENT = 'Total sales amount',
    sem_sales.avg_price AS AVG(average_price)
      COMMENT = 'Average price'
  )
  COMMENT = 'Sales Analysis semantic view';
```

## YAML-based Creation

Snowflake also supports creating semantic views from YAML:

```sql
-- Validate YAML without creating
CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML('<db>.<schema>', $$<yaml>$$, TRUE);

-- Create from YAML
CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML('<db>.<schema>', $$<yaml>$$);

-- Read YAML spec from existing semantic view
SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('<db>.<schema>.<name>');
```

## Management Commands

```sql
-- List all semantic views
SHOW SEMANTIC VIEWS [ IN SCHEMA <db>.<schema> ];

-- Describe a semantic view
DESCRIBE SEMANTIC VIEW <db>.<schema>.<name>;

-- Drop a semantic view
DROP SEMANTIC VIEW [ IF EXISTS ] <db>.<schema>.<name>;

-- Alter a semantic view
ALTER SEMANTIC VIEW <db>.<schema>.<name> SET COMMENT = '<new_comment>';
```

## Cortex Analyst Integration

Once a Semantic View exists, query it with Cortex Analyst:

```sql
SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_MESSAGE(
    '<database>.<schema>.<semantic_view_name>',
    '<natural_language_question>'
);
```

Example:
```sql
SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_MESSAGE(
    'DBT_DEV.SEMANTIC.SEM_REVENUE_ANALYSIS',
    'What was total revenue by region in 2024?'
);
```
