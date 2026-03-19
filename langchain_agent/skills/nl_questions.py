"""Skill: Natural Language Questions — answering data questions with dbt.

Source: dbt-agent-skills/skills/dbt/skills/answering-natural-language-questions-with-dbt
"""

SKILL_NAME = "nl_questions"

KEYWORDS = [
    "how many", "what is the total", "average", "top", "bottom",
    "trend", "compare", "breakdown", "which", "percentage",
    "natural language", "question", "answer", "report",
    "what were", "show me",
]

INSTRUCTIONS = """\
## Skill: Answering Natural Language Questions with dbt

### Decision Flow (4 approaches, in priority order)

1. **Semantic Layer Query** (preferred)
   - If MetricFlow semantic models exist with the needed metrics/dimensions
   - Use `query_semantic_layer` tool
   - Most reliable, handles aggregation correctly

2. **Modified Compiled SQL**
   - If an existing mart model answers the question with slight modifications
   - Use `read_model` to find the closest model
   - Compile it with `dbt_compile`, modify the SQL, run with `run_query`

3. **Model Discovery**
   - Search existing models using `list_models` and `read_model`
   - Find the right model, query it directly with `sample_data` or `run_query`

4. **Manifest Analysis**
   - As last resort, analyze `target/manifest.json` for model definitions
   - Suggest creating a new model if nothing exists

### Best Practices
- Always try to answer from existing models first
- When writing custom SQL, use the compiled model SQL as a base
- Never hard-code database/schema names in ad-hoc queries
- If the question reveals a gap, suggest creating a new mart model
- Suggest semantic layer improvements when patterns emerge

### Query Construction
- Use CTEs for complex queries
- Apply appropriate aggregations (SUM, COUNT, AVG)
- Include proper GROUP BY and ORDER BY
- Limit results to keep output manageable (LIMIT 100)
"""
