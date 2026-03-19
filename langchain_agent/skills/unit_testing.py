"""Skill: Unit Testing — dbt unit test generation and TDD workflow.

Source: dbt-agent-skills/skills/dbt/skills/adding-dbt-unit-test
"""

SKILL_NAME = "unit_testing"

KEYWORDS = [
    "unit test", "test", "tdd", "test-driven", "mock", "expected output",
    "given input", "assert", "unit_tests", "test case", "data_tests",
]

INSTRUCTIONS = """\
## Skill: dbt Unit Testing

### Unit Test Structure
dbt unit tests are defined in YAML (schema.yml or dedicated test files):

```yaml
unit_tests:
  - name: test_<model>_<scenario>
    model: <model_name>
    given:
      - input: ref('<upstream_model>')
        rows:
          - {col1: val1, col2: val2}
          - {col1: val3, col2: val4}
    expect:
      rows:
        - {output_col1: expected1, output_col2: expected2}
```

### Input Formats
- **dict format** (default): `rows: [{col: val}]` — best for small datasets
- **csv format**: `format: csv` with inline CSV data
- **sql format**: `format: sql` with a SQL query that generates mock data

### Best Practices
- Test one business rule per unit test
- Name tests descriptively: `test_<model>_<what_is_tested>`
- Provide only the columns referenced by the model (not all source columns)
- For incremental models, use `overrides: {is_incremental: true}` to test incremental logic
- Use `generate_unit_test` tool to scaffold the YAML

### Snowflake Type Handling
- Cast dates explicitly: `{order_date: "2024-01-01"}`
- Use integer for NUMBER types, not float (unless decimal needed)
- Boolean: `true`/`false` (lowercase)

### TDD Workflow
1. Write the unit test YAML first (expected behavior)
2. Run `dbt test --select test_name` — it should fail
3. Write/modify the model SQL
4. Run the test again — it should pass
5. Refactor if needed, re-run tests
"""
