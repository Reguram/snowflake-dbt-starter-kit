# Model Specifications (`specs/`)

**BA drop-zone for plain-English (or Excel) change requests against dbt
models.** The agent — running inside Snowflake Cortex Code, GitHub Copilot,
Claude Code, or any equivalent — reads the document and edits the dbt
models directly with its native file tools. No Python, no shell, no
external runtime required.

## Why

- BAs can't realistically curate hundreds of attributes in YAML.
- Snowflake Cortex Code can't execute arbitrary Python.
- The skill itself is the runtime: see [`spec-driven-model-sync`](../.agents/skills/spec-driven-model-sync/SKILL.md).

## Folder layout

```
specs/
├── README.md                                ← this file
├── _template_change_request.md              ← BA copies this to start
└── <source_name>/                           ← one folder per source
    ├── _changes/                            ← BA drops change docs here
    │   └── YYYY-MM-DD-<slug>.md|.txt|.xlsx
    ├── <model_name>.spec.yml                ← auto-generated/managed
    └── .lock/                               ← auto-managed, do NOT edit
        └── <model_name>.spec.lock.yml
```

**Rules**

| Item | Rule | Example |
|---|---|---|
| Change-doc location | `specs/<source>/_changes/` | `specs/japan_ecomm_data/_changes/2026-04-29-jane-doe.md` |
| Change-doc format | plain English `.md`/`.txt` or Excel `.xlsx` (CSV export accepted) | — |
| Spec file name | matches the model name + `.spec.yml` | `dim_items.spec.yml` |
| Spec source folder | matches `<source_name>` from `dbt_project.yml` vars | `specs/japan_ecomm_data/` |
| Versioning | `spec_version` bumps on every applied change; full history in git | `spec_version: 2` |

## How the skill uses this folder

1. BA writes plain-English bullets in `_changes/<file>.md` (or `.xlsx`).
2. Engineer (or the agent itself) invokes
   `$spec-driven-model-sync` and points it at the file + source.
3. The skill agent:
   - parses each bullet against a known directive table,
   - auto-bootstraps `<model>.spec.yml` on first use from the existing
     `.sql` + `schema.yml`,
   - applies edits in priority order (coalesce/concat → drop → rename →
     add/retype/redescribe/add_test),
   - rewrites `schema.yml` for affected columns and uses whole-word
     replace for renames in `.sql`,
   - appends `TODO[BA change]:` comments for unsafe SQL edits
     (drops/adds/derived columns) so the engineer integrates them with
     judgement,
   - bumps `spec_version` and writes the matching `.lock/` file so
     re-runs are idempotent.

If no `_changes/` document exists, the `onboard-*` skills fall back to
profiling-based scaffolding.

## Quick start (BA)

1. Copy [`_template_change_request.md`](_template_change_request.md) into
   `specs/<source>/_changes/<YYYY-MM-DD>-<slug>.md`.
2. Fill in plain-English bullets:
   ```
   - In dim_items, rename MAKER to manufacturer_name.
   - Drop column item_category from fct_sales.
   - Coalesce first_name and last_name into full_name in dim_customer.
   ```
3. Commit and ping the engineer (or open the change doc and ask the agent:
   *"Apply this change document to source `<source>`."*)

## Quick start (engineer)

Open the change document in your agent (Cortex Code / Copilot / Claude Code)
and say:

> "Apply `specs/<source>/_changes/<file>.md` to source `<source>`."

The agent will read, parse, preview, and (after your confirmation) apply
the edits. See [`spec-driven-model-sync`](../.agents/skills/spec-driven-model-sync/SKILL.md)
for the full procedure.
