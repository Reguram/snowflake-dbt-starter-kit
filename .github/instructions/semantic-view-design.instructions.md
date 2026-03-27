---
applyTo: "models/semantic/**,models/marts/**/*.sql,models/marts/**/schema.yml,macros/generate_semantic_view_ddl.sql"
description: "Snowflake Semantic View design and generation — CREATE SEMANTIC VIEW DDL, dimension/metric identification, Cortex Analyst integration. Auto-activates when editing mart models, semantic models, or the DDL macro. This is for Snowflake-native Semantic Views — NOT dbt Semantic Layer (MetricFlow)."
---

# Skill: Snowflake Semantic View Design

> **Important**: This skill is for **Snowflake-native Semantic Views** (`CREATE SEMANTIC VIEW` DDL). For dbt Semantic Layer / MetricFlow, see the `building-dbt-semantic-layer` agent skill in `.agents/skills/`.

## When to Use
- Creating a new Snowflake Semantic View from a mart model
- Identifying which columns should be dimensions vs metrics
- Generating `CREATE SEMANTIC VIEW` DDL
- Enabling Cortex Analyst natural language querying on a mart
- Editing any mart model (auto-suggests: "Consider creating a Semantic View for this mart")

## Active Behavior
When this skill activates on a mart model (`models/marts/**/*.sql`):
1. Analyze the model's columns and purpose
2. If no corresponding `sem_*.sql` exists in `models/semantic/`, suggest creating one
3. Identify likely dimensions and metrics from column names and types
4. Offer to generate the full semantic view workflow

## End-to-End Workflow

### Step 1: Analyze the Mart Model
Read the mart model SQL and its schema.yml to understand:
- **Grain**: What does one row represent? (e.g., one row per order)
- **Entity**: What business object is this about? (e.g., orders, customers)
- **Columns**: What data is available?

```bash
# Preview the model's output
dbt show --select fct_orders --limit 10

# Profile columns for cardinality and types
dbt show --inline "
  select
    count(*) as row_count,
    count(distinct order_key) as unique_pks,
    count(distinct customer_key) as unique_customers,
    min(order_date) as min_date,
    max(order_date) as max_date
  from {{ ref('fct_orders') }}
" --limit 1
```

### Step 2: Classify Columns as Dimensions vs Metrics

**Dimension Heuristics** (columns users filter/group by):
| Pattern | Example | Classification |
|---------|---------|---------------|
| DATE/TIMESTAMP columns | `order_date`, `created_at` | Time dimension |
| VARCHAR with low cardinality | `order_status`, `segment` | Categorical dimension |
| Entity name/identifier | `customer_name`, `region` | Entity dimension |
| Foreign keys | `customer_key`, `product_key` | Entity dimension (join target) |

**Metric Heuristics** (columns users aggregate):
| Pattern | Example | Aggregation |
|---------|---------|------------|
| Revenue/price/amount | `total_revenue`, `unit_price` | SUM |
| Count-worthy entities | `order_key`, `line_item_key` | COUNT |
| Rate/percentage | `discount_rate` | AVG |
| First/last dates | `first_order_date` | MIN/MAX |

### Step 3: Create the dbt Semantic Model
Semantic models are **disabled from `dbt build`** (`+enabled: false` in dbt_project.yml).
They exist as documentation-only files. The DDL references mart models directly.

Create `models/semantic/sem_<analysis_name>.sql` as a **comment block** with the reference SQL:

```sql
{#
  ======================================================================
  Semantic View: SEM_REVENUE_ANALYSIS
  ======================================================================
  This model is DISABLED (enabled: false in dbt_project.yml).
  It does NOT run during `dbt build`.

  The Snowflake Semantic View DDL is maintained in:
    ddl/semantic/sem_revenue_analysis_ddl.sql

  To generate DDL, use the macro:
    dbt run-operation generate_semantic_view_ddl --args '{"model_name": "sem_revenue_analysis", "base_model": "fct_orders"}'

  Original base SELECT (kept for reference):
  --------------------------------------------------------------------------
  with orders as (
      select * from {{ ref('fct_orders') }}
  ),
  customers as (
      select * from {{ ref('dim_customers') }}
  )
  select
      o.order_date,
      date_trunc('month', o.order_date) as order_month,
      ...
  from orders o
  left join customers c on o.customer_key = c.customer_key
  --------------------------------------------------------------------------
#}

-- This model is disabled. See comment block above for details.
select 1 as _placeholder
```

**IMPORTANT:** Do NOT use `{{ config(materialized='view') }}` in semantic models —
they will fail during `dbt build`. The `+enabled: false` in dbt_project.yml ensures
they are skipped entirely.

### Step 4: Add YAML Metadata
Add to `models/semantic/schema.yml`:

```yaml
models:
  - name: sem_revenue_analysis
    description: >
      Semantic view base model for revenue analysis.
      Joins orders with customers for multi-dimensional analysis.
      Grain: one row per order.
    meta:
      snowflake_semantic_view:
        name: SEM_REVENUE_ANALYSIS
        description: "Revenue analysis by customer, product, region, and time"
        dimensions:
          - name: order_date
            description: "Date the order was placed"
          - name: order_month
            description: "Month the order was placed (truncated)"
          - name: order_quarter
            description: "Quarter the order was placed"
          - name: order_year
            description: "Year the order was placed"
          - name: order_status
            description: "Order fulfillment status: F (fulfilled), O (open), P (partial)"
          - name: customer_name
            description: "Name of the customer who placed the order"
          - name: market_segment
            description: "Customer market segment"
          - name: nation_name
            description: "Customer nation"
          - name: region_name
            description: "Customer region (continent)"
        metrics:
          - name: total_revenue
            type: SUM
            expression: total_price
            description: "Total revenue from orders"
          - name: order_count
            type: COUNT
            expression: order_key
            description: "Number of orders"
          - name: avg_order_value
            type: AVG
            expression: total_price
            description: "Average order value"
    columns:
      - name: order_key
        tests:
          - not_null
```

### Step 5: Generate DDL
Two options:

**Option A: dbt macro** (recommended)
```bash
dbt run-operation generate_semantic_view_ddl --args '{"model_name": "sem_revenue_analysis"}'
```
This reads the `meta.snowflake_semantic_view` block from schema.yml and generates the DDL.

**Option B: MCP tool**
Use the `generate_semantic_view` MCP tool which connects to Snowflake and can auto-detect column types.

### Step 6: Execute DDL in Snowflake
Run the generated DDL in Snowsight or via the `run_sql` MCP tool:

```sql
CREATE OR REPLACE SEMANTIC VIEW DBT_DEV.SEMANTIC.SEM_REVENUE_ANALYSIS
  COMMENT = 'Revenue analysis by customer, product, region, and time'
AS SELECT * FROM DBT_DEV.DBT_MARTS.SEM_REVENUE_ANALYSIS
COLUMNS (
    order_date      AS DIMENSION COMMENT 'Date the order was placed',
    order_month     AS DIMENSION COMMENT 'Month the order was placed',
    order_quarter   AS DIMENSION COMMENT 'Quarter the order was placed',
    order_year      AS DIMENSION COMMENT 'Year the order was placed',
    order_status    AS DIMENSION COMMENT 'Fulfillment status: F/O/P',
    customer_name   AS DIMENSION COMMENT 'Customer name',
    market_segment  AS DIMENSION COMMENT 'Customer market segment',
    nation_name     AS DIMENSION COMMENT 'Customer nation',
    region_name     AS DIMENSION COMMENT 'Customer region'
)
METRICS (
    total_revenue   AS SUM(total_price)  COMMENT 'Total revenue from orders',
    order_count     AS COUNT(order_key)  COMMENT 'Number of orders',
    avg_order_value AS AVG(total_price)  COMMENT 'Average order value'
);
```

### Step 7: Validate
```bash
# Verify the base model builds
dbt build --select sem_revenue_analysis

# Verify the semantic view exists in Snowflake
dbt show --inline "SHOW SEMANTIC VIEWS IN SCHEMA DBT_DEV.SEMANTIC" --limit 10
```

## Cortex Analyst Integration
Once a Semantic View exists, Cortex Analyst can answer natural language questions:
```sql
-- Users can ask: "What was total revenue by region last quarter?"
-- Cortex Analyst generates SQL from the Semantic View definition
SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_MESSAGE(
  'DBT_DEV.SEMANTIC.SEM_REVENUE_ANALYSIS',
  'What was total revenue by region last quarter?'
);
```

The MCP server's `revenue_analyst` tool type (`CORTEX_ANALYST_MESSAGE`) provides this capability to AI agents.

## Distinction from dbt Semantic Layer
| Feature | Snowflake Semantic View | dbt Semantic Layer (MetricFlow) |
|---------|------------------------|-------------------------------|
| Definition | `CREATE SEMANTIC VIEW` DDL | YAML semantic models |
| Query interface | Cortex Analyst (NL) | `dbt sl query` / `mf` |
| Where it runs | Snowflake-native | dbt Cloud / MetricFlow |
| Best for | Self-service NL querying | Governed metric definitions |
| This project | `models/semantic/` + DDL macro | `.agents/skills/building-dbt-semantic-layer/` |

Both can coexist — use dbt Semantic Layer for governed metrics and Snowflake Semantic Views for Cortex Analyst NL access.

## Best Practices
- One Semantic View per analytical domain (revenue, supply chain, customer)
- Add COMMENT to every dimension and metric — Cortex Analyst uses these for NL understanding
- Include time dimensions at multiple granularities (date, month, quarter, year)
- Name metrics unambiguously: `total_revenue` not just `revenue`
- Test the base dbt model thoroughly before creating the Semantic View
- Keep the base query simple — avoid complex CTEs in the semantic model itself
