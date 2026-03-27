---
name: semantic-view-coverage-audit
description: >
  Audit semantic view coverage across all mart models. Detects marts missing semantic views,
  orphaned semantic views referencing non-existent marts, stale DDL files out of sync with
  schema.yml metadata, and column drift between mart models and their semantic view definitions.
  Use when asked to "check semantic view coverage", "find missing semantic views", "audit
  semantic views", or "which marts need Cortex Analyst views".
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "1.0"
---

# Semantic View Coverage Audit

> **Detects gaps, orphans, and drift** in the semantic view layer. Ensures every mart model
> that should have a Snowflake Semantic View for Cortex Analyst actually has one — and that
> existing views stay in sync with their underlying mart models.

## When to Invoke This Skill

- User asks "which marts are missing semantic views?"
- User asks to "audit semantic views" or "check Cortex Analyst coverage"
- User asks "are my semantic views up to date?"
- User modifies a mart model and wants to know if the semantic view needs updating
- Before deploying to production — validate semantic layer completeness
- User runs the project quality audit and wants deeper semantic analysis
- User asks "find orphaned or broken semantic views"

## Audit Procedure

### Phase 1: Build Inventory

#### 1a. Scan All Mart Models
```
For each models/marts/**/*.sql:
  → Extract model name (filename without .sql)
  → Record source domain (subdirectory under marts/)
  → Read schema.yml for column definitions
  → Build map: mart_name → {path, domain, columns[], has_schema}
```

#### 1b. Scan All Semantic Models
```
For each models/semantic/sem_*.sql:
  → Extract semantic view name
  → Read the Jinja comment block for the base mart reference
  → Read schema.yml meta.snowflake_semantic_view for dimensions/metrics
  → Build map: sem_name → {path, base_mart, dimensions[], metrics[]}
```

#### 1c. Scan All DDL Files
```
For each ddl/semantic/sem_*_ddl.sql:
  → Extract the target semantic view name
  → Extract the base table/view referenced in AS SELECT * FROM
  → Extract COLUMNS (dimensions) and METRICS defined
  → Build map: ddl_name → {path, base_table, ddl_dimensions[], ddl_metrics[]}
```

### Phase 2: Cross-Reference Checks

#### CHECK 1: Missing Semantic Views (CRITICAL)
Marts without any corresponding semantic model or DDL.

```
For each mart model:
  → Search semantic models for one referencing this mart
  → If none found → MISSING
  → Prioritize: fct_* models are highest priority, summary_* are high,
    dim_* are lower (usually joined into fact views)
```

**Priority classification:**
| Mart Type | Priority | Reasoning |
|-----------|----------|-----------|
| `fct_*` | 🔴 HIGH | Core analytical fact tables — primary Cortex Analyst targets |
| `summary_*` | 🟡 MEDIUM | Pre-aggregated summaries — good NL query candidates |
| `dim_*` | 🟢 LOW | Typically joined into fact views, not queried standalone via NL |

#### CHECK 2: Orphaned Semantic Views (CRITICAL)
Semantic models or DDL referencing marts that don't exist.

```
For each semantic model:
  → Extract base_mart reference from comment block
  → Verify that mart model exists in models/marts/**
  → If mart not found → ORPHANED
For each DDL file:
  → Extract base table from AS SELECT * FROM clause
  → Verify corresponding mart exists
  → If not found → ORPHANED DDL
```

#### CHECK 3: Missing DDL Files (WARNING)
Semantic models that have schema.yml metadata but no DDL file in ddl/semantic/.

```
For each semantic model in models/semantic/:
  → Check if ddl/semantic/<name>_ddl.sql exists
  → If missing → NO DDL (view cannot be deployed to Snowflake)
```

#### CHECK 4: Column Drift — Mart vs Semantic View (WARNING)
Detect when mart model columns have changed but the semantic view hasn't been updated.

```
For each semantic view with a valid base mart:
  → Read mart model's schema.yml column list
  → Read semantic model's dimensions + metrics
  → Compare:
    - Mart columns NOT in semantic view → potential missing dimensions/metrics
    - Semantic view columns NOT in mart → stale references (will fail DDL)
  → Flag differences
```

#### CHECK 5: DDL vs Schema.yml Drift (WARNING)
Detect when schema.yml metadata doesn't match the DDL file.

```
For each semantic view with both schema.yml and DDL:
  → Compare dimensions in schema.yml vs COLUMNS in DDL
  → Compare metrics in schema.yml vs METRICS in DDL
  → Flag mismatches (added/removed/renamed)
```

#### CHECK 6: Duplicate Coverage (INFO)
Multiple semantic views referencing the same mart model.

```
Group semantic models by base_mart reference.
Flag any mart with 2+ semantic views (may be intentional but should be verified).
```

#### CHECK 7: YAML Completeness (WARNING)
Semantic view YAML entries missing required fields.

```
For each semantic model in schema.yml:
  → Check meta.snowflake_semantic_view exists
  → Check name, description are non-empty
  → Check dimensions[] has entries with name + description
  → Check metrics[] has entries with name + type + expression + description
  → Flag incomplete entries
```

### Phase 3: Generate Coverage Report

```markdown
# Semantic View Coverage Audit Report

## Summary
| Metric | Value |
|--------|-------|
| Total mart models | X |
| Marts with semantic views | Y |
| Coverage percentage | Z% |
| Orphaned semantic views | N |
| DDL files missing | N |
| Column drift detected | N |

## 🔴 CRITICAL: Missing Semantic Views

### High Priority (fct_* models)
| Mart Model | Domain | Columns | Suggested Semantic View |
|-----------|--------|---------|------------------------|
| fct_example | japan_ecomm | 15 | sem_example_analysis |

### Medium Priority (summary_* models)
| Mart Model | Domain | Columns | Suggested Semantic View |
|-----------|--------|---------|------------------------|

### Low Priority (dim_* models)
| Mart Model | Domain | Columns | Suggested Semantic View |
|-----------|--------|---------|------------------------|

## 🔴 CRITICAL: Orphaned Semantic Views
| Semantic View | References | Issue |
|--------------|-----------|-------|
| sem_product_performance | fct_product_performance | Mart does not exist |

## ⚠️ WARNING: Missing DDL Files
| Semantic Model | Schema.yml | DDL File |
|---------------|------------|----------|
| sem_revenue_analysis | ✅ exists | ❌ missing |

## ⚠️ WARNING: Column Drift Detected
| Semantic View | Base Mart | New Mart Columns | Stale SV Columns |
|--------------|-----------|-------------------|-------------------|

## ⚠️ WARNING: DDL vs YAML Drift
| Semantic View | YAML Dimensions | DDL Dimensions | Diff |
|--------------|----------------|----------------|------|

## ℹ️ INFO: Duplicate Coverage
| Mart Model | Semantic Views |
|-----------|---------------|
| fct_sales | sem_sales_analysis, sem_revenue_analysis |

## ⚠️ WARNING: Incomplete YAML
| Semantic Model | Missing Fields |
|---------------|---------------|
```

### Phase 4: Recommendations

After generating the report, provide actionable next steps:

1. **For missing semantic views** — Suggest running the `snowflake-semantic-view-creator` skill
   or the `semantic-view-batch-sync` skill to batch-create views
2. **For orphaned views** — Suggest deleting the orphaned semantic model + DDL, or creating
   the missing mart model
3. **For column drift** — Suggest regenerating the DDL using:
   ```bash
   dbt run-operation generate_semantic_view_ddl --args '{"model_name": "sem_<name>", "base_model": "fct_<entity>"}'
   ```
4. **For missing DDL** — Generate the DDL file
5. **For duplicates** — Suggest consolidating or confirming intentional separation

## Integration with Other Skills

| Skill | Handoff |
|-------|---------|
| `snowflake-semantic-view-creator` | Create individual missing semantic views |
| `semantic-view-batch-sync` | Batch create/update semantic views for all gaps |
| `project-quality-audit` | This audit extends CHECK 6 (materialization) with deeper semantic analysis |
| `dbt-one-stop-agent` | Use `generate_semantic_view` tool for individual views |

## File Locations

- Mart models: `models/marts/**/`
- Semantic models: `models/semantic/sem_*.sql`
- Semantic schema: `models/semantic/schema.yml`
- DDL files: `ddl/semantic/sem_*_ddl.sql`
- DDL YAML configs: `ddl/semantic/sem_*.yaml`
- DDL macro: `macros/generate_semantic_view_ddl.sql`
