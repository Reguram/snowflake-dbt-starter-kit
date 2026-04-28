---
name: onboard-bronze-layer
description: >
  Bronze layer (staging) onboarding: profile a Snowflake source table, extract project patterns,
  generate _sources.yml + staging SQL + schema.yml with tests. Works on existing projects
  (infers patterns) and greenfield projects (uses default scaffolding). Portable across dbt
  projects — no hardcoded paths or names.
  Use when: creating a staging model for a new source table, building the bronze layer,
  generating _sources.yml, profiling a new Snowflake table.
  Triggers: bronze, staging, new source, profile table, _sources.yml, stg_ model.
tools: ["bash", "edit", "mcp"]
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "1.0"
---

# Onboard Bronze Layer (Staging)

> Discovers a Snowflake source table, profiles all columns, infers project style patterns
> (or uses default scaffolding), and generates source-conformed staging models.
> Bronze = 1:1 with raw data — rename columns, cast types, no business logic.

## Required Inputs

When the user invokes this skill, collect these parameters (ask if not provided):

| Parameter | Example | Description |
|-----------|---------|-------------|
| `SOURCE_DATABASE` | `MY_SNOWFLAKE_DB` | Snowflake database containing the raw table |
| `SOURCE_SCHEMA` | `RAW_DATA` | Schema inside that database |
| `SOURCE_TABLE` | `ORDERS` | Raw table name (UPPER_CASE in Snowflake) |
| `SOURCE_NAME` | `my_source` | Short snake_case alias for folders and naming |

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

## Step 2 — Profile the Source Table

Run these queries against `<SOURCE_DATABASE>.<SOURCE_SCHEMA>.<SOURCE_TABLE>`:

```sql
-- Column metadata
DESCRIBE TABLE <SOURCE_DATABASE>.<SOURCE_SCHEMA>.<SOURCE_TABLE>;

-- Row count
SELECT COUNT(*) AS row_count FROM <SOURCE_DATABASE>.<SOURCE_SCHEMA>.<SOURCE_TABLE>;

-- Sample data
SELECT * FROM <SOURCE_DATABASE>.<SOURCE_SCHEMA>.<SOURCE_TABLE> LIMIT 10;
```

Then profile each column:

```sql
SELECT
    '<COL>' AS column_name,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT "<COL>") AS distinct_count,
    COUNT(*) - COUNT("<COL>") AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT("<COL>")) / COUNT(*), 1) AS null_pct,
    ROUND(100.0 * COUNT(DISTINCT "<COL>") / NULLIF(COUNT("<COL>"), 0), 1) AS uniqueness_pct
FROM <SOURCE_DATABASE>.<SOURCE_SCHEMA>.<SOURCE_TABLE>;
```

Report a summary table:

| Column | Type | Nulls% | Distinct | Unique% | Classification |
|--------|------|--------|----------|---------|----------------|
| ... | ... | ... | ... | ... | PK / dimension / metric / date / exclude |

> See [references/column-classification.md](references/column-classification.md) for
> classification rules.

---

## Step 3 — Generate Bronze Layer Files

Create three files under `models/staging/<SOURCE_NAME>/`:

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

### File 2: `stg_<SOURCE_NAME>__<table_lower>.sql`

Generate using the pattern from Step 1.4 (inferred or default):

```sql
with source as (
    select * from {{ source('<SOURCE_NAME>', '<SOURCE_TABLE>') }}
),

staged as (
    select
        -- Rename EVERY column from source casing to snake_case
        -- Cast types if needed: TRY_TO_DATE for dates, TRY_TO_NUMBER for numbers
        -- Do NOT add business logic — bronze is 1:1 with source
    from source
)

select * from staged
```

**Rules:**
- List ALL columns explicitly in the transform CTE — no `SELECT *`
- Rename columns to snake_case (or match the project's convention)
- Use safe type casts (`TRY_TO_*` on Snowflake)
- If no single natural PK, create a surrogate: `{{ dbt_utils.generate_surrogate_key(['col1', 'col2']) }} as row_key`
- Match CTE names, keyword case, indentation from the pattern registry

### File 3: `schema.yml`

Generate using the pattern from Step 1.5 (inferred or default):

```yaml
version: 2

models:
  - name: stg_<SOURCE_NAME>__<table_lower>
    description: "Staged <SOURCE_TABLE> from <SOURCE_NAME> — renamed columns, 1:1 with source"
    columns:
      # Every column from the SQL output
      # PK: unique + not_null tests
      # Non-PK: name + description (match inferred test pattern)
```

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
| Files present | `_sources.yml`, `stg_*.sql`, `schema.yml` | Create missing |
| File naming | `stg_<SOURCE_NAME>__<table_lower>.sql` (double underscore) | Rename |
| No orphan SQL | Every `.sql` has a `schema.yml` entry | Add entry |
| No orphan YAML | Every `schema.yml` entry has a `.sql` file | Remove entry |

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
- [ ] `dbt build` passed with 0 test failures
- [ ] Validation report shows 0 failures

---

## Next Steps

| Action | Skill |
|--------|-------|
| Build silver (intermediate) layer | `$onboard-silver-layer` |
| Build gold (marts) layer directly | `$onboard-gold-layer` |
| Full pipeline (bronze → silver → gold) | `$onboard-new-source` |

---

## Example Invocation

```
$onboard-bronze-layer

Database: AMAZON_AND_ECOMMERCE_WEBSITES_PRODUCT_VIEWS_AND_PURCHASES
Schema: DATAFEEDS
Table: PRODUCT_VIEWS_AND_PURCHASES
Source name: datafeeds
```
