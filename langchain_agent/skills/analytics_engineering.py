"""Skill: Analytics Engineering — dbt model building best practices.

Source: dbt-agent-skills/skills/dbt/skills/using-dbt-for-analytics-engineering
"""

SKILL_NAME = "analytics_engineering"

KEYWORDS = [
    "build model", "create model", "new model", "staging", "intermediate",
    "marts", "fact table", "dimension table", "CTE", "ref(", "source(",
    "dag", "lineage", "DRY", "don't repeat yourself", "data model",
    "analytics engineering", "transform", "transformation",
]

INSTRUCTIONS = """\
## Skill: Analytics Engineering with dbt

When building dbt models, follow these principles:

### Discovery Phase
- Use `list_sources` and `list_models` to understand existing data assets
- Use `sample_data` and `describe_table` to inspect raw data
- Use `profile_data` to check cardinality, nulls, and data distribution
- Build a mental model of the DAG before writing SQL

### Model Building Best Practices
- **DRY (Don't Repeat Yourself)**: If logic appears in multiple models, extract it to an intermediate model
- **One model, one purpose**: Each model should represent a single business concept
- **CTE-based structure**: Always use CTEs, never subqueries
- **Staging models**: 1:1 with source tables, rename columns to snake_case, minimal transforms
- **Intermediate models**: Business logic, joins, type conversions, calculations
- **Mart models**: Final consumption-ready tables, explicit column lists (no SELECT *)

### Naming Conventions
- Staging: `stg_<source>__<table>` (double underscore)
- Intermediate: `int_<description>`
- Facts: `fct_<entity>` (events/transactions)
- Dimensions: `dim_<entity>` (descriptive attributes)

### Validation Workflow
1. After generating a model, run `run_dbt` with `command="compile"` to check SQL
2. Use `run_dbt` with the model selector to build it
3. Use `check_data_quality` to verify tests pass
4. Use `sample_data` to spot-check the output

### Debugging Errors
- Read the full error message carefully
- Check for missing refs, wrong column names, type mismatches
- Use `read_model` to inspect referenced models
- Use `describe_table` to verify column existence
"""
