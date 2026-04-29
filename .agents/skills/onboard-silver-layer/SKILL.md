---
name: onboard-silver-layer
description: >
  Silver layer (intermediate) onboarding: generate intermediate dbt models with business logic,
  joins, window functions, and deduplication. Only created when justified — if no transformation
  is needed, this skill advises skipping straight to gold. Works on existing projects (infers
  patterns) and greenfield projects (uses default scaffolding). Portable across dbt projects.
  Use when: building intermediate models, adding business logic between staging and marts,
  joining multiple staging models, flattening semi-structured data.
  Triggers: silver, intermediate, int_ model, join tables, business logic, enrich, flatten.
tools: ["bash", "edit", "mcp"]
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "1.0"
---

# Onboard Silver Layer (Intermediate)

> Generates intermediate dbt models that apply business logic, joins, window functions,
> and deduplication between staging (bronze) and marts (gold).
> Silver = business transformations — only created when justified.

## Step 0 — Consult the BA change folder

Look in `specs/<SOURCE_NAME>/_changes/` for a BA change document that mentions
the intermediate model. If present, delegate to `$spec-driven-model-sync`.
See [`specs/README.md`](../../../specs/README.md).

## Prerequisites

Before running this skill, ensure the **bronze layer exists** for the source:
- `models/staging/<SOURCE_NAME>/_sources.yml` ✅
- `models/staging/<SOURCE_NAME>/stg_<SOURCE_NAME>__*.sql` ✅
- `models/staging/<SOURCE_NAME>/schema.yml` ✅

If the bronze layer doesn't exist, run `$onboard-bronze-layer` first.

## Required Inputs

| Parameter | Example | Description |
|-----------|---------|-------------|
| `SOURCE_NAME` | `my_source` | The snake_case source alias (must match bronze layer) |
| `DESCRIPTION` | `orders_enriched` | What this intermediate model does |
| `UPSTREAM_MODELS` | `['stg_my_source__orders', 'stg_my_source__customers']` | Which staging models to consume |

Derived automatically:
- Model name: `int_<SOURCE_NAME>__<DESCRIPTION>` or `int_<DESCRIPTION>` (match project convention)
- Path: `models/intermediate/<SOURCE_NAME>/`

---

## Step 1 — Justify the Silver Layer (MANDATORY)

**Do NOT create an intermediate model by default.** It's only justified when at least one
of these conditions is true:

| Condition | Example | Why intermediate? |
|-----------|---------|-------------------|
| **Multi-table join** | Orders + Customers + Products | Can't do in staging (1:1 with source) |
| **Window functions** | Running totals, row numbers, lag/lead | Complex logic belongs in silver |
| **LATERAL FLATTEN** | VARIANT/ARRAY/OBJECT columns | Semi-structured → relational |
| **Deduplication** | `ROW_NUMBER() ... QUALIFY rn = 1` | Source has duplicates |
| **Business rules** | CASE expressions, status mapping, categorization | Domain logic |
| **Heavy type casting** | Multiple derived columns from raw types | Beyond simple `TRY_TO_*` |
| **Pre-aggregation filtering** | Remove test data, filter date ranges | Business-level row exclusion |

If **NONE** apply, skip this skill and say:
> "No intermediate model needed — the staging model feeds directly to the mart.
> Proceed with `$onboard-gold-layer`."

---

## Step 2 — Read Project Context & Extract Silver Patterns

### 2.1 — Read project configuration

Read `dbt_project.yml` and extract intermediate layer config:

| Setting | What to look for |
|---------|-----------------|
| **Intermediate schema** | `+schema:` under intermediate layer |
| **Intermediate materialization** | `+materialized:` (usually `view` or `ephemeral`) |
| **Intermediate tags** | `+tags:` (e.g., `["intermediate"]`) |

**Default scaffolding** (use if no intermediate config exists):
```yaml
intermediate:
  +materialized: view
  +schema: DBT_INTERMEDIATE
  +tags: ["intermediate"]
```

### 2.2 — Discover existing intermediate models

```bash
ls models/intermediate/*/
```

If existing `int_*.sql` files exist, read one and extract:

| Element | What to note |
|---------|-------------|
| File naming | `int_<source>__<desc>.sql`? `int_<desc>.sql`? Other? |
| Directory structure | `models/intermediate/<source>/`? Flat `models/intermediate/`? |
| CTE naming | `source_data`/`enriched`? `staged`/`transformed`? Other? |
| SQL keyword casing | Same as staging or different? |
| `config()` block | Present in file or managed by `dbt_project.yml`? |
| CTE spacing | Blank lines between CTEs? Compact? |
| Reference style | `{{ ref() }}` to staging? Direct `{{ source() }}`? |
| Business logic patterns | CASE, window functions, joins, LATERAL FLATTEN? |

> See [references/intermediate-patterns.md](references/intermediate-patterns.md) for the
> default scaffolding and detailed pattern guide.

### 2.3 — Build silver pattern registry

```
SILVER PATTERN REGISTRY
========================
Source: [INFERRED | DEFAULT SCAFFOLDING]

Intermediate schema:       <...>
Intermediate materialized: <view | ephemeral | ...>
File naming:               <int_source__desc | int_desc | ...>
Directory structure:        <per-source subdirs | flat | ...>

Intermediate SQL:
  cte_naming:        <source_data→enriched | staged→transformed | ...>
  keyword_case:      <UPPER | lowercase | ...>
  config_in_file:    <yes | no>
  cte_spacing:       <compact | spacious>
  reference_style:   <ref() to staging | source() | ...>
```

---

## Step 3 — Design the Intermediate Model

Before writing code, plan the transformation:

### 3.1 — Map upstream models

| Upstream Model | Columns Used | Join Key | Role |
|---------------|-------------|----------|------|
| `stg_<SOURCE_NAME>__<table1>` | col_a, col_b | col_a | Primary |
| `stg_<SOURCE_NAME>__<table2>` | col_x, col_y | col_x | Lookup |

### 3.2 — Define transformations

| Transformation | CTE | Logic |
|---------------|-----|-------|
| Join orders + customers | `joined` | `LEFT JOIN` on customer_id |
| Categorize order size | `enriched` | `CASE WHEN amount > 1000 THEN 'large' ...` |
| Deduplicate | `deduped` | `ROW_NUMBER() OVER (...) QUALIFY rn = 1` |

### 3.3 — Define output grain

> "One row per `<entity>` after `<transformation>`"

---

## Step 4 — Generate Silver Layer Files

### File 1: `models/intermediate/<SOURCE_NAME>/int_<SOURCE_NAME>__<description>.sql`

Generate using the pattern from Step 2 (inferred or default):

```sql
with <upstream_cte_1> as (
    select * from {{ ref('stg_<SOURCE_NAME>__<table1>') }}
),

<upstream_cte_2> as (
    select * from {{ ref('stg_<SOURCE_NAME>__<table2>') }}
),

<transform_cte> as (
    select
        <upstream_cte_1>.col_a,
        <upstream_cte_1>.col_b,
        <upstream_cte_2>.col_x,
        -- Business logic here
        case
            when <upstream_cte_1>.amount > 1000 then 'large'
            when <upstream_cte_1>.amount > 100 then 'medium'
            else 'small'
        end as order_size
    from <upstream_cte_1>
    left join <upstream_cte_2>
        on <upstream_cte_1>.customer_id = <upstream_cte_2>.customer_id
)

select * from <transform_cte>
```

**Rules:**
- Use `{{ ref() }}` for all upstream references — never hard-code schemas
- Match CTE naming, keyword case, spacing from the pattern registry
- Only add `config()` if the project convention puts it in-file
- Keep transformations focused — one intermediate model per logical transformation
- No aggregation here (that's gold layer) unless needed for dedup

### File 2: `models/intermediate/<SOURCE_NAME>/schema.yml`

```yaml
version: 2

models:
  - name: int_<SOURCE_NAME>__<description>
    description: >
      <What this model does — join, enrich, deduplicate, flatten>
      Grain: one row per <entity> after <transformation>.
    columns:
      - name: <pk_col>
        description: "<description>"
        tests:
          - unique
          - not_null
      - name: <other_col>
        description: "<description>"
```

---

## Step 5 — Build & Test Silver Layer

```bash
dbt build --select int_<SOURCE_NAME>__<description>
```

Report:
- Pass/fail for model + tests
- Row count comparison: staging input rows vs intermediate output rows
- Any test failures

**If tests fail, diagnose and fix before proceeding.**

---

## Step 6 — Validate Against Silver Patterns

### 6.1 — Structural validation

| Check | Rule | Fix |
|-------|------|-----|
| Directory matches pattern | `models/intermediate/<SOURCE_NAME>/` or flat | Match convention |
| File naming | `int_<SOURCE_NAME>__<description>.sql` or `int_<description>.sql` | Match convention |
| `schema.yml` entry | Model has description and PK tests | Add entry |

### 6.2 — SQL validation

| Check | Expected (from registry) |
|-------|-------------------------|
| CTE naming | Matches `cte_naming` from registry |
| Keyword case | Matches `keyword_case` from registry |
| `config()` block | Matches `config_in_file` from registry |
| CTE spacing | Matches `cte_spacing` from registry |
| All refs valid | `{{ ref() }}` targets exist as staging/source models |
| No aggregation | Unless dedup requires it |
| No hard-coded schemas | Uses `{{ ref() }}` or `{{ source() }}` only |

### 6.3 — Validation report

```
## Silver Layer Validation Report

| File | Check | Status | Detail |
|------|-------|--------|--------|
| int_*.sql | CTE structure | ✅ PASS | Matches inferred pattern |
| int_*.sql | References | ✅ PASS | All ref() targets exist |
| schema.yml | PK tests | ✅ PASS | unique + not_null on PK |
| schema.yml | Description | ✅ PASS | Includes grain statement |

Total: 4 checks — 4 passed, 0 failed
```

---

## Step 7 — Silver Checklist

- [ ] Intermediate model is **justified** (multi-join, window, flatten, dedup, or business rules)
- [ ] Uses `{{ ref() }}` for all upstream references
- [ ] No aggregation unless needed for deduplication
- [ ] CTE names and SQL style match project pattern
- [ ] `config()` presence matches project convention
- [ ] `schema.yml` entry with description including grain
- [ ] PK tests on output key column(s)
- [ ] `dbt build` passed with 0 test failures
- [ ] Validation report shows 0 failures

---

## Common Intermediate Patterns

> See [references/intermediate-patterns.md](references/intermediate-patterns.md) for detailed
> examples of each pattern.

| Pattern | When to Use | Key Elements |
|---------|------------|-------------|
| **Multi-table join** | Combining staging models | `LEFT JOIN` on shared keys |
| **Deduplication** | Source has duplicate rows | `ROW_NUMBER() ... QUALIFY rn = 1` |
| **LATERAL FLATTEN** | VARIANT/ARRAY columns | `LATERAL FLATTEN(input => col)` |
| **Window functions** | Running totals, rankings | `SUM() OVER (PARTITION BY ... ORDER BY ...)` |
| **Business categorization** | Status mapping, bucketing | `CASE WHEN ... THEN ... END` |
| **Code-to-label mapping** | Decode short codes (e.g. `'A'`→`'Excellent'`, `'P'`→`'Pending'`) | `CASE <col> WHEN '<code>' THEN '<label>' ... ELSE 'Unknown' END` + `accepted_values` test |
| **Type enrichment** | Derived columns from raw | `DATEDIFF`, `SPLIT_PART`, conditional logic |

---

## Next Steps

| Action | Skill |
|--------|-------|
| Build gold (marts) layer | `$onboard-gold-layer` |
| Full pipeline (bronze → silver → gold) | `$onboard-new-source` |

---

## Example Invocation

```
$onboard-silver-layer

Source name: datafeeds
Description: orders_enriched
Upstream models: ['stg_datafeeds__orders', 'stg_datafeeds__customers']
```
