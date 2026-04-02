---
description: "Analyze a mart model and generate a Cortex Analyst YAML semantic model with dimensions, facts, synonyms, verified queries, and custom instructions — using agentic exploration via MCP"
mode: "agent"
tools: ["run_in_terminal", "read_file", "create_file", "semantic_search", "grep_search"]
---

# Generate Cortex Analyst Semantic Model (Agentic)

Analyze the active mart model and generate a production-ready Cortex Analyst YAML semantic model
by exploring Snowflake data via MCP tools and using AI reasoning to classify columns.

## Steps

1. Read the mart model SQL and its `schema.yml` to understand the grain, columns, and business context
2. Check if a Snowflake Semantic View already exists in `ddl/semantic/` — bridge its dimension/metric metadata
3. **Explore the data via MCP**: Query Snowflake to profile column types, cardinality, and sample values
4. **Classify columns using AI reasoning**: Determine which columns are dimensions, time_dimensions, or facts based on actual data patterns — not just regex
5. **Generate rich synonyms**: Create 2-5 business-friendly synonyms per column based on domain context
6. **Generate and test verified queries**: Write 3-5 SQL queries representing common business questions, test each via MCP, fix any failures
7. **Write custom instructions**: Domain-specific rules for text-to-SQL accuracy
8. Write the complete YAML to `cortex-analyst-models/semantic_<name>.yaml`
9. Upload to Snowflake stage and test with `CORTEX_ANALYST_MESSAGE()`

Refer to `.agents/skills/cortex-analyst-semantic-model/SKILL.md` for the full agentic workflow.
