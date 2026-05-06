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

1. **List only columns that need a transformation.** Each entry must include
   the SQL expression to apply.
2. **Any column not mentioned is moved as-is** — i.e., emitted with a plain
   snake_case rename (`"SOURCE_COL" as source_col`) and no logic.
3. **Excluded columns must be called out explicitly** in the *Excluded
   columns* section. Anything not listed there is included.
4. The spec is layer-scoped: bronze specs only describe 1:1 transforms (rename,
   cast, trim, parse, basic null-handling). Business logic belongs in silver.

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

| Source column        | Output column         | Type        | SQL expression                              | Reason          |
|----------------------|-----------------------|-------------|----------------------------------------------|-----------------|
| `ORDER_DATE`         | `order_date`          | date        | `TRY_TO_DATE("ORDER_DATE")`                  | safe cast       |
| `QUANTITY`           | `quantity`            | number      | `TRY_TO_NUMBER("QUANTITY")`                  | safe cast       |
| `CUSTOMER_NAME`      | `customer_name`       | string      | `TRIM("CUSTOMER_NAME")`                      | trim whitespace |
| `RAW_PAYLOAD:status` | `status`              | string      | `"RAW_PAYLOAD":status::string`               | flatten variant |
| `COL_A` + `COL_B`    | `row_key`             | string      | `{{ dbt_utils.generate_surrogate_key(['"COL_A"', '"COL_B"']) }}` | surrogate PK |

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

## How the bronze skill consumes this file

1. Look for `models/staging/<source>/stg_<source>__<table>.md`.
2. **If present** — parse the *Transformations* table and the *Excluded
   columns* list. Treat every other column from the EDA report as as-is.
3. **If absent** — scaffold the file from the EDA column profile:
   - Pre-fill obvious safe casts (date → `TRY_TO_DATE`, numeric strings →
     `TRY_TO_NUMBER`, free-text → `TRIM`).
   - Pre-fill *Excluded columns* with anything flagged in the EDA red-flags
     section (all-null, replication metadata, etc.).
   - All remaining columns are listed under *As-is columns*.
4. Generate the `.sql` so that:
   - Every row in *Transformations* becomes a `<expression> as <output>`
     line in the `staged` CTE.
   - Every column in *Excluded columns* is omitted from the SQL.
   - Every other column is emitted as `"<SOURCE_COL>" as <snake_col>`.
5. The `schema.yml` is generated from the same set of output columns.

## Validation rules (the bronze skill enforces these)

| Rule | Check |
|------|-------|
| Every `Transformations.Output column` appears in the SQL | Yes |
| Every `Excluded columns` entry is **absent** from the SQL | Yes |
| Every source column is either transformed, excluded, or as-is — no orphans | Yes |
| `Output column` set in `.md` matches column set in `schema.yml` | Yes |
| No business logic (joins, aggregates, case logic) in the spec | Bronze is 1:1 |

If any rule fails, the bronze skill reports it and stops before writing files.
