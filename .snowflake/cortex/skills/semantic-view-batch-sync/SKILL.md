---
name: semantic-view-batch-sync
description: >
  Batch create and update Snowflake Semantic Views for Cortex Analyst across all uncovered
  mart models. Detects marts missing semantic views, auto-classifies dimensions/metrics,
  generates sem_*.sql models, schema.yml metadata, and CREATE SEMANTIC VIEW DDL. Also updates
  existing semantic views when mart columns change. Use when asked to "create semantic views
  for all marts", "sync semantic views", "update semantic views after model changes", or
  "enable Cortex Analyst for all data".
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "1.0"
---

# Semantic View Batch Sync

> **Batch creates missing semantic views and updates stale ones** across all mart models.
> Ensures Cortex Analyst has full coverage of the analytical layer. Works hand-in-hand
> with the `semantic-view-coverage-audit` skill for gap detection.

## When to Invoke This Skill

- User asks to "create semantic views for all marts"
- User asks to "sync" or "update" semantic views after mart changes
- User asks to "enable Cortex Analyst across the project"
- User asks to "batch generate semantic views"
- After running `semantic-view-coverage-audit` and finding gaps
- User asks to "fix missing semantic views" or "fill coverage gaps"
- User onboards a new data source and wants end-to-end semantic layer coverage

## Prerequisites

Before running batch sync:
1. Mart models must exist and build successfully (`dbt build --select tag:marts` or `dbt build --select models/marts/`)
2. Mart models should have `schema.yml` entries with column descriptions (for better dimension/metric naming)
3. The `generate_semantic_view_ddl` macro must be available in `macros/`
4. `dbt_project.yml` must have `models.semantic.+enabled: false`

## Batch Sync Workflow

### Step 1: Run Coverage Audit

First, identify what needs to be created or updated. Use the `semantic-view-coverage-audit` skill
or perform inline detection:

```
1. List all models/marts/**/*.sql → get all mart model names
2. List all models/semantic/sem_*.sql → get all existing semantic models
3. List all ddl/semantic/sem_*_ddl.sql → get all existing DDL files
4. Cross-reference to find:
   a) MISSING: marts with no semantic view at all
   b) INCOMPLETE: semantic model exists but DDL is missing
   c) STALE: mart columns changed since semantic view was last generated
```

### Step 2: Prioritize and Plan

Present a batch plan to the user before generating:

```markdown
## Semantic View Batch Sync Plan

### New Views to Create (X marts)
| # | Mart Model | Domain | Suggested Name | Est. Dimensions | Est. Metrics |
|---|-----------|--------|---------------|-----------------|-------------|
| 1 | fct_sales | japan_ecomm | sem_sales_analysis | ~8 | ~4 |
| 2 | fct_cdc_reported_patient_impact | covid19 | sem_cdc_patient_impact | ~6 | ~5 |

### Existing Views to Update (Y views)
| # | Semantic View | Issue | Action |
|---|--------------|-------|--------|
| 1 | sem_revenue_analysis | Missing DDL file | Generate DDL |
| 2 | sem_product_performance | Orphaned (mart missing) | Delete or create mart |

### Skipped (Z models)
| Model | Reason |
|-------|--------|
| dim_customers | Dimension table — typically not a standalone SV target |

Proceed with batch generation? [Y/n]
```

### Step 3: Auto-Classify Columns

For each mart model being processed, classify columns as dimensions or metrics:

#### Dimension Detection Rules
| Rule | Pattern | Example |
|------|---------|---------|
| Date/time columns | `*_date`, `*_at`, `*_timestamp`, `DATE`/`TIMESTAMP` type | `order_date` → Time dimension |
| Categorical strings | `*_status`, `*_type`, `*_category`, `*_segment`, `*_class` | `order_status` → Categorical dimension |
| Entity names | `*_name`, `*_region`, `*_country`, `*_city`, `*_state` | `customer_name` → Entity dimension |
| Boolean flags | `is_*`, `has_*`, `flag_*` | `is_active` → Boolean dimension |
| FK/PK identifiers | `*_key`, `*_id` (when used for grouping) | `customer_key` → Entity dimension |
| Low-cardinality codes | `*_code`, `*_tier`, `*_level` | `priority_code` → Categorical dimension |

#### Metric Detection Rules
| Rule | Pattern | Aggregation |
|------|---------|------------|
| Financial amounts | `*_revenue`, `*_amount`, `*_price`, `*_cost`, `*_total` | SUM |
| Quantities | `*_quantity`, `*_count`, `*_qty`, `*_number` | SUM |
| Rates/averages | `*_rate`, `*_percentage`, `*_pct`, `*_avg`, `*_ratio` | AVG |
| Unique entity counts | PK columns like `*_key`, `*_id` | COUNT |
| Min/max boundaries | `first_*`, `last_*`, `min_*`, `max_*`, `earliest_*`, `latest_*` | MIN / MAX |
| Durations | `*_days`, `*_hours`, `*_duration`, `*_lag` | AVG or SUM |
| Scores/indices | `*_score`, `*_index`, `*_rank` | AVG |

#### Derived Time Dimensions
For every DATE/TIMESTAMP dimension, also generate derived dimensions unless they already exist:
- `<col>_month` → `DATE_TRUNC('MONTH', <col>)` — Month dimension
- `<col>_quarter` → `DATE_TRUNC('QUARTER', <col>)` — Quarter dimension
- `<col>_year` → `DATE_TRUNC('YEAR', <col>)` — Year dimension

### Step 4: Generate Semantic Model Files

For each new semantic view, create `models/semantic/sem_<analysis_name>.sql`:

```sql
{#
  ======================================================================
  Semantic View: SEM_<ANALYSIS_NAME>
  ======================================================================
  This model is DISABLED (enabled: false in dbt_project.yml).
  It does NOT run during `dbt build`.

  Base mart: {{ ref('<mart_model_name>') }}
  Domain: <source_domain>
  Grain: <one row per ...>

  The Snowflake Semantic View DDL is maintained in:
    ddl/semantic/sem_<analysis_name>_ddl.sql

  To regenerate DDL after mart changes:
    dbt run-operation generate_semantic_view_ddl --args '{"model_name": "sem_<analysis_name>", "base_model": "<mart_model_name>"}'

  Dimensions:
    - <list of dimension columns>
  
  Metrics:
    - <list of metric columns with aggregation types>
  --------------------------------------------------------------------------
#}

-- This model is disabled. See comment block above for details.
select 1 as _placeholder
```

**CRITICAL:**
- Do NOT use `{{ config(materialized='view') }}` — causes build failures
- Do NOT reference `{{ ref() }}` in executable SQL — model is disabled
- Keep `{{ ref() }}` only inside Jinja comment blocks for documentation

### Step 5: Update schema.yml

Add entries to `models/semantic/schema.yml` for each new semantic model:

```yaml
models:
  - name: sem_<analysis_name>
    description: >
      Semantic view for <domain> <analysis_type> analysis.
      Base mart: <mart_model_name>.
      Grain: one row per <entity>.
    meta:
      snowflake_semantic_view:
        name: SEM_<ANALYSIS_NAME>
        description: "<Human-readable description for Cortex Analyst>"
        dimensions:
          - name: <column_name>
            description: "<What this dimension represents — be specific for NL>"
        metrics:
          - name: <metric_name>
            type: <SUM|COUNT|AVG|MIN|MAX>
            expression: <source_column_or_expression>
            description: "<What this metric measures — be specific for NL>"
    columns:
      - name: _placeholder
        description: "Placeholder — model is disabled"
```

**YAML best practices for Cortex Analyst:**
- Write descriptions as if explaining to a business user
- Include units where applicable: "Total revenue in USD", "Count of unique orders"
- Mention time ranges if relevant: "Daily order count"
- Use consistent naming: `total_*` for SUM, `avg_*` for AVG, `count_*` for COUNT

### Step 6: Generate DDL Files

For each semantic view, generate `ddl/semantic/sem_<analysis_name>_ddl.sql`:

**Option A: Use the dbt macro** (recommended — reads from schema.yml)
```bash
dbt run-operation generate_semantic_view_ddl --args '{"model_name": "sem_<name>", "base_model": "<mart_model>"}'
```

**Option B: Generate manually** following the DDL template:
```sql
-- =============================================================================
-- Semantic View: SEM_<ANALYSIS_NAME>
-- Generated by: semantic-view-batch-sync skill
-- Base model: <mart_model_name>
-- Domain: <source_domain>
-- =============================================================================

CREATE OR REPLACE SEMANTIC VIEW {{database}}.{{schema}}.SEM_<ANALYSIS_NAME>
  COMMENT = '<Description for Cortex Analyst NL understanding>'
AS SELECT * FROM {{database}}.{{mart_schema}}.<MART_TABLE_NAME>
COLUMNS (
    <dimension_col>  AS DIMENSION COMMENT '<description>',
    ...
)
METRICS (
    <metric_name>  AS <AGG_TYPE>(<expression>)  COMMENT '<description>',
    ...
);
```

**Also generate the companion YAML config** `ddl/semantic/sem_<analysis_name>.yaml`:
```yaml
semantic_view_name: SEM_<ANALYSIS_NAME>
base_model: <mart_model_name>
database: "{{var('source_database', 'DBT_DEV')}}"
schema: SEMANTIC
mart_schema: DBT_MARTS
description: "<description>"
dimensions:
  - name: <col>
    description: "<desc>"
metrics:
  - name: <metric>
    type: <AGG>
    expression: <expr>
    description: "<desc>"
```

### Step 7: Update Existing Views (Drift Repair)

For semantic views where the mart model has changed:

1. **Read the current mart schema.yml** — get the latest column list
2. **Read the existing semantic model's dimensions/metrics** — get current SV definition
3. **Diff the columns:**
   - New mart columns not in SV → classify and add as dimension or metric
   - SV columns no longer in mart → remove from SV (mark as REMOVED in report)
   - Column type changes → update aggregation type if needed
4. **Regenerate:**
   - Update `models/semantic/sem_*.sql` comment block
   - Update `models/semantic/schema.yml` dimensions/metrics
   - Regenerate `ddl/semantic/sem_*_ddl.sql`

### Step 8: Validate

After batch generation:

```bash
# 1. Ensure dbt project still compiles (semantic models should be skipped)
dbt compile

# 2. Build all mart models (semantic views depend on these)
dbt build --select models/marts/

# 3. Verify semantic models are disabled
dbt ls --select models/semantic/ --output name
# Should show models but they should NOT appear in dbt build output

# 4. List generated DDL files
ls -la ddl/semantic/sem_*_ddl.sql
```

### Step 9: Deploy DDL to Snowflake

DDL must be executed directly in Snowflake (not via dbt build):

```sql
-- Execute each DDL file in Snowflake
-- Option 1: Run via Snowsight SQL worksheet
-- Option 2: Use the run_sql MCP tool
-- Option 3: Use SnowSQL CLI

-- After execution, verify:
SHOW SEMANTIC VIEWS IN SCHEMA <database>.<schema>;

-- Test with Cortex Analyst:
SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_MESSAGE(
  '<database>.<schema>.SEM_<NAME>',
  'What is the total revenue by region?'
);
```

## Batch Generation Report

After completing the sync, output a summary:

```markdown
# Semantic View Batch Sync Report

## Actions Taken
| Action | Count | Details |
|--------|-------|---------|
| New views created | X | sem_a, sem_b, sem_c |
| Existing views updated | Y | sem_d (2 new columns) |
| DDL files generated | Z | ddl/semantic/sem_*_ddl.sql |
| Orphans flagged | N | sem_product_performance (needs manual resolution) |

## Files Created/Modified
| File | Action |
|------|--------|
| models/semantic/sem_new.sql | Created |
| models/semantic/schema.yml | Updated (added 3 entries) |
| ddl/semantic/sem_new_ddl.sql | Created |
| ddl/semantic/sem_new.yaml | Created |

## Next Steps
1. Review generated files for accuracy
2. Execute DDL files in Snowflake: `ddl/semantic/sem_*_ddl.sql`
3. Test with Cortex Analyst
4. Commit changes to version control
```

## Handling Edge Cases

### Mart with no schema.yml columns
If a mart model has no column definitions in schema.yml:
- Read the SQL file to extract column names from SELECT clause
- Use naming pattern heuristics for classification
- Mark as "best-effort classification — verify manually"
- Suggest adding column descriptions to schema.yml

### Very wide tables (50+ columns)
- Focus on the most analytically useful columns
- Group remaining columns under a "Other Dimensions" note
- Ask the user which columns matter most for NL querying

### Complex mart models with CTEs
- Trace through CTEs to the final SELECT
- Only classify columns in the final output
- Note any computed columns that may need special metric treatment

### Summary tables (pre-aggregated)
- `summary_*` tables may already have aggregated metrics
- Classify these as dimensions (they're already rolled up)
- Add COUNT(*) as row_count metric for basic querying
- Note in the description that data is pre-aggregated at a specific grain

## Integration with Other Skills

| Skill | Relationship |
|-------|-------------|
| `semantic-view-coverage-audit` | Run audit FIRST to identify gaps, then use this skill to fill them |
| `snowflake-semantic-view-creator` | This skill uses the same patterns but operates in batch mode |
| `dbt-one-stop-agent` | The `generate_semantic_view` tool can be used per-model; this skill orchestrates across all models |
| `project-quality-audit` | Extended by this skill to ensure semantic layer completeness |

## File Locations

- Mart models: `models/marts/**/`
- Semantic models: `models/semantic/sem_*.sql`
- Semantic schema: `models/semantic/schema.yml`
- DDL files: `ddl/semantic/sem_*_ddl.sql`
- DDL YAML configs: `ddl/semantic/sem_*.yaml`
- DDL macro: `macros/generate_semantic_view_ddl.sql`
- Generation script: `scripts/generate_semantic_view.py`
