---
name: spec-driven-model-sync
description: >
  BA-driven dbt model change pipeline. The Business Analyst writes change
  requests in plain English (.md / .txt) or Excel (.xlsx) and drops them in
  specs/<source>/_changes/. The agent reads the document, parses each
  directive, auto-bootstraps a per-model spec from the existing dbt artifacts
  on first use, and applies precise edits (rename / add / drop / coalesce /
  concat / retype / redescribe / add_test) to the model .sql and schema.yml
  using native file-edit tools — NO Python or other runtimes required, so it
  works inside Snowflake Cortex Code, GitHub Copilot, Claude Code and any
  agent that can read/write files. A lockfile records the last-applied state
  so re-runs are idempotent.
  Use when: a BA hands you a plain-English change document, an Excel sheet
  of attribute changes, or asks to rename / coalesce / drop / re-type
  columns across one or more models.
  Triggers: BA document, change request, requirements doc, rename column,
  coalesce columns, concat columns, drop column, add column, apply spec,
  iterate model.
tools: ["edit", "read", "search"]
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "3.0"
---

# Spec-Driven Model Sync (BA-Driven, Runtime-Free)

> The BA writes a plain-English document (or Excel sheet) describing
> column-level changes. The agent — running inside Cortex Code, Copilot,
> Claude Code, or any equivalent — reads the document and edits the dbt
> models directly with its native file tools. **No Python, no shell
> commands, no external runtime.**

## Why this exists

A BA can't realistically curate hundreds of attributes in a YAML template,
and Snowflake Cortex Code agents can't execute arbitrary Python. The
solution is to put the workflow entirely inside the agent: parse the BA's
document, edit the files, write the spec + lockfile.

```
specs/<source>/_changes/<file>.md|.txt|.xlsx          ← BA's input
            │
            ▼
   ┌─────────────────────────────────────┐
   │  AGENT (this skill)                 │
   │  • read change doc                  │
   │  • match each line to a directive   │
   │  • read existing model .sql + yml   │
   │  • apply edits via str-replace      │
   │  • write spec + lockfile            │
   └─────────────────────────────────────┘
            │
            ▼
   models/<layer>/<source>/{<model>.sql, schema.yml}
   specs/<source>/{<model>.spec.yml, .lock/<model>.spec.lock.yml}
```

## Required Inputs

| Parameter | Example |
|---|---|
| `CHANGE_DOC` | `specs/japan_ecomm_data/_changes/2026-04-29-jane-doe.md` |
| `SOURCE_NAME` | `japan_ecomm_data` |

If either is missing, ask the user. Do not guess.

## What the BA writes (plain English)

One directive per bullet. Case-insensitive. Backticks optional. Lines that
don't match any pattern below are **reported back to the user as
`unparsed`** — never silently dropped.

| Intent | Pattern (regex, case-insensitive) | Example |
|---|---|---|
| Rename | `In <model>, rename <old> to <new>` OR `rename <model>.<old> to <new>` | `In dim_items, rename MAKER to manufacturer_name.` |
| Add column | `Add column <name> to <model> (type: <t>; description: <d>; tests: <t1,t2>)` | `Add column is_active to dim_items (type: boolean; description: Item is for sale; tests: not_null).` |
| Drop column | `Drop column <name> from <model>` | `Drop column item_category from fct_sales.` |
| Coalesce → 1 col | `Coalesce <a> and <b> [and <c>...] into <new> in <model>` | `Coalesce MAKER and MODEL into manufacturer_model_label in dim_items.` |
| Concatenate → 1 col | `Concatenate <a> and <b> [and <c>...] into <new> in <model>` | `Concatenate first_name and last_name into full_name in dim_customer.` |
| Change type | `Change type of <model>.<col> to <new_type>` | `Change type of fct_sales.transaction_count to integer.` |
| Change description | `Change description of <model>.<col> to "<text>"` | `Change description of dim_items.ITEM_NAME to "Canonical product display name."` |
| Add test | `Add test <test_name> to <model>.<col>` | `Add test not_null to fct_sales.average_price.` |

Free-form headings (e.g. `## fct_sales`), prose paragraphs, and HTML
comments are ignored.

## What the BA writes (Excel — alternative)

If `CHANGE_DOC` is `.xlsx`, ask the user to export it as CSV in this exact
column order, OR open it as plain text via the agent's file reader and treat
each row as one directive. The agent is responsible for translating each row
into the same internal directive shape:

| action | model | old_name | new_name | name | type | description | tests | sources |
|---|---|---|---|---|---|---|---|---|
| rename | dim_items | MAKER | manufacturer_name | | | | | |
| add | dim_items | | | is_active | boolean | Item is for sale | not_null | |
| coalesce | dim_items | | manufacturer_model_label | | | | | MAKER, MODEL |
| drop | fct_sales | | | item_category | | | | |
| retype | fct_sales | | | transaction_count | integer | | | |

If `.xlsx` cannot be read directly by the agent, ask the BA to save the
sheet as `.csv` first.

---

## Procedure (the agent executes these steps in order)

### Step 0 — Validate inputs and read the change document

1. Confirm `CHANGE_DOC` exists. If not, stop and ask the user.
2. Read the entire change document.
3. Extract candidate directive lines: any `-` / `*` / numbered list line, or
   any non-blank non-heading line.
4. For each candidate, match against the patterns table above and produce
   a list of normalized **directives**, each with this shape:

   ```yaml
   action:    rename | add | drop | coalesce | concat | retype | redescribe | add_test
   model:     <model_name>
   old_name:  <col>           # rename only
   new_name:  <col>           # rename / coalesce / concat target
   name:      <col>           # add / drop / retype / redescribe / add_test target
   type:      <col-type>      # add / retype
   description: <text>        # add / redescribe
   tests:     [<test>, ...]   # add / add_test
   sources:   [<col>, ...]    # coalesce / concat
   source_line: "<verbatim line from BA doc>"
   ```

5. Print the parsed directives back to the user, plus any **unparsed** lines.
   Ask the user to confirm before any file edits. If they say "dry-run only",
   stop after this step.

### Step 1 — Group directives by model

Group the directive list by `model`. For each model, also record the affected
column names. The next steps loop per model.

### Step 2 — Locate the model on disk

For each `model` in the group, search in this order and stop at the first hit:

1. `models/marts/<SOURCE_NAME>/<model>.sql`
2. `models/intermediate/<SOURCE_NAME>/<model>.sql` (also try `int_<model>.sql`)
3. `models/staging/<SOURCE_NAME>/<model>.sql` (also try `stg_<SOURCE_NAME>__<model>.sql`)

Record:
- `MODEL_SQL_PATH`
- `MODEL_SCHEMA_PATH = <same-dir>/schema.yml`
- `LAYER` = `marts | intermediate | staging`

If the model isn't found, stop and ask the user to confirm the model name.

### Step 3 — Bootstrap the spec on first use (per model)

If `specs/<SOURCE_NAME>/<model>.spec.yml` does **not** exist:

1. Read `MODEL_SQL_PATH`. Find the **final projection** — the longest
   deduplicated `SELECT … FROM` column list (for CTE-heavy models, take the
   one feeding the final SELECT). Falls back: scan `as <alias>` tokens for
   identifiers if no explicit projection.
2. Read `MODEL_SCHEMA_PATH` and locate the block where `name: <model>`. Pull
   each column's `description` and `tests`.
3. Synthesize a spec file at `specs/<SOURCE_NAME>/<model>.spec.yml`:

   ```yaml
   spec_version: 1
   source_name: <SOURCE_NAME>
   model_name:  <model>
   layer:       <LAYER>
   materialization: table | view | incremental   # from {{ config(...) }} or default
   description: <copied from schema.yml block>
   bootstrap:
     from_sql:    <MODEL_SQL_PATH>
     from_schema: <MODEL_SCHEMA_PATH>
   upstream: []
   attributes:
     - id: attr_<col_lowercase>
       name: <col>
       type: <type from schema.yml or "string" if unknown>
       role: primary_key | dimension | metric | timestamp   # infer from name+tests
       description: <from schema.yml or "">
       tests: <from schema.yml or []>
   ```

4. Also write the matching lockfile at
   `specs/<SOURCE_NAME>/.lock/<model>.spec.lock.yml` mirroring
   `attributes` and `spec_version: 1`.

### Step 4 — Apply directives **in priority order**

This ordering matters — coalesce/concat must run before rename so they see
the original column names.

| Priority | Actions |
|---|---|
| 0 | `coalesce`, `concat` (read original names) |
| 1 | `drop` |
| 2 | `rename` |
| 3 | `add`, `retype`, `redescribe`, `add_test` |

For each directive:

- **rename** — In the spec attributes list, find the attribute whose `name ==
  old_name`; set `name = new_name`. In `MODEL_SQL_PATH`, do a **whole-word
  case-insensitive replace** of `old_name` → `new_name`. Use a regex
  boundary (`\b<old>\b` semantics — never substring-replace). In
  `MODEL_SCHEMA_PATH`, change the column entry's `name`.

- **drop** — Remove the attribute from the spec. Remove the column entry
  from `schema.yml`. **Do not** rewrite the SQL automatically — append a
  `TODO[BA change]:` comment block at the end of `MODEL_SQL_PATH`
  explaining that `<col>` should be removed from the projection. (The
  engineer integrates because deleting from arbitrary CTE chains is unsafe.)

- **add** — Append a new attribute to the spec with the requested
  type/description/tests. Append a column entry to `schema.yml`. Append a
  `TODO[BA change]:` comment to the SQL: `-- TODO[BA change]: add column
  <name> (<type>) — <description>`.

- **coalesce** / **concat** — Append a derived attribute to the spec
  (`role: dimension`, with `expression: COALESCE(<a>, <b>)` or
  `<a> || ' ' || <b>`). Append the column entry to `schema.yml`. Append
  a `TODO[BA change]:` comment to the SQL with the proposed CTE snippet.

- **retype** — In the spec, set `type` on the matching attribute. In
  `schema.yml`, update the `data_type` field if present. In SQL, attempt
  an in-place rewrite of any visible cast: `cast(<col> as ...)` →
  `cast(<col> as <new_type>)` and `<col>::...` → `<col>::<new_type>`.
  If neither pattern is present, append a `TODO[BA change]:` comment.

- **redescribe** — Update `description` on the spec attribute and on the
  schema.yml column entry. SQL is untouched.

- **add_test** — Append the test name to the attribute's `tests` list in
  the spec and to the schema.yml column entry's `tests:`. SQL untouched.

### Step 5 — Idempotency check (per directive)

Before applying, compare to the lockfile:

- If the directive has already been applied (e.g. `old_name` no longer
  exists in the lockfile, or the new state already matches), **skip with
  a `⚠ skipped` note** instead of failing.

### Step 6 — Bump versions and write lockfile

After all directives for the source have been applied:

1. In each modified `<model>.spec.yml`, increment `spec_version` by 1.
2. Rewrite each `.lock/<model>.spec.lock.yml` to mirror the **post-apply**
   state.
3. Print a one-line summary per model: number of changes applied vs skipped
   vs failed, plus the path of any SQL file that received `TODO[BA change]:`
   comments.

### Step 7 — Validate (optional, ask the user)

Suggest:

```sql
-- In Snowflake / dbt
dbt build --select <model_a> <model_b>
```

If the SQL has `TODO[BA change]:` comments, instruct the user to integrate
them before running `dbt build`. Schema.yml + spec are already in their
final state.

---

## Worked example (real models in this repo)

**Input:** [`specs/japan_ecomm_data/_changes/2026-04-29-jane-doe.md`](../../../specs/japan_ecomm_data/_changes/2026-04-29-jane-doe.md)

```
- In `dim_items`, rename `MAKER` to `manufacturer_name`.
- In `dim_items`, rename `MODEL` to `product_model`.
- Change description of `dim_items.ITEM_NAME` to "Canonical display name."
- Add column `is_active` to `dim_items` (type: boolean; description: ...; tests: not_null).
- Coalesce `MAKER` and `MODEL` into `manufacturer_model_label` in `dim_items`.
- In `fct_sales`, rename `total_sales` to `gross_sales_amount`.
- Change type of `fct_sales.transaction_count` to integer.
- Add test not_null to `fct_sales.average_price`.
- Drop column `item_category` from `fct_sales`.
```

**Outcome:**
- `fct_sales.sql`: `total_sales` → `gross_sales_amount` rewritten everywhere
  (whole-word). `item_category` flagged with a TODO at the end of the file.
- `fct_sales` block in `schema.yml`: column renamed, `not_null` added to
  `average_price`, `item_category` removed. **Other models in the file are
  untouched.**
- `dim_items`: spec auto-bootstrapped (7 attrs from the projection);
  coalesce + add + redescribe applied to spec/schema; SQL gets a TODO block
  because `dim_items.sql` is one minified line.
- Re-running the same document → every directive returns `⚠ skipped`
  (idempotent).

---

## Aspects covered

- ✅ **No Python or shell required** — agent does it all with file tools
- ✅ **Cortex-Code-safe** — works inside Snowflake's hosted agent runtime
- ✅ **Plain English input** — BA writes no YAML
- ✅ **Excel input** (via CSV export if needed)
- ✅ **Auto-bootstrap** — spec generated from existing model + schema.yml
- ✅ **Whole-word safe rename** — never rewrites substrings
- ✅ **Schema.yml authoritative** — surgical, only the affected model block
- ✅ **TODO markers** for ambiguous SQL edits — engineer integrates with judgement
- ✅ **Idempotent** — re-runs report skips, never duplicate
- ✅ **All actions:** rename, add, drop, coalesce, concat, retype, redescribe, add_test
- ✅ **Lockfile audit trail** committed alongside specs in git
- ✅ **Unparsed lines surfaced** — no silent drops

## Hooks for the onboarding skills

`$onboard-bronze-layer`, `$onboard-silver-layer`, `$onboard-gold-layer`, and
`$onboard-new-source` consult `specs/<SOURCE_NAME>/_changes/` first. If a
change document is present and addresses the model being created/modified,
they delegate here. Otherwise they fall back to profiling-based generation.

## Future extensions

- **LLM parse upgrade** — replace the regex pattern table with a single
  call to `AI_EXTRACT` / `AI_COMPLETE` for freer prose.
- **Snowflake column rename hooks** — emit `ALTER TABLE … RENAME COLUMN`
  for externally-managed tables.
- **Cross-model impact** — scan downstream models (semantic views, marts
  using `ref(<model>)`) and emit a TODO list.
- **Auto-regen** of semantic views & Cortex Analyst YAML after apply.
- **CI gate** — fail PRs where the lockfile drifts from the spec.
- **Rollback** — re-apply the previous lockfile to revert.

## Quick reference

The agent runs the entire procedure **without invoking any external tool**.
There are no commands to memorize. Just hand it:

> "Apply `specs/<source>/_changes/<file>.md` to source `<source>`."

…and it does Steps 0–6 above, then asks whether to run `dbt build`.
