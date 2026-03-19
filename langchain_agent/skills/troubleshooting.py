"""Skill: Troubleshooting — dbt job error diagnosis and resolution.

Source: dbt-agent-skills/skills/dbt/skills/troubleshooting-dbt-job-errors
"""

SKILL_NAME = "troubleshooting"

KEYWORDS = [
    "error", "fail", "failed", "failure", "bug", "issue", "broken",
    "not working", "troubleshoot", "debug", "fix", "investigate",
    "compilation error", "runtime error", "database error",
    "timeout", "permission", "access denied",
]

INSTRUCTIONS = """\
## Skill: Troubleshooting dbt Job Errors

### Error Classification
1. **Infrastructure errors**: Warehouse suspended, permissions, network
2. **Code errors**: SQL syntax, missing refs, undefined macros
3. **Data errors**: Type mismatches, constraint violations, unexpected NULLs

### Investigation Workflow
1. **Read error message** — Identify the model and error type
2. **Check run results** — Use `analyze_run_results` to see all failures
3. **Read the model SQL** — Use `read_model` to inspect the failing model
4. **Check upstream models** — Failures cascade; find the root cause
5. **Compare with data** — Use `describe_table` and `sample_data` to verify assumptions
6. **Check git history** — If a model was working before, review recent changes

### Common Error Patterns
- **"Object does not exist"**: Missing upstream model, run `dbt build` for dependencies
- **"Ambiguous column"**: Missing table alias in JOINs
- **"Division by zero"**: Add `NULLIF(denominator, 0)` or `IFF(denom = 0, NULL, ...)`
- **"Type mismatch"**: Explicit CAST needed (e.g., `VARCHAR` vs `NUMBER`)
- **"Access denied"**: Check role grants — user may lack SELECT on source tables

### IRON RULE
**Never modify a test to make it pass.** If a test fails, fix the data or the model logic,
not the test definition. Tests represent business requirements.

### Resolution Template
1. Identify the root cause
2. Propose a fix (model SQL change, config change, or data fix)
3. Apply the fix using `modify_model` if appropriate
4. Run `dbt build` on the fixed model
5. Run `check_data_quality` to verify tests pass
"""
