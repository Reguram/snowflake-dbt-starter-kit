---
description: "Perform a full code review of a dbt SQL model against project conventions"
---
# Review Model

Perform a comprehensive code review of the currently open SQL model.

## What to do:
1. Check against all rules in the `code-review` skill:
   - **Critical**: No hard-coded refs, no hard-coded DB/schema, PK tests exist, no credentials
   - **Warning**: No SELECT * in marts, naming conventions enforced, schema.yml exists, relationships tests
   - **Info**: CTE structure, surrogate keys, date functions, transient tables, clustering
   - **Snowflake-specific**: VARIANT handling, LATERAL FLATTEN, warehouse config
2. Check model against `dbt-model-generation` skill conventions:
   - DRY principles — is logic duplicated from another model?
   - Proper layer placement (staging vs intermediate vs mart)
   - Correct naming prefix (stg_, int_, fct_, dim_, sem_)
3. Check for missing tests by reading schema.yml
4. Output in the structured format:
   ```
   ## Code Review: <file_name>
   ### Summary
   ### Issues Found
   - [ERROR] / [WARNING] / [INFO] entries
   ### Recommendations
   ```

Use the `review_sql` MCP tool if available for additional static analysis.
