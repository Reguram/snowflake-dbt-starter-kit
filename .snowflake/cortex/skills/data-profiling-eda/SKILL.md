---
name: data-profiling-eda
description: >
  Data Analyst Agent for Snowflake tables. Given a fully-qualified table
  (DATABASE.SCHEMA.TABLE), runs structural inspection, column-level profiling,
  cardinality / null analysis, distribution and outlier checks, candidate primary-key
  detection, semantic role classification (PK / dimension / metric / date / FK / exclude),
  data-quality red flags, and high-level findings — then writes a Markdown EDA report
  to `specs/<SOURCE_NAME>/_eda/<table>__eda.md`.
  Pure profiling skill — does NOT generate dbt models. Designed to be chained BEFORE
  `onboard-bronze-layer` so the bronze skill can consume the report instead of
  re-profiling.
  Use when: a user asks to profile a table, run EDA, "what's in this table",
  data discovery, sanity-check a new source, or before bronze/staging onboarding.
  Triggers: profile table, EDA, data profiling, explore data, data discovery,
  describe table contents, column statistics, null analysis, cardinality,
  data quality scan, what is in this table, analyse this table.
tools: ["bash", "edit", "mcp"]
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "1.0"
---

# Data Profiling & EDA (Data Analyst Agent)

> Profiles a Snowflake source table and produces a Markdown EDA report.
> This skill **does not** create dbt models, _sources.yml, or staging SQL — it only
> analyses data and writes findings. Downstream skills (`onboard-bronze-layer`,
> `onboard-new-source`) consume the report instead of re-profiling.

---

## Required Inputs

Collect from the user (ask only if missing):

| Parameter | Example | Description |
|-----------|---------|-------------|
| `SOURCE_DATABASE` | `MY_SNOWFLAKE_DB` | Snowflake database |
| `SOURCE_SCHEMA` | `RAW_DATA` | Schema inside that database |
| `SOURCE_TABLE` | `ORDERS` | Table name (UPPER_CASE in Snowflake) |
| `SOURCE_NAME` | `my_source` | Short snake_case alias used for the report path |

Derived:
- Report path: `specs/<SOURCE_NAME>/_eda/<SOURCE_TABLE_lower>__eda.md`
- Fully-qualified name: `<SOURCE_DATABASE>.<SOURCE_SCHEMA>.<SOURCE_TABLE>`

---

## Step 1 — Structural Inspection

Use the available Snowflake MCP / SQL tooling. Do not assume a specific runner; if no
direct connector is available, emit the SQL and ask the user to run it.

```sql
-- 1.1 Column metadata
DESCRIBE TABLE <DB>.<SCHEMA>.<TABLE>;

-- 1.2 Row count
SELECT COUNT(*) AS row_count FROM <DB>.<SCHEMA>.<TABLE>;

-- 1.3 Sample rows
SELECT * FROM <DB>.<SCHEMA>.<TABLE> LIMIT 10;

-- 1.4 Object metadata (optional, may be unavailable)
SELECT
    BYTES, ROW_COUNT, CREATED, LAST_ALTERED, COMMENT
FROM <DB>.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = '<SCHEMA>' AND TABLE_NAME = '<TABLE>';
```

Capture: column list with types, total rows, table size (if available), creation /
last-altered timestamps, table comment.

---

## Step 2 — Per-Column Profiling

For every column, run:

```sql
SELECT
    '<COL>' AS column_name,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT "<COL>") AS distinct_count,
    COUNT(*) - COUNT("<COL>") AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT("<COL>")) / COUNT(*), 2) AS null_pct,
    ROUND(100.0 * COUNT(DISTINCT "<COL>") / NULLIF(COUNT("<COL>"), 0), 2) AS uniqueness_pct,
    MIN("<COL>")::VARCHAR AS min_value,
    MAX("<COL>")::VARCHAR AS max_value
FROM <DB>.<SCHEMA>.<TABLE>;
```

For numeric columns, additionally run:

```sql
SELECT
    '<COL>' AS column_name,
    AVG("<COL>") AS avg_value,
    STDDEV("<COL>") AS stddev_value,
    APPROX_PERCENTILE("<COL>", 0.25) AS p25,
    APPROX_PERCENTILE("<COL>", 0.50) AS p50,
    APPROX_PERCENTILE("<COL>", 0.75) AS p75,
    APPROX_PERCENTILE("<COL>", 0.95) AS p95,
    SUM(CASE WHEN "<COL>" < 0 THEN 1 ELSE 0 END) AS negative_count,
    SUM(CASE WHEN "<COL>" = 0 THEN 1 ELSE 0 END) AS zero_count
FROM <DB>.<SCHEMA>.<TABLE>;
```

For low-cardinality string / boolean columns (≤ 50 distinct values), capture the value
distribution:

```sql
SELECT "<COL>" AS value, COUNT(*) AS freq
FROM <DB>.<SCHEMA>.<TABLE>
GROUP BY 1 ORDER BY 2 DESC LIMIT 50;
```

For DATE / TIMESTAMP columns, capture the time range and gaps:

```sql
SELECT
    MIN("<COL>") AS min_ts,
    MAX("<COL>") AS max_ts,
    DATEDIFF('day', MIN("<COL>"), MAX("<COL>")) AS span_days,
    COUNT(DISTINCT DATE_TRUNC('day', "<COL>")) AS distinct_days
FROM <DB>.<SCHEMA>.<TABLE>;
```

---

## Step 3 — Primary-Key Detection

1. **Single-column PK candidates** — any column with `null_pct = 0` AND
   `uniqueness_pct = 100`.
2. **Composite PK candidates** — when no single PK exists, test plausible 2- and
   3-column combinations from `*_id`, `*_key`, `*_date` columns:

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT CONCAT_WS('|', "<C1>", "<C2>")) AS combo_distinct
FROM <DB>.<SCHEMA>.<TABLE>;
```

Mark a combination as a composite PK candidate when `combo_distinct = total_rows`.

---

## Step 4 — Semantic Role Classification

Apply the rules in [`references/column-classification.md`](references/column-classification.md)
to assign each column one of:

`PK` · `FK` · `date_dimension` · `categorical_dimension` · `entity_dimension` ·
`high_cardinality_dimension` · `sum_metric` · `avg_metric` · `boolean_flag` ·
`semi_structured` · `exclude`

Inputs to the classifier: data type, null %, distinct count, uniqueness %, naming pattern,
sample values.

---

## Step 5 — Data-Quality Red Flags

Flag any of the following in a dedicated section of the report:

| Flag | Trigger |
|------|---------|
| **Empty table** | `row_count = 0` |
| **Single-row table** | `row_count = 1` (likely metadata) |
| **All-null column** | `null_pct = 100` |
| **Constant column** | `distinct_count = 1` and `null_pct < 100` |
| **High null** | `null_pct ≥ 50` on a non-optional-looking column |
| **Suspected duplicates** | No PK candidate and `uniqueness_pct < 100` on every column |
| **Negative values on amount column** | `negative_count > 0` on `*_amount`, `*_price`, `*_qty` |
| **Future dates** | `max_ts > CURRENT_TIMESTAMP()` on `*_date`, `*_at` |
| **Wide cardinality on suspected categorical** | `distinct_count > 100` on `*_status`, `*_type` |
| **Variant / array** | Type is `VARIANT` / `ARRAY` / `OBJECT` — needs `LATERAL FLATTEN` downstream |

---

## Step 6 — Write the EDA Report

Create the directory if it does not exist, then write the report file:

```
specs/<SOURCE_NAME>/_eda/<source_table_lower>__eda.md
```

Use this template (replace placeholders with real values):

```markdown
# EDA Report — <SOURCE_DATABASE>.<SOURCE_SCHEMA>.<SOURCE_TABLE>

- **Source alias:** `<SOURCE_NAME>`
- **Generated:** <ISO timestamp>
- **Generated by:** `data-profiling-eda` skill

## 1. Overview
| Field | Value |
|-------|-------|
| Database | `<SOURCE_DATABASE>` |
| Schema | `<SOURCE_SCHEMA>` |
| Table | `<SOURCE_TABLE>` |
| Row count | … |
| Column count | … |
| Size (bytes) | … |
| Created | … |
| Last altered | … |
| Table comment | … |

## 2. Column Profile
| # | Column | Type | Nulls % | Distinct | Unique % | Min | Max | Classification |
|---|--------|------|---------|----------|----------|-----|-----|----------------|
| 1 | … | … | … | … | … | … | … | PK / dimension / metric / date / FK / exclude |
…

## 3. Primary Key Analysis
- **Single-column PK candidate(s):** `<col>` (null_pct=0, uniqueness=100%)
- **Composite PK candidate(s):** `(<col1>, <col2>)` — combo_distinct == total_rows
- **No PK detected:** propose surrogate key `dbt_utils.generate_surrogate_key([...])`

## 4. Numeric Column Stats
| Column | Avg | Stddev | P25 | P50 | P75 | P95 | Negatives | Zeros |
|--------|-----|--------|-----|-----|-----|-----|-----------|-------|
…

## 5. Categorical Distributions (≤ 50 distinct)
### `<column>`
| Value | Freq |
|-------|------|
…

## 6. Date / Time Coverage
| Column | Min | Max | Span (days) | Distinct days |
|--------|-----|-----|-------------|---------------|
…

## 7. Data Quality Red Flags
- ⚠️ … (one bullet per flag from Step 5)

## 8. Sample Rows
```sql
SELECT * FROM <DB>.<SCHEMA>.<TABLE> LIMIT 10;
```
| col_a | col_b | … |
|-------|-------|---|
…

## 9. Bronze-Layer Recommendations (Hand-off)
- **Suggested PK column(s):** …
- **Columns to exclude from staging:** … (ETL metadata, all-null, etc.)
- **Type casts to apply:** `TRY_TO_DATE`, `TRY_TO_NUMBER`, `TRIM` on …
- **Surrogate-key recipe (if no natural PK):** `dbt_utils.generate_surrogate_key([...])`
- **Accepted-values test candidates:** `<col>` ∈ {…}
- **Variant / flatten candidates:** …

## 10. Open Questions for the Engineer
- …
```

If `specs/<SOURCE_NAME>/_eda/` does not exist, create it. Do **not** overwrite an existing
report without explicit confirmation — instead, write to
`<table_lower>__eda__<YYYYMMDD-HHMM>.md` and note this in the response.

---

## Step 7 — Summarize and Hand Off

After writing the file, respond with:

1. **One-paragraph executive summary** (row count, PK status, biggest data-quality concern,
   anything unusual).
2. **Path to the report file** (relative to repo root).
3. **Suggested next step:**
   ```
   → Hand off to $onboard-bronze-layer with EDA_REPORT=<path>
   ```

Do not generate `_sources.yml`, staging SQL, or schema.yml — those belong to the bronze
skill, which will read this report.

---

## Checklist

- [ ] All required inputs collected (DB / schema / table / source name)
- [ ] `DESCRIBE TABLE` and row-count run
- [ ] Per-column profiling run for every column
- [ ] Numeric stats run for numeric columns
- [ ] Distribution captured for low-cardinality columns
- [ ] PK / composite-PK detection performed
- [ ] Each column has a semantic classification
- [ ] Data-quality red flags evaluated
- [ ] Report written under `specs/<SOURCE_NAME>/_eda/`
- [ ] Executive summary returned to user
- [ ] Hand-off line to `$onboard-bronze-layer` included

---

## Related Skills

| Next Step | Skill |
|-----------|-------|
| Build the bronze (staging) layer using this report | `$onboard-bronze-layer` |
| Run the full medallion pipeline (bronze → silver → gold) | `$onboard-new-source` |
| Build silver intermediate model | `$onboard-silver-layer` |
| Build gold mart model | `$onboard-gold-layer` |
