"""Skill: Semantic Layer — MetricFlow semantic models and metrics.

Source: dbt-agent-skills/skills/dbt/skills/building-dbt-semantic-layer
"""

SKILL_NAME = "semantic_layer"

KEYWORDS = [
    "semantic", "metric", "metrics", "metricflow", "dimension",
    "measure", "entity", "semantic model", "semantic view",
    "time spine", "cumulative", "derived metric", "ratio",
    "conversion metric", "semantic layer",
]

INSTRUCTIONS = """\
## Skill: dbt Semantic Layer (MetricFlow)

### Semantic Model Structure
Define in schema.yml under `semantic_models`:

```yaml
semantic_models:
  - name: <name>
    defaults:
      agg_time_dimension: <date_col>
    model: ref('<dbt_model>')
    entities:
      - name: <entity_name>
        type: primary|foreign|natural
        expr: <column>
    dimensions:
      - name: <dim_name>
        type: categorical|time
        type_params:  # for time dimensions
          time_granularity: day
    measures:
      - name: <measure_name>
        agg: sum|count|avg|min|max|count_distinct
        expr: <column_or_expression>
```

### Metric Types
1. **Simple**: Direct aggregation of a measure
2. **Derived**: Calculation from other metrics (e.g., `revenue_per_order = revenue / order_count`)
3. **Cumulative**: Running total over time (e.g., cumulative revenue)
4. **Ratio**: Ratio of two measures
5. **Conversion**: Funnel conversion metrics

### Snowflake Semantic Views
For Snowflake-native semantic views (not MetricFlow):
- Use `generate_semantic_view` tool to create DDL
- Dimensions = columns users filter/group by
- Metrics = aggregatable measures (SUM, COUNT, AVG)

### Validation Workflow
1. Define the semantic model YAML
2. Run `dbt parse` to validate syntax
3. If using MetricFlow: `mf validate-configs`
4. Query with `mf query --metrics <metric> --group-by <dimension>`

### Time Spine Setup
Required for cumulative and period-over-period metrics:
- Create a model with one row per day (or desired grain)
- Register it as a time spine in `dbt_project.yml`
"""
