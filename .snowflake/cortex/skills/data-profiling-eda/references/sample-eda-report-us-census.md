# Sample EDA Report — US Census Neighborhood (Multi-Table Source)

This is a **real-world reference** showing what an EDA report looks like for a
Snowflake Marketplace dataset with 70+ tables, wide demographic tables, VARIANT
columns, and multiple data years. Use it as a template when profiling large,
multi-table sources.

**Source:** `US_OPEN_CENSUS_DATA__NEIGHBORHOOD_INSIGHTS__FREE_DATASET.PUBLIC`
**Alias:** `us_census_neighborhood`
**Full report:** [`specs/us_census_neighborhood/_eda/us_open_census_data__eda.md`](../../../../../specs/us_census_neighborhood/_eda/us_open_census_data__eda.md)

---

## What makes this a good reference

| Aspect | Why it's instructive |
|--------|---------------------|
| **Multi-table source** | 73 objects — shows how to inventory and categorize tables by domain |
| **Wide tables** | B25 has 100s of columns — demonstrates selective-projection guidance |
| **VARIANT columns** | 7 semi-structured fields in Patterns — documents `LATERAL FLATTEN` needs |
| **Unix timestamps as VARCHAR** | Shows a common red flag and the recommended staging cast |
| **Sentinel values** | `-666666666` in ACS margin-of-error columns — documents domain-specific null encoding |
| **Composite PK** | FIPS Codes table uses `(STATE_FIPS, COUNTY_FIPS)` |
| **Near-PK with nulls** | Patterns table has 1 null in `CENSUS_BLOCK_GROUP` — shows edge case |
| **Cross-year schema drift** | 2019 vs 2020 tables have different object counts — surfaces comparison questions |
| **Typed bronze hand-off** | Section 10 gives per-table staging advice that `onboard-bronze-layer` consumes |

---

## Report structure at a glance

The EDA report follows the canonical sections defined in `SKILL.md`:

```
1.  Overview              — database, schema, table count, row counts, storage
2.  Key Tables — Profiles — per-column: type, nulls%, distinct, role, notes
3.  Primary Key Analysis  — PK candidates per table with status (✅ / ⚠️)
4.  Numeric Column Stats  — avg / min / max / median / percentiles
5.  Categorical Dists     — value frequency tables for low-cardinality columns
6.  Date / Time Coverage  — min/max dates, span, gaps
7.  Data Quality Red Flags — ⚠️ flags with recommended staging actions
8.  Sample Rows           — 3–5 representative rows per key table
9.  Table Topic Coverage  — domain map (ACS B/C series → human-readable topics)
10. Bronze Recommendations — per-table hand-off to onboard-bronze-layer
11. Open Questions         — engineer-facing questions before modeling
```

---

## Key patterns to replicate in your own EDA reports

### 1. Table inventory (Section 1)

For multi-table sources, group tables by category and include row counts:

```markdown
| Category | Tables (2019) | Tables (2020) | Row Count | Notes |
|----------|--------------|--------------|-----------|-------|
| ACS B-series demographics | 23 | 23 | 220,333 | Estimates + Margin of Error |
| Geometry / Geography | 2 | 1 | 220,740 | Boundary polygons + WKT |
| Metadata — Field Descriptions | 1 | 1 | 8,120 | ACS variable dictionary |
```

### 2. Column role classification (Section 2)

Assign every column a role from the classification taxonomy:

```markdown
| # | Column | Type | Nulls % | Distinct | Role | Notes |
|---|--------|------|---------|----------|------|-------|
| 1 | CENSUS_BLOCK_GROUP | VARCHAR | 0% | 220,333 | PK | 12-digit FIPS code |
| 2 | AMOUNT_LAND | NUMBER(38,0) | 0% | high | sum_metric | Land area in sq meters |
| 6 | VISITOR_HOME_CBGS | VARIANT | low | — | semi_structured | JSON dict: CBG→count |
```

### 3. Red flags with staging actions (Section 7)

Each red flag should include a concrete SQL fix for the bronze skill:

```markdown
- ⚠️ **Unix timestamps as VARCHAR** — `DATE_RANGE_START` and `DATE_RANGE_END`
  in `2019_CBG_PATTERNS` are unix epoch integers as VARCHAR.
  Apply `TO_TIMESTAMP(DATE_RANGE_START::INT)` in staging.
- ⚠️ **1 null CENSUS_BLOCK_GROUP in Patterns** — should be excluded:
  `WHERE CENSUS_BLOCK_GROUP IS NOT NULL`.
- ⚠️ **ACS sentinel value -666666666** in margin-of-error columns — cast to NULL.
```

### 4. Bronze hand-off (Section 10)

Per-table guidance that `onboard-bronze-layer` reads directly:

```markdown
### `2019_CBG_PATTERNS`
- **Cast dates:** `TO_TIMESTAMP(DATE_RANGE_START::INT)` ...
- **Exclude null CBG row:** `WHERE CENSUS_BLOCK_GROUP IS NOT NULL`
- **VARIANT columns:** need LATERAL FLATTEN for downstream marts
- **Surrogate key recipe:**
  {{ dbt_utils.generate_surrogate_key(['CENSUS_BLOCK_GROUP', 'DATE_RANGE_START']) }}
```

### 5. Open questions (Section 11)

Surface ambiguities for the engineer — not silent assumptions:

```markdown
1. Why does `2019_CBG_PATTERNS` use Oct–Nov 2018 data despite "2019" prefix?
2. Should CENSUS_BLOCK_GROUP be parsed into state/county/tract/group components?
3. ACS margin-of-error columns: drop in staging or retain for statistical modeling?
```

---

## How `onboard-bronze-layer` consumes this report

When the bronze skill receives this EDA report as `EDA_REPORT`:

1. **Section 1** → `_sources.yml` table description (row count, data years).
2. **Section 2** → Column rename plan + type-cast decisions for the `.md` spec.
3. **Section 3** → PK selection → `unique` + `not_null` tests in `schema.yml`.
4. **Section 7** → Pre-fills *Excluded columns* and *Transformations* in `<stg_model>.md`.
5. **Section 10** → Direct per-table staging guidance drives the transformation spec.
6. **Section 11** → Surfaced to the user before generating files (non-blocking).
