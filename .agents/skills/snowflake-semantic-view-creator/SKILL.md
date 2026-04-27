---
name: snowflake-semantic-view-creator
description: >
  Create Snowflake-native Semantic Views from dbt mart models using the dbt_semantic_view package.
  Uses DDL-like SQL syntax (TABLES/DIMENSIONS/METRICS) materialized via `dbt build`.
  Verified queries are appended via a publish_verified_queries() post-hook macro.
  Distinct from dbt Semantic Layer / MetricFlow.
  Use when creating Snowflake semantic views, defining dimensions/metrics for Cortex Analyst,
  or enabling natural language querying.
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "2.0"
---

# Snowflake Semantic View Creator

> **This skill creates Snowflake-native Semantic Views** via `dbt build` using the [`Snowflake-Labs/dbt_semantic_view`](https://github.com/Snowflake-Labs/dbt_semantic_view) package. This is **NOT** the dbt Semantic Layer (MetricFlow). For MetricFlow semantics, use the `building-dbt-semantic-layer` skill.

## What is a Snowflake Semantic View?
A database object that defines **dimensions** (filter/group-by columns) and **metrics** (aggregatable measures) over base tables. Once created, Cortex Analyst can answer natural language questions by generating SQL from the semantic view's definition. **Verified queries** improve text-to-SQL accuracy by providing known-good SQL examples.

## When to Invoke This Skill
- User asks to "create a semantic view" for a mart model
- User wants to enable natural language querying on their data
- User is working with Cortex Analyst
- User edits a mart model and wants analytics metadata defined
- User wants to add verified queries to a semantic view

## How It Works (Architecture)

```
dbt_project.yml                   dbt_packages/dbt_semantic_view/
  semantic:                         macros/materializations/semantic_view.sql
    +materialized: semantic_view      → CREATE OR REPLACE SEMANTIC VIEW
    +post_hook: publish_verified_queries()
                                    macros/publish_verified_queries.sql
                                      → SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML
                                      → Appends verified_queries from .yml meta
```

## End-to-End Workflow

### 1. Identify the Base Mart Model
Start from a `fct_*`, `dim_*`, or `summary_*` model in `models/marts/`. Read its SQL and schema.yml to understand:
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

### 3. Create Semantic View Model (subfolder)
Create `models/semantic/sem_<name>/sem_<name>.sql` with DDL-like syntax:

```sql
{{
  config(
    materialized = 'semantic_view',
    schema = 'SEMANTIC',
    tags = ['semantic', 'sem_<name>'],
    post_hook = [
      "{{ publish_verified_queries() }}"
    ]
  )
}}

TABLES (
  t AS {{ ref('fct_<name>') }}
)
DIMENSIONS (
  t.column1 AS column1 COMMENT = 'Description of dimension',
  t.date_col AS date_col COMMENT = 'Date dimension'
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
- Describe what questions this view answers and how to interpret metrics
$$
```

**Key rules:**
- Use `TABLES()` with an alias and `{{ ref() }}` — the alias is used in DIMENSIONS/METRICS
- Every dimension and metric MUST have a `COMMENT`
- The `COMMENT = '...'` at the end is the view-level description
- AI_SQL_GENERATION comments guide Cortex Analyst behavior (not parsed by dbt)

### 4. Add Verified Queries (.yml)
Create `models/semantic/sem_<name>/sem_<name>.yml`:

```yaml
version: 2
models:
  - name: sem_<name>
    description: "Semantic view for ... Grain: one row per (...)."
    config:
      meta:
        verified_queries:
          - name: descriptive_query_name
            question: "Natural language business question?"
            verified_at: 1745452800
            verified_by: author
            sql: >
              SELECT dimension, SUM(metric) AS total
              FROM t
              GROUP BY dimension
              ORDER BY total DESC
```

**Verified query rules:**
- `sql` uses the **table alias** from TABLES(), not the physical table name
- `verified_at` is a Unix timestamp (seconds since epoch)
- Write 3-5 queries covering the most common business questions
- Test SQL against the actual data before adding

### 5. Build and Validate

```bash
# Compile first to check for Jinja errors
dbt compile --select sem_<name>

# Build — creates the semantic view + appends verified queries
dbt build --select sem_<name>
```

### 6. Verify in Snowflake

```sql
-- Check the semantic view exists
SHOW SEMANTIC VIEWS IN SCHEMA DBT_DEV.SEMANTIC;

-- Read the full YAML (should include verified_queries block)
SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('DBT_DEV.SEMANTIC.SEM_<NAME>');

-- Test with Cortex Analyst
-- (via Snowsight or programmatically)
```

## File Structure

```
models/semantic/sem_<name>/
├── sem_<name>.sql    # DDL-like syntax (TABLES/DIMENSIONS/METRICS)
├── sem_<name>.yml    # Verified queries + model description
└── sem_<name>.md     # Optional: additional documentation
```

## Dimension/Metric Design Best Practices
- **COMMENT everything** — Cortex Analyst uses comments to understand semantics
- **Time at multiple grains** — include date, month, quarter, year dimensions
- **Unambiguous metric names** — `total_revenue` not `revenue`, `avg_order_value` not `avg`
- **One view per domain** — revenue analysis, customer analysis, supply chain analysis
- **Test base model first** — ensure data quality before exposing via Semantic View
- **AI_SQL_GENERATION comments** — add instructions for text-to-SQL accuracy after METRICS

## Project-Specific Paths
- Semantic models: `models/semantic/<name>/sem_<name>.sql` (subfolder per view)
- Verified queries: `models/semantic/<name>/sem_<name>.yml`
- Package: `dbt_packages/dbt_semantic_view/` (Snowflake-Labs materialization)
- Post-hook macro: `macros/publish_verified_queries.sql`
- Column classifier: `scripts/generate_semantic_view.py` (helper for dimension/metric detection)
- Project config: `dbt_project.yml` → `semantic:` block

## Distinction from building-dbt-semantic-layer
| Aspect | This Skill (Snowflake SV) | building-dbt-semantic-layer (MetricFlow) |
|--------|--------------------------|------------------------------------------|
| Output | Snowflake Semantic View object | YAML semantic model definitions |
| SQL syntax | DDL-like (TABLES/DIMS/METRICS) | N/A (YAML-only) |
| Built via | `dbt build` (semantic_view materialization) | N/A (metadata only) |
| Verified queries | Yes (publish_verified_queries post-hook) | No |
| Query via | Cortex Analyst (NL) | `dbt sl query` / `mf` |
| Runs on | Snowflake-native | dbt Cloud / MetricFlow engine |
| Best for | Self-service NL analytics | Governed enterprise metrics |
| Coexist? | **Yes** — both can live in the same project | **Yes** |
