# Bronze Transformation Spec — `<stg_model>.md`

Every staging (bronze) model is now authored as a **trio**:

```
models/staging/<source_name>/
├── stg_<source>__<table>.sql      # generated SQL (1:1 transform of source)
├── stg_<source>__<table>.yml      # schema.yml entry for this model only (or merged into schema.yml)
└── stg_<source>__<table>.md       # transformation spec — source of truth
```

The `.md` file is **the source of truth for column transformations**. The
agent reads it (or scaffolds it on first run) and generates the `.sql` from it.
The SQL is mechanically derivable from the spec — never edit the SQL by hand
without first updating the spec.

## Authoring rules (per the team standard)

1. **Describe transforms in plain English, not SQL.** Each row in the
   *Transformations* table carries a natural-language *description* of what
   the column should be — e.g. *"total sales divided by total volume"*,
   *"safely cast to date"*, *"trim whitespace"*. The agent translates the
   description into a SQL expression when it generates the `.sql` file.
2. **List only columns that need a transformation.** Columns that are a
   plain rename do not belong here.
3. **Any column not mentioned is moved as-is** — emitted with a plain
   snake_case rename (`"SOURCE_COL" as source_col`) and no logic.
4. **Excluded columns must be called out explicitly** in the *Excluded
   columns* section. Anything not listed there is included.
5. The spec is layer-scoped: bronze specs only describe 1:1 transforms (rename,
   cast, trim, parse, simple null-handling, simple per-row arithmetic on
   columns of the **same row**, surrogate keys). Joins, aggregates, window
   functions, and any cross-row logic belong in silver.
6. The agent fills in the *Resolved SQL* column after generation, so the spec
   doubles as a record of what was actually emitted. Reviewers compare it
   against the description.

## Template

````markdown
# Transformations — `stg_<source>__<table>`

**Source:** `<SOURCE_DATABASE>.<SOURCE_SCHEMA>.<SOURCE_TABLE>`
**Generated SQL:** [`stg_<source>__<table>.sql`](./stg_<source>__<table>.sql)
**Last updated:** <YYYY-MM-DD>

> Default rule: any column NOT listed in the *Transformations* table or the
> *Excluded columns* list is moved through with a plain snake_case rename and
> no transformation.

## Transformations

<!-- Author the first four columns in natural language. The agent fills in
     the "Resolved SQL" column when it generates the .sql file. -->

| Output column     | Type    | Source column(s)             | Description (natural language)                                       | Resolved SQL (auto-filled) |
|-------------------|---------|------------------------------|----------------------------------------------------------------------|----------------------------|
| `order_date`      | date    | `ORDER_DATE`                 | Safely cast to a date; invalid values become null.                   | `TRY_TO_DATE("ORDER_DATE")` |
| `quantity`        | number  | `QUANTITY`                   | Safely cast to a number; invalid values become null.                 | `TRY_TO_NUMBER("QUANTITY")` |
| `customer_name`   | string  | `CUSTOMER_NAME`              | Trim leading and trailing whitespace.                                | `TRIM("CUSTOMER_NAME")` |
| `status`          | string  | `RAW_PAYLOAD`                | Pull the `status` field out of the RAW_PAYLOAD JSON as text.         | `"RAW_PAYLOAD":status::string` |
| `avg_unit_price`  | number  | `TOTAL_SALE`, `TOTAL_VOLUME` | Total sale divided by total volume; null when volume is 0 or null.   | `div0null("TOTAL_SALE", "TOTAL_VOLUME")` |
| `row_key`         | string  | `COL_A`, `COL_B`             | Surrogate key built from COL_A and COL_B.                            | `{{ dbt_utils.generate_surrogate_key(['"COL_A"', '"COL_B"']) }}` |

## Excluded columns

<!-- One bullet per column. Anything not listed here is INCLUDED. -->
- `INTERNAL_HASH` — internal Snowflake bookkeeping, not analytic value
- `_FIVETRAN_DELETED` — replication metadata; handled upstream

## As-is columns (informational)

<!-- Optional. The agent enumerates these for traceability. The list does NOT
     drive generation — anything not transformed and not excluded is as-is. -->
- `COUNTRY_REGION` → `country_region`
- `PROVINCE_STATE` → `province_state`
- `ISO3166_1`      → `iso3166_1`
````

## Natural-language vocabulary the agent understands

The agent maps common phrases to canonical Snowflake SQL. Authors do not need
to memorise this list — the agent will ask for clarification on anything
ambiguous — but these phrasings are guaranteed to translate cleanly:

| Description phrase                                            | Resolved SQL                                              |
|---------------------------------------------------------------|------------------------------------------------------------|
| "safely cast to date" / "parse as date"                       | `TRY_TO_DATE("COL")`                                       |
| "safely cast to timestamp"                                    | `TRY_TO_TIMESTAMP("COL")`                                  |
| "safely cast to number" / "parse as number"                   | `TRY_TO_NUMBER("COL")`                                     |
| "safely cast to decimal(P,S)"                                 | `TRY_TO_DECIMAL("COL", P, S)`                              |
| "trim whitespace"                                             | `TRIM("COL")`                                              |
| "uppercase" / "lowercase"                                     | `UPPER("COL")` / `LOWER("COL")`                            |
| "treat empty string as null"                                  | `NULLIF(TRIM("COL"), '')`                                  |
| "coalesce A and B"                                            | `COALESCE("A", "B")`                                       |
| "X divided by Y" / "ratio of X to Y"                          | `div0null("X", "Y")` (null-safe; Snowflake `DIV0NULL`)     |
| "X minus Y" / "X plus Y" / "X times Y"                        | `("X" - "Y")` / `("X" + "Y")` / `("X" * "Y")`              |
| "extract field F from variant V as type T"                    | `"V":F::T`                                                 |
| "surrogate key from A, B, C"                                  | `{{ dbt_utils.generate_surrogate_key(['"A"','"B"','"C"']) }}` |
| "boolean flag where COL = 'Y'"                                | `("COL" = 'Y')`                                            |
| "default to 0 when null" / "default to '' when null"          | `COALESCE("COL", 0)` / `COALESCE("COL", '')`               |

If a description does not match any pattern above, the agent must:
1. Propose a SQL expression in the *Resolved SQL* column,
2. Surface it in its summary output, and
3. Ask the user to confirm before generating the `.sql` file.

## How the bronze skill consumes this file

1. Look for `models/staging/<source>/stg_<source>__<table>.md`.
2. **If present** — parse the *Transformations* table and the *Excluded
   columns* list. For each transform row:
   - Read the *Output column*, *Type*, *Source column(s)*, and *Description*.
   - Resolve the *Description* into a Snowflake SQL expression using the
     vocabulary above (or, for novel phrasings, compose from primitive
     casts/operators and ask the user to confirm).
   - Write the resolved expression back into the *Resolved SQL* column so
     the spec stays self-documenting.
   - Validate that every name in *Source column(s)* exists in the EDA column
     profile.
   - Treat every other column from the EDA report as as-is.
3. **If absent** — scaffold the file from the EDA column profile:
   - Pre-fill obvious safe casts as natural-language descriptions
     (e.g. *"safely cast to date"* for date-shaped text columns,
     *"safely cast to number"* for numeric strings,
     *"trim whitespace"* for free-text columns).
   - Pre-fill *Excluded columns* with anything flagged in the EDA red-flags
     section (all-null, replication metadata, etc.).
   - Leave *Resolved SQL* empty in the scaffold; it is filled in on the
     first generation pass.
   - All remaining columns are listed under *As-is columns*.
4. Generate the `.sql` so that:
   - Every row in *Transformations* becomes a `<resolved expression> as <output>`
     line in the `staged` CTE.
   - Every column in *Excluded columns* is omitted from the SQL.
   - Every other column is emitted as `"<SOURCE_COL>" as <snake_col>`.
5. The `schema.yml` is generated from the same set of output columns.

## Validation rules (the bronze skill enforces these)

| Rule | Check |
|------|-------|
| Every transform row has a non-empty *Description* | Yes |
| Every transform row has at least one entry in *Source column(s)* | Yes |
| Every *Source column* exists in the source table (per the EDA report) | Yes |
| Every *Resolved SQL* expression is non-empty after generation | Yes |
| Every `Output column` appears in the generated SQL | Yes |
| Every `Excluded columns` entry is **absent** from the SQL | Yes |
| Every source column is either transformed, excluded, or as-is — no orphans | Yes |
| `Output column` set in `.md` matches column set in `schema.yml` | Yes |
| No business logic (joins, aggregates, case-on-other-rows) in the spec | Bronze is 1:1 |

If any rule fails, the bronze skill reports it and stops before writing files.
