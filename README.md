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
4. [Project Structure](#project-structure)
5. [Models Overview](#models-overview)
6. [MCP Server (Tools for AI Agents)](#mcp-server-tools-for-ai-agents)
7. [Claude Skills](#claude-skills)
8. [Evaluation Framework](#evaluation-framework)
9. [Troubleshooting](#troubleshooting)

---

## What Is This Project?

This is a **dbt (data build tool)** project that transforms raw Snowflake data into clean, analytics-ready tables. On top of that, it includes:

- **MCP Server**: AI agent tools that Claude/Copilot can use to generate dbt models, review SQL, check data quality, and more — running natively inside Snowflake as a Managed MCP Server.
- **Streamlit App**: A chat-based dashboard running inside Snowflake with Cortex AI.
- **Evaluation Framework**: 8 structured tasks to compare Cortex Code vs Claude Code vs Copilot CLI.

**If you're new to dbt**, here's the mental model:
- **Sources** = your raw data tables (any Snowflake database/schema you point it to)
- **Staging models** = clean/rename those raw tables (1:1 mapping)
- **Intermediate models** = join and transform staging models
- **Mart models** = final tables your analysts/dashboards query (facts + dimensions)
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

The bootstrap script works with **any Snowflake database/schema** as a source. When prompted, enter your source database and schema names. The script automatically:
- Discovers all tables and columns via `INFORMATION_SCHEMA`
- Verifies primary key uniqueness against actual data
- Generates `_sources.yml`, staging models, and `schema.yml` with tests
- Creates a starter fact table from the most analytical table
- Updates `dbt_project.yml` vars to point to your source
- Cleans up old models from any previous source

You can also run the discovery script standalone:

```bash
# Interactive mode
python scripts/discover_and_generate.py

# CLI mode
python scripts/discover_and_generate.py \
  --source-database MY_DB \
  --source-schema MY_SCHEMA \
  --source-name my_source

# Preview without writing files
python scripts/discover_and_generate.py \
  --source-database MY_DB \
  --source-schema MY_SCHEMA \
  --dry-run
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

-- Source data (read-only access) — replace with your actual source database/schema
GRANT USAGE ON DATABASE <YOUR_SOURCE_DATABASE> TO ROLE DBT_ROLE;
GRANT USAGE ON SCHEMA <YOUR_SOURCE_DATABASE>.<YOUR_SOURCE_SCHEMA> TO ROLE DBT_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA <YOUR_SOURCE_DATABASE>.<YOUR_SOURCE_SCHEMA> TO ROLE DBT_ROLE;

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
   - Created **staging views** (one per source table, with renamed columns)
   - Created **mart tables** (fact tables with surrogate keys and date parts)
   - Ran all **tests** (unique, not_null on verified primary keys)

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
dbt run                          # Build models only (no tests)
dbt test                         # Run tests only
dbt run --select staging         # Build only staging models
dbt run --select fct_orders+     # Build fct_orders and everything downstream
dbt docs generate && dbt docs serve  # Generate and view documentation
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

## Project Structure

```
├── models/
│   ├── staging/          # Source-conformed views (stg_<source>__*)
│   ├── intermediate/     # Business logic joins (int_*)
│   ├── marts/            # Consumption tables (fct_*, dim_*)
│   └── semantic/         # Semantic View definitions (sem_*)
├── macros/               # Reusable Jinja (surrogate keys, dev limits, semantic DDL)
├── tests/                # Custom singular tests
├── seeds/                # Reference CSVs
├── snapshots/            # SCD Type 2 tracking
├── snowflake-dbt-mcp/
│   ├── server.py         # Local fallback MCP server (6 tools)
│   ├── pyproject.toml
│   └── setup/            # Snowflake Managed MCP Server setup scripts
│       ├── 01_database_objects.sql
│       ├── 02_udf_tools.sql
│       ├── 03_mcp_server.sql
│       ├── 04_oauth_security.sql
│       └── 05_grants.sql
├── streamlit/            # Streamlit-in-Snowflake agent app
│   ├── dbt_agent_app.py  # Chat + Model Gen + Quality + Review + Dashboard
│   └── deploy.sql
├── evaluation/           # Cortex Code vs Claude Code comparison
│   ├── README.md         # Rubric and methodology
│   ├── REPORT.md         # Results template
│   ├── tasks/            # 8 standardized evaluation prompts
│   └── results/          # Captured outputs + scores
├── .github/
│   ├── copilot-instructions.md  # Project conventions for Copilot
│   ├── skills/           # Domain-specific skill files
│   └── workflows/        # CI: dbt build on PRs
└── .vscode/
    └── mcp.json          # MCP server config (Snowflake managed or local)
```

## Source Data

This project works with **any Snowflake database/schema**. The bootstrap script auto-discovers your source tables and generates all models. Point it at any accessible database/schema during setup.

## Models Overview

Models are auto-generated based on your source data:

| Layer | Pattern | Materialization | Description |
|-------|---------|-----------------|-------------|
| Staging | `stg_<source>__<table>` | view | Source-conformed with renamed columns |
| Intermediate | `int_<description>` | ephemeral | Business logic transforms (add manually) |
| Mart | `fct_<entity>` | table | Fact tables with surrogate keys + date parts |
| Semantic | `sem_<analysis>` | view | Semantic View definitions (add manually) |

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

---

## License

MIT
