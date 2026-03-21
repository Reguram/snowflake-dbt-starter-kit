---
applyTo: "models/**/schema.yml,models/**/_sources.yml"
description: "dbt documentation patterns — schema.yml descriptions, column docs, doc blocks, and dbt docs site. Auto-activates when editing YAML documentation files."
---

# Skill: dbt Documentation

## When to Use
Use this skill when adding descriptions, documenting models/columns, or generating dbt docs.

## Documentation Requirements
Every model MUST have:
1. A `description` in schema.yml
2. Column-level descriptions for key columns (PKs, FKs, business-critical)
3. Tests defined alongside descriptions

## Schema.yml Pattern
```yaml
models:
  - name: fct_orders
    description: >
      Grain: one row per order. Contains order-level facts including
      revenue, status, and customer relationship. Built from staged
      TPC-H orders joined with line items and customer dimensions.
    columns:
      - name: order_key
        description: "Primary key — unique order identifier from source"
        tests:
          - unique
          - not_null
      - name: customer_key
        description: "Foreign key to dim_customers"
        tests:
          - not_null
          - relationships:
              to: ref('dim_customers')
              field: customer_key
      - name: total_revenue
        description: "Sum of extended price minus discount for all line items"
      - name: order_status
        description: "Order fulfillment status: F (fulfilled), O (open), P (partial)"
        tests:
          - accepted_values:
              values: ['F', 'O', 'P']
```

## Doc Blocks (Reusable Descriptions)
For descriptions used across multiple models, create `docs/` blocks:

```markdown
{% docs order_status %}
Order fulfillment status code:
- **F** (Fulfilled): All line items shipped
- **O** (Open): Order placed but not yet shipped
- **P** (Partial): Some line items shipped
{% enddocs %}
```

Reference in schema.yml:
```yaml
- name: order_status
  description: '{{ doc("order_status") }}'
```

## Source Documentation
```yaml
sources:
  - name: tpch
    description: "TPC-H benchmark dataset — standard analytical workload"
    database: "{{ var('source_database', 'SNOWFLAKE_SAMPLE_DATA') }}"
    schema: "{{ var('source_schema', 'TPCH_SF1') }}"
    tables:
      - name: ORDERS
        description: "Raw orders table — one row per customer order"
        columns:
          - name: O_ORDERKEY
            description: "Primary key"
```

## Generating Docs Site
```bash
# Generate documentation
dbt docs generate

# Serve locally
dbt docs serve --port 8080
```

## dbt Docs Online Lookup
To look up dbt documentation pages:
- Append `.md` to any `docs.getdbt.com` URL for clean markdown
- Search the index: `https://docs.getdbt.com/llms.txt`
- For specific topics: search the index first, then fetch individual pages

## Best Practices
- Write descriptions from the **consumer's perspective** — what does this column mean to a business user?
- Include grain definition in model description ("one row per...")
- Document edge cases and business rules in column descriptions
- Keep descriptions concise but unambiguous
- Use doc blocks for enum values shared across models
