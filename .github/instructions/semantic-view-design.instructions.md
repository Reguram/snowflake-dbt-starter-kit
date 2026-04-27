---
applyTo: "models/semantic/**,models/marts/**/*.sql,models/marts/**/schema.yml,macros/publish_verified_queries.sql"
description: "Snowflake Semantic View design — DDL-like SQL via dbt_semantic_view package, dimension/metric classification, verified queries, Cortex Analyst integration. Auto-activates when editing mart or semantic models."
---

# Skill: Snowflake Semantic View Design

> **Important**: This skill is for **Snowflake-native Semantic Views** materialized via `dbt build` using the `dbt_semantic_view` package. For dbt Semantic Layer / MetricFlow, see the `building-dbt-semantic-layer` agent skill.

## When to Use
- Creating a new Snowflake Semantic View from a mart model
- Identifying which columns should be dimensions vs metrics
- Adding verified queries to improve Cortex Analyst accuracy
- Enabling Cortex Analyst natural language querying on a mart

## Active Behavior
When this skill activates on a mart model (`models/marts/**/*.sql`):
1. Analyze the model's columns and purpose
2. If no corresponding `sem_*/` subfolder exists in `models/semantic/`, suggest creating one
3. Identify likely dimensions and metrics from column names and types
4. Offer to generate the semantic view model + verified queries

## How It Works

The project uses `dbt_semantic_view` package (at `dbt_packages/dbt_semantic_view/`) which provides a `semantic_view` materialization. When you run `dbt build`, it executes `CREATE OR REPLACE SEMANTIC VIEW`. A `publish_verified_queries()` post-hook macro then appends verified queries from the YAML config.

```
dbt build --select sem_<name>
  → materialization: CREATE OR REPLACE SEMANTIC VIEW
  → post-hook: publish_verified_queries() appends verified queries
  → Result: Snowflake Semantic View with dimensions, metrics, and verified queries
```

## End-to-End Workflow

### Step 1: Analyze the Mart Model
Read the mart model SQL and its schema.yml to understand:
- **Grain**: What does one row represent?
- **Entity**: What business object is this about?
- **Columns**: What data is available?

```bash
dbt show --select fct_sales --limit 10
```

### Step 2: Classify Columns as Dimensions vs Metrics

**Dimension Heuristics** (columns users filter/group by):
| Pattern | Example | Classification |
|---------|---------|---------------|
| DATE/TIMESTAMP columns | `order_date`, `created_at` | Time dimension |
| VARCHAR with low cardinality | `order_status`, `segment` | Categorical dimension |
| Entity name/identifier | `customer_name`, `region` | Entity dimension |
| Foreign keys | `customer_key`, `product_key` | Entity dimension |

**Metric Heuristics** (columns users aggregate):
| Pattern | Example | Aggregation |
|---------|---------|------------|
| Revenue/price/amount | `total_revenue`, `unit_price` | SUM |
| Count-worthy entities | `order_key` | COUNT |
| Rate/percentage | `discount_rate` | AVG |

### Step 3: Create the Semantic View Model
Create a subfolder `models/semantic/sem_<name>/` with `sem_<name>.sql`:

```sql
{{ config(materialized='semantic_view', schema='SEMANTIC') }}

TABLES (
  t AS {{ ref('fct_<name>') }}
)
DIMENSIONS (
  t.date_col AS date_col COMMENT = 'Date dimension',
  t.category AS category COMMENT = 'Category dimension'
)
METRICS (
  t.total_amount AS SUM(amount)
    COMMENT = 'Total amount',
  t.avg_rate AS AVG(rate)
    COMMENT = 'Average rate'
)
COMMENT = 'Description for Cortex Analyst'

- AI_SQL_GENERATION $$
- Instructions for Cortex Analyst text-to-SQL accuracy
$$
```

**Key rules:**
- Use `TABLES()` with an alias and `{{ ref() }}` — alias is used in DIMENSIONS/METRICS
- Every dimension and metric MUST have a `COMMENT`
- AI_SQL_GENERATION comments guide Cortex Analyst (not parsed by dbt)
- Do NOT use `SELECT *` — this is DDL-like syntax, not a SQL query

### Step 4: Add Verified Queries
Create `models/semantic/sem_<name>/sem_<name>.yml`:

```yaml
version: 2
models:
  - name: sem_<name>
    description: "Semantic view for ... Grain: one row per (...)."
    config:
      meta:
        verified_queries:
          - name: query_name
            question: "Business question?"
            verified_at: 1745452800
            verified_by: author
            sql: "SELECT dim, SUM(metric) AS total FROM t GROUP BY dim"
```

**Rules:**
- `sql` uses the table alias from `TABLES()` (e.g., `t`), not the physical table name
- Write 3-5 queries covering common business questions
- Test SQL against actual data before adding

### Step 5: Build and Validate

```bash
# Compile to check for Jinja errors
dbt compile --select sem_<name>

# Build — creates semantic view + appends verified queries
dbt build --select sem_<name>
```

### Step 6: Verify in Snowflake

```sql
SHOW SEMANTIC VIEWS IN SCHEMA DBT_DEV.SEMANTIC;
SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('DBT_DEV.SEMANTIC.SEM_<NAME>');
```

## Cortex Analyst Integration
Once created, Cortex Analyst can answer natural language questions:
```sql
SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_MESSAGE(
  'DBT_DEV.SEMANTIC.SEM_REVENUE_ANALYSIS',
  'What was total revenue by category?'
);
```

## File Structure (per semantic view)
```
models/semantic/sem_<name>/
├── sem_<name>.sql    # DDL-like syntax (TABLES/DIMENSIONS/METRICS)
└── sem_<name>.yml    # Verified queries + model description
```

## Distinction from dbt Semantic Layer
| Feature | Snowflake Semantic View | dbt Semantic Layer (MetricFlow) |
|---------|------------------------|-------------------------------|
| Definition | DDL-like SQL (TABLES/DIMS/METRICS) | YAML semantic models |
| Built via | `dbt build` (semantic_view materialization) | N/A (metadata only) |
| Query interface | Cortex Analyst (NL) | `dbt sl query` / `mf` |
| Where it runs | Snowflake-native | dbt Cloud / MetricFlow |
| Best for | Self-service NL querying | Governed metric definitions |

Both can coexist — use dbt Semantic Layer for governed metrics and Snowflake Semantic Views for Cortex Analyst NL access.

## Best Practices
- One Semantic View per analytical domain (revenue, supply chain, customer)
- Add COMMENT to every dimension and metric — Cortex Analyst uses these for NL understanding
- Include time dimensions at multiple granularities (date, month, quarter, year)
- Name metrics unambiguously: `total_revenue` not just `revenue`
- Test the base dbt model thoroughly before creating the Semantic View
- Keep the base query simple — avoid complex CTEs in the semantic model itself
