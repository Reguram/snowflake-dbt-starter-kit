---
name: onboard-bronze-layer
description: >
  Bronze layer (staging) onboarding: consume a Data-Analyst EDA report (or run a minimal
  profile if missing), extract project patterns, author/read a per-model transformation
  spec `<stg_model>.md`, then generate _sources.yml + staging SQL + schema.yml with
  tests — driven by the `.md` spec. Works on existing projects (infers patterns) and
  greenfield projects (uses default scaffolding). Portable across dbt projects — no
  hardcoded paths or names.
  NOTE: Deep profiling / EDA now lives in the `data-profiling-eda` skill. Invoke that
  skill FIRST and pass the resulting report path here as `EDA_REPORT`.
  Use when: creating a staging model for a new source table, building the bronze layer,
  generating _sources.yml.
  Triggers: bronze, staging, new source, _sources.yml, stg_ model.
tools: ["bash", "edit", "mcp"]
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "2.0"
---

# Onboard Bronze Layer (Staging)

> Discovers a Snowflake source table, profiles all columns, infers project style patterns
> (or uses default scaffolding), and generates source-conformed staging models.
> Bronze = 1:1 with raw data — rename columns, cast types, no business logic.

## Step 0 — Consult the BA change folder

Before profiling, look in `specs/<SOURCE_NAME>/_changes/` for a Business
Analyst change document (`.md`, `.txt`, or `.xlsx`) that mentions the model
you’re about to create or modify. If one exists, **delegate to
`$spec-driven-model-sync`** — the BA document is the source of truth for
column names, types, and tests. That skill is runtime-free: the agent
parses and applies the edits using its own file tools (no Python, no
shell), so it works inside Snowflake Cortex Code.

If no change document exists, fall through to the standard
profile-and-generate flow below. See [`specs/README.md`](../../../specs/README.md)
for the BA document format.

## Required Inputs

When the user invokes this skill, collect these parameters (ask if not provided):

| Parameter | Example | Description |
|-----------|---------|-------------|
| `SOURCE_DATABASE` | `MY_SNOWFLAKE_DB` | Snowflake database containing the raw table |
| `SOURCE_SCHEMA` | `RAW_DATA` | Schema inside that database |
| `SOURCE_TABLE` | `ORDERS` | Raw table name (UPPER_CASE in Snowflake) |
| `SOURCE_NAME` | `my_source` | Short snake_case alias for folders and naming |
| `EDA_REPORT` *(optional)* | `specs/my_source/_eda/orders__eda.md` | Path to an EDA report produced by the `data-profiling-eda` skill. Strongly recommended — when present, this skill skips re-profiling and uses the report's column profile, classifications, and PK recommendations. |

Derived automatically:
- Staging model: `stg_<SOURCE_NAME>__<SOURCE_TABLE_lower>`
- Staging path: `models/staging/<SOURCE_NAME>/`

---

## Step 1 — Read Project Context & Extract Bronze Patterns (MANDATORY)

Before generating ANY file, read existing project files and extract the actual patterns in use.

**Two modes:**
- **Existing project** (has `models/staging/` with at least one source): Infer ALL patterns
  from the existing codebase. The inferred patterns override the defaults below.
- **Greenfield project** (empty `models/` or no existing sources): Use the default scaffolding
  patterns below as-is.

### 1.1 — Read project configuration

Read `dbt_project.yml` and extract:

| Setting | What to look for | Where |
|---------|-----------------|-------|
| **Project name** | Top-level `name:` | Used as the key under `models:` |
| **Staging schema** | `+schema:` under staging layer | e.g., `DBT_STAGING`, `RAW`, `STG` |
| **Staging materialization** | `+materialized:` under staging | `view`, `table`, `ephemeral` |
| **Staging tags** | `+tags:` under staging | e.g., `["staging"]` |
| **Vars** | `vars:` block | Source database/schema defaults |
| **Custom schemas** | Check if `macros/generate_schema_name.sql` exists | Determines schema resolution |

**Default scaffolding** (use if `dbt_project.yml` has no staging config):
```yaml
models:
  <project_name>:
    staging:
      +materialized: view
      +schema: DBT_STAGING
      +tags: ["staging"]
```

### 1.2 — Discover existing sources

Scan `models/staging/` and list all existing source directories:

```bash
ls -d models/staging/*/
```

**What to extract:**
- Directory naming convention: snake_case? kebab-case? Other?
- Number of existing sources (0 = greenfield, 1+ = infer from them)
- Check if `models/staging/<SOURCE_NAME>/` already exists
  - If yes: ask user whether to merge or replace

**Pattern rule**: directory name = `SOURCE_NAME` alias used in `{{ source() }}` calls.

### 1.3 — Extract `_sources.yml` pattern

**If existing sources exist:** Read one `_sources.yml` from `models/staging/*/` and extract:

| Element | What to note |
|---------|-------------|
| Source `name` casing | snake_case? camelCase? |
| `database` / `schema` | Hard-coded or using `var()`? Quoted? |
| `quoting` block | Present? Which fields? |
| Table `name` casing | UPPER_CASE? lowercase? |
| Table `description` format | Free text? Template? |
| Column `name` casing | UPPER_CASE? snake_case? |
| Column `description` | Empty string? Populated? |
| Tests on PK columns | `unique` + `not_null`? Different? |
| Tests on non-PK columns | None? `not_null`? Other? |

> See [references/sources-yml-patterns.md](references/sources-yml-patterns.md) for default
> scaffolding and detailed field-by-field rules.

### 1.4 — Extract staging SQL pattern

**If existing staging models exist:** Read one `stg_*.sql` file and extract:

| Element | What to note |
|---------|-------------|
| CTE naming | `source`/`staged`? `src`/`renamed`? Other? |
| First CTE body | `select *` or explicit columns? |
| Column casing in transform CTE | snake_case? camelCase? |
| Column listing style | One per line? Multiple per line? |
| Indentation | 4-space? 2-space? Tabs? |
| Trailing commas | Yes or no? |
| `config()` block | Present in file or managed by `dbt_project.yml`? |
| SQL keyword casing | lowercase? UPPER_CASE? |
| Final select | `select * from <cte>` or explicit columns? |
| Type casting | `TRY_TO_*`? `CAST()`? `::type`? |

> See [references/staging-sql-patterns.md](references/staging-sql-patterns.md) for default
> scaffolding and detailed element-by-element rules.

### 1.5 — Extract staging `schema.yml` pattern

**If existing staging schema.yml exists:** Read one and extract:

| Element | What to note |
|---------|-------------|
| Description format | Template pattern or free text? |
| Column names | snake_case matching SQL output? |
| Column descriptions | Empty string? Populated? |
| Test placement | PK only? All columns? |
| Indentation style | 2-space? 4-space? |

### 1.6 — Build bronze pattern registry

Compile all extracted patterns (or defaults) into a registry:

```
BRONZE PATTERN REGISTRY
========================
Source: [INFERRED | DEFAULT SCAFFOLDING]

Project name:         <from dbt_project.yml>
Staging schema:       <...>
Staging materialized: <view | table | ...>
Existing sources:     <list or "none (greenfield)">

_sources.yml:
  source_name_case:   <snake_case | ...>
  db_schema_case:     <UPPER_CASE | ...>
  quoting:            <true | false | absent>
  table_name_case:    <UPPER_CASE | ...>
  column_name_case:   <UPPER_CASE | ...>
  pk_tests:           <unique+not_null | ...>

Staging SQL:
  cte_names:          <source→staged | ...>
  keyword_case:       <lowercase | UPPER | ...>
  config_in_file:     <yes | no (dbt_project.yml)>
  indentation:        <4-space | 2-space | ...>
  trailing_commas:    <yes | no>
  final_select:       <select * from staged | ...>
```

**This registry drives ALL code generation and validation in this skill.**

---

## Step 2 — Acquire the EDA Profile

Deep profiling has been moved to the dedicated **`data-profiling-eda`** skill. This
skill consumes the report it produces.

### 2.1 — If `EDA_REPORT` was provided

Read the file at `EDA_REPORT` and extract:

| From the report | Used for |
|-----------------|----------|
| Section 1 (Overview) — row count, table comment | `_sources.yml` table description |
| Section 2 (Column Profile) — column / type / classification | Renaming + type-cast plan |
| Section 3 (Primary Key Analysis) — PK candidate(s) | `unique` + `not_null` tests, surrogate-key decision |
| Section 7 (Red Flags) — all-null / variant / future dates | Columns to exclude or special-case |
| Section 9 (Bronze Recommendations) — explicit hand-off | Direct guidance for staging design |

Validate that the report's table identifier matches `<SOURCE_DATABASE>.<SOURCE_SCHEMA>.<SOURCE_TABLE>`.
If it does not, stop and ask the user to confirm or regenerate the report.

### 2.2 — If `EDA_REPORT` was NOT provided

**Stop and delegate.** This skill does not perform profiling itself.

1. Invoke `$data-profiling-eda` with the same `SOURCE_DATABASE` / `SOURCE_SCHEMA` /
   `SOURCE_TABLE` / `SOURCE_NAME` inputs.
2. Wait for that skill to produce
   `specs/<SOURCE_NAME>/_eda/<source_table_lower>__eda.md`.
3. Resume this skill with `EDA_REPORT` set to that path and re-enter Step 2.1.

Do not run `DESCRIBE TABLE`, per-column profiling queries, classification logic, or
PK detection inside this skill. All of that lives in `data-profiling-eda` and is
consumed here only via the report file.

### 2.3 — Report the column summary

Using the report from Step 2.1, produce this short summary before generating files:

| Column | Type | Nulls% | Unique% | Classification |
|--------|------|--------|---------|----------------|
| ... | ... | ... | ... | PK / dimension / metric / date / exclude |

---

## Step 2.5 — Author or read the transformation spec `<stg_model>.md` (MANDATORY)

Every staging model is authored as a **trio**: `.sql`, `.yml`, and `.md`. The `.md`
file is the **source of truth for column transformations** — the SQL is generated
from it. See [references/transformations-md-template.md](references/transformations-md-template.md)
for the canonical format.

### Authoring rules (team standard)

1. **Only columns that need a transformation are listed** in the *Transformations*
   table — each row carries the SQL expression to apply.
2. **Any column not mentioned is moved as-is** — emitted as a plain snake_case
   rename (`"SOURCE_COL" as source_col`) with no logic.
3. **Excluded columns are called out explicitly** under *Excluded columns*.
4. The spec is bronze-scoped — only 1:1 transforms (rename, safe-cast, trim,
   variant flatten, surrogate key). No joins, aggregates, or business logic.

### 2.5.1 — If `<stg_model>.md` already exists

Read it. Parse the *Transformations* table and the *Excluded columns* list.
Validate that:
- Every `Source column` exists in the EDA column profile (else stop and report).
- No `Output column` collides with another row.
- No row contains forbidden constructs (`join`, `group by`, `union`, `from {{ ref(`).

Use the spec verbatim to drive Step 3. Do not infer additional transforms.

### 2.5.2 — If `<stg_model>.md` does NOT exist — scaffold it

Generate the file using the EDA column profile and these defaults:

| EDA classification / red flag        | Pre-filled action          | Section          |
|--------------------------------------|----------------------------|------------------|
| `date` (text type)                   | `TRY_TO_DATE("COL")`       | Transformations  |
| `metric` (numeric stored as text)    | `TRY_TO_NUMBER("COL")`     | Transformations  |
| `dimension` text with whitespace     | `TRIM("COL")`              | Transformations  |
| `VARIANT` field referenced in EDA    | `"COL":path::type`         | Transformations  |
| Multi-column natural PK              | `dbt_utils.generate_surrogate_key([...])` as `row_key` | Transformations |
| Red flag: all-null / replication metadata / future dates flagged for removal | listed | Excluded columns |
| Everything else                      | snake_case rename           | As-is columns    |

Write the scaffolded `.md` to `models/staging/<SOURCE_NAME>/stg_<SOURCE_NAME>__<table_lower>.md`,
present the diff to the user, and **proceed** with the scaffolded spec (do not
block waiting for user edits — the user can iterate and re-run later).

### 2.5.3 — Echo the resolved column plan

```
## Bronze Transformation Plan — stg_<source>__<table>

Transformed (N): order_date (TRY_TO_DATE), quantity (TRY_TO_NUMBER), ...
Excluded   (M): _fivetran_deleted, internal_hash
As-is      (K): country_region, province_state, ...
```

This plan is the contract between Step 2.5 and Step 3.

---

## Step 3 — Generate Bronze Layer Files

Create four artifacts under `models/staging/<SOURCE_NAME>/` — the `.md` from
Step 2.5 plus three generated files driven by it:

### File 1: `_sources.yml`

Generate using the pattern from Step 1.3 (inferred or default):

```yaml
version: 2

sources:
  - name: <SOURCE_NAME>
    description: "Raw source from <SOURCE_DATABASE>.<SOURCE_SCHEMA>"
    database: "<SOURCE_DATABASE>"
    schema: "<SOURCE_SCHEMA>"
    quoting:
      identifier: true
    tables:
      - name: <SOURCE_TABLE>
        description: "<description based on profiling — include row count>"
        columns:
          # List ALL columns from DESCRIBE TABLE
          # PK column: unique + not_null tests
          # Non-PK columns: name + description only (match inferred pattern)
```

### File 2: `stg_<SOURCE_NAME>__<table_lower>.sql` — generated FROM the `.md` spec

Do not author this file by hand. Generate it deterministically from the
transformation plan resolved in Step 2.5:

- For each row in *Transformations* → emit `<sql_expression> as <output_column>`.
- For each column in *Excluded columns* → omit it entirely.
- For every other source column → emit `"<SOURCE_COL>" as <snake_col>`.
- Preserve source-column ordering except where surrogate keys are added.

Using the pattern from Step 1.4 (inferred or default):

```sql
with source as (
    select * from {{ source('<SOURCE_NAME>', '<SOURCE_TABLE>') }}
),

staged as (
    select
        -- Lines below are emitted from <stg_model>.md:
        --   • Transformations  → <expression> as <output>
        --   • Excluded columns → omitted
        --   • Anything else    → "SOURCE_COL" as snake_col
    from source
)

select * from staged
```

**Rules:**
- List ALL kept columns explicitly in the transform CTE — no `SELECT *`.
- Every emitted line must trace back to a row in the `.md` plan.
- Use safe type casts (`TRY_TO_*` on Snowflake).
- Surrogate keys come from the `.md` plan, never invented in SQL.
- Match CTE names, keyword case, indentation from the pattern registry.

### File 3: `schema.yml`

Generate using the pattern from Step 1.5 (inferred or default). The column
list must match the SQL output exactly — which is itself a mechanical
derivation from `<stg_model>.md`:

```yaml
version: 2

models:
  - name: stg_<SOURCE_NAME>__<table_lower>
    description: "Staged <SOURCE_TABLE> from <SOURCE_NAME> — renamed columns, 1:1 with source"
    columns:
      # Every column from the SQL output (= every kept column from the .md plan)
      # PK: unique + not_null tests
      # Non-PK: name + description (match inferred test pattern)
```

### File 4: `stg_<SOURCE_NAME>__<table_lower>.md` — the transformation spec

This is the artifact authored or scaffolded in Step 2.5. It must remain in
the directory alongside the SQL and YAML and is the only place where
per-column transformations are documented. See
[references/transformations-md-template.md](references/transformations-md-template.md).

---

## Step 4 — Build & Test Bronze Layer

```bash
dbt build --select "source:<SOURCE_NAME>+"
```

Report:
- Pass/fail count per model
- Any test failures (column, failing row count)
- Compilation errors (exact line + fix)

**If any test fails, diagnose and fix before proceeding.**

---

## Step 5 — Validate Against Bronze Patterns

Validate every generated file against the patterns from Step 1.

### 5.1 — Structural validation

| Check | Rule | Fix |
|-------|------|-----|
| Directory exists | `models/staging/<SOURCE_NAME>/` | Create it |
| Files present | `_sources.yml`, `stg_*.sql`, `schema.yml`, **`stg_*.md` transformation spec** | Create missing |
| File naming | `stg_<SOURCE_NAME>__<table_lower>.{sql,md}` (double underscore) | Rename |
| No orphan SQL | Every `.sql` has a `schema.yml` entry **and a sibling `.md` spec** | Add entry / scaffold spec |
| No orphan YAML | Every `schema.yml` entry has a `.sql` file | Remove entry |
| No orphan `.md` | Every `stg_*.md` has a sibling `.sql` | Generate SQL or remove spec |

### 5.2 — `_sources.yml` validation

Compare against Step 1.3 pattern registry:

| Check | Expected (from registry) |
|-------|-------------------------|
| `version: 2` present | First line |
| `name` casing | Matches `source_name_case` from registry |
| `database` / `schema` casing | Matches `db_schema_case` from registry |
| `quoting` block | Matches `quoting` from registry |
| Table `name` casing | Matches `table_name_case` from registry |
| Column `name` casing | Matches `column_name_case` from registry |
| PK tests | Matches `pk_tests` from registry |

### 5.3 — Staging SQL validation

Compare against Step 1.4 pattern registry:

| Check | Expected (from registry) |
|-------|-------------------------|
| CTE names | Matches `cte_names` from registry |
| Keyword case | Matches `keyword_case` from registry |
| `config()` block | Matches `config_in_file` from registry |
| Indentation | Matches `indentation` from registry |
| Trailing commas | Matches `trailing_commas` from registry |
| Final select | Matches `final_select` from registry |
| No `SELECT *` in transform CTE | All columns listed explicitly |
| No hard-coded schemas | Uses `{{ source() }}` only |

### 5.4 — Cross-file consistency

| Check | Rule |
|-------|------|
| `_sources.yml` columns match staging SQL columns | Same columns, casing transformed per pattern |
| Staging SQL columns match `schema.yml` columns | 1:1 match |
| **Staging SQL columns match the `.md` plan** | Every Transformations row produced an output column; every Excluded column is absent; every other source column is emitted as-is |
| **`.md` spec contains no business logic** | No `join`, `group by`, `union`, `from {{ ref(`, or aggregate functions in any expression |
| Model name in `schema.yml` matches filename | `stg_<source>__<table>` |
| No duplicate model names | Across all schema.yml files in the project |

### 5.5 — Validation report

```
## Bronze Layer Validation Report

| File | Check | Status | Detail |
|------|-------|--------|--------|
| _sources.yml | Structure | ✅ PASS | Matches inferred pattern |
| _sources.yml | Naming | ✅ PASS | Casing matches registry |
| stg_*.sql | CTE structure | ✅ PASS | CTE names match registry |
| stg_*.sql | Column case | ⚠️ FIXED | Renamed columns to match pattern |
| schema.yml | PK tests | ✅ PASS | unique + not_null on PK |
| Cross-file | Column consistency | ✅ PASS | All columns match |

Total: 6 checks — 5 passed, 1 auto-fixed, 0 failed
```

---

## Step 6 — Bronze Checklist

- [ ] `_sources.yml` has `database:` and `schema:` (allowed only in _sources.yml)
- [ ] `_sources.yml` quoting matches project pattern
- [ ] Staging model uses `{{ source('<SOURCE_NAME>', '<SOURCE_TABLE>') }}`
- [ ] Staging SQL CTE names match project pattern
- [ ] All columns renamed to project convention (e.g., snake_case)
- [ ] No `SELECT *` in transform CTE (all columns listed explicitly)
- [ ] No business logic in staging — 1:1 with source
- [ ] Every column listed in `schema.yml`
- [ ] PK column(s) have tests matching project pattern
- [ ] `stg_*.md` transformation spec exists alongside `.sql` and `schema.yml`
- [ ] SQL is mechanically derivable from the `.md` plan (Transformations / Excluded / as-is)
- [ ] `dbt build` passed with 0 test failures
- [ ] Validation report shows 0 failures

---

## Next Steps

| Action | Skill |
|--------|-------|
| Run table EDA / data-quality scan first | `$data-profiling-eda` |
| Build silver (intermediate) layer | `$onboard-silver-layer` |
| Build gold (marts) layer directly | `$onboard-gold-layer` |
| Full pipeline (EDA → bronze → silver → gold) | `$onboard-new-source` |

---

## Example Invocation

```
$onboard-bronze-layer

Database:    AMAZON_AND_ECOMMERCE_WEBSITES_PRODUCT_VIEWS_AND_PURCHASES
Schema:      DATAFEEDS
Table:       PRODUCT_VIEWS_AND_PURCHASES
Source name: datafeeds
EDA report:  specs/datafeeds/_eda/product_views_and_purchases__eda.md
```

If the EDA report does not yet exist, invoke `$data-profiling-eda` first — then
re-run this skill with the resulting path.
