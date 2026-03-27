# Snowflake dbt Starter Kit - Repository Review Findings

## Executive Summary
The repository has **1 critical issue** (semantic view DDL handling), **3 moderate issues** (deprecation warnings), and **1 configuration issue** (unused snapshots config). All issues have been identified and most have been fixed.

---

## ✅ FIXED ISSUES

### 1. **CRITICAL: Semantic View DDL Files in models/ Directory**
**Status:** ✅ FIXED

**Problem:**
- File `models/semantic/sem_sales_analysis_ddl.sql` contains `CREATE SEMANTIC VIEW` DDL syntax
- dbt treats all `.sql` files in `/models/` as models and wraps them with `CREATE VIEW AS ...`
- This causes **dbt build failure** because dbt can't wrap a DDL statement

**Root Cause:**
- The Python script `scripts/generate_semantic_view.py` was generating DDL files in `/models/semantic/`
- DDL files should NOT be in dbt's model paths

**Solution Applied:**
1. ✅ Created `/ddl/semantic/` directory outside the models path
2. ✅ Moved `sem_sales_analysis_ddl.sql` to `/ddl/semantic/`
3. ✅ Updated `generate_semantic_view.py` (lines 39-43):
   - Added `DDL_DIR = PROJECT_ROOT / "ddl" / "semantic"` constant
   - Modified file write logic to use `DDL_DIR` instead of `SEMANTIC_DIR`
   - Updated next steps output to reflect new location

**Verification:**
```bash
dbt parse  # Now runs successfully without DDL-related errors
```

---

### 2. **YAML Schema Deprecation: `meta` Outside `config`**
**Status:** ✅ FIXED

**Problem:**
- dbt deprecation warning: `meta` property was at model level, should be nested under `config`
- File: `models/semantic/schema.yml` (line 66)

**Solution Applied:**
1. ✅ Moved `meta` inside `config` block for `sem_sales_analysis` model
2. ✅ Updated `generate_semantic_view.py` (line 261) to generate correct structure:
```python
"config": {
    "meta": {
        "snowflake_semantic_view": {...}
    }
}
```

**Before:**
```yaml
- name: sem_sales_analysis
  meta:
    snowflake_semantic_view: ...
```

**After:**
```yaml
- name: sem_sales_analysis
  config:
    meta:
      snowflake_semantic_view: ...
```

---

## ⚠️ REMAINING ISSUES (Should Be Fixed)

### 3. **YAML File in models/ - Snowflake Semantic View YAML**
**Status:** ⚠️ NEEDS FIX

**Problem:**
- File: `models/semantic/sem_sales_analysis.yaml`
- This is a **Snowflake-specific YAML for `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML`**, NOT a dbt model
- dbt treats it as a model and complains about unexpected top-level keys: `name`, `tables`, `description`
- This file should NOT be in the models directory

**Solution Recommended:**
Move to `ddl/semantic/` alongside the DDL files:
```bash
mv models/semantic/sem_sales_analysis.yaml ddl/semantic/
```

**Why:** This file is for Snowflake's semantic view creation API, not part of dbt's model layer.

---

### 4. **Deprecated Test Syntax: `accepted_values`**
**Status:** ⚠️ NEEDS FIX

**File:** `models/staging/datafeeds/schema.yml` (line 28-29)

**Problem:**
```yaml
tests:
  - not_null
  - accepted_values:
      values: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # ❌ Old syntax
```

**Solution:**
```yaml
tests:
  - not_null
  - accepted_values:
      arguments:  # ✅ Required wrapper
        values: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
```

**Change Required:** Wrap test parameters under `arguments` key.

---

### 5. **Unused Configuration Path**
**Status:** ⚠️ CAN CLEAN UP

**Issue:** `dbt_project.yml` (line 46) defines `snapshots.snowflake_dbt_starter_kit`, but:
- No snapshots currently use this configuration
- No snapshots exist in `snapshots/` directory

**Current Configuration:**
```yaml
snapshots:
  snowflake_dbt_starter_kit:
    +target_schema: snapshots
    +strategy: timestamp
```

**Solution Options:**
1. **Remove** if snapshots aren't planned
2. **Keep** if snapshots will be added later (document the intent)
3. **Move** to a `_snapshots.yml` example file in `snapshots/`

---

## 📊 Architecture Issues

### 6. **Semantic View Generation Workflow**
**Status:** ⚠️ NEEDS DOCUMENTATION

**Current Flow:**
1. Run `scripts/generate_semantic_view.py --model fct_sales`
   - Generates: `models/semantic/sem_*.sql`
   - Generates: `models/semantic/schema.yml` block
   - Generates: `ddl/semantic/sem_*_ddl.sql` ✅ (after fix)

2. Run `dbt build --select sem_sales_analysis`
   - Creates the base view in Snowflake

3. **Manual step:** Execute DDL in Snowsight
   - Copies SQL from `ddl/semantic/sem_*_ddl.sql`
   - Runs: `CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML(...)`

**Improvement Opportunities:**
- Add a macro to execute DDL post-hook
- Or create a Snowflake native app/stored procedure to automate step 3
- Document that semantic views are **separate from dbt models**

---

## 🔍 Code Quality Observations

### Positive Aspects:
✅ Good separation of concerns (staging → intermediate → marts → semantic)
✅ Comprehensive tagging strategy (staging, intermediate, marts, semantic)
✅ Schema validation and tests on critical columns
✅ Python automation for semantic view generation

### Potential Improvements:
- Add `.gitignore` entries for `ddl/` generated files
- Add CI/CD validation to prevent DDL files in models/
- Document the two-step semantic view creation (dbt view + DDL)
- Add error handling in `generate_semantic_view.py` for missing Snowflake credentials

---

## ✅ Summary of Changes Made

| Issue | Fix | File | Status |
|-------|-----|------|--------|
| DDL in models/ | Move to ddl/ directory | `sem_sales_analysis_ddl.sql` | ✅ Fixed |
| DDL script output | Update script to use ddl/ path | `scripts/generate_semantic_view.py` | ✅ Fixed |
| meta outside config | Nest meta under config | `models/semantic/schema.yml` | ✅ Fixed |
| Schema generation | Update YAML structure | `scripts/generate_semantic_view.py` | ✅ Fixed |
| Semantic YAML location | Move to ddl/ | `models/semantic/sem_sales_analysis.yaml` | ⏳ Needs manual fix |
| accepted_values syntax | Add arguments wrapper | `models/staging/datafeeds/schema.yml` | ⏳ Needs manual fix |
| Unused snapshots config | Remove or document | `dbt_project.yml` | ⏳ Optional cleanup |

---

## 📝 Next Steps

**Immediate (To resolve build errors):**
1. ✅ Move `models/semantic/sem_sales_analysis.yaml` → `ddl/semantic/`
2. ✅ Fix `accepted_values` test syntax in `models/staging/datafeeds/schema.yml`

**Verify with:**
```bash
dbt parse        # Check for syntax errors
dbt build        # Full build test
dbt test         # Validate tests
```

**Long-term (Quality improvements):**
- Add pre-commit hook to prevent `.sql` files in models/ that contain DDL
- Document semantic view creation workflow in README
- Consider automating step 3 of semantic view deployment

---

## File Locations Reference

```
snowflake-dbt-starter-kit/
├── models/semantic/
│   ├── sem_sales_analysis.sql        ✅ (dbt model - stays here)
│   ├── schema.yml                    ✅ (dbt metadata - stays here, now fixed)
│   └── sem_sales_analysis.yaml       ⚠️ (Snowflake YAML - should move to ddl/)
├── ddl/semantic/
│   ├── sem_sales_analysis_ddl.sql    ✅ (Create Semantic View DDL - correct location)
│   └── sem_sales_analysis.yaml       ⏳ (Should move here)
└── scripts/
    └── generate_semantic_view.py     ✅ (Now generates files in correct locations)
```
