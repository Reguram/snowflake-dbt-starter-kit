---
applyTo: "models/semantic/**,models/marts/**/schema.yml"
description: "Natural language querying via Snowflake Semantic Views and Cortex Analyst. Translates business questions into SQL using mart models and semantic views. Auto-activates when editing semantic or mart schema files."
---

# Skill: Natural Language Queries

## When to Use
Use this skill when a user asks a business question that should be answered by querying data, or when designing models to support natural language querying via Cortex Analyst.

## Querying Approach (Priority Order)
When answering a business question, try these approaches in order:

### 1. Semantic View Query (Best)
If a Snowflake Semantic View exists for the domain:
- Cortex Analyst can answer directly via natural language
- Use the `revenue_analyst` MCP tool or `CORTEX_ANALYST_MESSAGE` function
- The semantic view defines dimensions (filter/group-by) and metrics (aggregations) — Cortex Analyst generates SQL automatically

### 2. Mart Model Query
If no semantic view exists but a mart model covers the domain:
- Read the mart model's schema.yml to understand columns
- Write SQL using `{{ ref('mart_model') }}`
- Preview with `dbt show --inline "<sql>" --limit 20`
- **After answering, suggest creating a Semantic View** if the question is likely to recur

### 3. Staged Model Query
If no mart exists:
- Explore staging models that cover the data
- Write SQL joining staged models
- **Suggest creating a mart model** to formalize the analytical pattern

### 4. Manifest/Catalog Analysis
If no database access:
- Read `target/manifest.json` to find relevant models
- Read `target/catalog.json` for column metadata
- Write SQL and explain it can't be executed without warehouse access

## Designing for Natural Language Queries
When creating or modifying models to support NL querying:

### Good Dimension Design
- Use human-readable column names (not codes)
- Include multiple time granularities: `order_date`, `order_month`, `order_quarter`, `order_year`
- Keep categorical values clean and documented
- Add `COMMENT` to every dimension explaining what it represents

### Good Metric Design
- Name metrics unambiguously: `total_revenue` not just `revenue`
- Include both raw and derived metrics: `order_count`, `avg_order_value`
- Document the aggregation type: "Sum of extended price minus discount"
- Avoid metrics that require complex pre-filtering

## Semantic View for Cortex Analyst
```sql
CREATE OR REPLACE SEMANTIC VIEW db.schema.sem_revenue_analysis
  COMMENT = 'Revenue analysis by customer, product, and time'
AS SELECT * FROM db.schema.fct_orders
COLUMNS (
    order_date    AS DIMENSION COMMENT 'Date the order was placed',
    customer_name AS DIMENSION COMMENT 'Customer who placed the order',
    order_status  AS DIMENSION COMMENT 'Fulfillment status: F/O/P'
)
METRICS (
    total_revenue AS SUM(total_price) COMMENT 'Total revenue from orders',
    order_count   AS COUNT(order_key) COMMENT 'Number of orders'
);
```

Once created, users can ask: "What was total revenue by customer last quarter?" and Cortex Analyst generates the SQL.

## After Answering a Question
Always suggest improvements:
- Missing semantic view → suggest creating one
- Missing dimension → suggest adding to existing semantic view
- Missing metric → suggest adding to existing semantic view
- Complex ad-hoc query → suggest formalizing in a mart model
