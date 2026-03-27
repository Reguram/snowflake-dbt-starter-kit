---
description: "Run a full project quality audit — scan all models for missing tests, empty descriptions, SELECT * violations, and semantic view issues"
---
# Audit Project

Run a full quality audit across the entire dbt project.

## What to do:
1. Use the `project-quality-audit` skill for the complete audit procedure
2. Scan ALL model directories under `models/` (staging, intermediate, marts, semantic)
3. Check every model against these rules:

### Critical Checks
- **Schema coverage**: Every `.sql` model must have a `schema.yml` entry
- **PK tests**: Every model with `generate_surrogate_key()` must have `unique` + `not_null` tests
- **Column definitions**: Every model's schema.yml must have a `columns:` section with non-empty descriptions
- **Semantic materialization**: Semantic models must be `+enabled: false` in dbt_project.yml (not materialized as view/table)

### Warning Checks
- **SELECT * violations**: No `SELECT *` in mart or semantic models
- **Empty source descriptions**: Source columns should have non-empty descriptions
- **Naming conventions**: Enforce `stg_`, `int_`, `fct_`, `dim_`, `sem_` prefixes per layer
- **FK relationship tests**: Columns ending in `_key`/`_id` should have `relationships` tests

### Info Checks
- **Empty directories**: Flag model directories with no files
- **Missing FK tests**: Suggest relationship test targets

## Output format:
Generate a structured report grouped by severity (CRITICAL / WARNING / INFO) with:
- Summary counts
- Tables listing each issue with file path and details
- Auto-fix suggestions where applicable

Offer to auto-fix issues when the user says "fix it".
