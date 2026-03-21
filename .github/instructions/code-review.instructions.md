---
applyTo: "models/**/*.sql"
description: "SQL code review checklist for Snowflake dbt projects — critical, warning, and info severity rules. Auto-activates when editing SQL model files."
---

# Skill: Snowflake SQL Code Review

## When to Use
Use this skill when asked to review, audit, or check SQL code for a Snowflake dbt project.

## Review Checklist

### Critical (Must Fix)
- [ ] **No hard-coded references**: All table references must use `{{ ref() }}` or `{{ source() }}`
- [ ] **No hard-coded database/schema**: Never write `MY_DB.MY_SCHEMA.TABLE`
- [ ] **Primary key tests**: Every model needs `unique` + `not_null` on its primary key
- [ ] **No credentials in code**: No passwords, tokens, or account IDs in SQL files

### Warnings (Should Fix)
- [ ] **No SELECT * in marts**: List columns explicitly in marts and semantic models
- [ ] **Naming convention**: `stg_`, `int_`, `fct_`, `dim_`, `sem_` prefixes enforced
- [ ] **Missing schema.yml**: Every model directory should have a schema.yml with descriptions
- [ ] **Missing relationships tests**: Foreign keys should have `relationships` tests
- [ ] **No LIMIT in production models**: LIMIT clauses shouldn't be in production code
- [ ] **Column naming**: All columns should be snake_case in staging and downstream

### Info (Best Practice)
- [ ] **CTE structure**: Use `with` blocks, not nested subqueries
- [ ] **Surrogate keys**: Use `dbt_utils.generate_surrogate_key()` not manual hashing
- [ ] **Date functions**: Use Snowflake-native `DATEADD`, `DATEDIFF`, `DATE_TRUNC`
- [ ] **Transient tables**: Staging/intermediate should use `{{ config(transient=true) }}`
- [ ] **Clustering**: Large fact tables should have `cluster_by` configured
- [ ] **Documentation**: Models should have column-level descriptions

### Snowflake-Specific
- [ ] Check for proper `VARIANT` handling if semi-structured data is involved
- [ ] Verify `LATERAL FLATTEN` usage for array/object parsing
- [ ] Ensure warehouses are not hard-coded — use profile/environment config
- [ ] Check for `CREATE OR REPLACE` patterns that might cause data loss
- [ ] Verify streams/tasks are not bypassing dbt orchestration

## Review Output Format
```
## Code Review: <file_name>

### Summary
<one-line summary>

### Issues Found
- [ERROR] <rule>: <description> (line X)
- [WARNING] <rule>: <description> (line X)
- [INFO] <rule>: <description> (line X)

### Recommendations
- <actionable suggestion>
```
