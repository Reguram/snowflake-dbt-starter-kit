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
| `COMBINE_MODE` | `join` \| `union` \| `none` | How upstream models are combined. `none` = single-source enrichment. |
| `JOIN_SPEC` *(if `join`)* | `[{left: 'orders', right: 'customers', on: ['customer_id'], type: 'left'}]` | One entry per join. `type` ∈ `inner`, `left`, `right`, `full`. |
| `UNION_SPEC` *(if `union`)* | `{kind: 'union_all', column_map: {...}}` | `kind` ∈ `union` (dedup) or `union_all`. `column_map` aligns differently-named columns across the inputs. |
| `TRANSFORMATION_RULES` | see below | Ordered list of business + cleansing rules to apply. |
| `EDA_REPORTS` *(optional)* | `['specs/my_source/_eda/orders__eda.md', ...]` | Auto-discovered from `specs/<SOURCE_NAME>/_eda/` if not supplied. Used to drive type-conversion decisions. |

**`TRANSFORMATION_RULES` shape** — each rule is one of:

| Rule kind | Fields | Example |
|-----------|--------|---------|
| `rename` | `from`, `to` | `{kind: 'rename', from: 'cust_id', to: 'customer_id'}` |
| `cast` | `column`, `to_type`, `safe` (bool) | `{kind: 'cast', column: 'amount', to_type: 'number(14,2)', safe: true}` |
| `trim` / `upper` / `lower` | `column` | `{kind: 'trim', column: 'email'}` |
| `null_if` | `column`, `values` | `{kind: 'null_if', column: 'status', values: ['', 'N/A', 'UNKNOWN']}` |
| `coalesce` | `column`, `default` | `{kind: 'coalesce', column: 'segment', default: 'unknown'}` |
| `case_when` | `column`, `cases`, `else` | `{kind: 'case_when', column: 'order_size', cases: [{when: "amount > 1000", then: "'large'"}], else: "'small'"}` |
| `filter` | `where` | `{kind: 'filter', where: 'is_test = false'}` |
| `derive` | `column`, `expression` | `{kind: 'derive', column: 'order_age_days', expression: "datediff('day', order_date, current_date())"}` |
| `dedup` | `partition_by`, `order_by` | `{kind: 'dedup', partition_by: ['order_id'], order_by: ['updated_at desc']}` |

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
| **Multi-table union** | Yearly partitioned tables, multi-region feeds | Stack into one canonical grain |
| **Window functions** | Running totals, row numbers, lag/lead | Complex logic belongs in silver |
| **LATERAL FLATTEN** | VARIANT/ARRAY/OBJECT columns | Semi-structured → relational |
| **Deduplication** | `ROW_NUMBER() ... QUALIFY rn = 1` | Source has duplicates |
| **Business rules** | CASE expressions, status mapping, categorization | Domain logic |
| **Cleansing rules** | TRIM / NULL-IF / COALESCE / standardisation | Data quality fixes spanning columns |
| **Heavy type casting** | Multiple derived columns from raw types | Beyond simple `TRY_TO_*` |
| **Cross-table type alignment** | `union` of tables with mismatched types | Cast to common target type before stacking |
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

## Step 2.5 — Consume EDA Reports (drive type conversions)

For every upstream staging model, locate the matching EDA report from
[`$data-profiling-eda`](../data-profiling-eda/SKILL.md). Reports live under:

```
specs/<SOURCE_NAME>/_eda/
```

### Discovery rules (apply in order — first match wins per upstream)

If `EDA_REPORTS` was not supplied, list `specs/<SOURCE_NAME>/_eda/*.md` and resolve
as follows for each upstream `stg_<SOURCE_NAME>__<table>` model:

1. **Per-table file** — exact filename `<table>__eda.md` (case-insensitive). E.g.
   `stg_japan_ecomm_data__mall_markets_monthly_transaction` →
   `mall_markets_monthly_transaction__eda.md`.
2. **Per-table file with prefix variants** — `<source>__<table>__eda.md` or
   `<table>_eda.md` (single underscore).
3. **Multi-table report fallback** — if no per-table file matches, look for a
   single multi-table report named `<source>__eda.md` (or any single `*.md` in the
   directory) and parse the per-table sections inside it. Multi-table reports
   typically have a `## Tables` table in §1 and per-table sub-sections in §2 keyed
   by the table name.
4. **Hard fail** — if neither rule 1–3 matches, **stop and ask the user** to either
   run `$data-profiling-eda` first, supply `EDA_REPORTS` explicitly, or confirm
   they want to proceed without EDA-driven type conversion (in which case skip
   Step 2.5 entirely and rely solely on `TRANSFORMATION_RULES`).

Report the resolution per upstream before continuing, e.g.

```
EDA resolution:
  stg_japan_ecomm_data__mall_markets_monthly_transaction → specs/japan_ecomm_data/_eda/japan_ecomm__eda.md (multi-table, §2 row 1)
  stg_japan_ecomm_data__mall_markets_yearly_report       → specs/japan_ecomm_data/_eda/japan_ecomm__eda.md (multi-table, §2 row 2)
```

From each resolved report (or section thereof), extract:

| EDA section | Use it for |
|-------------|------------|
| **§2 Column Profile** (Type column) | Current data type of each column |
| **§7 Data Quality Red Flags** | Cleansing rules to add automatically (e.g. negative amounts, future dates, all-null columns to drop) |
| **§9 Bronze-Layer Recommendations → Type casts to apply** | Any casts the bronze skill couldn't do safely (deferred to silver) |
| **§9 Variant / flatten candidates** | LATERAL FLATTEN targets |

### 2.5.1 — Type-conversion decision matrix

For each column of interest, decide whether a cast is needed in this silver model:

| Source type (from EDA) | Target type (intent) | Decision | How |
|------------------------|----------------------|----------|-----|
| `VARCHAR` holding numbers | `NUMBER(p,s)` | **CAST** | `try_to_number(col, p, s)` |
| `VARCHAR` holding dates | `DATE` / `TIMESTAMP_NTZ` | **CAST** | `try_to_date(col, '<fmt>')` / `try_to_timestamp(col)` |
| `VARCHAR` holding booleans (`'Y'/'N'`, `'true'/'false'`) | `BOOLEAN` | **CAST** | `case when col in ('Y','true','1') then true ... end` |
| `NUMBER` already correct | same | **SKIP** | passthrough |
| `VARIANT` | typed scalar | **CAST** + flatten | `col:"path"::<type>` |
| `union` inputs with mismatched types for the same logical column | common target | **CAST on both sides** | use the wider type (`number(38,4)`, `varchar`, `timestamp_ntz`) |

**Rule:** prefer `TRY_TO_*` over `TO_*` to avoid load-time failures, and never cast a
column that the EDA already shows in the correct type — that work belongs in bronze.

### 2.5.2 — UNION column-alignment check (only if `COMBINE_MODE = union`)

Build a per-input column matrix from the EDA reports:

| Logical column | Input A type | Input B type | Input C type | Common target | Cast plan |
|----------------|--------------|--------------|--------------|---------------|-----------|
| `order_id` | `NUMBER(38,0)` | `VARCHAR(50)` | `NUMBER(38,0)` | `VARCHAR(50)` | cast A & C `::varchar` |
| `amount`   | `NUMBER(14,2)` | `NUMBER(18,4)` | `NUMBER(14,2)` | `NUMBER(18,4)` | cast A & C `::number(18,4)` |
| `created_at` | `TIMESTAMP_NTZ` | `DATE` | `TIMESTAMP_NTZ` | `TIMESTAMP_NTZ` | cast B `::timestamp_ntz` |

Columns missing from one input are added as `cast(null as <target>) as <col>` in that
branch. Columns with different names but the same meaning use `UNION_SPEC.column_map`.

### 2.5.3 — Append auto-cleansing rules from EDA red flags

Promote red flags into `TRANSFORMATION_RULES` automatically (record this in the response):

| EDA red flag | Auto-rule |
|--------------|-----------|
| All-null column | drop column from `select` (do not include in output) |
| Negative values on amount | `{kind: 'filter', where: '<col> >= 0'}` *(only if user confirms)* or `{kind: 'derive', column: '<col>_was_negative', expression: '<col> < 0'}` |
| Future dates on `*_date` | `{kind: 'null_if', column: '<col>', values_expr: "<col> > current_date()"}` |
| `VARCHAR` whitespace risk | `{kind: 'trim', column: '<col>'}` for high-cardinality string PKs/FKs |

Surface auto-promoted rules to the user before generating SQL — never silently filter rows.

---

## Step 3 — Design the Intermediate Model

Before writing code, plan the transformation. The plan **must** be combine-mode-aware.

### 3.1 — Map upstream models

| Upstream Model | Columns Used | Role | EDA report |
|---------------|-------------|------|------------|
| `stg_<SOURCE_NAME>__<table1>` | col_a, col_b | Primary | `specs/<SOURCE_NAME>/_eda/<table1>__eda.md` |
| `stg_<SOURCE_NAME>__<table2>` | col_x, col_y | Lookup / union branch | `specs/<SOURCE_NAME>/_eda/<table2>__eda.md` |

### 3.2 — Combine plan

**If `COMBINE_MODE = join`:** list each join in order.

| # | Left | Right | On | Type | Notes |
|---|------|-------|----|------|-------|
| 1 | `orders` | `customers` | `customer_id` | `left` | Lookup |
| 2 | `(prev)` | `products` | `product_id` | `left` | Lookup |

**If `COMBINE_MODE = union`:** list each branch and the column-alignment matrix from
Step 2.5.2. State `union` (dedup) vs `union_all`.

**If `COMBINE_MODE = none`:** single upstream — only enrichment / cleansing applies.

### 3.3 — Apply transformation rules in order

Translate `TRANSFORMATION_RULES` (and EDA-promoted auto-rules) into a CTE pipeline. Apply
rules in this canonical order (each becomes its own CTE if non-trivial):

1. **typed** — type casts from Step 2.5
2. **cleansed** — `trim`, `upper`/`lower`, `null_if`, `coalesce`
3. **combined** — the join or union (or passthrough)
4. **enriched** — `derive`, `case_when`, business categorization
5. **deduped** — `dedup` rules (always last so it sees final keys)
6. **filtered** — `filter` rules (apply at the end unless they materially reduce join cost — then move before `combined`)

### 3.4 — Define output grain

> "One row per `<entity>` after `<transformation>`"

For `union`, also state which input owns which subset (e.g. via a `source_system`
discriminator column added per branch).

---

## Step 4 — Generate Silver Layer Files

### File 1: `models/intermediate/<SOURCE_NAME>/int_<SOURCE_NAME>__<description>.sql`

Generate using the pattern from Step 2 (inferred or default). Pick the template below
that matches `COMBINE_MODE` — and consult
[`references/intermediate-patterns.md`](references/intermediate-patterns.md) for the
full set of CTE patterns (join, union, dedup, flatten, type-conversion, cleansing).

#### Template A — `COMBINE_MODE = join`

```sql
with orders_raw as (
    select * from {{ ref('stg_<SOURCE_NAME>__orders') }}
),

customers_raw as (
    select * from {{ ref('stg_<SOURCE_NAME>__customers') }}
),

orders_typed as (
    -- type casts deferred from bronze (see EDA: orders__eda.md §9)
    select
        order_id,
        customer_id,
        try_to_number(amount_str, 14, 2) as amount,
        try_to_date(order_date_str, 'YYYY-MM-DD') as order_date,
        trim(status) as status
    from orders_raw
),

orders_cleansed as (
    select
        *,
        nullif(status, '') as status_clean
    from orders_typed
),

joined as (
    select
        o.order_id,
        o.customer_id,
        o.amount,
        o.order_date,
        o.status_clean as status,
        c.customer_name,
        c.segment
    from orders_cleansed o
    left join customers_raw c
        on o.customer_id = c.customer_id
),

enriched as (
    select
        *,
        case
            when amount > 1000 then 'large'
            when amount > 100  then 'medium'
            else 'small'
        end as order_size
    from joined
)

select * from enriched
```

#### Template B — `COMBINE_MODE = union`

```sql
with na_raw as (
    select * from {{ ref('stg_<SOURCE_NAME>__orders_na') }}
),

eu_raw as (
    select * from {{ ref('stg_<SOURCE_NAME>__orders_eu') }}
),

na_aligned as (
    -- align to common target types from Step 2.5.2
    select
        order_id::varchar             as order_id,
        customer_id::varchar          as customer_id,
        amount::number(18,4)          as amount,
        order_date::timestamp_ntz     as order_event_at,
        cast(null as varchar)         as eu_vat_id,   -- column missing in NA branch
        'na'                          as source_system
    from na_raw
),

eu_aligned as (
    select
        order_id::varchar             as order_id,
        customer_id::varchar          as customer_id,
        amount::number(18,4)          as amount,
        order_event_ts::timestamp_ntz as order_event_at,
        eu_vat_id::varchar            as eu_vat_id,
        'eu'                          as source_system
    from eu_raw
),

stacked as (
    select * from na_aligned
    union all   -- use `union` only if cross-branch dedup is required
    select * from eu_aligned
),

cleansed as (
    select
        order_id,
        customer_id,
        amount,
        order_event_at,
        nullif(trim(eu_vat_id), '') as eu_vat_id,
        source_system
    from stacked
),

deduped as (
    select *
    from cleansed
    qualify row_number() over (
        partition by order_id, source_system
        order by order_event_at desc
    ) = 1
)

select * from deduped
```

#### Template C — `COMBINE_MODE = none` (single-source enrichment)

```sql
with raw as (
    select * from {{ ref('stg_<SOURCE_NAME>__<table>') }}
),

typed as (
    select
        *,
        try_to_number(amount_str, 14, 2) as amount,
        try_to_date(order_date_str)      as order_date
    from raw
),

cleansed as (
    select
        *,
        trim(email)        as email_clean,
        nullif(status, '') as status_clean
    from typed
),

enriched as (
    select
        *,
        datediff('day', order_date, current_date()) as order_age_days
    from cleansed
)

select * from enriched
```

**Rules:**
- Use `{{ ref() }}` for all upstream references — never hard-code schemas.
- Match CTE naming, keyword case, spacing from the pattern registry.
- Only add `config()` if the project convention puts it in-file.
- Never add a `cast` that the EDA shows is unnecessary (column already has the target type).
- For `union`, use `union all` by default; only use `union` (dedup) when the user explicitly asks to deduplicate identical rows across branches.
- For `union`, every branch must `select` the **same columns in the same order with the same types**.
- No aggregation here (that's gold layer) unless needed for dedup.

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
| Combine-mode honoured | If `join`: every entry in `JOIN_SPEC` is rendered exactly once. If `union`: every branch projects identical columns/types in the same order. |
| Type casts justified by EDA | Every cast in the SQL maps to either an EDA recommendation or a user-supplied `cast` rule (no speculative casts) |
| `union all` vs `union` | `union all` used unless cross-branch dedup explicitly requested |
| Cleansing rules applied | Every rule in `TRANSFORMATION_RULES` (and EDA-promoted rule) is visible in the generated SQL |

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

- [ ] Intermediate model is **justified** (multi-join, union, window, flatten, dedup, cleansing, or business rules)
- [ ] `COMBINE_MODE` resolved (`join` / `union` / `none`) and matches the SQL written
- [ ] EDA reports for every upstream located and consulted (Step 2.5)
- [ ] Type-conversion plan documented and only necessary casts emitted
- [ ] If `union`: column-alignment matrix verified; every branch has identical column order/types
- [ ] All `TRANSFORMATION_RULES` translated into SQL (cleansing + business rules)
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
| **Multi-table union** | Stacking same-grain feeds (regions, time partitions) | `UNION ALL` + per-branch alignment CTEs + `source_system` discriminator |
| **Cross-branch type alignment** | `union` of mismatched types | Common target type per column, cast in each branch |
| **Deduplication** | Source has duplicate rows | `ROW_NUMBER() ... QUALIFY rn = 1` |
| **LATERAL FLATTEN** | VARIANT/ARRAY columns | `LATERAL FLATTEN(input => col)` |
| **Window functions** | Running totals, rankings | `SUM() OVER (PARTITION BY ... ORDER BY ...)` |
| **Business categorization** | Status mapping, bucketing | `CASE WHEN ... THEN ... END` |
| **Code-to-label mapping** | Decode short codes (e.g. `'A'`→`'Excellent'`, `'P'`→`'Pending'`) | `CASE <col> WHEN '<code>' THEN '<label>' ... ELSE 'Unknown' END` + `accepted_values` test |
| **Cleansing pipeline** | Trim/null-if/coalesce on dirty source | Dedicated `cleansed` CTE applying string hygiene before joins |
| **Type enrichment** | Derived columns from raw | `DATEDIFF`, `SPLIT_PART`, conditional logic |
| **EDA-driven type cast** | Column type wrong in source (per EDA report) | `try_to_number` / `try_to_date` / `try_to_timestamp` in a `typed` CTE |

---

## Next Steps

| Action | Skill |
|--------|-------|
| Build gold (marts) layer | `$onboard-gold-layer` |
| Full pipeline (bronze → silver → gold) | `$onboard-new-source` |

---

## Example Invocations

### Join two staging models with cleansing + EDA-driven type casts
```
$onboard-silver-layer

Source name: datafeeds
Description: orders_enriched
Upstream models: ['stg_datafeeds__orders', 'stg_datafeeds__customers']
Combine mode: join
Join spec: [{left: 'orders', right: 'customers', on: ['customer_id'], type: 'left'}]
Transformation rules:
  - {kind: 'cast', column: 'amount', to_type: 'number(14,2)', safe: true}
  - {kind: 'trim', column: 'email'}
  - {kind: 'null_if', column: 'status', values: ['', 'N/A']}
  - {kind: 'case_when', column: 'order_size',
     cases: [{when: 'amount > 1000', then: "'large'"}, {when: 'amount > 100', then: "'medium'"}],
     else: "'small'"}
EDA reports: auto-discover from specs/datafeeds/_eda/
```

### Union region-partitioned tables into one canonical feed
```
$onboard-silver-layer

Source name: datafeeds
Description: orders_unified
Upstream models: ['stg_datafeeds__orders_na', 'stg_datafeeds__orders_eu', 'stg_datafeeds__orders_apac']
Combine mode: union
Union spec:
  kind: union_all
  column_map:
    order_event_at:
      stg_datafeeds__orders_na: order_date          # date  → cast to timestamp_ntz
      stg_datafeeds__orders_eu: order_event_ts      # already timestamp_ntz
      stg_datafeeds__orders_apac: created_at        # timestamp_ntz
Transformation rules:
  - {kind: 'derive', column: 'source_system', expression: "<branch literal>"}
  - {kind: 'dedup', partition_by: ['order_id', 'source_system'], order_by: ['order_event_at desc']}
EDA reports: auto-discover from specs/datafeeds/_eda/
```
