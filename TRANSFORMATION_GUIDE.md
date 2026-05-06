# Transformation Template & dbt-one-stop-agent Guide

> A beginner-friendly explanation of how data moves through this project and how the AI agent orchestrator works.

---

## The Big Picture: Medallion Architecture

Think of data flowing through three floors of a building:

```
Raw Snowflake Tables (source)
        ↓
  🥉 STAGING layer      →  Clean & rename columns (views in DBT_STAGING)
        ↓
  🥈 INTERMEDIATE layer →  Join, enrich, business logic (views in DBT_INTERMEDIATE)
        ↓
  🥇 MARTS layer        →  Final analytics-ready tables (tables in DBT_MARTS)
        ↓
  💬 SEMANTIC layer     →  Natural language querying (disabled from dbt build)
```

---

## Layer 1 — Staging (Bronze): The "Clean & Rename" Floor

**Rule: One staging model per raw source table. Touch nothing except renaming columns to snake_case.**

Every staging model is a **trio of three files**:

| File | Purpose |
|------|---------|
| `stg_<source>__<table>.sql` | The actual SQL that runs |
| `schema.yml` | Column descriptions + data quality tests |
| `stg_<source>__<table>.md` | Transformation spec — source of truth for what changes |

### The `.md` file is the blueprint

It tells you:
- Which columns are **transformed** (listed in the Transformations table)
- Which columns are **excluded** (listed separately)
- Which columns are passed through **as-is** (everything else)

**You author transforms in plain English**, not SQL. For each transformed
column, write the *Output column*, *Type*, *Source column(s)*, and a
*Description* such as *"safely cast to a date"*, *"trim whitespace"*, or
*"total sales divided by total volume"*. The agent translates the
description into a Snowflake SQL expression when it generates the `.sql`
and writes the resolved expression back into the *Resolved SQL* column of
the spec for traceability. See
[.agents/skills/onboard-bronze-layer/references/transformations-md-template.md](.agents/skills/onboard-bronze-layer/references/transformations-md-template.md)
for the full vocabulary the agent understands.

**Example:** [stg_covid19_data__apple_mobility.md](models/staging/covid19_data/stg_covid19_data__apple_mobility.md) shows all columns pass through as-is with a simple lowercase rename.

### The SQL pattern (always the same structure)

```sql
-- Step 1: pull raw data using {{ source() }} — never hard-code DB/schema names
with source as (
    select * from {{ source('covid19_data', 'APPLE_MOBILITY') }}
),

-- Step 2: rename columns to snake_case, apply any transforms listed in the .md
staged as (
    select
        country_region,    -- was COUNTRY_REGION in Snowflake
        province_state,
        date,
        transportation_type,
        difference,
        iso3166_1,
        iso3166_2,
        last_updated_date,
        last_reported_flag
    from source
)

-- Step 3: expose the staged CTE
select * from staged
```

### Naming convention

`stg_<source_name>__<table_name>` — note the **double underscore** separating source from table.

- ✅ `stg_covid19_data__apple_mobility`
- ✅ `stg_japan_ecomm_data__transactions`
- ❌ `stg_covid19_apple_mobility` (missing double underscore)

---

## Layer 2 — Intermediate (Silver): The "Business Logic" Floor

**Rule: Only create this layer when you need joins, unions, deduplication, type conversions, or cleansing.**

Intermediate models reference other models using `{{ ref() }}`:

```sql
-- int_enriched_transactions.sql
with source_data as (
    -- ref() links to another dbt model — dbt tracks the dependency automatically
    select * from {{ ref('int_cleaned_transactions') }}
),
enriched_data as (
    select
        *,
        -- Add a derived column: how old is the item at time of sale?
        DATEDIFF('year', RELEASE_DATE, SALES_DATE) AS ITEM_AGE,
        -- Add a business category using a CASE expression
        CASE
            WHEN ITEM_NAME LIKE '%iPhone%' THEN 'Smartphone'
            ELSE 'Other'
        END AS ITEM_CATEGORY
    from source_data
)
select * from enriched_data
```

**Naming convention:** `int_<description>` (e.g., `int_enriched_transactions`, `int_orders_enriched`)

**When to create an intermediate model:**
- Joining two or more staging models together
- Unioning multiple feeds into one dataset
- Deduplicating rows
- Applying business rules (`CASE WHEN`, code-to-label mappings)
- Type conversions (`TRY_TO_NUMBER`, `TRY_TO_DATE`)
- Cleansing (`TRIM`, `NULL_IF`, `COALESCE`)

---

## Layer 3 — Marts (Gold): The "Serve to Analysts" Floor

**Rule: Final tables that analysts query. Never use `SELECT *`. Always list columns explicitly. Always add a surrogate key.**

```sql
-- fct_cdc_reported_patient_impact.sql
with source as (
    -- Always reference staging (or intermediate) via {{ ref() }}
    select * from {{ ref('stg_covid19_data__cdc_reported_patient_impact') }}
)
select
    -- Surrogate key = a unique hash ID generated from one or more columns
    {{ dbt_utils.generate_surrogate_key(['hospital_onset_covid']) }} as "cdc_reported_patient_impact_id",
    state,
    inpatient_beds,
    inpatient_beds_used,
    inpatient_beds_used_covid,
    -- ... all columns listed explicitly
from source
```

**Naming conventions:**
- `fct_<entity>` for fact tables (e.g., `fct_orders`, `fct_cdc_reported_patient_impact`)
- `dim_<entity>` for dimension tables (e.g., `dim_customers`, `dim_products`)

---

## How `dbt_project.yml` Wires Everything Together

```yaml
models:
  snowflake_dbt_starter_kit:
    staging:
      +materialized: view      # runs as a SQL view — no data stored
      +schema: DBT_STAGING     # deploys to this Snowflake schema
    intermediate:
      +materialized: view
      +schema: DBT_INTERMEDIATE
    marts:
      +materialized: table     # actually stores data as a Snowflake table
      +schema: DBT_MARTS
    semantic:
      +materialized: semantic_view
      +schema: SEMANTIC
      +enabled: false          # disabled from dbt build — DDL run directly in Snowflake
```

> **Important:** The custom macro `macros/generate_schema_name.sql` ensures models deploy to exactly `DBT_STAGING` (not `PUBLIC_DBT_STAGING`). Do not remove it.

---

## Key dbt Concepts

| Concept | What it does | Example |
|---------|-------------|---------|
| `{{ source() }}` | References a raw Snowflake table | `{{ source('covid19_data', 'APPLE_MOBILITY') }}` |
| `{{ ref() }}` | References another dbt model | `{{ ref('stg_covid19_data__apple_mobility') }}` |
| `{{ dbt_utils.generate_surrogate_key() }}` | Creates a unique hash key from column(s) | `{{ dbt_utils.generate_surrogate_key(['order_id', 'date']) }}` |
| CTE (`with ... as (...)`) | Organises SQL into readable named steps | See SQL examples above |

---

## How the `dbt-one-stop-agent` Works

Think of it as a **smart receptionist** that never does work itself — it reads your request and routes you to the right specialist skill.

### Step-by-Step Flow

```
You type a natural language request
               ↓
  dbt-one-stop-agent parses your intent
               ↓
  Looks up the "Required Chains" routing table
               ↓
  Reads each matched specialist SKILL.md file
               ↓
  Delegates execution to that specialist
               ↓
  Reports: "Skills used: skill-1, skill-2, ..."
```

### The Routing Table — Intent to Skills

| What you say | Skills invoked (in order) |
|---|---|
| "Build a staging model for this table" | `data-profiling-eda` → `onboard-bronze-layer` |
| "Build an intermediate model joining orders + customers" | `onboard-silver-layer` |
| "Create a fact table for sales" | `onboard-gold-layer` |
| "Build a fact that joins orders + customers + products" | `onboard-silver-layer` → `onboard-gold-layer` |
| "Onboard a new source end-to-end" | `onboard-new-source` → `data-profiling-eda` → `onboard-bronze-layer` → `onboard-silver-layer` → `onboard-gold-layer` → `snowflake-semantic-view-creator` → `cortex-agent` |
| "Create a semantic view for my mart" | `snowflake-semantic-view-creator` |
| "Run `dbt build`" | `running-dbt-commands` |
| "Audit the whole project" | `project-quality-audit` → `semantic-view-coverage-audit` |
| "What were total sales last quarter?" | `answering-natural-language-questions-with-dbt` |
| "Visualise the dbt DAG" | `creating-mermaid-dbt-dag` |
| "Classify PII columns" | `data-governance` |
| "Show Snowflake costs by warehouse" | `cost-intelligence` |

### How to Invoke the Agent

**Option 1 — In Copilot Chat (VS Code)**

Just type naturally. The agent auto-activates when editing any `models/**/*.sql` or `models/**/*.yml` file. Examples:

- *"Build a staging model for the ORDERS table in MY_DB.MY_SCHEMA"*
- *"Create a fact table for sales from the staging models"*
- *"Run dbt build and show me the results"*

**Option 2 — Use the reusable prompts**

Defined in `.github/`, these are click-to-run shortcuts:

| Prompt | What it does |
|--------|-------------|
| `validate-and-build` | Compile, build, and validate a model |
| `review-model` | Full code review against project conventions |
| `audit-project` | Full quality scan (missing tests, descriptions, SELECT * violations) |
| `suggest-semantic-view` | Analyse a mart and generate a Snowflake Semantic View |

**Option 3 — Reference the custom Copilot agent**

```
@dbt-semantic-advisor  <your question about semantic views>
```

### The Silver-Layer Rule (Automatic!)

The agent has a built-in rule: if your request contains any of these signals, it **automatically** inserts the intermediate (`onboard-silver-layer`) step — you don't need to ask for it:

| Signal type | Examples |
|-------------|---------|
| Multiple tables | referencing more than one source/staging model |
| Join/union words | `join`, `combine`, `merge`, `union`, `stack`, `enrich`, `dedup` |
| Cleansing operations | `trim`, `null_if`, `coalesce`, `case when`, code-to-label mapping |
| Type conversions | `try_to_number`, `try_to_date`, boolean coding, VARIANT extraction |
| EDA red flags | high nulls, sentinel values, future dates, negative amounts |

### Where Skill Files Live

```
.agents/skills/<skill-name>/SKILL.md          ← primary location
.snowflake/cortex/skills/<skill-name>/SKILL.md ← fallback location
```

The agent always reads the SKILL.md **before** acting — it never generates code from memory alone.

---

## Quick Reference Cheatsheet

### File Naming

| Layer | Prefix | Example |
|-------|--------|---------|
| Staging | `stg_<source>__<table>` | `stg_covid19_data__apple_mobility` |
| Intermediate | `int_<description>` | `int_enriched_transactions` |
| Fact (Mart) | `fct_<entity>` | `fct_orders` |
| Dimension (Mart) | `dim_<entity>` | `dim_customers` |
| Semantic | `sem_<analysis>` | `sem_revenue_analysis` |

### Common dbt Commands

```bash
dbt deps                              # install packages
dbt debug                             # test Snowflake connection
dbt build                             # build all models + run all tests
dbt build --select <model_name>       # build one model + its tests
dbt compile --select <model_name>     # preview compiled SQL without running
dbt test --select <model_name>        # run tests only
dbt run --select <model_name>         # run model only (no tests)
```

### Snowflake Schemas After Build

| dbt Layer | Snowflake Schema |
|-----------|-----------------|
| Staging | `DBT_STAGING` |
| Intermediate | `DBT_INTERMEDIATE` |
| Marts | `DBT_MARTS` |
| Semantic | `SEMANTIC` |

---

## One-Line Summaries

- **Staging** — rename raw columns to snake_case, one-to-one with the source table, always a view.
- **Intermediate** — business logic (joins, cleansing, enrichment), only created when needed.
- **Marts** — final analytics tables, explicit column lists, surrogate keys, materialised as tables.
- **dbt-one-stop-agent** — a routing layer that reads your intent, picks the right specialist skill, and delegates — it never generates code itself.
