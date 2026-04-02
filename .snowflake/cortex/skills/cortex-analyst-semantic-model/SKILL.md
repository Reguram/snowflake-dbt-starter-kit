---
name: cortex-analyst-semantic-model
description: >
  Generate Cortex Analyst YAML semantic model files from dbt mart models. Auto-detects
  dimensions, time_dimensions, and facts from column types and naming patterns. Generates
  synonyms, sample_values, verified_queries, custom_instructions, and relationships.
  Bridges with existing Snowflake Semantic Views for consistency. Output YAML follows
  Snowflake's Cortex Analyst Semantic Model Specification and can be uploaded to a
  Snowflake stage for natural language querying via CORTEX_ANALYST_MESSAGE().
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "2.0"
---

# Cortex Analyst Semantic Model Generator (Agentic Skill)

> **This is an AGENTIC skill.** The AI agent (Copilot, Cortex Code, etc.) performs each
> step itself — exploring Snowflake via MCP tools, running SQL queries to understand the
> data, using AI reasoning to classify columns, and generating a production-ready YAML
> semantic model. The agent does NOT simply call a script; it intelligently creates the
> model through exploration, analysis, and validation.

> For a **deterministic fallback** (no agent reasoning, batch mode), use:
> `python scripts/generate_cortex_analyst_model.py --model <name>`

## Two Cortex Analyst Approaches (Both Coexist)

| Aspect | YAML Semantic Model (this skill) | Snowflake Semantic View |
|--------|----------------------------------|------------------------|
| **Format** | YAML file uploaded to stage | `CREATE SEMANTIC VIEW` DDL |
| **Storage** | `@stage/model.yaml` | Database object |
| **Rich metadata** | synonyms, sample_values, verified_queries, custom_instructions | Dimensions + Metrics only |
| **Query via** | `CORTEX_ANALYST_MESSAGE()` with stage reference | `CORTEX_ANALYST_MESSAGE()` with SV reference |
| **Best for** | Rich NL understanding, multi-table relationships | Simple single-view analytics |
| **Project path** | `cortex-analyst-models/` | `ddl/semantic/` |

## When to Invoke This Skill

- User asks to "create a Cortex Analyst semantic model" or "generate a semantic model YAML"
- User wants to enable natural language querying with rich synonyms and verified queries
- User wants to upload a semantic model to a Snowflake stage for Cortex Analyst
- User references the Cortex Analyst Semantic Model Specification
- User wants to generate verified queries for text-to-SQL accuracy
- User wants to bridge existing Semantic Views with richer YAML metadata
- After creating a new mart model and wanting Cortex Analyst coverage

## Prerequisites

- Snowflake MCP server connected (provides `run_sql` / `run_query` tools)
- Mart model(s) exist in `models/marts/` and have been built (`dbt build --select <model>`)

---

## Agentic Workflow: Step by Step

> **CRITICAL**: You (the agent) must execute each phase yourself. Do NOT delegate to a
> script. Use MCP tools to query Snowflake, read files, and reason about the data.

### Phase 1: Context Gathering

#### Step 1.1: Identify Target Model

Ask the user which mart model to generate a semantic model for. If not specified, scan:
```
models/marts/**/*.sql
```
Look for `fct_*` and `summary_*` models (optionally `dim_*` if the user requests it).

Read the model's SQL to understand:
- What CTEs and joins are used
- What the grain is (what one row represents)
- What `{{ ref() }}` dependencies exist

#### Step 1.2: Read Existing Metadata

Read the model's `schema.yml` in its directory to get:
- Column descriptions (these become YAML `description` fields)
- Existing tests (tells you which columns are PKs via `unique` + `not_null`, FKs via `relationships`, categoricals via `accepted_values`)
- Model description (becomes the table-level description)

Also check for existing Semantic View metadata:
- `ddl/semantic/sem_*.yaml` — if exists for this model, bridge its dimension/metric classifications
- `models/semantic/schema.yml` — check for `snowflake_semantic_view` metadata blocks
- `Sample-semantic-view-cortex-analyst/` — check for existing Cortex Analyst YAML as reference

#### Step 1.3: Determine Snowflake Context

Extract the Snowflake coordinates:
- **Database**: from `dbt_project.yml` vars (`source_database`) or default `DBT_DEV`
- **Schema**: `DBT_MARTS` (configured in `dbt_project.yml` under `+schema: DBT_MARTS`)
- **Table name**: the mart model name in UPPERCASE (e.g., `fct_sales` → `FCT_SALES`)

### Phase 2: Data Exploration via MCP

> **This is what makes this agentic.** You query Snowflake directly to understand the
> data, rather than relying on regex patterns alone.

#### Step 2.1: Profile Column Metadata

Run SQL via MCP to get column types:
```sql
SELECT column_name, data_type, is_nullable
FROM <DATABASE>.information_schema.columns
WHERE table_catalog = '<DATABASE>'
  AND table_schema = '<SCHEMA>'
  AND table_name = '<TABLE>'
ORDER BY ordinal_position;
```

#### Step 2.2: Profile Cardinality and Sample Values

For each column, understand its distribution. Run a single profiling query:
```sql
SELECT
  '<COLUMN>' AS col,
  COUNT(*) AS total_rows,
  COUNT(DISTINCT "<COLUMN>") AS distinct_count,
  COUNT(*) - COUNT("<COLUMN>") AS null_count
FROM <DATABASE>.<SCHEMA>.<TABLE>;
```

Then get sample values for each relevant column:
```sql
SELECT DISTINCT "<COLUMN>"
FROM <DATABASE>.<SCHEMA>.<TABLE>
WHERE "<COLUMN>" IS NOT NULL
LIMIT 5;
```

**Agent reasoning**: Use the cardinality ratio (`distinct_count / total_rows`) to inform classification:
- Ratio < 0.01 → likely categorical dimension (e.g., status, type)
- Ratio ~1.0 → likely unique identifier (PK) or high-cardinality entity
- Between → use column name, type, and actual sample values for judgment

#### Step 2.3: Understand Relationships (Multi-Table)

If the mart model joins multiple tables (detected from reading its SQL in Step 1.1):
1. Identify what columns are used in JOIN conditions
2. Query both tables to confirm the join relationship:
```sql
SELECT COUNT(*) AS left_rows,
       COUNT(DISTINCT l."<JOIN_COL>") AS left_distinct,
       COUNT(DISTINCT r."<JOIN_COL>") AS right_distinct
FROM <LEFT_TABLE> l
LEFT JOIN <RIGHT_TABLE> r ON l."<JOIN_COL>" = r."<JOIN_COL>";
```
3. Determine relationship type: `many_to_one` or `one_to_one`

### Phase 3: Intelligent Column Classification

> **This is where AI reasoning matters.** Don't just apply regex — consider the
> column's actual data, its cardinality, its description from schema.yml, and how
> business users would want to query it.

#### Classification Guidelines

**Time Dimensions** (`time_dimensions` in YAML):
- DATE or TIMESTAMP data types → always time_dimension
- Columns named `*_date`, `*_at`, `*_timestamp`, `*_period`
- These are the axes for trend analysis and time-based filtering

**Dimensions** (`dimensions` in YAML):
- VARCHAR/TEXT columns with **low cardinality** (< 50 distinct values, or < 1% of total rows)
- BOOLEAN columns (True/False categorical)
- Columns named `*_status`, `*_type`, `*_category`, `*_segment`, `*_flag`, `*_level`
- Entity columns: `*_name`, `*_region`, `*_country`, `*_state`, `*_brand`, `*_maker`
- Geographic codes: `*_code`, `*_fips`, `*_iso*`
- These are what users filter/group by in natural language queries

**Facts** (`facts` in YAML):
- Numeric columns (NUMBER, FLOAT, DECIMAL) that represent aggregatable measures
- Columns named `*_sales`, `*_revenue`, `*_amount`, `*_cost`, `*_count`, `*_quantity`
- Default aggregation:
  - SUM for amounts, totals, counts, quantities
  - AVG for rates, averages, percentages, ratios
  - MAX for peaks, maximums
  - COUNT for entity counts

**Skip** (do not include):
- Surrogate keys: `*_key` (hash-based), `*_sk`
- ETL columns: `*_loaded`, `*_etl`, `*_batch`
- Internal/system columns

**Agent judgment calls:**
- A column like `maker` may have moderate cardinality — check sample values to decide if it's
  a useful dimension (brand names → yes) or high-cardinality noise (→ skip)
- A column like `year_period` is a NUMBER but represents time → classify as dimension, not fact
- When in doubt, include as dimension — users can always filter/group by it

### Phase 4: Generate Synonyms

For each column, generate 2-5 natural language synonyms that business users might use:

**Agent approach:**
1. Consider the column name: `ITEM_CATEGORY` → "category", "product type", "product category"
2. Consider the domain context: in e-commerce, `MAKER` → "brand", "manufacturer", "vendor"
3. Consider the column description from schema.yml
4. Consider sample values for context

**Important:** Synonyms are critical for Cortex Analyst accuracy. A user might ask
"What were sales by brand?" when the column is called `MAKER`.

### Phase 5: Generate and Test Verified Queries

> **This is the highest-value agentic step.** The agent generates SQL queries that
> represent real business questions, then TESTS them against Snowflake via MCP.

Create 3-5 verified queries. Each must:
1. Answer a common business question about this data
2. Use fully qualified table names (`DATABASE.SCHEMA.TABLE`)
3. Execute successfully against Snowflake (test via MCP `run_sql`)
4. Return meaningful results

**Query patterns to generate:**

| Pattern | Example Question | SQL Pattern |
|---------|-----------------|-------------|
| Summary | "What is the overall total?" | `SELECT SUM(metric) FROM table` |
| Time Trend | "Show the trend over time" | `SELECT date, SUM(metric) FROM table GROUP BY date ORDER BY date` |
| Top-N | "Top categories by revenue" | `SELECT dim, SUM(metric) FROM table GROUP BY dim ORDER BY 2 DESC LIMIT 10` |
| Dimensional Breakdown | "Sales by category over time" | `SELECT date, dim, SUM(metric) GROUP BY 1,2` |
| Recent Snapshot | "What is the latest data?" | `SELECT * FROM table ORDER BY date DESC LIMIT 5` |

**For each query:**
1. Write the SQL based on your understanding of the data
2. Run it via MCP to verify it executes successfully
3. If it fails, fix the SQL and retry (note: column names must be double-quoted in Snowflake)
4. Record the working SQL in the `verified_queries` section

### Phase 6: Generate Custom Instructions

Write free-text instructions that help Cortex Analyst generate accurate SQL:

**Include:**
- Which column to use for common business terms (e.g., "revenue" → `SUM(TOTAL_SALES)`)
- How to handle time filters (e.g., "last month" → `DATEADD('month', -1, CURRENT_DATE())`)
- Case sensitivity rules if applicable
- Join instructions (if multi-table)
- Default ordering (e.g., "always order by date DESC for trend queries")
- Column-name-to-business-term mapping for ambiguous cases

### Phase 7: Assemble and Write the YAML

Build the complete YAML file following the Cortex Analyst Semantic Model Specification.
Full spec reference: `.agents/skills/cortex-analyst-semantic-model/references/cortex_analyst_yaml_spec.md`
Example model: `.agents/skills/cortex-analyst-semantic-model/references/example_semantic_model.yaml`

Write it to: `cortex-analyst-models/semantic_<name>.yaml`

**YAML structure:**
```yaml
name: SEM_<NAME>
tables:
  - name: <TABLE_NAME>
    description: |
      <Multi-line description including grain, key features, business context>
    base_table:
      database: <DATABASE>
      schema: <SCHEMA>
      table: <TABLE>
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
        sample_values: [<val1>]
    facts:
      - name: <METRIC>
        synonyms: [<syn1>, <syn2>]
        description: <desc>
        expr: <METRIC>
        data_type: <TYPE>
        default_aggregation: <sum|avg|count|min|max>
        sample_values: [<val1>]
    primary_key:
      columns: [<pk_col1>, <pk_col2>]
relationships:       # Only for multi-table models
  - name: <rel_name>
    join_type: <left_outer|inner>
    relationship_type: <many_to_one|one_to_one>
    left_table: <LEFT>
    right_table: <RIGHT>
    relationship_columns:
      - left_column: <COL>
        right_column: <COL>
verified_queries:
  - name: <query_name>
    question: <NL question>
    use_as_onboarding_question: true
    sql: <TESTED SQL>
    verified_by: <agent_name>
    verified_at: <unix_timestamp>
custom_instructions: |
  <Free text instructions for text-to-SQL accuracy>
```

### Phase 8: Upload and Test

1. Upload to Snowflake stage via MCP:
```sql
CREATE STAGE IF NOT EXISTS <DB>.SEMANTIC.CORTEX_ANALYST_MODELS
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');
```

Then use the upload script for the PUT command:
```bash
python scripts/upload_semantic_model_to_stage.py --file semantic_<name>.yaml
```

Or instruct the user to run the PUT command in Snowsight:
```sql
PUT file://cortex-analyst-models/<filename>.yaml
  @<DB>.SEMANTIC.CORTEX_ANALYST_MODELS
  AUTO_COMPRESS = FALSE OVERWRITE = TRUE;
```

2. Test with a natural language question via MCP:
```sql
SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_MESSAGE(
  '@<DB>.SEMANTIC.CORTEX_ANALYST_MODELS/<filename>.yaml',
  [{'role': 'user', 'content': '<test question from verified_queries>'}]
);
```

3. If the response is incorrect, refine the model:
   - Add more synonyms for misunderstood terms
   - Add more verified queries covering the failing pattern
   - Update custom_instructions with explicit rules

---

## Deterministic Fallback (Batch / Offline)

If MCP tools are unavailable, or for batch processing of many models, use the script:

```bash
# Single model
python scripts/generate_cortex_analyst_model.py --model fct_sales

# Batch all marts
python scripts/generate_cortex_analyst_model.py --batch

# Dry run
python scripts/generate_cortex_analyst_model.py --model fct_sales --dry-run

# Skip query verification (offline)
python scripts/generate_cortex_analyst_model.py --model fct_sales --skip-verify

# Include dimension tables
python scripts/generate_cortex_analyst_model.py --batch --include-dims

# Upload after generation
python scripts/upload_semantic_model_to_stage.py --all
```

The script uses regex-based classification and static profiling. The agentic workflow above
produces higher-quality models because the agent reasons about column meaning, data context,
and business semantics — generating richer synonyms, better descriptions, and validated
verified queries.

---

## Bridging with Existing Semantic Views

When generating, check for existing metadata to ensure consistency:
1. **`ddl/semantic/sem_*.yaml`** — Reuse dimension/metric classifications
2. **`models/semantic/schema.yml`** — Read `snowflake_semantic_view` metadata blocks
3. **`models/marts/**/schema.yml`** — Use column descriptions
4. **`Sample-semantic-view-cortex-analyst/`** — Reference existing YAML examples for format

Both approaches (Semantic Views + YAML models) coexist — the YAML model adds synonyms,
sample_values, verified_queries, and custom_instructions that Semantic Views don't support.

## Project-Specific Paths

| Path | Purpose |
|------|---------|
| `cortex-analyst-models/` | Generated Cortex Analyst YAML files |
| `scripts/generate_cortex_analyst_model.py` | Deterministic fallback generator |
| `scripts/upload_semantic_model_to_stage.py` | Stage upload script |
| `ddl/semantic/` | Existing Semantic View DDL + YAML (read for bridging) |
| `models/semantic/schema.yml` | Existing Semantic View metadata (read for bridging) |
| `.agents/skills/cortex-analyst-semantic-model/references/` | YAML spec + example model |

## Distinction from Other Skills

| This Skill | `snowflake-semantic-view-creator` | `building-dbt-semantic-layer` | `semantic-view` (bundled) |
|------------|----------------------------------|-------------------------------|--------------------------|
| Cortex Analyst YAML | `CREATE SEMANTIC VIEW` DDL | MetricFlow YAML models | Snowflake SV creation/audit |
| Stage-uploaded | Database object | dbt Cloud engine | Database object |
| Rich NL metadata | Dimensions + Metrics only | Measures + Entities | DDL + optimization |
| `cortex-analyst-models/` | `ddl/semantic/` | `models/semantic/` | Snowflake-native |
| **Agentic** (agent explores data) | Script-based | YAML manual | Script-based |
