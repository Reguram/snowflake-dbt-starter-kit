"""Skill: dbt Docs — efficient documentation lookup.

Source: dbt-agent-skills/skills/dbt/skills/fetching-dbt-docs
"""

SKILL_NAME = "dbt_docs"

KEYWORDS = [
    "documentation", "docs", "dbt docs", "schema.yml", "description",
    "catalog", "manifest", "column description",
]

INSTRUCTIONS = """\
## Skill: dbt Documentation

### Documentation Best Practices
- Every model MUST have a `description` in schema.yml
- Column descriptions should explain business meaning, not just data type
- Use doc blocks for long/reusable descriptions:
  ```
  {% docs my_doc %}
  Long description here...
  {% enddocs %}
  ```
  Then reference: `description: '{{ doc("my_doc") }}'`

### Finding Documentation
- Check `schema.yml` files alongside models for descriptions
- Check `target/manifest.json` (compiled) for full catalog
- Use `read_model` tool to see model SQL
- Use `list_models` to find models by layer

### Documentation Structure
- `models/<layer>/schema.yml` — Model and column descriptions + tests
- `models/<layer>/_sources.yml` — Source table documentation
- `docs/` directory — Markdown doc blocks (if used)
"""
