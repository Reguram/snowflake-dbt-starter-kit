---
description: "Analyze a mart model and suggest a Snowflake Semantic View with dimensions and metrics"
---
# Suggest Semantic View

Analyze the currently open mart model (or the model I specify) and suggest a Snowflake Semantic View.

## What to do:
1. Read the model's SQL and schema.yml
2. Identify the grain (what one row represents)
3. Classify columns as **dimensions** (filter/group-by) or **metrics** (aggregations)
4. Generate a complete `sem_*.sql` model in `models/semantic/`
5. Generate the `schema.yml` metadata block with `meta.snowflake_semantic_view`
6. Generate the `CREATE SEMANTIC VIEW` DDL
7. Explain which columns were chosen as dimensions vs metrics and why

Use the dimension/metric classification heuristics from the `semantic-view-design` skill.
Reference the `generate_semantic_view_ddl` macro in `macros/generate_semantic_view_ddl.sql`.

If the `generate_semantic_view` MCP tool is available, use it for auto-detection.
