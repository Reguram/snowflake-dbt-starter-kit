# Snowflake dbt Starter Kit + Cortex vs Claude Evaluation

Production-ready dbt project for Snowflake with a **Snowflake Managed MCP Server** (+ local fallback) and a structured evaluation framework comparing Snowflake Cortex Code against Claude Code/Copilot CLI.

---

## Table of Contents

1. [What Is This Project?](#what-is-this-project)
2. [Prerequisites](#prerequisites)
3. [Quick Start (Automated)](#quick-start-automated)
4. [Step-by-Step Setup Guide](#step-by-step-setup-guide)
   - [Step 1: Clone the Repository](#step-1-clone-the-repository)
   - [Step 2: Set Up Python Environment](#step-2-set-up-python-environment)
   - [Step 3: Create Your Snowflake Objects](#step-3-create-your-snowflake-objects)
   - [Step 4: Configure dbt Connection](#step-4-configure-dbt-connection)
   - [Step 5: Install dbt Packages](#step-5-install-dbt-packages)
   - [Step 6: Validate Your Setup](#step-6-validate-your-setup)
   - [Step 7: Run Your First dbt Build](#step-7-run-your-first-dbt-build)
   - [Step 8: Set Up the MCP Server](#step-8-set-up-the-mcp-server)
   - [Step 9: Deploy Streamlit App (Optional)](#step-9-deploy-streamlit-app-optional)
   - [Step 10: Run the Evaluation](#step-10-run-the-evaluation-optional)
5. [How Model Generation Works](#how-model-generation-works)
6. [Project Structure](#project-structure)
7. [Models Overview](#models-overview)
8. [MCP Server (Tools for AI Agents)](#mcp-server-tools-for-ai-agents)
9. [AI Agent Skills & Copilot Integration](#ai-agent-skills--copilot-integration)
   - [dbt Agent Skills (Upstream)](#dbt-agent-skills-upstream)
   - [VS Code Active Skills (Auto-Activation)](#vs-code-active-skills-auto-activation)
   - [Snowflake Semantic View Creator (Custom Skill)](#snowflake-semantic-view-creator-custom-skill)
   - [Three Semantic Approaches](#three-semantic-approaches)
   - [Cortex Analyst Semantic Model Generator (Agentic)](#cortex-analyst-semantic-model-generator-agentic)
   - [Reusable Copilot Prompts](#reusable-copilot-prompts)
   - [Custom Copilot Agent](#custom-copilot-agent)
   - [Semantic View Generator Script](#semantic-view-generator-script)
10. [Medallion Architecture Agent](#medallion-architecture-agent)
11. [Evaluation Framework](#evaluation-framework)
12. [Troubleshooting](#troubleshooting)

---

## What Is This Project?

This is a **dbt (data build tool)** project that transforms raw Snowflake data into clean, analytics-ready tables. On top of that, it includes:

- **Auto-Discovery & Generation**: A Python script that connects to any Snowflake database, discovers tables, profiles column data, and generates all dbt models (staging + marts) automatically — no AI agent involved.
- **MCP Server**: AI agent tools that Claude/Copilot can use to generate dbt models, review SQL, check data quality, and more — running natively inside Snowflake as a Managed MCP Server.
- **Streamlit App**: A chat-based dashboard running inside Snowflake with Cortex AI.
- **Evaluation Framework**: 8 structured tasks to compare Cortex Code vs Claude Code vs Copilot CLI.

**If you're new to dbt**, here's the mental model:
- **Sources** = your raw data tables (any Snowflake database/schema you point it to)
- **Staging models** = clean/rename those raw tables (1:1 mapping)
- **Intermediate models** = join and transform staging models
- **Mart models** = final tables your analysts/dashboards query (facts + dimensions + summaries)
- **Semantic models** = metadata layer enabling natural-language queries via Cortex Analyst

---

## Prerequisites

Before starting, make sure you have:

| Requirement | How to Get It |
|------------|---------------|
| **Snowflake Account** | [Sign up for free trial](https://signup.snowflake.com/) — includes $400 credit |
| **Python 3.9+** | [Download Python](https://www.python.org/downloads/) or use `brew install python` on macOS |
| **pip** | Comes with Python. Verify: `pip --version` |
| **Git** | [Download Git](https://git-scm.com/downloads) or `brew install git` |
| **VS Code** (recommended) | [Download VS Code](https://code.visualstudio.com/) |
| **VS Code Copilot Extension** (for MCP) | Install from VS Code marketplace |

---

## Quick Start (Automated)

If you want to skip the manual steps below, use the **one-command bootstrap**:

```bash
chmod +x scripts/bootstrap.sh
./scripts/bootstrap.sh
```

This interactively walks you through Steps 1–7: creates a Python venv, installs dbt, prompts for your Snowflake credentials and source database/schema, auto-discovers your tables, generates all dbt models, configures `~/.dbt/profiles.yml`, and runs the full `dbt build`.

### Automatic Source Discovery

The bootstrap script works with **any Snowflake database/schema** as a source — including Snowflake Marketplace shared datasets. When prompted, enter your source database and schema names. The script automatically:
- Discovers all tables and columns via `DESCRIBE TABLE` (more reliable than `INFORMATION_SCHEMA` for shared datasets)
- Verifies primary key uniqueness against actual data using `COUNT(DISTINCT ...)`
- Profiles every column for cardinality (distinct count, null count) to classify dimensions vs. measures
- Generates source-named subdirectories: `models/staging/<source_name>/` and `models/marts/<source_name>/`
- Generates `_sources.yml`, staging models, `schema.yml` with tests, fact tables, and summary mart aggregations
- Handles mixed-case columns, numeric-prefixed table names, and special characters in column names
- Cleans up stale mart files from any previous generation
- Builds only the new source: `dbt build --select "source:<source_name>+"`

You can also run the discovery script standalone:

```bash
# Interactive mode
python scripts/discover_and_generate.py

# CLI mode
python scripts/discover_and_generate.py \
  --source-database MY_DB \
  --source-schema MY_SCHEMA \
  --source-name my_source

# Regenerate an existing source (overwrites)
python scripts/discover_and_generate.py \
  --source-database MY_DB \
  --source-schema MY_SCHEMA \
  --source-name my_source \
  --overwrite

# Preview without writing files
python scripts/discover_and_generate.py \
  --source-database MY_DB \
  --source-schema MY_SCHEMA \
  --dry-run
```

### Selective Builds

Each source is self-contained with its own `_sources.yml` (hardcoded database/schema). You can build a single source without affecting others:

```bash
# Build only one source and all its downstream models
dbt build --select "source:free_company_data+"

# Build everything
dbt build
```

> **Using Copilot/Claude?** Just say: *"Set up this dbt project for me"* — the agent skill in `.github/skills/project-setup.instructions.md` will guide the process automatically.

If you prefer to understand each step, follow the manual guide below.

---

## Step-by-Step Setup Guide

### Step 1: Clone the Repository

```bash
git clone <repo-url>
cd snowflake-dbt-starter-kit
```

### Step 2: Set Up Python Environment

Create a virtual environment to keep dependencies isolated:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Install dbt for Snowflake
pip install dbt-snowflake

# Install MCP SDK (for local fallback server)
pip install mcp
```

**Verify installation:**
```bash
dbt --version
# Should show dbt-core 1.x.x and dbt-snowflake 1.x.x
```

### Step 3: Create Your Snowflake Objects

Log into your Snowflake account (via the Snowflake web UI / Snowsight) and run these SQL commands. You can run them in a **Worksheet** — just copy-paste each block:

```sql
-- 3a. Create a database for dbt output
CREATE DATABASE IF NOT EXISTS DBT_DEV;
CREATE SCHEMA IF NOT EXISTS DBT_DEV.DBT_STAGING;
CREATE SCHEMA IF NOT EXISTS DBT_DEV.DBT_INTERMEDIATE;
CREATE SCHEMA IF NOT EXISTS DBT_DEV.DBT_MARTS;
CREATE SCHEMA IF NOT EXISTS DBT_DEV.SEMANTIC;
CREATE SCHEMA IF NOT EXISTS DBT_DEV.SNAPSHOTS;

-- 3b. Create a warehouse (XS is fine for development — $0.0003/second)
CREATE WAREHOUSE IF NOT EXISTS DBT_AGENT_WH
  WAREHOUSE_SIZE = 'X-SMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

-- 3c. Create a role for dbt (with full database permissions)
CREATE ROLE IF NOT EXISTS DBT_ROLE;
GRANT ALL PRIVILEGES ON DATABASE DBT_DEV TO ROLE DBT_ROLE;
GRANT ALL PRIVILEGES ON ALL SCHEMAS IN DATABASE DBT_DEV TO ROLE DBT_ROLE;
GRANT ALL PRIVILEGES ON FUTURE SCHEMAS IN DATABASE DBT_DEV TO ROLE DBT_ROLE;
GRANT USAGE ON WAREHOUSE DBT_AGENT_WH TO ROLE DBT_ROLE;

-- Source data (read-only access) — replace with your actual source database
-- For Marketplace shared databases, use IMPORTED PRIVILEGES:
GRANT IMPORTED PRIVILEGES ON DATABASE <YOUR_SOURCE_DATABASE> TO ROLE DBT_ROLE;
-- For regular databases, use USAGE + SELECT:
-- GRANT USAGE ON DATABASE <YOUR_SOURCE_DATABASE> TO ROLE DBT_ROLE;
-- GRANT USAGE ON SCHEMA <YOUR_SOURCE_DATABASE>.<YOUR_SOURCE_SCHEMA> TO ROLE DBT_ROLE;
-- GRANT SELECT ON ALL TABLES IN SCHEMA <YOUR_SOURCE_DATABASE>.<YOUR_SOURCE_SCHEMA> TO ROLE DBT_ROLE;

-- 3d. Assign the role to your user (replace YOUR_USERNAME)
GRANT ROLE DBT_ROLE TO USER YOUR_USERNAME;
```

> **Tip**: To find your username, run `SELECT CURRENT_USER();` in Snowsight.

### Step 4: Configure dbt Connection

dbt needs a `profiles.yml` file to know how to connect to Snowflake.

```bash
# Create the .dbt directory (first time only) and copy the template
mkdir -p ~/.dbt
cp profiles.yml.template ~/.dbt/profiles.yml
```

Now edit `~/.dbt/profiles.yml` with your Snowflake credentials. You have two options:

**Option A: Direct credentials** (simpler for beginners):
```yaml
snowflake_dbt_starter_kit:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: xy12345.us-east-1     # Your Snowflake account identifier
      user: YOUR_USERNAME             # Your Snowflake username
      password: YOUR_PASSWORD         # Your password
      role: DBT_ROLE
      database: DBT_DEV
      warehouse: DBT_AGENT_WH
      schema: PUBLIC
      threads: 4
```

**Option B: Environment variables** (recommended for security):
```bash
# Add to your shell profile (~/.zshrc or ~/.bashrc):
export SNOWFLAKE_ACCOUNT="xy12345.us-east-1"
export SNOWFLAKE_USER="YOUR_USERNAME"
export SNOWFLAKE_PASSWORD="YOUR_PASSWORD"
export SNOWFLAKE_ROLE="DBT_ROLE"
export SNOWFLAKE_DATABASE="DBT_DEV"
export SNOWFLAKE_WAREHOUSE="DBT_AGENT_WH"
export SNOWFLAKE_SCHEMA="PUBLIC"
```
Then `profiles.yml` uses `"{{ env_var('SNOWFLAKE_ACCOUNT') }}"` etc. (the template already has this).

> **Where to find your account identifier**: In Snowsight, click your name (bottom-left) → Account → copy the locator. Format is typically `ORGNAME-ACCOUNTNAME` or `ACCOUNTLOCATOR.REGION`.

### Step 5: Install dbt Packages

```bash
# From the project root directory:
dbt deps
```

This downloads `dbt_utils` and `dbt_expectations` packages into `dbt_packages/`.

### Step 6: Validate Your Setup

```bash
dbt debug
```

This checks:
- Can dbt find your `profiles.yml`? ✓
- Can it connect to Snowflake? ✓
- Does the database/schema exist? ✓

**You should see `All checks passed!`** If not, see [Troubleshooting](#troubleshooting).

### Step 7: Run Your First dbt Build

Now for the exciting part — building all the models:

```bash
# Seed reference data first
dbt seed

# Build all models + run all tests
dbt build
```

**What just happened?**
1. `dbt seed` loaded `seeds/order_priority_mapping.csv` into a Snowflake table
2. `dbt build` executed in dependency order:
   - Created **staging views** in `DBT_STAGING` (one per source table, with renamed columns)
   - Created **mart tables** in `DBT_MARTS` (fact tables with surrogate keys, summary mart aggregations)
   - Ran all **tests** (unique, not_null on verified primary keys, foreign key relationships)

**Verify in Snowsight:**
```sql
-- Check your new tables
USE DATABASE DBT_DEV;
SELECT TABLE_NAME, ROW_COUNT FROM INFORMATION_SCHEMA.TABLES
  WHERE TABLE_SCHEMA IN ('DBT_STAGING','DBT_INTERMEDIATE','DBT_MARTS','SEMANTIC')
  ORDER BY TABLE_SCHEMA, TABLE_NAME;
```

**Useful dbt commands to know:**
```bash
dbt run                                       # Build models only (no tests)
dbt test                                      # Run tests only
dbt build --select "source:my_source+"        # Build only one source + downstream
dbt run --select staging                      # Build only staging models
dbt run --select fct_orders+                  # Build fct_orders and everything downstream
dbt docs generate && dbt docs serve           # Generate and view documentation
```

### Step 8: Set Up the MCP Server

You have **two options** for the MCP server:

#### Option A: Snowflake Managed MCP Server (Recommended)

This runs the MCP server natively inside Snowflake — no local Python process needed.

1. **Run the setup scripts** in Snowsight, in order:

   ```
   snowflake-dbt-mcp/setup/01_database_objects.sql   -- Database, schema, warehouse, role
   snowflake-dbt-mcp/setup/02_udf_tools.sql          -- UDFs and stored procedures (the tools)
   snowflake-dbt-mcp/setup/03_mcp_server.sql          -- CREATE MCP SERVER statement
   snowflake-dbt-mcp/setup/04_oauth_security.sql       -- OAuth security integration
   snowflake-dbt-mcp/setup/05_grants.sql               -- RBAC permissions
   ```

   > Run each file top-to-bottom in a Snowsight worksheet. They must be run in order.

2. **Get OAuth credentials** (run in Snowsight after `04_oauth_security.sql`):
   ```sql
   CALL SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('DBT_MCP_OAUTH_SNOWFLAKE');
   ```
   Save the `client_id` and `client_secret` — you'll need them for VS Code.

3. **Configure VS Code**: Open `.vscode/mcp.json` and replace `<YOUR_ACCOUNT>` with your Snowflake account identifier:
   ```json
   {
     "servers": {
       "snowflake-dbt-mcp": {
         "type": "streamableHttp",
         "url": "https://xy12345.us-east-1.snowflakecomputing.com/api/v2/databases/DBT_DEV/schemas/MCP_TOOLS/mcp-servers/DBT_AGENT_MCP/sse"
       }
     }
   }
   ```

4. **Restart VS Code** to pick up the MCP server.

5. **Test**: Ask Copilot: *"Use the generate_dbt_model tool to create a staging model for the SUPPLIER table"*

#### Option B: Local MCP Server (Development/Offline)

If you prefer running the MCP server locally (e.g., for offline development):

1. Edit `.vscode/mcp.json` — comment out Option 1 and uncomment Option 2:
   ```json
   {
     "servers": {
       "snowflake-dbt-mcp-local": {
         "type": "stdio",
         "command": "python",
         "args": ["snowflake-dbt-mcp/server.py"],
         "env": {}
       }
     }
   }
   ```

2. Install the MCP SDK: `pip install mcp`

3. Restart VS Code.

### Step 9: Deploy Streamlit App (Optional)

Deploy the chat-based AI dashboard inside Snowflake:

```sql
-- Run in Snowsight (or copy from streamlit/deploy.sql):
CREATE STAGE IF NOT EXISTS DBT_DEV.PUBLIC.STREAMLIT_STAGE;

-- Upload the app file to the stage:
PUT file://streamlit/dbt_agent_app.py @DBT_DEV.PUBLIC.STREAMLIT_STAGE
  AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

-- Create the Streamlit app:
CREATE STREAMLIT IF NOT EXISTS DBT_DEV.PUBLIC.DBT_AGENT_APP
  ROOT_LOCATION = '@DBT_DEV.PUBLIC.STREAMLIT_STAGE'
  MAIN_FILE = 'dbt_agent_app.py'
  QUERY_WAREHOUSE = 'DBT_AGENT_WH';
```

Open it from Snowsight: **Projects → Streamlit → DBT_AGENT_APP**

### Step 10: Run the Evaluation (Optional)

Compare AI coding tools (Cortex Code vs Claude Code vs Copilot CLI) using the 8 standardized tasks:

1. Read [evaluation/README.md](evaluation/README.md) for the rubric
2. Open each task in `evaluation/tasks/` (task_01 through task_08)
3. Run the same prompt in each tool and record outputs
4. Score using [evaluation/results/score_template.json](evaluation/results/score_template.json)
5. Fill in [evaluation/REPORT.md](evaluation/REPORT.md) with your results

---

## How Model Generation Works

All staging and mart SQL files are generated by a **deterministic Python script** — `scripts/discover_and_generate.py` — not by an AI agent. The script connects to Snowflake, queries metadata, profiles actual data, and generates SQL using rule-based heuristics. Here's the full pipeline:

### Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  scripts/discover_and_generate.py                                   │
│                                                                     │
│  1. DISCOVER   ──→  DESCRIBE TABLE on each table in source schema   │
│                     (column names, data types, nullability)          │
│                                                                     │
│  2. VERIFY PKs ──→  COUNT(DISTINCT col) vs COUNT(*)                 │
│                     Only add unique/not_null tests when PK verified  │
│                                                                     │
│  3. PROFILE    ──→  COUNT(DISTINCT col), SUM(CASE NULL) per column  │
│                     Classifies: dimensions, measures, dates          │
│                                                                     │
│  4. GENERATE   ──→  Staging SQL + _sources.yml + schema.yml         │
│                     Fact table + Summary marts + mart schema.yml     │
│                                                                     │
│  5. WRITE      ──→  models/staging/<source_name>/                   │
│                     models/marts/<source_name>/                      │
│                     Cleans stale files from previous runs            │
└─────────────────────────────────────────────────────────────────────┘
```

### Step 1: Schema Discovery

The script runs `DESCRIBE TABLE` against each table in the source database/schema (more reliable than `INFORMATION_SCHEMA` for Marketplace shared datasets). Data types are normalized — e.g., `VARCHAR(16777216)` becomes `VARCHAR`, `NUMBER(38,0)` becomes `NUMBER`.

### Step 2: Primary Key Verification

For each table, the script detects a candidate primary key (first column ending in `KEY`, `ID`, or `_PK`), then **verifies it against actual data**:
```sql
SELECT COUNT(*) AS total, COUNT(DISTINCT col) AS distinct_count, COUNT(col) AS non_null_count
FROM source_table
```
Only when `total == distinct == non_null` does the script add `unique` + `not_null` tests. This prevents false test failures.

### Step 3: Column Profiling & Classification

The script queries Snowflake for cardinality of every column:
```sql
SELECT COUNT(*), COUNT(DISTINCT col1), SUM(CASE WHEN col1 IS NULL THEN 1 ELSE 0 END), ...
FROM source_table
```

Using this profile data, columns are classified:

| Classification | Rule | Example |
|---------------|------|---------|
| **Dimension** | String with <500 distinct values or <5% cardinality ratio | `COUNTRY` (250 distinct in 24M rows) |
| **Measure** | Numeric type, not a key column | `PRICE`, `FOUNDED` |
| **Date** | Actual `DATE`/`TIMESTAMP_*` data type | `SALES_DATE` (DATE) |
| **High-cardinality** | Too many distinct values, excluded from dimensions | `NAME`, `URL` |

### Step 4: SQL Generation

**Staging models** (`stg_<source>__<table>.sql`):
- CTE-based: `source` → `renamed` → `select *`
- Columns listed explicitly (no `SELECT *` in the output)
- Single-letter prefixes stripped (e.g., `O_ORDERKEY` → `orderkey`)
- Mixed-case columns quoted with double-quotes (e.g., `"B25001e1"`)
- `_sources.yml` has `quoting: identifier: true` for tables with special names

**Fact table** (`fct_<table>.sql`):
- Picks the "richest" table (most numeric + date columns), or the largest table as fallback
- Adds a surrogate key via `dbt_utils.generate_surrogate_key()`
- Includes `DATE_TRUNC('month', ...)` and `YEAR(...)` columns — only when the column has an actual date/timestamp data type (not just a name containing "date")

**Summary marts** (`summary_<table>.sql`):
- GROUP BY all dimension columns
- `COUNT(*)` as record count
- `SUM()`, `AVG()`, `MIN()`, `MAX()` on each numeric measure
- Date truncations (month/year) only for real date-typed columns

### Step 5: File Output & Cleanup

Files are written to source-named subdirectories:
```
models/staging/<source_name>/
  ├── _sources.yml           # Source definition with hardcoded database/schema
  ├── stg_<source>__<table>.sql   # One per table
  └── schema.yml             # Column descriptions + tests

models/marts/<source_name>/
  ├── fct_<table>.sql        # Fact table from the richest source table
  ├── summary_<table>.sql    # Aggregated summary per table (if dimensions found)
  └── schema.yml             # Mart model descriptions
```

On re-generation (`--overwrite`), stale mart files from previous runs are automatically removed.

### What This Script Does NOT Do

- **No AI/LLM calls** — All generation is deterministic, based on metadata and profile queries
- **No intermediate models** — These are for custom business logic; add them manually in `models/intermediate/`
- **No semantic models** — These require manual dimension/metric definitions; use the MCP server or add manually
- **No cross-source joins** — Each source is self-contained; cross-source marts can be added manually

---

## Project Structure

```
├── scripts/
│   ├── bootstrap.sh              # One-command setup (Steps 1-7 automated)
│   ├── discover_and_generate.py  # Source discovery + model generation (the core script)
│   ├── generate_semantic_view.py # Semantic view scaffold (profile → classify → generate)
│   ├── medallion_agent.py        # CLI agent for silver/gold model design (Cortex-powered)
│   └── snowflake_setup.sql       # Generated Snowflake setup SQL (run in Snowsight)
├── models/
│   ├── staging/<source_name>/    # Source-conformed views (stg_<source>__*)
│   │   ├── _sources.yml          # dbt source definition (hardcoded db/schema)
│   │   ├── stg_<source>__*.sql   # One staging model per table
│   │   └── schema.yml            # Column tests (unique, not_null, relationships)
│   ├── intermediate/             # Business logic joins (int_*) — add manually
│   ├── marts/<source_name>/      # Consumption tables (fct_*, summary_*)
│   │   ├── fct_<table>.sql       # Detail fact table from richest source table
│   │   ├── summary_<table>.sql   # Aggregated summaries per dimension
│   │   └── schema.yml            # Mart model descriptions
│   └── semantic/                 # Semantic View definitions (sem_*) — add manually
├── macros/                       # Reusable Jinja (surrogate keys, dev limits, semantic DDL)
├── tests/                        # Custom singular tests
├── seeds/                        # Reference CSVs
├── snapshots/                    # SCD Type 2 tracking
├── snowflake-dbt-mcp/
│   ├── server.py                 # Local fallback MCP server (6 tools)
│   ├── pyproject.toml
│   └── setup/                    # Snowflake Managed MCP Server setup scripts
│       ├── 01_database_objects.sql
│       ├── 02_udf_tools.sql
│       ├── 03_mcp_server.sql
│       ├── 04_oauth_security.sql
│       └── 05_grants.sql
├── streamlit/                    # Streamlit-in-Snowflake agent app
│   ├── dbt_agent_app.py          # Chat + Model Gen + Quality + Review + Dashboard
│   └── deploy.sql
├── evaluation/                   # Cortex Code vs Claude Code comparison
│   ├── README.md                 # Rubric and methodology
│   ├── REPORT.md                 # Results template
│   ├── tasks/                    # 8 standardized evaluation prompts
│   └── results/                  # Captured outputs + scores
├── .agents/
│   └── skills/                   # dbt-agent-skills (upstream from dbt-labs)
│       ├── using-dbt-for-analytics-engineering/
│       ├── building-dbt-semantic-layer/
│       ├── adding-dbt-unit-test/
│       ├── running-dbt-commands/
│       ├── troubleshooting-dbt-job-errors/
│       ├── configuring-dbt-mcp-server/
│       ├── fetching-dbt-docs/
│       ├── answering-natural-language-questions-with-dbt/
│       ├── creating-mermaid-dbt-dag/
│       ├── migrating-dbt-core-to-fusion/
│       └── migrating-dbt-project-across-platforms/
├── .cortex/
│   └── skills/                   # Same 11 upstream + custom Snowflake SV Creator
│       ├── (11 upstream skills)  # Mirror of .agents/skills/ for Cortex Code
│       └── snowflake-semantic-view-creator/  # Custom skill for Snowflake Semantic Views
├── .github/
│   ├── copilot-instructions.md   # Project conventions for Copilot
│   ├── skills/                   # VS Code auto-activation skills (10 skills)
│   ├── prompts/                  # Reusable Copilot Chat prompts (4 prompts)
│   ├── agents/                   # Custom Copilot agents (@dbt-semantic-advisor)
│   └── workflows/                # CI: dbt build on PRs
└── .vscode/
    └── mcp.json                  # MCP server config (Snowflake managed or local)
```

## Source Data

This project works with **any Snowflake database/schema**, including Snowflake Marketplace shared datasets. The discovery script auto-discovers your source tables and generates all models. You can have **multiple sources** side-by-side — each lives in its own subdirectory under `models/staging/<source_name>/` and `models/marts/<source_name>/` with a hardcoded `database:` and `schema:` in its `_sources.yml`, so sources never conflict.

**Tested with:**
- Snowflake Marketplace: `FREE_COMPANY_DATASET`, `JAPANESE_ECOMMERCE__C2C_SALES_DATA`, `US_OPEN_CENSUS_DATA` (73 tables, 1700+ columns each)
- Any regular Snowflake database with user-created tables

## Models Overview

Models are auto-generated based on your source data:

| Layer | Pattern | Materialization | Generated By | Description |
|-------|---------|-----------------|-------------|-------------|
| Staging | `stg_<source>__<table>` | view | `discover_and_generate.py` | Source-conformed with renamed columns, explicit column listing |
| Mart (fact) | `fct_<table>` | table | `discover_and_generate.py` | Surrogate key + all columns from richest source table, date parts for real date columns |
| Mart (summary) | `summary_<table>` | table | `discover_and_generate.py` | GROUP BY dimensions + COUNT/SUM/AVG/MIN/MAX on measures |
| Intermediate | `int_<description>` | ephemeral | Manual | Business logic transforms (add manually) |
| Semantic | `sem_<analysis>` | view | Manual | Semantic View definitions (add manually) |

## MCP Server (Tools for AI Agents)

The MCP server exposes 11+ tools that Claude/Copilot can use:

| Tool | Description |
|------|-------------|
| `generate_dbt_model` | Scaffold staging SQL + schema.yml from source table metadata |
| `generate_semantic_view_ddl` | Create Semantic View DDL from dimensions + metrics |
| `review_sql` | Static analysis: naming, refs, hard-coded values (score 0-10) |
| `check_data_quality` | Null checks, duplicate detection, row counts |
| `generate_streamlit_app` | Scaffold Streamlit-in-Snowflake dashboard |
| `execute_query` | Run read-only SQL (SELECT, SHOW, DESCRIBE) |
| `revenue_analyst` | Natural language queries via Cortex Analyst + Semantic View |
| `run_sql` | Execute SQL via SYSTEM_EXECUTE_SQL (managed MCP only) |
| `list_medallion_models` | List dbt models by medallion layer |
| `read_model_sql` | Read any model's SQL source code |
| `suggest_silver_model` | Suggest intermediate (silver) layer models |
| `suggest_gold_model` | Suggest marts (gold) layer fact/dimension models |
| `write_medallion_model` | Write a generated model to disk with schema.yml |

**Architecture**:
- **Snowflake Managed** (default): Tools run as UDFs/stored procs inside Snowflake. No local process. OAuth authentication. Endpoint: `https://<account>/api/v2/databases/DBT_DEV/schemas/MCP_TOOLS/mcp-servers/DBT_AGENT_MCP/sse`
- **Local Fallback**: Python stdio server for offline/development. See `server.py`.

## AI Agent Skills & Copilot Integration

This project has a comprehensive AI skill system with three layers:
1. **Upstream dbt-agent-skills** (`.agents/skills/` and `.cortex/skills/`) — Deep dbt expertise from [dbt-labs](https://github.com/dbt-labs/dbt-agent-skills)
2. **VS Code active skills** (`.github/skills/`) — Auto-activate when you open matching files
3. **Custom skills, prompts & agents** — Project-specific Snowflake Semantic View expertise

### dbt Agent Skills (Upstream)

11 skills from [dbt-labs/dbt-agent-skills](https://github.com/dbt-labs/dbt-agent-skills), installed to `.agents/skills/` (for GitHub Copilot) and `.cortex/skills/` (for Cortex Code). These are passive — they activate when Copilot matches your prompt to the skill's description.

| Skill | What It Does | Example Prompt |
|-------|-------------|----------------|
| `using-dbt-for-analytics-engineering` | Build/modify models, DRY principles, `dbt show` validation | *"Create a staging model for the orders table"* |
| `building-dbt-semantic-layer` | dbt Semantic Layer (MetricFlow) — YAML semantic models, metrics | *"Add a MetricFlow semantic model for revenue"* |
| `adding-dbt-unit-test` | Unit testing / TDD patterns for dbt models | *"Write a unit test for the tax calculation in fct_orders"* |
| `running-dbt-commands` | CLI commands with correct flags and selectors | *"How do I build only staging models?"* |
| `troubleshooting-dbt-job-errors` | Diagnose job failures, log analysis | *"My dbt Cloud job failed, help me debug"* |
| `configuring-dbt-mcp-server` | MCP server setup and configuration | *"Set up the dbt MCP server for VS Code"* |
| `fetching-dbt-docs` | Documentation lookup from docs.getdbt.com | *"How do incremental models work in dbt?"* |
| `answering-natural-language-questions-with-dbt` | NL querying via Semantic Layer | *"What were total sales last quarter?"* |
| `creating-mermaid-dbt-dag` | Mermaid DAG visualization | *"Show me the lineage DAG for fct_orders"* |
| `migrating-dbt-core-to-fusion` | Migration to dbt Fusion | *"Help me migrate to dbt Fusion"* |
| `migrating-dbt-project-across-platforms` | Cross-platform migration | *"Migrate this project from Snowflake to Databricks"* |

#### Installing / Updating dbt Agent Skills

Skills are installed via the [Vercel Skills CLI](https://agentskills.io). To reinstall or update:

```bash
# Install for GitHub Copilot (writes to .agents/skills/)
npx skills add dbt-labs/dbt-agent-skills --agent github-copilot --copy -y

# Install for Cortex Code (writes to .cortex/skills/)
npx skills add dbt-labs/dbt-agent-skills --agent cortex --copy -y
```

Each skill contains a `SKILL.md` file with YAML frontmatter (name, description, allowed-tools) and detailed instructions that the AI reads at query time.

### VS Code Active Skills (Auto-Activation)

Skills in `.github/skills/` use `applyTo` glob patterns to **automatically activate** when you open or edit matching files. No prompting required — the AI reads the skill context as soon as the file is active.

> **Important**: Files must use the `.instructions.md` extension for VS Code Copilot auto-activation to work. Plain `.md` files are ignored by the `applyTo` mechanism.

| Skill File | Triggers On | What It Does |
|-----------|------------|-------------|
| `dbt-model-generation.instructions.md` | `models/**/*.sql`, `models/**/*.yml` | Staging/intermediate/mart generation patterns, DRY principles, `dbt show` validation |
| `code-review.instructions.md` | `models/**/*.sql` | SQL review checklist (critical/warning/info severity levels) |
| `data-quality.instructions.md` | `models/**/schema.yml`, `tests/**` | Schema tests, unit tests (TDD), custom singular tests, freshness checks |
| `semantic-view-design.instructions.md` | `models/semantic/**`, `models/marts/**/*.sql`, `models/marts/**/schema.yml` | Snowflake-native Semantic View design, dimension/metric classification, DDL generation |
| `natural-language-queries.instructions.md` | `models/semantic/**`, `models/marts/**/schema.yml` | NL querying via Cortex Analyst + Semantic Views |
| `running-dbt-commands.instructions.md` | `dbt_project.yml`, `profiles.yml*`, `packages.yml` | CLI commands, selectors, flags, cost management |
| `troubleshooting.instructions.md` | `logs/**`, `target/**/*.json` | Error classification, log reading, run result analysis |
| `dbt-docs.instructions.md` | `models/**/schema.yml`, `models/**/_sources.yml` | Documentation patterns, schema.yml structure, doc blocks |
| `project-setup.instructions.md` | `scripts/bootstrap.sh`, `dbt_project.yml`, `profiles.yml` | Project setup, MCP server configuration |
| `streamlit-generation.instructions.md` | `streamlit/**/*.py` | Streamlit-in-Snowflake app patterns |

**Example — auto-activation in action:**
1. Open `models/marts/japan_ecomm_data/fct_sales.sql` in VS Code
2. The `dbt-model-generation`, `code-review`, and `semantic-view-design` skills all auto-activate
3. Ask Copilot: *"Review this model"* — it applies all three skills' knowledge automatically
4. Ask Copilot: *"Create a semantic view for this mart"* — it uses the `semantic-view-design` skill to classify columns and generate DDL

### Snowflake Semantic View Creator (Custom Skill)

A custom skill at `.cortex/skills/snowflake-semantic-view-creator/` for creating Snowflake-native `CREATE SEMANTIC VIEW` DDL. This is distinct from the upstream `building-dbt-semantic-layer` (MetricFlow) skill.

**Contents:**
```
.cortex/skills/snowflake-semantic-view-creator/
├── SKILL.md                                # Main skill file with classification heuristics
└── references/
    ├── semantic-view-ddl-syntax.md          # Full DDL syntax reference
    └── dimension-metric-patterns.md         # Column classification patterns
```

**What it does:**
- Reads a mart model's SQL and schema.yml
- Classifies columns as dimensions (filter/group-by) or metrics (aggregatable measures)
- Generates `sem_*.sql` dbt model, `schema.yml` metadata, and `CREATE SEMANTIC VIEW` DDL
- Provides heuristics for dimension vs metric classification:

| Column Pattern | Classification | Reasoning |
|---------------|---------------|----------|
| `*_id`, `*_key` | Dimension | Entity identifiers, used for joins/filters |
| `*_name`, `*_type`, `*_status`, `*_category` | Dimension | Categorical, used for group-by |
| `*_date`, `*_at`, `*_timestamp` | Dimension (time) | Time-based filtering |
| `*_amount`, `*_total`, `*_revenue`, `*_cost` | Metric (SUM) | Additive currency measures |
| `*_count`, `*_qty`, `*_quantity` | Metric (SUM) | Additive count measures |
| `*_rate`, `*_ratio`, `*_pct`, `*_percent` | Metric (AVG) | Non-additive rate measures |

### Three Semantic Approaches

This project supports **three** semantic approaches — they coexist without conflict:

| Aspect | dbt Semantic Layer (MetricFlow) | Snowflake Semantic Views | Cortex Analyst YAML Models |
|--------|-------------------------------|-------------------------|----------------------------|
| **Definition** | YAML semantic models in `schema.yml` | `CREATE SEMANTIC VIEW` DDL | YAML files uploaded to stage |
| **Query tool** | `dbt sl query`, MetricFlow | Cortex Analyst (NL) | `CORTEX_ANALYST_MESSAGE()` API |
| **Skill** | `building-dbt-semantic-layer` | `snowflake-semantic-view-creator` | `cortex-analyst-semantic-model` |
| **Generation** | Manual YAML | Script / skill | **Agentic** (AI explores data) |
| **Rich metadata** | Measures + Entities | Dimensions + Metrics | Synonyms, verified queries, custom instructions |
| **Project path** | `models/semantic/` | `ddl/semantic/` | `cortex-analyst-models/` |
| **Best for** | Cross-platform BI tools, dbt Cloud | Simple Snowflake-native NL | Rich NL understanding, multi-table |

**When to use which:**
- Use **MetricFlow** if you need metrics consumed by BI tools (Tableau, Looker) via dbt Cloud Semantic Layer
- Use **Snowflake Semantic Views** if you want simple Cortex Analyst NL querying with dimension/metric classification
- Use **Cortex Analyst YAML Models** if you want the richest NL experience — with synonyms, sample values, verified queries, and custom instructions for maximum text-to-SQL accuracy
- Use **all three** if you want maximum coverage — they define metrics differently and don't conflict

### Cortex Analyst Semantic Model Generator (Agentic)

An **agentic skill** that enables AI agents (GitHub Copilot, Cortex Code) to autonomously generate Cortex Analyst YAML semantic models by exploring Snowflake data through MCP tools — not just running a deterministic script.

**What makes it agentic:**
- The AI agent queries Snowflake via MCP to profile columns, cardinality, and sample values
- It uses AI reasoning (not regex) to classify columns as dimensions, time dimensions, or facts
- It generates contextually relevant synonyms based on domain understanding
- It writes and **tests** SQL verified queries against Snowflake, fixing failures automatically
- It creates rich custom instructions for text-to-SQL accuracy

**Agentic workflow (8 phases):**

```
User: "Generate a Cortex Analyst model for fct_sales"
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 1: Context Gathering                             │
│  ─ Read model SQL, schema.yml, existing Semantic Views  │
├─────────────────────────────────────────────────────────┤
│  Phase 2: Data Exploration (MCP)                        │
│  ─ Query column types, cardinality, sample values       │
│  ─ Analyze table relationships and join patterns        │
├─────────────────────────────────────────────────────────┤
│  Phase 3: Intelligent Classification (AI Reasoning)     │
│  ─ Classify as dimensions / time_dimensions / facts     │
│  ─ Assign default_aggregation (SUM, AVG, COUNT, MAX)    │
├─────────────────────────────────────────────────────────┤
│  Phase 4: Synonym Generation                            │
│  ─ 2-5 business-friendly synonyms per column            │
├─────────────────────────────────────────────────────────┤
│  Phase 5: Verified Query Generation + Testing           │
│  ─ Write 3-5 SQL queries for common business questions  │
│  ─ Test each via MCP, fix failures, record working SQL  │
├─────────────────────────────────────────────────────────┤
│  Phase 6: Custom Instructions                           │
│  ─ Domain rules for text-to-SQL accuracy                │
├─────────────────────────────────────────────────────────┤
│  Phase 7: Assemble YAML                                 │
│  ─ Write to cortex-analyst-models/semantic_<name>.yaml  │
├─────────────────────────────────────────────────────────┤
│  Phase 8: Upload + Test                                 │
│  ─ PUT to @stage, test with CORTEX_ANALYST_MESSAGE()    │
└─────────────────────────────────────────────────────────┘
```

**Skill location:** `.agents/skills/cortex-analyst-semantic-model/SKILL.md`

**Output directory:** `cortex-analyst-models/`

**Deterministic fallback** (batch mode / no MCP):
```bash
# Single model
python scripts/generate_cortex_analyst_model.py --model fct_sales

# Batch all marts
python scripts/generate_cortex_analyst_model.py --batch

# Upload to Snowflake stage
python scripts/upload_semantic_model_to_stage.py --all
```

**Test with Cortex Analyst:**
```sql
SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_MESSAGE(
  '@DBT_DEV.SEMANTIC.CORTEX_ANALYST_MODELS/semantic_sales.yaml',
  [{'role': 'user', 'content': 'What were total sales by category last month?'}]
);
```

**Key files:**

| File | Purpose |
|------|---------|
| `.agents/skills/cortex-analyst-semantic-model/SKILL.md` | Agentic skill (guides AI agent through 8 phases) |
| `.github/instructions/cortex-analyst-model.instructions.md` | Auto-activates on mart model / YAML edits |
| `.github/prompts/suggest-cortex-analyst-model.prompt.md` | Clickable Copilot prompt |
| `scripts/generate_cortex_analyst_model.py` | Deterministic fallback generator |
| `scripts/upload_semantic_model_to_stage.py` | Upload YAML to Snowflake stage |
| `cortex-analyst-models/` | Generated YAML output directory |
| `Sample-semantic-view-cortex-analyst/` | Reference YAML examples |

### Reusable Copilot Prompts

5 clickable prompts in `.github/prompts/` for common workflows. In VS Code Copilot Chat, click the prompt icon or type `/` to see them:

| Prompt | File | What It Does |
|--------|------|-------------|
| **Suggest Semantic View** | `suggest-semantic-view.prompt.md` | Analyzes a mart model, classifies columns, generates `sem_*.sql` + `schema.yml` + DDL |
| **Suggest Cortex Analyst Model** | `suggest-cortex-analyst-model.prompt.md` | Agentically explores Snowflake data, classifies columns, generates YAML with synonyms + verified queries |
| **Suggest Tests** | `suggest-tests.prompt.md` | Analyzes a model and suggests schema tests, unit tests, and custom singular tests |
| **Validate and Build** | `validate-and-build.prompt.md` | Compiles, builds, runs tests, diagnoses errors, previews results with `dbt show` |
| **Review Model** | `review-model.prompt.md` | Full code review against project conventions (critical/warning/info) |

**Example — using a prompt:**
1. Open a mart model (e.g., `fct_orders.sql`)
2. Open Copilot Chat (Ctrl+Shift+I / Cmd+Shift+I)
3. Click the prompt icon (bookmark/slash) → select **"Suggest Semantic View"**
4. Copilot reads the model, classifies columns, and generates all three artifacts

### Custom Copilot Agent

A custom agent `@dbt-semantic-advisor` defined in `.github/agents/dbt-semantic-advisor.agent.md`. Invoke it in Copilot Chat by typing `@dbt-semantic-advisor`.

**What it can do:**
- Analyze any mart model and classify columns as dimensions vs metrics
- Generate `sem_*.sql` models, `schema.yml` metadata, and `CREATE SEMANTIC VIEW` DDL
- Explain the difference between MetricFlow and Snowflake Semantic Views
- Recommend which semantic approach to use for a given use case
- Validate semantic view designs

**Example usage:**
```
@dbt-semantic-advisor Analyze fct_sales and create a semantic view for revenue analysis

@dbt-semantic-advisor What's the difference between MetricFlow and Snowflake Semantic Views?

@dbt-semantic-advisor Which columns in fct_orders should be dimensions vs metrics?
```

### Semantic View Generator Script

A Python script at `scripts/generate_semantic_view.py` that automates semantic view scaffolding by connecting to Snowflake, profiling column data, and auto-classifying columns.

#### Prerequisites

```bash
pip install snowflake-connector-python pyyaml
```

Ensure your Snowflake env vars are set (same as dbt — `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, etc.).

#### Usage

```bash
# Generate semantic view artifacts for a mart model
python scripts/generate_semantic_view.py --model fct_orders

# Preview without writing files (dry run)
python scripts/generate_semantic_view.py --model fct_orders --dry-run

# Custom analysis name (default: derived from model name)
python scripts/generate_semantic_view.py --model fct_orders --analysis-name revenue_analysis

# Skip Snowflake profiling (uses schema.yml metadata only)
python scripts/generate_semantic_view.py --model fct_orders --skip-profile
```

#### What It Generates

For `--model fct_orders`, the script creates:

**1. `models/semantic/sem_orders_analysis.sql`** — dbt view model:
```sql
{{ config(materialized='view', schema='SEMANTIC') }}

with source as (
    select * from {{ ref('fct_orders') }}
)

select
    -- Dimensions
    order_status,
    customer_segment,
    order_date,
    order_month,
    order_year,
    -- Metrics
    order_amount,
    discount_amount,
    quantity
from source
```

**2. `models/semantic/schema.yml`** — metadata block:
```yaml
models:
  - name: sem_orders_analysis
    description: "Semantic view for orders analysis"
    meta:
      snowflake_semantic_view:
        target_database: DBT_DEV
        target_schema: SEMANTIC
        dimensions:
          - name: order_status
            synonyms: ["status", "order state"]
            data_type: VARCHAR
          - name: order_date
            synonyms: ["date", "when"]
            data_type: DATE
        metrics:
          - name: total_revenue
            expression: "SUM(order_amount)"
            description: "Total order revenue"
          - name: avg_order_value
            expression: "AVG(order_amount)"
            description: "Average order value"
```

**3. `CREATE SEMANTIC VIEW` DDL** (printed to stdout or written to file):
```sql
CREATE OR REPLACE SEMANTIC VIEW DBT_DEV.SEMANTIC.SEM_ORDERS_ANALYSIS
  AS SELECT * FROM DBT_DEV.SEMANTIC.SEM_ORDERS_ANALYSIS
  COMMENT = 'Semantic view for orders analysis'
  COLUMNS (
    order_status DIMENSION SYNONYMS ('status', 'order state'),
    customer_segment DIMENSION,
    order_date DIMENSION SYNONYMS ('date', 'when'),
    order_amount METRIC SUM SYNONYMS ('revenue', 'sales'),
    quantity METRIC SUM
  )
  METRICS (
    total_revenue AS SUM(order_amount),
    avg_order_value AS AVG(order_amount)
  );
```

#### How Classification Works

The script connects to Snowflake and runs:
```sql
SELECT COUNT(*), COUNT(DISTINCT col1), ... FROM mart_table
```

Then applies heuristic rules:
- **Dimension**: String/boolean columns with low cardinality (<500 distinct or <5% cardinality ratio)
- **Metric**: Numeric columns that aren't keys (no `_id`, `_key` suffix)
- **Time dimension**: DATE/TIMESTAMP columns
- **Skip**: High-cardinality strings (names, URLs), key columns

## Medallion Architecture Agent

An AI-powered agent that reads your bronze (staging) layer data and helps you design, generate, and refine silver (intermediate) and gold (marts) layer dbt models through natural language conversation.

### How It Works

```
 User: "Create a dim_companies table from free_company_data"
       │
       ▼
 ┌──────────────────────────────────────┐
 │  Medallion Agent (Cortex LLM)       │
 │  ─ Reads staging models & schemas   │
 │  ─ Profiles data (nulls, cardinality)│
 │  ─ Suggests transformations          │
 │  ─ Generates dbt SQL with ref()     │
 │  ─ Writes models to disk            │
 └──────────────┬───────────────────────┘
                │
       ┌────────┴────────┐
       ▼                 ▼
  int_*.sql          fct_*.sql / dim_*.sql
  (silver layer)     (gold layer)
```

### Three Access Methods

| Method | Best For | Location |
|--------|----------|----------|
| **CLI Agent** | Local development, scripted usage | `scripts/medallion_agent.py` |
| **Streamlit App** | Interactive use in Snowsight | `streamlit/medallion_advisor_app.py` |
| **MCP Tools** | VS Code / Copilot integration | `snowflake-dbt-mcp/server.py` |

### CLI Agent

```bash
# Interactive chat mode
python scripts/medallion_agent.py

# Single question
python scripts/medallion_agent.py --ask "Suggest silver models for japan_ecomm_data"

# Use a different Cortex model
python scripts/medallion_agent.py --model llama3.1-70b
```

The CLI agent connects to Snowflake, queries actual data, and can write models directly to disk.

**Agent Tools:**
- `list_sources` / `list_models` — See what data and models exist
- `sample_data` / `describe_table` / `profile_data` — Inspect actual data
- `run_query` — Execute read-only SQL
- `generate_silver_model` / `generate_gold_model` — Write new dbt models
- `generate_semantic_view` — Scaffold a Snowflake Semantic View from a mart model
- `modify_model` — Update existing models

### Streamlit Advisor App

Deploy to Snowflake for browser-based access:

```sql
-- In Snowsight SQL worksheet
CREATE STREAMLIT DBT_DEV.MCP_TOOLS.MEDALLION_ADVISOR_APP
  ROOT_LOCATION = '@dbt_stage/streamlit'
  MAIN_FILE = 'medallion_advisor_app.py';
```

Features:
- **Chat Advisor** — Conversational model design with data-aware context
- **Data Explorer** — Browse tables, profile columns, run queries
- **Model Generator** — Select source tables, describe requirements, generate SQL with AI

### MCP Tools (VS Code)

The MCP server includes 5 medallion-specific tools for Copilot/Claude:

| Tool | Description |
|------|-------------|
| `list_medallion_models` | List models by layer (bronze/silver/gold) |
| `read_model_sql` | Read any model's SQL source |
| `suggest_silver_model` | Get silver layer model suggestions with context |
| `suggest_gold_model` | Get gold layer fact/dimension suggestions |
| `write_medallion_model` | Write generated model to disk |

## Evaluation Framework

8 standardized tasks comparing **Cortex Code** vs **Claude Code** vs **Copilot CLI**:

| Task | Focus Area |
|------|-----------|
| 1. Generate staging model | dbt model generation |
| 2. Create semantic view | Semantic View DDL |
| 3. Build Streamlit dashboard | App scaffolding |
| 4. Code review (planted bugs) | Bug detection |
| 5. OpenFlow pipeline | Snowflake Tasks/Streams |
| 6. Add data quality tests | Testing coverage |
| 7. Optimize slow query | Snowflake performance |
| 8. End-to-end new source | Full pipeline |

Scoring: 1-5 per dimension, 8 dimensions, weighted average.
See [evaluation/README.md](evaluation/README.md) for full rubric.

## Environment Variables

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `SNOWFLAKE_ACCOUNT` | Yes | — | Account identifier (e.g., `xy12345.us-east-1`) |
| `SNOWFLAKE_USER` | Yes | — | Your Snowflake username |
| `SNOWFLAKE_PASSWORD` | Yes | — | Your password |
| `SNOWFLAKE_ROLE` | No | `DBT_ROLE` | Role to use |
| `SNOWFLAKE_DATABASE` | No | `DBT_DEV` | Target database |
| `SNOWFLAKE_WAREHOUSE` | No | `DBT_AGENT_WH` | Compute warehouse |
| `SNOWFLAKE_SCHEMA` | No | `PUBLIC` | Default schema |

---

## Troubleshooting

### `dbt debug` fails with "connection refused"
- Verify your `SNOWFLAKE_ACCOUNT` is correct. Format: `orgname-accountname` (new format) or `accountlocator.region.cloud` (legacy).
- Check your password. Try logging into Snowsight with the same credentials.

### `dbt debug` fails with "database does not exist"
- Run the SQL in Step 3 first to create `DBT_DEV` and grant permissions.

### `dbt build` fails with "insufficient privileges"
- Make sure you granted `CREATE TABLE` and `CREATE VIEW` on all schemas to your role.
- Check: `SHOW GRANTS TO ROLE DBT_ROLE;`

### `dbt deps` fails
- Make sure you're running from the project root (where `dbt_project.yml` is).
- Check your internet connection (packages are downloaded from dbt hub).

### MCP server not showing tools in VS Code
- Make sure `.vscode/mcp.json` has the correct account URL.
- Restart VS Code completely (not just reload window).
- Check VS Code Output panel → "MCP" for error messages.

### "Table not found" errors in staging models
- Make sure your source database/schema exists and your role has SELECT access.
- Verify: `SELECT COUNT(*) FROM <YOUR_DB>.<YOUR_SCHEMA>.<TABLE_NAME>;`

### `GRANT USAGE ON DATABASE` fails for Marketplace shared databases
- Marketplace shared databases require `GRANT IMPORTED PRIVILEGES ON DATABASE` instead of `GRANT USAGE`.
- The bootstrap script generates the correct SQL automatically.

### Mixed-case or special-character column names
- The discovery script handles these automatically:
  - Mixed-case columns (e.g., `B25001e1`) are double-quoted in SQL
  - Columns with special characters are quoted in YAML
  - Tables with numeric-prefixed names use `quoting: identifier: true`

### Adding a new source to an existing project
```bash
python scripts/discover_and_generate.py \
  --source-database NEW_DB \
  --source-schema NEW_SCHEMA \
  --source-name new_source

# Build only the new source
dbt build --select "source:new_source+"
```

---

## License

MIT
