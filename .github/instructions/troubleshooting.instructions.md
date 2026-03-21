---
applyTo: "logs/**,target/**/*.json,target/run_results.json"
description: "dbt troubleshooting and error diagnosis — log reading, run result analysis, compilation errors, test failures, and data issues. Auto-activates when viewing logs or run results."
---

# Skill: dbt Troubleshooting

## When to Use
Use this skill when diagnosing dbt build failures, test failures, compilation errors, or data quality issues.

## Iron Rule
**Never modify a test to make it pass without understanding WHY it's failing.** Investigate the root cause first.

## Troubleshooting Workflow
1. **Gather info** — read error messages, check `target/run_results.json`, check logs
2. **Classify error** — infrastructure, code/compilation, or data/test failure
3. **Investigate** — targeted analysis based on classification
4. **Resolve** — fix, add regression test, document

## Error Classification

### Infrastructure Errors
- **Timeouts**: Warehouse too small, query too complex, or concurrent jobs
- **Permission denied**: Role lacks grants on database/schema/table
- **Connection failed**: Account URL, credentials, or network issues

**Actions**: Check warehouse size, verify grants in `scripts/snowflake_setup.sql`, run `dbt debug`

### Code / Compilation Errors
- **Syntax errors**: Invalid SQL, missing commas, unclosed parentheses
- **Undefined ref/source**: Model or source doesn't exist or is misspelled
- **Undefined macro**: Package not installed (`dbt deps`) or macro name wrong
- **Jinja errors**: Template syntax issues in `{{ }}` or `{% %}`

**Actions**:
```bash
# Parse to check syntax
dbt parse

# Compile specific model to see generated SQL
dbt compile --select failing_model

# Check for recent changes that may have caused the issue
git log --oneline -10 -- models/
git diff HEAD~3..HEAD -- models/
```

### Data / Test Failures
- **Unique test failed**: Duplicate primary keys in source or join fanout
- **Not null test failed**: Source data has NULLs in expected non-null columns
- **Relationships test failed**: Orphan foreign keys
- **Accepted values failed**: New category appeared in source data
- **Custom test failed**: Business rule violation

**Actions**:
```bash
# Compile the failing test to get its SQL
dbt compile --select test_name

# Preview failing rows (use the compiled test SQL)
dbt show --inline "<compiled_test_sql>" --limit 20

# Check for data shape issues
dbt show --inline "select count(*), count(distinct pk_col) from {{ ref('model') }}" --limit 1
```

## Reading Run Results
```bash
# Show all failures with timing
cat target/run_results.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data['results']:
    if r['status'] in ('fail', 'error'):
        print(f\"[{r['status'].upper()}] {r['unique_id']}\")
        print(f\"  Message: {r.get('message', 'N/A')}\")
        print(f\"  Time: {r.get('execution_time', 0):.1f}s\")
        print()"

# Show slowest models
cat target/run_results.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
results = sorted(data['results'], key=lambda r: r.get('execution_time', 0), reverse=True)
for r in results[:5]:
    print(f\"{r.get('execution_time', 0):.1f}s  {r['unique_id']}\")"
```

## Common Mistakes
| Mistake | Do This Instead |
|---------|-----------------|
| Modifying test to make it pass | Investigate why data fails the test |
| Skipping git history | `git log` reveals what changed |
| Best-guess fix under pressure | Document findings, create investigation ticket |
| Running full build to diagnose | Use `dbt compile` + `dbt show` on the specific failure |
| Not adding regression test | Always add a test that would catch this issue again |
