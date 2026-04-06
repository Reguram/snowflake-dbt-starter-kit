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

Extract the Snowflake coordinates. **IMPORTANT — two schemas are involved:**
- **Database**: from `profiles.yml` → target `database` (e.g., `DBT_DEV`). Do **NOT** use `dbt_project.yml` vars `source_database` — that is the raw source database (e.g., `COVID19_EPIDEMIOLOGICAL_DATA`), not where dbt materializes models.
- **Data schema** (`base_table`): `DBT_MARTS` — where mart tables physically live. Used in `base_table.schema` and verified query SQL.
- **Semantic schema** (stage): `SEMANTIC` — where YAML files are uploaded. The stage `CORTEX_ANALYST_MODELS` lives here.
- **Table name**: the mart model name in UPPERCASE (e.g., `fct_sales` → `FCT_SALES`)

> **Do NOT confuse these two schemas.** The YAML `base_table.schema` must be `DBT_MARTS`
> (where the data is). The upload stage must be `@<DB>.SEMANTIC.CORTEX_ANALYST_MODELS`.

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
      database: DBT_DEV                # Snowflake database
      schema: DBT_MARTS                # Where the mart TABLE lives (NOT SEMANTIC)
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

> **IMPORTANT:** The upload stage is in the `SEMANTIC` schema — NOT `DBT_MARTS`.
> `base_table.schema` = `DBT_MARTS` (data), stage = `SEMANTIC` (YAML files).

#### Step 8.1: Ensure Stage Exists

```sql
CREATE STAGE IF NOT EXISTS <DATABASE>.SEMANTIC.CORTEX_ANALYST_MODELS
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  COMMENT = 'Internal stage for Cortex Analyst YAML semantic models';
```

#### Step 8.2: Upload YAML to Stage (Pure SQL — Cortex Code Compatible)

Use the **TEMP TABLE → COPY INTO** pattern. This is pure SQL with zero dependencies —
works in Cortex Code, Snowsight, or any SQL client. No Python, no PUT, no local filesystem.

Generate the upload SQL by embedding the entire YAML from Phase 7 into a `$$` dollar-quoted
string inside a temporary table, then COPY INTO the stage:

```sql
-- Create temp table with the YAML content as a single row
CREATE OR REPLACE TEMPORARY TABLE <DATABASE>.SEMANTIC.TEMP_YAML_CONTENT (LINE_CONTENT VARCHAR)
AS SELECT $$
<ENTIRE YAML CONTENT FROM PHASE 7>
$$;

-- Copy to stage as a single uncompressed file
COPY INTO @<DATABASE>.SEMANTIC.CORTEX_ANALYST_MODELS/<filename>.yaml
  FROM (SELECT LINE_CONTENT FROM <DATABASE>.SEMANTIC.TEMP_YAML_CONTENT)
  FILE_FORMAT = (TYPE = 'CSV' COMPRESSION = 'NONE' FIELD_DELIMITER = 'NONE' RECORD_DELIMITER = 'NONE')
  SINGLE = TRUE
  OVERWRITE = TRUE
  HEADER = FALSE;

-- Clean up
DROP TABLE IF EXISTS <DATABASE>.SEMANTIC.TEMP_YAML_CONTENT;
```

**Key settings explained:**
- `COMPRESSION = 'NONE'` — YAML must be uncompressed for Cortex Analyst to read it
- `FIELD_DELIMITER = 'NONE'` / `RECORD_DELIMITER = 'NONE'` — preserves YAML formatting
- `SINGLE = TRUE` — writes one file (not partitioned)
- `OVERWRITE = TRUE` — replaces existing file on re-upload

Verify the upload:
```sql
LIST @<DATABASE>.SEMANTIC.CORTEX_ANALYST_MODELS PATTERN = '.*<filename>.*';
```

#### Step 8.3: Test with Cortex Analyst

```sql
SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_MESSAGE(
  '@<DATABASE>.SEMANTIC.CORTEX_ANALYST_MODELS/<filename>.yaml',
  [{'role': 'user', 'content': '<test question from verified_queries>'}]
);
```

#### Step 8.4: Iterate if Needed

If the response is incorrect, refine the model:
- Add more synonyms for misunderstood terms
- Add more verified queries covering the failing pattern
- Update custom_instructions with explicit rules
- Re-upload using Step 8.2 (OVERWRITE = TRUE replaces the file)

### Phase 9: Deploy to Snowflake Intelligence (Agentic Workflow)

> **This phase makes the semantic model visible in the Snowflake Intelligence UI.**
> Without it, the YAML works only via `CORTEX_ANALYST_MESSAGE()` API — the SI UI
> shows nothing. This is all SQL — executable in Cortex Code or a Snowflake Worksheet.
>
> **The agent dynamically generates all SQL from context — no hardcoded files needed.**

#### Step 9.1: Derive Variables from Context

Read the YAML file produced in Phase 7 (or the existing file in `cortex-analyst-models/`)
and extract these variables automatically:

| Variable | How to Derive |
|----------|---------------|
| `DATABASE` | From `profiles.yml` → target `database` (e.g., `DBT_DEV`). Do NOT use `dbt_project.yml` `vars.source_database` — that is the raw source DB, not the dbt target. |
| `SCHEMA` | The schema where agents and stage live — typically `SEMANTIC` |
| `STAGE` | Stage name — typically `CORTEX_ANALYST_MODELS` (from `snowflake_setup.sql`) |
| `YAML_FILENAME` | Name of the YAML file from Phase 7 output (e.g., `semantic_sales_analysis.yaml`) |
| `AGENT_NAME` | Derive from YAML `name` field: `AGENT_` + uppercase domain (e.g., `AGENT_SALES_ANALYSIS`) |
| `AGENT_DESC` | From YAML `description` field — first sentence or a summary |
| `TOOL_DESC` | Compose from YAML tables: list table names, what data they contain, example questions |
| `WAREHOUSE` | From `dbt_project.yml` or `profiles.yml` — the execution warehouse (e.g., `DBT_AGENT_WH`) |
| `ROLE` | From `snowflake_setup.sql` — typically `DBT_ROLE` |
| `MARTS_SCHEMA` | From `dbt_project.yml` → marts custom_schema (e.g., `DBT_MARTS`) |

**Do NOT ask the user for these values.** Derive them from existing project files.

#### Step 9.2: Check for Existing Agent

Before creating, check whether an agent already exists for this domain:

```sql
SHOW AGENTS IN SCHEMA <DATABASE>.<SCHEMA>;
```

- If agent exists with the same name → use `CREATE OR REPLACE` (update)
- If a different agent covers the same tables → warn user about overlap
- If no agent exists → proceed with creation

#### Step 9.3: Generate and Present CREATE AGENT SQL

Generate the concrete SQL with all placeholders resolved:

```sql
CREATE OR REPLACE AGENT <DATABASE>.<SCHEMA>.<AGENT_NAME>
  COMMENT = '<AGENT_DESC>'
  FROM SPECIFICATION $$
  {
    "models": {"orchestration": "auto"},
    "tools": [
      {
        "tool_spec": {
          "type": "cortex_analyst_text_to_sql",
          "name": "analyst",
          "description": "<TOOL_DESC>"
        }
      }
    ],
    "tool_resources": {
      "analyst": {
        "semantic_model_file": "@<DATABASE>.<SCHEMA>.<STAGE>/<YAML_FILENAME>",
        "execution_environment": {
          "type": "warehouse",
          "warehouse": "<WAREHOUSE>"
        }
      }
    }
  }
  $$;
```

**Multi-model agents:** If the domain has multiple YAML files on stage, add one tool per YAML:
```json
"tools": [
  {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "sales_data", "description": "..."}},
  {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "market_data", "description": "..."}}
],
"tool_resources": {
  "sales_data": {"semantic_model_file": "@stage/sales.yaml", "execution_environment": {...}},
  "market_data": {"semantic_model_file": "@stage/market.yaml", "execution_environment": {...}}
}
```
Best practice: 5-10 tools per agent max. Create separate agents for unrelated domains.

#### Step 9.4: Generate SI Registration SQL

```sql
-- Ensure Snowflake Intelligence object exists (account-level singleton)
SHOW SNOWFLAKE INTELLIGENCES;
-- If empty: CREATE SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;

-- Register the agent
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT
  ADD AGENT <DATABASE>.<SCHEMA>.<AGENT_NAME>;
```

#### Step 9.5: Generate Permission Grants

```sql
GRANT USAGE ON DATABASE <DATABASE> TO ROLE <ROLE>;
GRANT USAGE ON SCHEMA <DATABASE>.<SCHEMA> TO ROLE <ROLE>;
GRANT USAGE ON AGENT <DATABASE>.<SCHEMA>.<AGENT_NAME> TO ROLE <ROLE>;
GRANT USAGE ON WAREHOUSE <WAREHOUSE> TO ROLE <ROLE>;
GRANT READ ON STAGE <DATABASE>.<SCHEMA>.<STAGE> TO ROLE <ROLE>;
GRANT SELECT ON ALL TABLES IN SCHEMA <DATABASE>.<MARTS_SCHEMA> TO ROLE <ROLE>;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE <ROLE>;
```

#### Step 9.6: Present Complete Deployment Script

Combine Steps 9.3–9.5 into a single executable SQL script and present it to the user.
The user copies this script into Cortex Code or a Snowflake Worksheet and executes it.

Include a verification section at the end:
```sql
-- Verify deployment
SHOW AGENTS IN SCHEMA <DATABASE>.<SCHEMA>;
DESCRIBE AGENT <DATABASE>.<SCHEMA>.<AGENT_NAME>;
SHOW SNOWFLAKE INTELLIGENCES;
-- Test: Snowsight → AI & ML → Snowflake Intelligence → select agent → ask a question
```

> **Reference template:** `ddl/cortex-analyst/deploy_agent_to_intelligence.sql`
> contains the generic placeholder version of this SQL for manual use.

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
