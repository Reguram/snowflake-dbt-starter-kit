# Dimension and Metric Classification Patterns

## Dimension Patterns

### Time Dimensions
Columns representing time — users filter by date ranges, group by time periods.

| Column Name Pattern | Example | Notes |
|-------------------|---------|-------|
| `*_date` | `order_date`, `ship_date` | Primary time dimension |
| `*_at` | `created_at`, `updated_at` | Timestamp precision |
| `*_timestamp` | `event_timestamp` | Timestamp precision |
| `*_month` | `order_month` | Pre-truncated (derived) |
| `*_quarter` | `order_quarter` | Pre-truncated (derived) |
| `*_year` | `order_year` | Pre-truncated (derived) |

**Best practice**: Always include multiple granularities. If only `order_date` exists in the base table, create derived dimensions:
```sql
date_trunc('month', order_date) as order_month,
date_trunc('quarter', order_date) as order_quarter,
extract(year from order_date) as order_year
```

### Categorical Dimensions
Low-cardinality string columns — users filter by category, group for comparison.

| Column Name Pattern | Example | Typical Cardinality |
|-------------------|---------|-------------------|
| `*_status` | `order_status`, `payment_status` | 3–10 values |
| `*_type` | `order_type`, `customer_type` | 5–20 values |
| `*_category` | `product_category` | 10–50 values |
| `*_segment` | `market_segment` | 3–10 values |
| `*_priority` | `order_priority` | 3–5 values |
| `*_tier` | `customer_tier` | 3–5 values |
| `*_flag` | `is_returned`, `is_active` | 2 values (boolean) |

### Entity / Geographic Dimensions
Names and geographic attributes — users group by entity, drill into geography.

| Column Name Pattern | Example | Notes |
|-------------------|---------|-------|
| `*_name` | `customer_name`, `product_name` | High cardinality, use carefully |
| `*_region` | `sales_region` | Geographic hierarchy |
| `*_country` / `*_nation` | `nation_name` | Geographic |
| `*_city` | `customer_city` | High cardinality |
| `*_brand` | `product_brand` | Product hierarchy |

## Metric Patterns

### Sum Metrics (Additive)
Columns that represent amounts — summing across rows is meaningful.

| Column Name Pattern | Example | Metric Name |
|-------------------|---------|------------|
| `*_price` / `*_revenue` | `total_price`, `net_revenue` | `total_revenue` |
| `*_amount` | `order_amount`, `discount_amount` | `total_amount` |
| `*_cost` | `unit_cost`, `shipping_cost` | `total_cost` |
| `*_quantity` / `*_qty` | `order_quantity` | `total_quantity` |
| `*_discount` | `discount_value` | `total_discounts` |

### Count Metrics
Counting distinct entities or rows.

| Expression | Example | Metric Name |
|-----------|---------|------------|
| `COUNT(pk_column)` | `COUNT(order_key)` | `order_count` |
| `COUNT(DISTINCT fk)` | `COUNT(DISTINCT customer_key)` | `unique_customers` |

### Average Metrics
Rates, averages, per-unit measures.

| Expression | Example | Metric Name |
|-----------|---------|------------|
| `AVG(amount_col)` | `AVG(total_price)` | `avg_order_value` |
| `AVG(rate_col)` | `AVG(discount_rate)` | `avg_discount_rate` |

### Min/Max Metrics
Boundary values, first/last occurrences.

| Expression | Example | Metric Name |
|-----------|---------|------------|
| `MIN(date_col)` | `MIN(order_date)` | `earliest_order` |
| `MAX(date_col)` | `MAX(order_date)` | `latest_order` |

## Anti-Patterns (Do NOT Make These Dimensions or Metrics)

| Column | Why Not |
|--------|---------|
| Surrogate keys (`*_sk`, hashed keys) | No analytical meaning |
| Comment/description text | Too high cardinality, no grouping value |
| Raw JSON/VARIANT | Not aggregatable or filterable |
| Audit columns (`_loaded_at`, `_etl_batch`) | Internal, not for analysts |
| Already-aggregated columns in a pre-agg table | Would double-aggregate |
