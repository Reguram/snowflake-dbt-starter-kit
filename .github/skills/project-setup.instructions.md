---
applyTo: "scripts/bootstrap.sh,scripts/snowflake_setup.sql,dbt_project.yml,profiles.yml"
description: "Project setup and bootstrap — Python venv, Snowflake objects, dbt configuration, discover_and_generate.py, and troubleshooting. Auto-activates when editing setup scripts or project config."
---

# Skill: Project Setup & Bootstrap

## When to Use
Use this skill when a user wants to:
- Set up this dbt project from scratch
- Bootstrap the Snowflake dbt Starter Kit
- Automate Steps 1–7 of the README
- Configure their Snowflake connection and build all models
- Troubleshoot setup errors during initial project deployment

## Prerequisites Check
Before starting, verify:
1. The user has **Python 3.9+** installed (`python3 --version`)
2. The user has a **Snowflake account** (free trial from https://signup.snowflake.com/)
3. The user has **Git** installed and the repo cloned
4. The user is in the project root directory

## Instructions

### Phase 1: Local Environment (Steps 1–2)

Run the following commands in the terminal:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate   # macOS/Linux

# Install dbt-snowflake and MCP SDK
pip install --upgrade pip
pip install dbt-snowflake mcp

# Verify
dbt --version
```

If `venv/` already exists, skip creation and just activate it.

### Phase 2: Snowflake Objects (Step 3)

The user must run SQL in Snowsight as ACCOUNTADMIN. There are two approaches:

**Approach A: Use the pre-built SQL script**
Direct the user to open `scripts/snowflake_setup.sql` in Snowsight. They must:
1. Replace `YOUR_USERNAME` in the SET statement at the top with their actual Snowflake username
2. Optionally customize database/warehouse/role names
3. Run the entire script as ACCOUNTADMIN

**Approach B: Quick inline SQL**
If they prefer copy-paste, provide this block (replace `YOUR_USERNAME`):

```sql
USE ROLE ACCOUNTADMIN;
CREATE DATABASE IF NOT EXISTS DBT_DEV;
CREATE SCHEMA IF NOT EXISTS DBT_DEV.DBT_STAGING;
CREATE SCHEMA IF NOT EXISTS DBT_DEV.DBT_INTERMEDIATE;
CREATE SCHEMA IF NOT EXISTS DBT_DEV.DBT_MARTS;
CREATE SCHEMA IF NOT EXISTS DBT_DEV.SEMANTIC;
CREATE SCHEMA IF NOT EXISTS DBT_DEV.SNAPSHOTS;

CREATE WAREHOUSE IF NOT EXISTS DBT_AGENT_WH
  WAREHOUSE_SIZE = 'X-SMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;

CREATE ROLE IF NOT EXISTS DBT_ROLE;
GRANT ALL PRIVILEGES ON DATABASE DBT_DEV TO ROLE DBT_ROLE;
GRANT ALL PRIVILEGES ON ALL SCHEMAS IN DATABASE DBT_DEV TO ROLE DBT_ROLE;
GRANT ALL PRIVILEGES ON FUTURE SCHEMAS IN DATABASE DBT_DEV TO ROLE DBT_ROLE;
GRANT USAGE ON WAREHOUSE DBT_AGENT_WH TO ROLE DBT_ROLE;
GRANT USAGE ON DATABASE SNOWFLAKE_SAMPLE_DATA TO ROLE DBT_ROLE;
GRANT USAGE ON SCHEMA SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 TO ROLE DBT_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 TO ROLE DBT_ROLE;
GRANT ROLE DBT_ROLE TO USER YOUR_USERNAME;
```

**Wait for user confirmation** that the SQL has been executed before proceeding.

### Phase 3: dbt Connection (Step 4)

Create `~/.dbt/profiles.yml`. Ask the user for their credentials or check environment variables:

```bash
mkdir -p ~/.dbt
```

**Option A — Direct credentials** (simpler for beginners):
Write `~/.dbt/profiles.yml` with the user's actual values:

```yaml
snowflake_dbt_starter_kit:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: <ACCOUNT>
      user: <USERNAME>
      password: <PASSWORD>
      role: DBT_ROLE
      database: DBT_DEV
      warehouse: DBT_AGENT_WH
      schema: PUBLIC
      threads: 4
      client_session_keep_alive: true
      query_tag: "dbt_starter_kit"
```

**Option B — Environment variables** (recommended):
Guide the user to add exports to `~/.zshrc` (macOS) or `~/.bashrc` (Linux):

```bash
export SNOWFLAKE_ACCOUNT="<ACCOUNT>"
export SNOWFLAKE_USER="<USERNAME>"
export SNOWFLAKE_PASSWORD="<PASSWORD>"
export SNOWFLAKE_ROLE="DBT_ROLE"
export SNOWFLAKE_DATABASE="DBT_DEV"
export SNOWFLAKE_WAREHOUSE="DBT_AGENT_WH"
export SNOWFLAKE_SCHEMA="PUBLIC"
```

Then copy the template: `cp profiles.yml.template ~/.dbt/profiles.yml`

### Phase 4: Install, Validate, Build (Steps 5–7)

Run these sequentially, checking each step:

```bash
# Step 5: Install packages
dbt deps
# Expected: installs dbt_utils and dbt_expectations cleanly

# Step 6: Validate connection
dbt debug
# Expected: "All checks passed!"

# Step 7: Seed and build
dbt seed
dbt build
# Expected: exit code 0, ~10 models built, all tests pass
```

### Phase 5: Verify Results

After `dbt build` completes, tell the user to verify in Snowsight:

```sql
SELECT COUNT(*) FROM DBT_DEV.DBT_MARTS.FCT_ORDERS;     -- ~1,500,000
SELECT COUNT(*) FROM DBT_DEV.DBT_MARTS.DIM_CUSTOMERS;   -- ~150,000
```

### One-Command Bootstrap Alternative

For users who want full automation, point them to the bootstrap script:

```bash
chmod +x scripts/bootstrap.sh
./scripts/bootstrap.sh
```

This script automates all of Steps 1–7 interactively:
- Creates venv and installs dependencies
- Prompts for Snowflake credentials (or reads env vars)
- Asks whether to use TPC-H or a custom data source
- If custom source: runs `discover_and_generate.py` to auto-discover tables and generate staging models
- Generates a customized `snowflake_setup.sql`
- Pauses for the user to run SQL in Snowsight
- Writes `~/.dbt/profiles.yml`
- Runs `dbt deps`, `dbt debug`, `dbt seed`, `dbt build`

### Custom Data Source (Non-TPC-H)

If the user has their own data in Snowflake and doesn't want to use TPC-H:

1. During bootstrap, answer **"n"** to "Use TPC-H sample data?"
2. Or run the discovery script directly:

```bash
python scripts/discover_and_generate.py \
  --source-database MY_DATABASE \
  --source-schema MY_SCHEMA \
  --source-name my_source
```

This will:
- Connect to Snowflake and query `INFORMATION_SCHEMA`
- Discover all tables and columns in the given schema
- Auto-generate `_sources.yml`, staging SQL models, and `schema.yml` with tests
- Create a starter fact table from the most analytical table
- Update `dbt_project.yml` vars to point to the custom source

Use `--dry-run` to preview without writing files.

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Env var required but not provided: SNOWFLAKE_ACCOUNT` | Env vars not set in current shell | Add exports to `~/.zshrc` and run `source ~/.zshrc`, or use direct credentials |

## MCP Server Configuration

This project includes an MCP server for AI agent tooling. There are two modes:

### Local Python MCP Server (Development)
Use for local development — runs via stdio, no Snowflake-managed server needed:

1. Ensure `mcp` package is installed: `pip install mcp`
2. In `.vscode/mcp.json`, use the stdio configuration:
```json
{
  "servers": {
    "snowflake-dbt-mcp": {
      "type": "stdio",
      "command": "python",
      "args": ["snowflake-dbt-mcp/server.py"],
      "env": {
        "DBT_PROJECT_DIR": "${workspaceFolder}"
      }
    }
  }
}
```
3. Restart VS Code — MCP tools will be available in Copilot Chat

### Snowflake-Managed MCP Server (Production)
For full data access and Cortex Analyst integration:

1. Run setup scripts in Snowsight as ACCOUNTADMIN (in order):
   - `snowflake-dbt-mcp/setup/01_database_objects.sql`
   - `snowflake-dbt-mcp/setup/02_udf_tools.sql`
   - `snowflake-dbt-mcp/setup/03_mcp_server.sql`
   - `snowflake-dbt-mcp/setup/04_oauth_security.sql`
   - `snowflake-dbt-mcp/setup/05_grants.sql`
2. Get the MCP endpoint URL from Snowflake
3. Update `.vscode/mcp.json` with the streamableHttp configuration
4. Use OAuth for authentication (configured in step 4)

### MCP Tools Available
| Tool | Purpose |
|------|---------|
| `generate_dbt_model` | Auto-scaffold staging model from source table |
| `generate_semantic_view` | Generate CREATE SEMANTIC VIEW DDL |
| `run_dbt_command` | Execute dbt CLI commands |
| `review_sql` | Static analysis against best practices |
| `check_data_quality` | Null/duplicate/row-count checks |
| `generate_streamlit_app` | Scaffold Streamlit dashboard |
| `list_medallion_models` | List models by layer (bronze/silver/gold) |
| `suggest_silver_model` / `suggest_gold_model` | AI-powered model suggestions |
| `003001 (42501): Insufficient privileges` | Role missing grants | Run the GRANT statements as ACCOUNTADMIN in Snowsight |
| `Compilation Error: source ... not found` | `dbt deps` not run | Run `dbt deps` to install packages |
| Tables in wrong schema (PUBLIC instead of DBT_MARTS) | Missing `generate_schema_name` macro | Verify `macros/generate_schema_name.sql` exists — it overrides dbt default schema behavior |
| `~/.dbt directory not found` | First-time dbt user | Run `mkdir -p ~/.dbt` before copying profiles |
| `dbt_expectations` deprecation warnings | Old package reference | Verify `packages.yml` uses `metaplane/dbt_expectations` (not `calogica/`) |

## Next Steps After Setup
After Steps 1–7 are complete, guide the user to:
1. **Step 8**: Set up the MCP Server (Snowflake Managed or local) — see README.md
2. **Step 9**: Deploy Streamlit App (optional) — see README.md
3. **Step 10**: Run the Evaluation Framework (optional) — see `evaluation/README.md`

## Example Prompt → Output

**Prompt**: "Set up this dbt project for me. My Snowflake account is xy12345.us-east-1 and my username is JOHN_DOE."

**Agent actions**:
1. Run `python3 -m venv venv && source venv/bin/activate && pip install dbt-snowflake mcp`
2. Show the user the SQL for Step 3, customized with their username, and wait for confirmation
3. Create `~/.dbt/profiles.yml` with their account/username (ask for password)
4. Run `dbt deps && dbt debug && dbt seed && dbt build`
5. Show verification queries and next steps
