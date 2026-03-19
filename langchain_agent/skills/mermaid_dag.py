"""Skill: Mermaid DAG — generate Mermaid diagrams from dbt project DAG.

Source: dbt-agent-skills/skills/dbt/skills/creating-mermaid-dbt-dag
"""

SKILL_NAME = "mermaid_dag"

KEYWORDS = [
    "mermaid", "dag", "diagram", "graph", "lineage", "flowchart",
    "visualization", "visualize", "dependency graph", "model graph",
]

INSTRUCTIONS = """\
## Skill: Creating Mermaid DAG Diagrams

### Mermaid Syntax for dbt DAGs
Generate flowcharts showing model dependencies:

```mermaid
graph LR
    source[source.my_source.table] --> stg[stg_source__table]
    stg --> int[int_enriched]
    int --> fct[fct_orders]
    stg --> dim[dim_customers]
```

### Node Shapes
- Sources: `source[source_name]` (square brackets)
- Staging: `stg[stg_model]` (square brackets)
- Intermediate: `int([int_model])` (rounded)
- Facts: `fct{{fct_model}}` (hexagon)
- Dimensions: `dim{{dim_model}}` (hexagon)

### Generation Workflow
1. Use `list_models` to get all models by layer
2. Use `read_model` to parse `{{ ref() }}` calls and find dependencies
3. Build edges from ref() → model relationships
4. Use `generate_mermaid_dag` tool for automated diagram generation

### Best Practices
- Filter by source/layer to keep diagrams readable
- Use left-to-right (`graph LR`) for medallion architecture
- Color-code layers with Mermaid styles
- Include only direct dependencies (not transitive)
"""
