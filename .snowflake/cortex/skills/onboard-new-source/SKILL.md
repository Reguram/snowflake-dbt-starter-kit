---
name: onboard-new-source
description: >
  End-to-end onboarding of a new Snowflake source into any dbt project. Orchestrates the full
  medallion pipeline by chaining bronze → silver (always delegated) → gold layer skills.
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

> Thin orchestrator that chains four skills to onboard a new Snowflake
> source end-to-end: **EDA** (Data-Analyst profiling) → **Bronze** (staging) →
> **Silver** (intermediate, always delegated to `$onboard-silver-layer`) → **Gold** (marts). Each layer skill
> handles its own pattern discovery, code generation, testing, and validation.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│               onboard-new-source (this skill)        │
│                    ORCHESTRATOR                      │
│                                                      │
│  1. Collect inputs                                   │
│  2. Chain skills:                                    │
│     ┌──────────────────┐                              │
│     │ data-profiling   │ ← EDA report (Markdown)        │
│     │ -eda             │                              │
│     └────────┬─────────┘                              │
│              │                                       │
│     ┌────────▼─────────┐                              │
│     │ onboard-bronze   │ ← Consumes EDA → staging+tests │
│     └────────┬─────────┘                              │
│              │                                       │
│     ┌────────▼─────────┐                              │
│     │ onboard-silver   │ ← Always delegated; emits   │
│     │ (if justified)   │   join/union/cleansing/     │
│     │                  │   type-cast/dedup/flatten   │
│     └────────┬─────────┘                              │
│              │                                       │
│     ┌────────▼─────────┐                              │
│     │ onboard-gold     │ ← Facts, dims, schema.yml     │
│     └──────────────────┘                              │
│                                                      │
│  3. Final validation (full pipeline build)           │
└──────────────────────────────────────────────────────┘
```

---

## Step 0 — Consult the BA change folder

Before profiling, scan `specs/<SOURCE_NAME>/_changes/` for `.md`/`.txt`/`.xlsx`
change documents from the Business Analyst. If any are present, delegate the
entire pipeline to `$spec-driven-model-sync`, which uses the BA's plain-English
(or Excel) document as the source of truth and only re-applies what changed.
That skill is runtime-free and works inside Snowflake Cortex Code.
See [`specs/README.md`](../../../specs/README.md). Profiling-based fallback runs
only when no BA change document is present.

## Required Inputs

When the user invokes this skill, collect these parameters (ask if not provided):

| Parameter | Example | Description |
|-----------|---------|-------------|
| `SOURCE_DATABASE` | `MY_DATABASE` | Snowflake database containing the raw table |
| `SOURCE_SCHEMA` | `PUBLIC` | Schema inside that database |
| `SOURCE_TABLE` | `RAW_ORDERS` | Raw table name (UPPER_CASE) |
| `SOURCE_NAME` | `my_source` | Short snake_case alias for folders and naming |

---

## Step 1 — Data Profiling & EDA (MANDATORY)

Before any model generation, run the Data-Analyst profiling skill to produce a
Markdown EDA report.

**Delegate to:** `$data-profiling-eda`

**Pass these inputs:**
- `SOURCE_DATABASE` → as provided
- `SOURCE_SCHEMA` → as provided
- `SOURCE_TABLE` → as provided
- `SOURCE_NAME` → as provided

**Expected output:**
- `specs/<SOURCE_NAME>/_eda/<source_table_lower>__eda.md` — the EDA report
- Executive summary returned in the response

Capture the report path — it becomes the `EDA_REPORT` input for the bronze skill.

**Do not proceed to Step 2 until the EDA report has been written and the executive
summary surfaces no blocking issues** (empty table, fundamental access errors, etc.).

---

## Step 2 — Bronze Layer (MANDATORY)

Invoke the bronze layer skill, passing the EDA report path so it can skip re-profiling:

**Delegate to:** `$onboard-bronze-layer`

**Pass these inputs:**
- `SOURCE_DATABASE` → as provided
- `SOURCE_SCHEMA` → as provided
- `SOURCE_TABLE` → as provided
- `SOURCE_NAME` → as provided
- `EDA_REPORT` → path from Step 1

**Expected outputs from bronze skill:**
- `models/staging/<SOURCE_NAME>/_sources.yml` — source definition
- `models/staging/<SOURCE_NAME>/stg_<SOURCE_NAME>__<table>.sql` — staging model (generated FROM the `.md` spec)
- `models/staging/<SOURCE_NAME>/stg_<SOURCE_NAME>__<table>.md` — **transformation spec** (source of truth for column-level transforms; only columns that need a transform are listed; excluded columns are called out; everything else is moved as-is)
- `models/staging/<SOURCE_NAME>/schema.yml` — tests and descriptions
- Bronze validation report (all checks passed, including SQL ↔ `.md` consistency)
- `dbt build` passed for the staging model

**Do not proceed to Step 3 until bronze is complete and all tests pass.**

---

## Step 3 — Silver Layer (MANDATORY DELEGATION)

After bronze completes, **always delegate to** `$onboard-silver-layer`. This step is
not optional from this orchestrator's perspective — the decision of whether to
emit a silver model belongs to the silver skill itself (its Step 1 justification
check), not to this skill.

**Delegate to:** `$onboard-silver-layer`

**Pass these inputs:**
- `SOURCE_NAME` — as provided.
- `UPSTREAM_MODELS` — every staging model produced in Step 2 that could feed the
  same logical entity (do not pre-filter).
- `EDA_REPORTS` — auto-discover from `specs/<SOURCE_NAME>/_eda/*.md`.
- `COMBINE_MODE` — `join` if multiple tables share keys, `union` if multiple tables
  share grain (regions / time partitions), `none` if single upstream.
- `JOIN_SPEC` / `UNION_SPEC` — derived from the EDA `Tables` section + bronze keys.
- `TRANSFORMATION_RULES` — any cleansing / type-conversion rules surfaced by EDA
  red flags (high-null whitespace columns, sentinel `'N/A'`, dates-as-VARCHAR, etc.).

The silver skill creates an intermediate model when at least one is true:

| Condition | Example |
|-----------|---------|
| Multi-table **join** | Orders + Customers tables |
| Multi-table **union** | Region- or time-partitioned feeds |
| **Cleansing** rules | `trim`, `null_if`, `coalesce`, sentinel handling |
| **Type conversion** beyond bronze | `try_to_number`, `try_to_date`, boolean coding, VARIANT typed extraction |
| Window functions | Running totals, rankings |
| LATERAL FLATTEN | VARIANT/ARRAY columns |
| Deduplication | Source has duplicate rows |
| Business rules | CASE expressions, categorization, code-to-label mapping |
| Heavy type enrichment | Multiple derived columns |

**If the silver skill emits its standard "no intermediate model justified" message**
(single upstream with no transformation), record that decision and proceed to
Step 4 with the staging model as the upstream for gold. **Do not skip the
delegation — the silver skill must be invoked so its EDA-driven analysis runs.**

**Expected outputs from silver skill (if created):**
- `models/intermediate/<SOURCE_NAME>/int_<SOURCE_NAME>__<description>.sql`
- `models/intermediate/<SOURCE_NAME>/schema.yml`
- EDA-resolution log + transformation-rule plan
- Silver validation report
- `dbt build` passed

---

## Step 4 — Gold Layer (MANDATORY)

After bronze and the silver delegation in Step 3 complete, generate the mart models.

**Delegate to:** `$onboard-gold-layer`

**Pass these inputs:**
- `SOURCE_NAME` → as provided
- `UPSTREAM_MODEL` → the intermediate model from Step 3 if silver emitted one,
  otherwise the staging model from Step 2
- `ENTITY` → derived from the table name or ask the user

**Expected outputs from gold skill:**
- `models/marts/<SOURCE_NAME>/fct_<entity>.sql` — fact table
- `models/marts/<SOURCE_NAME>/dim_<entity>.sql` — dimension table(s) (if applicable)
- `models/marts/<SOURCE_NAME>/schema.yml` — tests and descriptions
- Gold validation report (all checks passed)
- `dbt build` passed for all mart models

---

## Step 5 — Final Pipeline Validation

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
| EDA report | specs/<SOURCE_NAME>/_eda/<table>__eda.md | ✅ GENERATED |
| Bronze (staging) | stg_<SOURCE_NAME>__<table> | ✅ PASS |
| Silver (intermediate) | int_<SOURCE_NAME>__<desc> | ✅ PASS / ⏭️ SKIPPED |
| Gold (marts) | fct_<entity>, dim_<entity> | ✅ PASS |

### Files Created
- specs/<SOURCE_NAME>/_eda/<source_table_lower>__eda.md
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
