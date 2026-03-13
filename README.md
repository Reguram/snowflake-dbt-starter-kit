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
9. [Claude Skills](#claude-skills)
10. [Evaluation Framework](#evaluation-framework)
11. [Troubleshooting](#troubleshooting)

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

> **Using Copilot/Claude?** Just say: *"Set up this dbt project for me"* — the agent skill in `.github/skills/project-setup.md` will guide the process automatically.

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
├── .github/
│   ├── copilot-instructions.md   # Project conventions for Copilot
│   ├── skills/                   # Domain-specific skill files
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

The MCP server exposes 6+ tools that Claude/Copilot can use:

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

**Architecture**:
- **Snowflake Managed** (default): Tools run as UDFs/stored procs inside Snowflake. No local process. OAuth authentication. Endpoint: `https://<account>/api/v2/databases/DBT_DEV/schemas/MCP_TOOLS/mcp-servers/DBT_AGENT_MCP/sse`
- **Local Fallback**: Python stdio server for offline/development. See `server.py`.

## Claude Skills

Skill files in `.github/skills/` encode domain knowledge:

- **dbt-model-generation.md** — Staging/intermediate/mart generation patterns
- **semantic-view-design.md** — Snowflake Semantic View design and DDL
- **code-review.md** — SQL review checklist (critical/warning/info)
- **data-quality.md** — Test types, custom tests, freshness checks
- **streamlit-generation.md** — Streamlit-in-Snowflake app patterns

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
