---
description: "Compile and build the current dbt model, report results and fix any errors"
---
# Validate and Build

Compile and build the currently open dbt model (or the model I specify).

## What to do:
1. Run `dbt compile --select <model>` to check for compilation errors
2. If compilation fails, diagnose and fix the issue
3. Run `dbt build --select <model> --quiet` to materialize + run tests
4. If build fails:
   - Read the error message
   - Check `target/run_results.json` for details
   - Diagnose the root cause (SQL error, test failure, permission issue)
   - Suggest a fix
5. If build succeeds:
   - Report pass/fail counts for tests
   - Show execution time for slowest steps
   - Run `dbt show --select <model> --limit 5` to preview results

Use the `run_dbt_command` MCP tool if available, otherwise run CLI commands directly.
