"""Skill: dbt Commands — CLI usage, selectors, and run analysis.

Source: dbt-agent-skills/skills/dbt/skills/running-dbt-commands
"""

SKILL_NAME = "dbt_commands"

KEYWORDS = [
    "dbt run", "dbt build", "dbt test", "dbt compile", "dbt ls",
    "dbt list", "dbt show", "dbt debug", "dbt deps", "selector",
    "select", "exclude", "full-refresh", "incremental",
    "run results", "dbt command",
]

INSTRUCTIONS = """\
## Skill: Running dbt Commands

### Common Commands
- `dbt build` — Run + test all models (recommended)
- `dbt run` — Materialize models only (no tests)
- `dbt test` — Run tests only
- `dbt compile` — Compile SQL without executing (great for debugging)
- `dbt ls` — List resources matching a selector
- `dbt show` — Preview model output (like SELECT * with LIMIT)
- `dbt debug` — Verify connection and project setup
- `dbt deps` — Install packages from packages.yml

### Selector Syntax
- Model name: `--select my_model`
- With descendants: `--select my_model+`  (downstream)
- With ancestors: `--select +my_model`  (upstream)
- Both: `--select +my_model+`
- By tag: `--select tag:nightly`
- By path: `--select path:models/staging`
- Exclude: `--exclude my_model`
- Multiple: `--select model1 model2`
- Intersection: `--select tag:nightly,schema:staging`

### Best Practices
- Use `--select` to limit scope — avoid building everything
- Use `dbt compile --select model` to debug SQL before running
- Use `dbt show --select model --limit 5` to preview output
- Check `target/run_results.json` after runs for timing and status
- Use `--quiet` for cleaner CI output
- Use `--warn-error-options '{"include": "all"}'` in CI to fail on warnings

### Run Results Analysis
After a dbt run, check `target/run_results.json` for:
- Execution time per model
- Error messages for failures
- Rows affected
- Adapter response details
"""
