---
name: onboard-new-source
description: >
  End-to-end onboarding of a new Snowflake source into any dbt project. Orchestrates the full
  medallion pipeline by chaining bronze → silver (conditional) → gold layer skills.
  Collects source inputs, delegates to specialized layer skills, and runs final validation.
  Works on existing projects (infers patterns) and greenfield projects (uses default scaffolding).
  Portable across dbt projects — no hardcoded paths or names.
  Use when: onboarding a new source, discovering a new table, building staging+marts for a new dataset,
  creating a full medallion pipeline from scratch.
  Triggers: onboard, new source, discover source, add source, new table, build pipeline, medallion pipeline.
tools: ["bash", "edit", "mcp"]
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "4.0"
---

# Onboard New Source — Full Medallion Pipeline (Orchestrator)

> Thin orchestrator that chains three layer-specific skills to onboard a new Snowflake
> source end-to-end: **Bronze** (staging) → **Silver** (intermediate, conditional) →
> **Gold** (marts). Each layer skill handles its own pattern discovery, code generation,
> testing, and validation.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│               onboard-new-source (this skill)        │
│                    ORCHESTRATOR                      │
│                                                      │
│  1. Collect inputs                                   │
│  2. Chain layer skills:                              │
│     ┌──────────────────┐                             │
│     │ onboard-bronze   │ ← Profile + staging + tests │
│     └────────┬─────────┘                             │
│              │                                       │
│     ┌────────▼─────────┐                             │
│     │ onboard-silver   │ ← Conditional: joins,       │
│     │ (if justified)   │   dedup, flatten, business  │
│     └────────┬─────────┘                             │
│              │                                       │
│     ┌────────▼─────────┐                             │
│     │ onboard-gold     │ ← Facts, dims, schema.yml   │
│     └──────────────────┘                             │
│                                                      │
│  3. Final validation (full pipeline build)           │
└──────────────────────────────────────────────────────┘
```

---

## Required Inputs

When the user invokes this skill, collect these parameters (ask if not provided):

| Parameter | Example | Description |
|-----------|---------|-------------|
| `SOURCE_DATABASE` | `MY_DATABASE` | Snowflake database containing the raw table |
| `SOURCE_SCHEMA` | `PUBLIC` | Schema inside that database |
| `SOURCE_TABLE` | `RAW_ORDERS` | Raw table name (UPPER_CASE) |
| `SOURCE_NAME` | `my_source` | Short snake_case alias for folders and naming |

---

## Step 1 — Bronze Layer (MANDATORY)

Invoke the bronze layer skill to profile the source and generate staging models:

**Delegate to:** `$onboard-bronze-layer`

**Pass these inputs:**
- `SOURCE_DATABASE` → as provided
- `SOURCE_SCHEMA` → as provided
- `SOURCE_TABLE` → as provided
- `SOURCE_NAME` → as provided

**Expected outputs from bronze skill:**
- `models/staging/<SOURCE_NAME>/_sources.yml` — source definition
- `models/staging/<SOURCE_NAME>/stg_<SOURCE_NAME>__<table>.sql` — staging model
- `models/staging/<SOURCE_NAME>/schema.yml` — tests and descriptions
- Bronze validation report (all checks passed)
- `dbt build` passed for the staging model

**Do not proceed to Step 2 until bronze is complete and all tests pass.**

---

## Step 2 — Silver Layer (CONDITIONAL)

After bronze completes, evaluate whether a silver (intermediate) layer is needed.

**Delegate to:** `$onboard-silver-layer`

The silver skill will self-evaluate justification. It creates an intermediate model
ONLY when at least one of these conditions is true:

| Condition | Example |
|-----------|---------|
| Multi-table join needed | Orders + Customers tables |
| Window functions needed | Running totals, rankings |
| LATERAL FLATTEN needed | VARIANT/ARRAY columns |
| Deduplication needed | Source has duplicate rows |
| Business rules needed | CASE expressions, categorization |
| Heavy type enrichment | Multiple derived columns |

**If the silver skill determines no intermediate model is justified**, it will say so
and you should skip directly to Step 3 (gold).

**Expected outputs from silver skill (if created):**
- `models/intermediate/<SOURCE_NAME>/int_<SOURCE_NAME>__<description>.sql`
- `models/intermediate/<SOURCE_NAME>/schema.yml`
- Silver validation report
- `dbt build` passed

---

## Step 3 — Gold Layer (MANDATORY)

After bronze (and optionally silver) complete, generate the mart models.

**Delegate to:** `$onboard-gold-layer`

**Pass these inputs:**
- `SOURCE_NAME` → as provided
- `UPSTREAM_MODEL` → the staging model name (or intermediate model if silver was created)
- `ENTITY` → derived from the table name or ask the user

**Expected outputs from gold skill:**
- `models/marts/<SOURCE_NAME>/fct_<entity>.sql` — fact table
- `models/marts/<SOURCE_NAME>/dim_<entity>.sql` — dimension table(s) (if applicable)
- `models/marts/<SOURCE_NAME>/schema.yml` — tests and descriptions
- Gold validation report (all checks passed)
- `dbt build` passed for all mart models

---

## Step 4 — Final Pipeline Validation

After all layers are complete, run a full pipeline build from source:

```bash
dbt build --select "source:<SOURCE_NAME>+"
```

This builds everything downstream of the source in dependency order:
staging → intermediate (if exists) → marts

### Final report

```
## Full Pipeline Onboarding Report

Source: <SOURCE_DATABASE>.<SOURCE_SCHEMA>.<SOURCE_TABLE>
Alias: <SOURCE_NAME>

### Layers Created
| Layer | Model(s) | Status |
|-------|----------|--------|
| Bronze (staging) | stg_<SOURCE_NAME>__<table> | ✅ PASS |
| Silver (intermediate) | int_<SOURCE_NAME>__<desc> | ✅ PASS / ⏭️ SKIPPED |
| Gold (marts) | fct_<entity>, dim_<entity> | ✅ PASS |

### Files Created
- models/staging/<SOURCE_NAME>/_sources.yml
- models/staging/<SOURCE_NAME>/stg_<SOURCE_NAME>__<table>.sql
- models/staging/<SOURCE_NAME>/schema.yml
- [models/intermediate/<SOURCE_NAME>/int_<SOURCE_NAME>__<desc>.sql]
- [models/intermediate/<SOURCE_NAME>/schema.yml]
- models/marts/<SOURCE_NAME>/fct_<entity>.sql
- models/marts/<SOURCE_NAME>/dim_<entity>.sql
- models/marts/<SOURCE_NAME>/schema.yml

### Test Results
| Test Type | Count | Passed | Failed |
|-----------|-------|--------|--------|
| unique | X | X | 0 |
| not_null | X | X | 0 |
| accepted_values | X | X | 0 |
| relationships | X | X | 0 |

### Full Pipeline Build
dbt build --select "source:<SOURCE_NAME>+" → ✅ ALL PASSED
```

---

## Next Steps (Delegate to Other Skills)

After the pipeline is running, the user may want to:

| Action | Skill |
|--------|-------|
| Create Snowflake Semantic Views | `$snowflake-semantic-view-creator` or `$semantic-view` |
| Generate Cortex Analyst YAML | `$cortex-analyst-semantic-model` |
| Deploy a Snowflake Agent | `$cortex-agent` |
| Add unit tests | `$adding-dbt-unit-test` |
| Run full project quality audit | `$project-quality-audit` |
| Set up data quality monitoring | `$data-quality` |
| Visualize model lineage | `$creating-mermaid-dbt-dag` |
| Create a Streamlit dashboard | `$developing-with-streamlit` |
| Build a React analytics app | `$build-react-app` |

---

## Example Invocation

```
$onboard-new-source

Source database: AMAZON_AND_ECOMMERCE_WEBSITES_PRODUCT_VIEWS_AND_PURCHASES
Source schema: DATAFEEDS
Source table: PRODUCT_VIEWS_AND_PURCHASES
Source name: datafeeds
```

The orchestrator will:
1. Run `$onboard-bronze-layer` → staging model + tests
2. Evaluate `$onboard-silver-layer` → skip or create intermediate
3. Run `$onboard-gold-layer` → fact + dimension tables
4. Run `dbt build --select "source:datafeeds+"` → full pipeline validation
