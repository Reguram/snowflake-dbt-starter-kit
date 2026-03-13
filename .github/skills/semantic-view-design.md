# Skill: Snowflake Semantic View Design

## When to Use
Use this skill when asked to create, design, or generate a Snowflake Semantic View.

## Instructions

### What is a Semantic View?
A Snowflake Semantic View is a named database object that defines **dimensions** (groupable/filterable columns) and **metrics** (aggregatable measures) over a base query. It enables natural-language querying via Cortex Analyst and structured analytics.

### Design Process
1. **Identify the base model** — typically a mart (fct/dim) or a purpose-built semantic model
2. **Define dimensions** — columns users will filter or group by:
   - Date/time dimensions (date, month, quarter, year)
   - Categorical dimensions (status, segment, region)
   - Entity dimensions (customer_name, product_name)
3. **Define metrics** — aggregatable measures:
   - SUM: revenue, quantity, amount
   - COUNT: order_count, customer_count
   - AVG: avg_order_value, avg_discount
   - MIN/MAX: first_order_date, last_order_date
4. **Create the dbt model** in `models/semantic/sem_<name>.sql`
5. **Add YAML metadata** in `models/semantic/schema.yml` under `meta.snowflake_semantic_view`
6. **Generate DDL** using the macro or MCP tool

### Semantic View DDL Pattern
```sql
CREATE OR REPLACE SEMANTIC VIEW <database>.<schema>.<name>
  COMMENT = '<description>'
AS SELECT * FROM <base_table>
COLUMNS (
    <col1> AS DIMENSION COMMENT '<description>',
    <col2> AS DIMENSION COMMENT '<description>'
)
METRICS (
    <metric1> AS SUM(<expression>) COMMENT '<description>',
    <metric2> AS COUNT(<expression>) COMMENT '<description>'
);
```

### Best Practices
- Keep dimensions to columns that are meaningful for self-service analytics
- Metrics should be unambiguous — name clearly (total_revenue vs avg_revenue)
- Include time dimensions at multiple granularities
- Add COMMENT to every dimension and metric for Cortex Analyst
- Test the base dbt model thoroughly before creating the Semantic View
- One Semantic View per analytical domain (revenue, supply chain, customer)
