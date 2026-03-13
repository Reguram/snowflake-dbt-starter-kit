# Evaluation Framework: Snowflake Cortex Code vs Claude Code/Copilot CLI

## Purpose
Structured comparison of Snowflake's native AI assistant (Cortex Code) against external coding assistants (Claude Code, GitHub Copilot CLI) across key Snowflake development workflows.

## Evaluation Dimensions

| # | Dimension | What to Measure | Weight |
|---|-----------|-----------------|--------|
| 1 | **dbt Model Generation** | Correctness, naming compliance, test coverage, ref/source usage | 20% |
| 2 | **Semantic View Creation** | Valid DDL, metric/dimension accuracy, Snowflake compatibility | 15% |
| 3 | **Streamlit App Scaffolding** | Runnable code, Snowflake-native API usage, UI quality | 10% |
| 4 | **Data Pipeline / OpenFlow** | Task DAG correctness, error handling, schedule config | 15% |
| 5 | **Code Review** | Bug detection rate, false positives, actionable suggestions | 10% |
| 6 | **Context Awareness** | Understands existing project structure, refs, sources | 10% |
| 7 | **Iteration Speed** | Time-to-working-code, number of correction rounds | 10% |
| 8 | **Snowflake-native Integration** | Warehouse/role awareness, cost hints, native features | 10% |

## Scoring Rubric

Each dimension is scored 1–5:

| Score | Label | Definition |
|-------|-------|------------|
| 5 | Excellent | Output is production-ready with no edits needed |
| 4 | Good | Minor edits needed (cosmetic, naming) |
| 3 | Acceptable | Works but needs moderate fixes (missing tests, wrong pattern) |
| 2 | Poor | Fundamentally wrong approach, requires significant rework |
| 1 | Failing | Does not compile, completely wrong, or refuses task |

## Methodology

### Setup
1. Both tools receive identical prompts from `evaluation/tasks/`
2. Each tool uses the same project context (this repository)
3. Capture verbatim outputs in `evaluation/results/`
4. Score independently per rubric before comparing

### Execution Protocol
For each task:
1. Reset environment (clean git state)
2. Provide the task prompt verbatim
3. Record wall-clock time to first working output
4. Count correction rounds needed
5. Save final output + all intermediate attempts
6. Score each dimension that applies

### Output Capture Format
```
evaluation/results/
├── task_01/
│   ├── cortex_code_output.md
│   ├── claude_code_output.md
│   ├── cortex_code_score.json
│   └── claude_code_score.json
├── task_02/
│   └── ...
```

### Score JSON Format
```json
{
  "task_id": "task_01",
  "tool": "cortex_code",
  "timestamp": "2026-03-10T00:00:00Z",
  "model_version": "cortex-code-v1.x",
  "scores": {
    "dbt_model_generation": 4,
    "semantic_view_creation": null,
    "streamlit_scaffolding": null,
    "data_pipeline": null,
    "code_review": null,
    "context_awareness": 3,
    "iteration_speed": 4,
    "snowflake_integration": 5
  },
  "time_to_first_output_seconds": 12,
  "correction_rounds": 1,
  "notes": "Minor naming issue in column"
}
```

## Reproducibility
- Pin Cortex model version at evaluation start
- Record Claude model version (e.g., claude-sonnet-4-20250514)
- Record Copilot CLI version
- Use identical system prompts / project context
- Run evaluations on same date to control for model updates

## Cost Tracking
- Cortex: Track credit consumption per task via `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY`
- Claude API: Track token usage per task from API response headers
- Copilot: Record subscription tier (note: no per-query billing)
