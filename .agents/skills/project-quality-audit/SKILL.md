---
name: project-quality-audit
description: >
  Automated full-project audit that scans ALL models for quality violations: missing PK tests,
  empty column descriptions, SELECT * in marts/semantic, broken semantic view materialization,
  missing schema.yml entries, and orphaned directories. Use when asked to "audit the project",
  "run quality checks", "validate before deployment", or "find issues across the project".
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "1.0"
---

# Project Quality Audit

> **Full-project scanner** that checks every model, source, and schema file against project
> conventions. Produces a structured report with severity levels and auto-fix suggestions.

## When to Invoke This Skill
- User asks to "audit", "review", or "check the project" for issues
- User says "validate before deployment" or "pre-build checks"
- User asks "are there any problems?" or "find drawbacks"
- User asks to check quality across all models
- Before any major dbt build/deploy

## Audit Procedure

### Phase 1: Scan All Models
For each directory under `models/`:
1. List all `.sql` files
2. List all `schema.yml` and `_sources.yml` files
3. Build a map: `model_name → {sql_path, schema_entry, columns, tests}`

### Phase 2: Run Checks

#### CHECK 1: Schema Coverage (CRITICAL)
Every `.sql` model file must have a corresponding entry in `schema.yml`.

**Scan pattern:**
```
For each models/**/layer/*.sql:
  → Find models/**/layer/schema.yml
  → Verify model entry exists with matching name
  → Flag if missing
```

**Output:** List of models with no schema.yml entry.

#### CHECK 2: Primary Key Tests (CRITICAL)
Every model using `dbt_utils.generate_surrogate_key()` must have `unique` + `not_null` tests on the generated column.

**Scan pattern:**
```
For each .sql file containing 'generate_surrogate_key':
  → Extract output column name (the `as <column_name>` alias)
  → Find that column in schema.yml
  → Verify 'unique' and 'not_null' in tests list
  → Flag if either is missing
```

**Output:** Table of models × PK column × missing tests.

#### CHECK 3: Column Definitions (CRITICAL)
Every model's schema.yml entry must have a `columns:` section with non-empty descriptions.

**Scan pattern:**
```
For each model in schema.yml:
  → Check if 'columns:' key exists
  → If exists, check each column has description != ""
  → Flag models with missing columns section
  → Flag columns with empty descriptions
```

**Output:** Count of models missing columns, count of empty descriptions.

#### CHECK 4: Source Descriptions (WARNING)
Source column descriptions in `_sources.yml` should not be empty.

**Scan pattern:**
```
For each _sources.yml:
  → Count columns where description: "" or description is missing
  → Report percentage of columns documented
```

**Output:** Per-source file coverage percentage.

#### CHECK 5: SELECT * Violations (WARNING)
Models in `marts/` and `semantic/` layers must not use `SELECT *` in the final output.

**Scan pattern:**
```
For each models/marts/**/*.sql and models/semantic/**/*.sql:
  → Check if final SELECT statement contains 'select *'
  → Staging models are EXEMPT (select * from renamed is OK)
```

**Output:** List of violating files with line numbers.

#### CHECK 6: Semantic View Materialization (CRITICAL)
Semantic models must be disabled from `dbt build` to prevent build failures.

**Scan pattern:**
```
1. Check dbt_project.yml → models.semantic.+enabled == false
2. For each models/semantic/sem_*.sql:
   → Check for {{ config(materialized='view') }} or {{ config(materialized='table') }}
   → Flag if found (should be disabled or documentation-only)
3. Check ddl/semantic/*.sql files reference mart models directly (not sem_* views)
```

**Output:** Materialization configuration status.

#### CHECK 7: Naming Convention Violations (WARNING)
Enforce prefix rules per layer.

**Scan pattern:**
```
models/staging/ → must start with stg_
models/intermediate/ → must start with int_
models/marts/ → must start with fct_ or dim_ (or summary_ by convention)
models/semantic/ → must start with sem_
```

**Output:** List of files violating naming conventions.

#### CHECK 8: Foreign Key Relationship Tests (INFO)
Columns ending in `_key` or `_id` in mart models should have `relationships` tests.

**Scan pattern:**
```
For each mart model column ending in _key or _id (excluding PKs):
  → Check if a 'relationships' test exists
  → Flag if missing
```

**Output:** List of FK columns missing relationship tests.

#### CHECK 9: Orphaned Directories (INFO)
Empty model directories should be flagged.

**Scan pattern:**
```
For each subdirectory under models/:
  → Count .sql and .yml files
  → Flag if directory contains zero model files
```

**Output:** List of empty directories.

### Phase 3: Generate Report

Output a structured report grouped by severity:

```markdown
# Project Quality Audit Report

## Summary
- Total models scanned: X
- Total issues found: X (Y critical, Z warning, W info)

## 🔴 CRITICAL Issues
### Missing Schema Coverage
| Model | File | Issue |
|-------|------|-------|
| fct_example | models/marts/.../fct_example.sql | No schema.yml entry |

### Missing PK Tests
| Model | PK Column | Missing Tests |
|-------|-----------|---------------|
| fct_example | example_key | unique, not_null |

### Missing Column Definitions
| Model | File | Issue |
|-------|------|-------|
| fct_example | schema.yml | No columns section |

### Semantic Build Failures
| Issue | Detail |
|-------|--------|
| sem_*.sql materialized as view | Will fail during dbt build |

## ⚠️ WARNING Issues
### SELECT * Violations
| File | Line | Context |
|------|------|---------|

### Empty Source Descriptions
| File | Empty | Total | Coverage |
|------|-------|-------|----------|

### Naming Violations
| File | Expected Prefix | Actual |
|------|----------------|--------|

## ℹ️ INFO Issues
### Missing FK Tests
| Model | Column | Suggested Target |
|-------|--------|-----------------|

### Empty Directories
| Directory | Recommendation |
|-----------|---------------|

## Auto-Fix Available
The following issues can be auto-fixed. Say "fix <issue_number>" to apply:
1. Add PK tests to fct_example (unique + not_null)
2. Generate column definitions for fct_example
3. Disable semantic model materialization
4. Remove empty models/staging/supplier/ directory
```

### Phase 4: Auto-Fix (On Request)
When user says "fix it" or "auto-fix":
1. **PK tests** → Add `unique` + `not_null` entries to schema.yml
2. **Column definitions** → Parse SQL for column names, scaffold `columns:` section
3. **Semantic materialization** → Set `+enabled: false`, wrap SQL in comment block
4. **Empty dirs** → Prompt user before removing

## Integration
This skill uses file reading and grep to perform static analysis. No Snowflake connection required.
It complements the per-file `project-quality-gate.instructions.md` which runs on individual file edits.
