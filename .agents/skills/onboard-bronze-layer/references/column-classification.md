# Column Classification Rules

## Purpose
After profiling a source table (`DESCRIBE TABLE` + cardinality/null analysis), classify each
column to determine its role in the medallion pipeline: primary key, dimension, metric, date,
or exclude.

## Classification Decision Tree

```
Column Type?
├── DATE / TIMESTAMP_*
│   └── → DATE dimension + clustering key candidate
├── BOOLEAN
│   └── → Categorical dimension
├── VARCHAR / STRING / TEXT
│   ├── 0% nulls AND 100% unique → PK candidate
│   ├── <20 distinct values → Categorical dimension + accepted_values test candidate
│   ├── 20–100 distinct values → Entity dimension
│   └── >100 distinct values → High-cardinality dimension (use carefully in metrics)
├── NUMBER / INT / FLOAT / DECIMAL
│   ├── 0% nulls AND 100% unique → PK candidate (or FK)
│   ├── Name matches *_id, *_key, *_sk → FK / surrogate key → exclude from metrics
│   ├── Name matches *_amount, *_price, *_revenue, *_cost, *_total → SUM metric
│   ├── Name matches *_rate, *_pct, *_ratio, *_percentage → AVG metric
│   ├── Name matches *_count, *_qty, *_quantity → SUM metric
│   └── Other numeric → Evaluate based on sample values and business context
└── VARIANT / ARRAY / OBJECT
    └── → Semi-structured — needs LATERAL FLATTEN in intermediate layer
```

## Classification Table

| Classification | Criteria | Layer Impact | Test Impact |
|---------------|----------|-------------|-------------|
| **PK** | 0% nulls + 100% unique | Used in surrogate key generation | `unique` + `not_null` |
| **Date dimension** | DATE/TIMESTAMP type | Clustering key candidate in marts | `not_null` if required |
| **Categorical dimension** | VARCHAR + <20 distinct | GROUP BY column in marts | `accepted_values` candidate |
| **Entity dimension** | VARCHAR + 20–100 distinct | GROUP BY / filter column | `not_null` if required |
| **High-cardinality dimension** | VARCHAR + >100 distinct | Filter only (not group by) | — |
| **SUM metric** | NUMBER + amount/price/qty names | Aggregated in marts | `not_null` on critical |
| **AVG metric** | NUMBER + rate/pct/ratio names | Aggregated in marts | — |
| **FK** | NUMBER + *_id/*_key pattern | `relationships` test | `relationships` in marts |
| **Exclude** | ETL metadata: *_loaded_at, *_etl_* | Skip in semantic views | — |
| **Semi-structured** | VARIANT/ARRAY/OBJECT | LATERAL FLATTEN in intermediate | — |

## Naming Pattern Matching

### Dimension Indicators
```
*_date, *_at, *_timestamp           → Time dimension
*_status, *_state                   → Categorical (3–10 values)
*_type, *_kind                      → Categorical (5–20 values)
*_category, *_group, *_class        → Categorical (10–50 values)
*_name, *_title, *_label            → Entity (high cardinality)
*_region, *_country, *_city         → Geographic
*_segment, *_tier, *_priority       → Categorical (3–10 values)
*_flag, is_*, has_*                 → Boolean / categorical (2 values)
```

### Metric Indicators
```
*_amount, *_total, *_sum            → SUM
*_price, *_revenue, *_cost          → SUM
*_quantity, *_qty, *_count          → SUM
*_rate, *_pct, *_ratio              → AVG
*_score, *_rating                   → AVG
*_weight, *_size                    → Context-dependent (SUM or AVG)
```

### Exclude Indicators
```
*_loaded_at, *_inserted_at          → ETL timestamp
*_etl_*, *_dw_*                     → ETL metadata
*_hash, *_checksum                  → Data integrity
_fivetran_*, _airbyte_*             → Ingestion tool metadata
```

## Profiling SQL Template

Run this for each column to get classification inputs:

```sql
SELECT
    '<COL>' AS column_name,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT "<COL>") AS distinct_count,
    COUNT(*) - COUNT("<COL>") AS null_count,
    ROUND(100.0 * (COUNT(*) - COUNT("<COL>")) / COUNT(*), 1) AS null_pct,
    ROUND(100.0 * COUNT(DISTINCT "<COL>") / NULLIF(COUNT("<COL>"), 0), 1) AS uniqueness_pct,
    MIN("<COL>")::VARCHAR AS min_value,
    MAX("<COL>")::VARCHAR AS max_value
FROM <DATABASE>.<SCHEMA>.<TABLE>;
```

## Composite Key Detection

When no single column is 100% unique, test column combinations:

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT CONCAT("<COL1>", '|', "<COL2>")) AS combo_distinct
FROM <DATABASE>.<SCHEMA>.<TABLE>;
```

If `combo_distinct = total_rows`, the combination `(COL1, COL2)` is a composite PK candidate.
