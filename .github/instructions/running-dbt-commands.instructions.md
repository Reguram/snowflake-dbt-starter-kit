---
applyTo: "dbt_project.yml,profiles.yml*,Makefile,packages.yml"
description: "dbt CLI command patterns — build, show, test, compile, selectors, and flags. Auto-activates when editing project config files."
---

# Skill: Running dbt Commands

## When to Use
Use this skill when asked to run dbt commands, debug build issues, or work with selectors and flags.

## Command Preferences
1. **Use MCP tools if available** — check for `run_dbt_command` MCP tool first
2. **Use `dbt build` not separate `dbt run` + `dbt test`** — build does both + seeds + snapshots
3. **Always use `--select`** — never run the full project unless explicitly asked
4. **Always use `--quiet`** — reduces noise in output

## Key Commands

### Build & Run
```bash
# Build specific model (run + test)
dbt build --select fct_orders --quiet

# Build with downstream dependencies
dbt build --select fct_orders+ --quiet

# Build with upstream dependencies
dbt build --select +fct_orders --quiet

# Full refresh for incremental models
dbt build --select my_incremental_model --full-refresh --quiet
```

### Preview & Explore
```bash
# Preview model output (cheap, fast)
dbt show --select my_model --limit 10

# Run arbitrary SQL against your warehouse
dbt show --inline "select count(*) from {{ ref('fct_orders') }}" --limit 1

# Profile a column
dbt show --inline "select min(order_date), max(order_date), count(distinct order_date) from {{ ref('fct_orders') }}" --limit 1
```

### Testing
```bash
# Test specific model
dbt test --select fct_orders

# Unit tests only
dbt test --select "fct_orders,test_type:unit"

# Test by tag
dbt test --select tag:marts

# Source freshness
dbt source freshness --select source:tpch
```

### Compilation & Debugging
```bash
# Compile to see generated SQL
dbt compile --select fct_orders

# List models matching a selector (dry run)
dbt list --select staging.* --output-keys unique_id resource_type

# Parse project (syntax check)
dbt parse

# Debug connection
dbt debug
```

## Selector Patterns
| Pattern | Meaning |
|---------|---------|
| `model_name` | Single model |
| `model+` | Model + all downstream |
| `+model` | Model + all upstream |
| `+model+` | Model + upstream + downstream |
| `model+2` | Model + 2 levels downstream |
| `staging.*` | All models in staging namespace |
| `path:models/marts` | All models in folder |
| `tag:marts` | Models with specific tag |
| `source:tpch` | Source-related models |
| `model1 model2` | Union (space-separated) |
| `model1,model2` | Intersection (comma-separated) |
| `--exclude model` | Remove from selection |

## Variables
```bash
# Single variable
dbt build --select model --vars 'is_test_run: true'

# Multiple variables
dbt build --select model --vars '{"source_database": "RAW", "source_schema": "ECOMM"}'
```

## Analyzing Run Results
After a build, inspect results:
```bash
# Check for failures
cat target/run_results.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data['results']:
    if r['status'] != 'pass':
        print(f\"{r['status']}: {r['unique_id']} ({r.get('message', 'no message')})\")"
```

## Cost Management
- Always use `--limit` with `dbt show` (never let it scan full tables)
- Use `--select` to avoid building unrelated models
- Use `--defer --state prod-artifacts/` to skip unchanged models
- Use `dbt clone` for zero-copy dev environments
