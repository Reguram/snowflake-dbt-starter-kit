---
name: onboard-new-source
description: >
  End-to-end onboarding of a new Snowflake source into this dbt project: profile source table,
  generate staging model with tests, suggest intermediate/mart models, run dbt build, and create
  a Snowflake Semantic View for Cortex Analyst. Always reads project context first.
  Use when: onboarding a new source, discovering a new table, building staging+marts for a new dataset,
  creating a full medallion pipeline from scratch.
  Triggers: onboard, new source, discover source, add source, new table, build pipeline, medallion pipeline.
tools: ["bash", "edit", "mcp"]
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "1.0"
---

# Onboard New Source — Full Medallion Pipeline

> End-to-end skill that discovers a Snowflake source table, generates all dbt layers
> (staging → intermediate → marts), runs `dbt build`, and creates a Snowflake Semantic View.

## Required Inputs

When the user invokes this skill, collect these parameters (ask if not provided):

| Parameter | Example | Description |
|-----------|---------|-------------|
| `SOURCE_DATABASE` | `AMAZON_AND_ECOMMERCE_WEBSITES_PRODUCT_VIEWS_AND_PURCHASES` | Snowflake database |
| `SOURCE_SCHEMA` | `DATAFEEDS` | Schema inside that database |
| `SOURCE_TABLE` | `PRODUCT_VIEWS_AND_PURCHASES` | Raw table name (UPPER_CASE) |
| `SOURCE_NAME` | `datafeeds` | Short snake_case alias for folders and naming |

Derived automatically:
- Staging model: `stg_<SOURCE_NAME>__<SOURCE_TABLE_lower>`
- Staging path: `models/staging/<SOURCE_NAME>/`

---

## Step 0 — Read Project Context (MANDATORY — do NOT skip)

Before generating ANY file:

1. Read `dbt_project.yml` to confirm schema names (`DBT_STAGING`, `DBT_INTERMEDIATE`, `DBT_MARTS`).
2. Scan `models/staging/` — list existing source directories to understand naming patterns.
3. Check if `models/staging/<SOURCE_NAME>/` already exists. If yes, diff rather than overwrite.
4. Read one existing `_sources.yml` (e.g., `models/staging/japan_ecomm_data/_sources.yml`) as a template.
5. Read one existing staging `.sql` model and its `schema.yml` to match the code style exactly.

**Do NOT generate generic boilerplate. Match the existing project style.**

---

## Step 1 — Profile the Source Table

Run these queries against `<SOURCE_DATABASE>.<SOURCE_SCHEMA>.<SOURCE_TABLE>`:

```sql
-- Column metadata
DESCRIBE TABLE <SOURCE_DATABASE>.<SOURCE_SCHEMA>.<SOURCE_TABLE>;

-- Row count
SELECT COUNT(*) AS row_count FROM <SOURCE_DATABASE>.<SOURCE_SCHEMA>.<SOURCE_TABLE>;

-- Sample data
SELECT * FROM <SOURCE_DATABASE>.<SOURCE_SCHEMA>.<SOURCE_TABLE> LIMIT 10;
```

Then profile each column:

```sql
SELECT
    '<COL>' AS column_name,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT "<COL>") AS distinct_count,
    COUNT(*) - COUNT("<COL>") AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT("<COL>")) / COUNT(*), 1) AS null_pct,
    ROUND(100.0 * COUNT(DISTINCT "<COL>") / NULLIF(COUNT("<COL>"), 0), 1) AS uniqueness_pct
FROM <SOURCE_DATABASE>.<SOURCE_SCHEMA>.<SOURCE_TABLE>;
```

Report a summary table:

| Column | Type | Nulls% | Distinct | Unique% | Classification |
|--------|------|--------|----------|---------|----------------|
| ... | ... | ... | ... | ... | PK / dimension / metric / date / exclude |

Classification rules:
- **PK candidate**: 0% nulls AND 100% unique
- **Date/timestamp column**: DATE, TIMESTAMP_* types → dimension + clustering key candidate
- **High-cardinality VARCHAR** (>100 distinct): dimension
- **Low-cardinality VARCHAR** (<5 distinct): dimension + `accepted_values` test candidate
- **INT/FLOAT/NUMBER**: metric (SUM/AVG/COUNT)
- **Surrogate key / FK**: exclude from semantic view

---

## Step 2 — Generate the Staging Layer

Create three files under `models/staging/<SOURCE_NAME>/`:

### File 1: `_sources.yml`

```yaml
version: 2

sources:
  - name: <SOURCE_NAME>
    description: "Raw source from <SOURCE_DATABASE>.<SOURCE_SCHEMA>"
    database: "<SOURCE_DATABASE>"
    schema: "<SOURCE_SCHEMA>"
    quoting:
      identifier: true
    tables:
      - name: <SOURCE_TABLE>
        description: "<one-sentence description based on profiling>"
        columns:
          # PK column: unique + not_null tests
          # Low-cardinality columns: accepted_values tests
          # All columns listed with name
```

### File 2: `stg_<SOURCE_NAME>__<table_lower>.sql`

```sql
with source as (
    select * from {{ source('<SOURCE_NAME>', '<SOURCE_TABLE>') }}
),

staged as (
    select
        -- Rename EVERY column from UPPER_CASE to snake_case
        -- Cast types: TRY_TO_DATE for dates, TRY_TO_NUMBER for numbers
        -- Do NOT add business logic here
    from source
)

select * from staged
```

Rules:
- List ALL columns explicitly in the `staged` CTE — no `SELECT *`.
- Rename all source columns to `snake_case`.
- Use `TRY_TO_DATE` / `TRY_TO_NUMBER` for type casts.
- If no single natural PK, create a surrogate key: `{{ dbt_utils.generate_surrogate_key(['col1', 'col2']) }} as row_key`.

### File 3: `schema.yml`

```yaml
version: 2

models:
  - name: stg_<SOURCE_NAME>__<table_lower>
    description: "Staged <SOURCE_TABLE> from <SOURCE_NAME> — renamed columns, 1:1 with source"
    columns:
      # Every column with a non-empty description
      # PK: unique + not_null
      # Low-cardinality: accepted_values
```

---

## Step 3 — Intermediate Model (only if justified)

Generate an intermediate model ONLY IF at least one of these conditions is true:
- Multiple tables need joining before aggregation
- Window functions or running totals are needed
- VARIANT / ARRAY columns need LATERAL FLATTEN
- Significant deduplication or business-rule filtering is required

If NONE of these apply, **skip this step** and say:
> "No intermediate model needed — the staging model feeds directly to the mart."

If justified, create `models/intermediate/<SOURCE_NAME>/int_<SOURCE_NAME>__<description>.sql`:

```sql
{{ config(materialized='view', tags=['intermediate']) }}

with staged as (
    select * from {{ ref('stg_<SOURCE_NAME>__<table_lower>') }}
),

enriched as (
    select
        -- Business logic, joins, window functions
    from staged
)

select * from enriched
```

Add `schema.yml` with description and PK tests.

---

## Step 4 — Mart Models (fact and/or dimension)

Generate marts ONLY if they add value beyond the staging model. Justify each with the grain.

### Fact model: `models/marts/<SOURCE_NAME>/fct_<entity>.sql`

```sql
{{ config(
    materialized='table',
    tags=['marts'],
    cluster_by=['<date_column>']
) }}

with source as (
    select * from {{ ref('stg_<SOURCE_NAME>__<table_lower>') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['<pk_columns>']) }} as <entity>_id,
        -- All columns listed explicitly — NO SELECT *
    from source
)

select * from final
```

### Dimension model (only if clear lookup entities exist): `models/marts/<SOURCE_NAME>/dim_<entity>.sql`

Add `schema.yml` with:
- `unique` + `not_null` on surrogate key
- `relationships` tests for FKs
- `dbt_expectations.expect_column_values_to_be_between` on numeric measures

---

## Step 5 — Run dbt build

```bash
dbt build --select "source:<SOURCE_NAME>+"
```

Report:
- Pass/fail count per model
- Any test failures (column, failing row count)
- Compilation errors (exact line + fix)
- Execution time per model

**If any step fails, diagnose and fix before proceeding to Step 6.**

---

## Step 6 — Cortex Analyst Semantic Model (YAML)

> **This step uses the `$cortex-analyst-semantic-model` skill workflow.**
> We generate a Cortex Analyst YAML semantic model (NOT a Snowflake Semantic View DDL).
> The YAML is richer — it includes synonyms, sample_values, verified_queries, and
> custom_instructions for accurate natural language querying via `CORTEX_ANALYST_MESSAGE()`.

For each mart model generated in Step 4, follow these sub-steps:

### 6.1 — Classify columns using Step 1 profile + AI reasoning

| Column Pattern | Classify As | YAML Section |
|---------------|-------------|--------------|
| DATE / TIMESTAMP types | time_dimension | `time_dimensions` |
| VARCHAR low-cardinality (<50 distinct) | dimension | `dimensions` |
| VARCHAR high-cardinality (>50 distinct, e.g. names) | dimension | `dimensions` |
| BOOLEAN | dimension | `dimensions` |
| INT / FLOAT / NUMBER (aggregatable measures) | fact | `facts` |
| Columns named `*_rate`, `*_pct`, `*_ratio` | fact (default_aggregation: avg) | `facts` |
| Columns named `*_count`, `*_total`, `*_amount`, `*_sales` | fact (default_aggregation: sum) | `facts` |
| Surrogate key (`*_id`, `*_key`, `*_sk`) | primary_key / exclude | `primary_key` |
| ETL columns (`*_loaded`, `*_etl`) | exclude | skip |

**Do NOT just apply regex.** Consider the column's actual sample values, cardinality, description
from schema.yml, and how business users would phrase questions about this data.

### 6.2 — Generate synonyms for each column

For every dimension, time_dimension, and fact, generate 2–5 natural language synonyms:
- Column name variations: `ITEM_CATEGORY` → `["category", "product type", "product category"]`
- Domain-specific terms: `MAKER` → `["brand", "manufacturer", "vendor"]`
- Business shorthand: `TOTAL_VIEWS` → `["views", "page views", "impressions"]`

### 6.3 — Get sample values via MCP

For each dimension and time_dimension, query Snowflake:
```sql
SELECT DISTINCT "<COLUMN>"
FROM <DATABASE>.DBT_MARTS.<TABLE>
WHERE "<COLUMN>" IS NOT NULL
ORDER BY 1
LIMIT 5;
```

### 6.4 — Generate and TEST verified queries

Create 3–5 verified queries covering common business question patterns:

| Pattern | Example Question |
|---------|-----------------|
| Summary | "What is the total <metric>?" |
| Time Trend | "Show <metric> by <time_dim> over time" |
| Top-N | "Top 10 <dimension> by <metric>" |
| Dimensional Breakdown | "<metric> by <dimension> and <time_dim>" |
| Filtered | "<metric> for <dimension_value> in <time_range>" |

**CRITICAL:** Run each query via MCP `run_query` / `run_sql` to verify it executes.
If it fails, fix the SQL (double-quote column names in Snowflake). Only include passing queries.

### 6.5 — Write custom_instructions

Write free-text instructions that help Cortex Analyst map natural language to SQL:
- Which column maps to common business terms
- How to handle time filters ("last month" → `DATEADD('month', -1, CURRENT_DATE())`)
- Default ordering for trend queries
- Any gotchas (case sensitivity, null handling)

### 6.6 — Assemble and write the YAML

Write the file to: `cortex-analyst-models/semantic_<SOURCE_NAME>_<entity>.yaml`

```yaml
name: SEM_<ENTITY>
tables:
  - name: FCT_<ENTITY>
    description: |
      <Multi-line description: grain, key features, business context>
    base_table:
      database: <TARGET_DB>        # From profiles.yml target database (e.g., DBT_DEV)
      schema: DBT_MARTS            # Where the mart TABLE lives
      table: FCT_<ENTITY>
    dimensions:
      - name: <COLUMN>
        synonyms: [<syn1>, <syn2>]
        description: <desc>
        expr: <COLUMN>
        data_type: <TYPE>
        sample_values: [<val1>, <val2>]
    time_dimensions:
      - name: <DATE_COLUMN>
        synonyms: [<syn1>]
        description: <desc>
        expr: <DATE_COLUMN>
        data_type: DATE
        sample_values: ["2024-01-01", "2024-06-15"]
    facts:
      - name: <METRIC>
        synonyms: [<syn1>, <syn2>]
        description: <desc>
        expr: <METRIC>
        data_type: NUMBER
        default_aggregation: sum    # or avg, count, min, max
        sample_values: [100, 500]
    primary_key:
      columns: [<pk_col>]
verified_queries:
  - name: <query_name>
    question: "<NL business question>"
    use_as_onboarding_question: true
    sql: "<TESTED SQL with fully qualified table names>"
    verified_by: cortex_code_agent
    verified_at: <unix_timestamp>
custom_instructions: |
  <Free text instructions for text-to-SQL accuracy>
```

**IMPORTANT schema distinction:**
- `base_table.schema` = `DBT_MARTS` (where data lives)
- Upload stage = `SEMANTIC` schema (where YAML files go)

### 6.7 — Upload YAML to Snowflake stage

Use the pure-SQL TEMP TABLE → COPY INTO pattern (works in Cortex Code, no local filesystem needed):

```sql
-- Ensure stage exists
CREATE STAGE IF NOT EXISTS <TARGET_DB>.SEMANTIC.CORTEX_ANALYST_MODELS
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  COMMENT = 'Internal stage for Cortex Analyst YAML semantic models';

-- Upload YAML content via temp table
CREATE OR REPLACE TEMPORARY TABLE <TARGET_DB>.SEMANTIC.TEMP_YAML_CONTENT (LINE_CONTENT VARCHAR)
AS SELECT $$
<ENTIRE YAML CONTENT>
$$;

COPY INTO @<TARGET_DB>.SEMANTIC.CORTEX_ANALYST_MODELS/semantic_<SOURCE_NAME>_<entity>.yaml
  FROM (SELECT LINE_CONTENT FROM <TARGET_DB>.SEMANTIC.TEMP_YAML_CONTENT)
  FILE_FORMAT = (TYPE = 'CSV' COMPRESSION = 'NONE' FIELD_DELIMITER = 'NONE' RECORD_DELIMITER = 'NONE')
  SINGLE = TRUE
  OVERWRITE = TRUE
  HEADER = FALSE;

-- Verify upload
LIST @<TARGET_DB>.SEMANTIC.CORTEX_ANALYST_MODELS PATTERN = '.*semantic_<SOURCE_NAME>.*';

-- Clean up
DROP TABLE IF EXISTS <TARGET_DB>.SEMANTIC.TEMP_YAML_CONTENT;
```

### 6.8 — Test with Cortex Analyst

```sql
SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_MESSAGE(
  '@<TARGET_DB>.SEMANTIC.CORTEX_ANALYST_MODELS/semantic_<SOURCE_NAME>_<entity>.yaml',
  [{'role': 'user', 'content': '<first verified query question>'}]
);
```

If the response is incorrect, refine synonyms, verified_queries, or custom_instructions and re-upload.

### 6.9 — (Optional) Deploy to Snowflake Intelligence

To make the semantic model visible in the Snowflake Intelligence UI:

```sql
CREATE OR REPLACE AGENT <TARGET_DB>.SEMANTIC.AGENT_<ENTITY>
  COMMENT = '<description>'
  FROM SPECIFICATION $$
  {
    "models": {"orchestration": "auto"},
    "tools": [{
      "tool_spec": {
        "type": "cortex_analyst_text_to_sql",
        "name": "analyst",
        "description": "<what data and questions this covers>"
      }
    }],
    "tool_resources": {
      "analyst": {
        "semantic_model_file": "@<TARGET_DB>.SEMANTIC.CORTEX_ANALYST_MODELS/semantic_<SOURCE_NAME>_<entity>.yaml",
        "execution_environment": {"type": "warehouse", "warehouse": "<WAREHOUSE>"}
      }
    }
  }
  $$;

ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT
  ADD AGENT <TARGET_DB>.SEMANTIC.AGENT_<ENTITY>;
```

> For full Phase 9 details (permissions, multi-model agents, verification), reference
> the `$cortex-analyst-semantic-model` skill.

---

## Step 7 — Final Checklist

Verify ALL of these before finishing:

- [ ] `_sources.yml` has `database:` and `schema:` hardcoded (allowed only in _sources.yml)
- [ ] Staging model uses `{{ source('<SOURCE_NAME>', '<SOURCE_TABLE>') }}`
- [ ] All mart/intermediate models use `{{ ref('model_name') }}` — no raw schema references
- [ ] No `SELECT *` in any mart or semantic model
- [ ] No `LIMIT` clause in any production model
- [ ] Every model has a `schema.yml` entry with a non-empty `description`
- [ ] PK column(s) have `unique` + `not_null` tests
- [ ] Surrogate keys use `{{ dbt_utils.generate_surrogate_key([...]) }}`
- [ ] `dbt build` passed with 0 test failures
- [ ] Cortex Analyst YAML written to `cortex-analyst-models/semantic_<SOURCE_NAME>_<entity>.yaml`
- [ ] YAML includes synonyms, sample_values, verified_queries, and custom_instructions
- [ ] All verified_queries tested and passing against Snowflake
- [ ] YAML uploaded to `@<TARGET_DB>.SEMANTIC.CORTEX_ANALYST_MODELS/` stage
- [ ] `CORTEX_ANALYST_MESSAGE()` test returned correct answer

---

## Example Invocation

```
$onboard-new-source

Database: AMAZON_AND_ECOMMERCE_WEBSITES_PRODUCT_VIEWS_AND_PURCHASES
Schema: DATAFEEDS
Table: PRODUCT_VIEWS_AND_PURCHASES
Source name: datafeeds
```

The agent will execute all 7 steps autonomously — profiling data, generating code, building, and creating the semantic view.
