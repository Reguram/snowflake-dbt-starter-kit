---
applyTo: "scripts/dbt_agent.py,models/**/*.sql,models/**/*.yml,dbt_project.yml"
description: "Unified one-stop dbt agent — source discovery, model generation, semantic views, code review, data quality, medallion advising. Context-aware: reads existing project state before generating code. Auto-activates when editing any model, schema, or the agent script."
---

# Skill: dbt One-Stop Agent

## When to Use
Use this skill for ANY dbt development task:
- Discovering new data sources from Snowflake
- Generating staging, intermediate, or marts models
- Creating Snowflake Semantic Views for Cortex Analyst
- Reviewing models against project best practices
- Running dbt commands (build, test, compile)
- Checking data quality (null rates, cardinality, test results)
- Getting medallion architecture advice (what silver/gold models to build)
- Generating Streamlit dashboards

## The Agent
The unified agent lives at `scripts/dbt_agent.py` and can run in three modes:

1. **Interactive CLI**: `python scripts/dbt_agent.py` — chat with Cortex LLM
2. **Single question**: `python scripts/dbt_agent.py --ask "your question"`
3. **MCP server**: `python scripts/dbt_agent.py --mcp` — for VS Code/Cortex Code

## Context-Awareness
The agent reads existing project state before generating ANY code:
- Existing models (staging/intermediate/marts/semantic)
- Source definitions (_sources.yml)
- Schema tests and descriptions (schema.yml)
- Actual column types and cardinality from Snowflake

This ensures generated code fits the project rather than being generic boilerplate.

## Key Commands

### Source Discovery
```bash
python scripts/dbt_agent.py --ask "Discover tables from MY_DATABASE.MY_SCHEMA"
```

### Model Generation
The agent's `generate_model` tool writes SQL + updates schema.yml for any layer:
- `layer="staging"` — `stg_<source>__<table>`
- `layer="intermediate"` — `int_<description>`
- `layer="marts"` — `fct_<entity>` or `dim_<entity>`
- `layer="semantic"` — `sem_<analysis_name>`

### MCP Integration
To use via Copilot Chat or Cortex Code, configure `.vscode/mcp.json`:
```json
{
  "servers": {
    "dbt-agent": {
      "type": "stdio",
      "command": "python",
      "args": ["scripts/dbt_agent.py", "--mcp"],
      "env": { "DBT_PROJECT_DIR": "${workspaceFolder}" }
    }
  }
}
```

## Available Tools (15 total)
| Tool | Purpose |
|------|---------|
| `project_context` | Project summary (sources, models, counts) |
| `discover_source` | Discover Snowflake tables → generate staging + marts |
| `list_sources` | List dbt source definitions |
| `list_models` | List models by layer |
| `read_model` | Read model SQL |
| `sample_data` | Query sample rows |
| `describe_table` | Column metadata + row count |
| `profile_data` | Distinct counts, null rates, cardinality |
| `run_query` | Execute read-only SQL |
| `generate_model` | Create/update model + schema.yml |
| `generate_semantic_view` | Auto-generate Semantic View DDL |
| `review_sql` | Static analysis for best practices |
| `check_data_quality` | Run dbt tests |
| `run_dbt` | Execute dbt CLI commands |
| `generate_streamlit_app` | Scaffold Streamlit dashboard |
