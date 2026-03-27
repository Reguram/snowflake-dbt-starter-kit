---
name: snowflake-semantic-view-creator
description: >
  Create Snowflake-native Semantic Views (CREATE SEMANTIC VIEW DDL) from dbt mart models.
  Distinct from dbt Semantic Layer / MetricFlow — this generates Snowflake DDL for Cortex Analyst
  natural language querying. Auto-detects dimensions and metrics from column types and naming
  patterns, generates sem_*.sql models, schema.yml metadata, and CREATE SEMANTIC VIEW DDL.
  Use when creating Snowflake semantic views, defining dimensions/metrics for Cortex Analyst,
  or generating CREATE SEMANTIC VIEW DDL.
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "1.0"
---

# Snowflake Semantic View Creator

> **This skill creates Snowflake-native Semantic Views** (`CREATE SEMANTIC VIEW` DDL). This is **NOT** the dbt Semantic Layer (MetricFlow). For MetricFlow semantics, use the `building-dbt-semantic-layer` skill.

## What is a Snowflake Semantic View?
A database object that defines **dimensions** (filter/group-by columns) and **metrics** (aggregatable measures) over a base SQL query. Once created, Cortex Analyst can answer natural language questions by generating SQL from the semantic view's definition.

## When to Invoke This Skill
- User asks to "create a semantic view" for a mart model
- User wants to enable natural language querying on their data
- User is working with Cortex Analyst
- User edits a mart model and wants analytics metadata defined
- User runs `generate_semantic_view_ddl` macro

## End-to-End Workflow

### 1. Identify the Base Mart Model
Start from a `fct_*` or `dim_*` model in `models/marts/`. Read its SQL and schema.yml to understand:
- **Grain**: What one row represents
- **Columns**: Available for dimension/metric classification
- **Joins**: What entities are involved

### 2. Auto-Classify Columns

**Dimension Detection Rules:**
| Column Type | Naming Pattern | Classification |
|-------------|---------------|---------------|
| DATE / TIMESTAMP | `*_date`, `*_at`, `*_timestamp` | Time dimension |
| VARCHAR (low cardinality) | `*_status`, `*_type`, `*_category`, `*_segment` | Categorical dimension |
| VARCHAR (entity name) | `*_name`, `*_region`, `*_country` | Entity dimension |
| NUMBER (FK/PK) | `*_key`, `*_id` | Entity dimension (if needed for grouping) |

**Metric Detection Rules:**
| Column Type | Naming Pattern | Aggregation |
|-------------|---------------|------------|
| NUMBER (amount) | `*_price`, `*_revenue`, `*_amount`, `*_cost` | SUM |
| NUMBER (quantity) | `*_quantity`, `*_count`, `*_qty` | SUM |
| NUMBER (rate) | `*_rate`, `*_percentage`, `*_pct` | AVG |
| Any unique key | `*_key`, `*_id` (when counting) | COUNT |
| DATE (boundary) | `first_*`, `last_*`, `min_*`, `max_*` | MIN / MAX |

### 3. Generate dbt Semantic Model
Create `models/semantic/sem_<analysis_name>.sql` as a **documentation-only** file:
- **DISABLED from dbt build** (`+enabled: false` in dbt_project.yml)
- Contains the original SELECT logic wrapped in a Jinja comment block (`{# ... #}`)
- The actual executable body is just `select 1 as _placeholder`
- Do NOT use `{{ config(materialized='view') }}` — this causes build failures
- The DDL in `ddl/semantic/` references the mart model (`fct_*`) directly

### 4. Generate schema.yml Metadata
Add `meta.snowflake_semantic_view` block with:
- `name`: Uppercase semantic view name
- `description`: What this view analyzes
- `dimensions[]`: Each with `name` and `description`
- `metrics[]`: Each with `name`, `type` (SUM/COUNT/AVG/MIN/MAX), `expression`, and `description`

### 5. Generate DDL
Use the `generate_semantic_view_ddl` macro with `base_model` parameter:
```bash
dbt run-operation generate_semantic_view_ddl --args '{"model_name": "sem_<name>", "base_model": "fct_<entity>"}'
```

Or use the `generate_semantic_view` MCP tool.

### 6. Execute and Validate
- The semantic model is NOT built during `dbt build` (it is disabled)
- Build the upstream mart model: `dbt build --select fct_<entity>`
- Execute DDL in Snowflake (via Snowsight or `run_sql` MCP tool)
- DDL references the mart model directly — no intermediate sem_* view needed
- Verify: `SHOW SEMANTIC VIEWS IN SCHEMA <db>.<schema>`
- Test with Cortex Analyst: `CORTEX_ANALYST_MESSAGE('<sv_name>', '<question>')`

## DDL Syntax Reference

```sql
CREATE OR REPLACE SEMANTIC VIEW <database>.<schema>.<name>
  COMMENT = '<description for Cortex Analyst>'
AS SELECT * FROM <base_table_or_view>
COLUMNS (
    <column_name> AS DIMENSION COMMENT '<what this dimension represents>',
    ...
)
METRICS (
    <metric_name> AS <AGG_TYPE>(<expression>) COMMENT '<what this metric measures>',
    ...
);
```

**Supported aggregation types**: `SUM`, `COUNT`, `AVG`, `MIN`, `MAX`

## Dimension/Metric Design Best Practices
- **COMMENT everything** — Cortex Analyst uses comments to understand semantics
- **Time at multiple grains** — include date, month, quarter, year dimensions
- **Unambiguous metric names** — `total_revenue` not `revenue`, `avg_order_value` not `avg`
- **One view per domain** — revenue analysis, customer analysis, supply chain analysis
- **Test base model first** — ensure data quality before exposing via Semantic View

## Project-Specific Paths
- Semantic models: `models/semantic/sem_*.sql`
- Schema metadata: `models/semantic/schema.yml`
- DDL macro: `macros/generate_semantic_view_ddl.sql`
- MCP tool: `generate_semantic_view` (local or Snowflake-managed)
- Scaffold script: `scripts/generate_semantic_view.py`

## Distinction from building-dbt-semantic-layer
| Aspect | This Skill (Snowflake SV) | building-dbt-semantic-layer (MetricFlow) |
|--------|--------------------------|------------------------------------------|
| Output | `CREATE SEMANTIC VIEW` DDL | YAML semantic model definitions |
| Query via | Cortex Analyst (NL) | `dbt sl query` / `mf` |
| Runs on | Snowflake-native | dbt Cloud / MetricFlow engine |
| Best for | Self-service NL analytics | Governed enterprise metrics |
| Coexist? | **Yes** — both can live in the same project | **Yes** |
