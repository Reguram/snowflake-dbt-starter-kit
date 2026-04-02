---
applyTo: "cortex-analyst-models/**,Sample-semantic-view-cortex-analyst/**,models/marts/**/*.sql"
description: "Cortex Analyst YAML semantic model generation — auto-classifies dimensions/facts, generates synonyms/sample_values/verified_queries/custom_instructions from dbt mart models. Auto-activates when editing mart models or Cortex Analyst YAML files."
---

# Skill: Cortex Analyst Semantic Model Generation (Agentic)

> **This is an AGENTIC instruction.** When activated, the AI agent explores Snowflake
> via MCP tools, reasons about data structures, and generates production-ready YAML
> semantic models. It does NOT simply call a deterministic script.
>
> For Snowflake Semantic Views (`CREATE SEMANTIC VIEW` DDL), see `semantic-view-design.instructions.md`.
> Both approaches coexist and can be generated from the same mart models.

## When This Activates

- Editing any mart model SQL (`models/marts/**/*.sql`)
- Editing any Cortex Analyst YAML (`cortex-analyst-models/**`)
- Editing sample semantic models (`Sample-semantic-view-cortex-analyst/**`)

## Active Behavior

When activated on a **mart model** (`models/marts/**/fct_*.sql` or `summary_*.sql`):
1. Check if a corresponding Cortex Analyst YAML exists in `cortex-analyst-models/`
2. If not, offer to generate one using the **agentic workflow** (see below)
3. If it exists, check for column drift (mart columns changed but YAML not updated)

When activated on a **YAML file** (`cortex-analyst-models/*.yaml`):
1. Validate structure against the Cortex Analyst Semantic Model Specification
2. Check for: missing descriptions, empty synonyms, untested verified queries
3. Suggest improvements (more synonyms, better custom_instructions, additional verified queries)

## Agentic Generation Workflow

When a user wants to create a Cortex Analyst semantic model, follow these phases:

### Phase 1: Explore (Context Gathering)
1. **Read the model SQL** — understand CTEs, joins, grain, `{{ ref() }}` dependencies
2. **Read schema.yml** — get column descriptions, tests (PK, FK, accepted_values)
3. **Check existing Semantic Views** — bridge from `ddl/semantic/sem_*.yaml` if present
4. **Identify Snowflake coordinates** — two schemas are involved:
   - **Data schema**: `DBT_MARTS` — where mart tables live. Use in `base_table.schema` and verified query SQL.
   - **Semantic schema**: `SEMANTIC` — where YAML files are uploaded. Stage: `@DBT_DEV.SEMANTIC.CORTEX_ANALYST_MODELS`.
   - Do NOT confuse them: `base_table.schema` = `DBT_MARTS`, upload stage = `SEMANTIC`.

### Phase 2: Profile (Data Exploration via MCP)
Run SQL via MCP to understand the actual data:
1. **Column metadata**: `SELECT column_name, data_type FROM information_schema.columns WHERE ...`
2. **Cardinality**: `SELECT COUNT(DISTINCT col), COUNT(*) FROM table` — informs classification
3. **Sample values**: `SELECT DISTINCT col FROM table LIMIT 5` — for synonyms and sample_values
4. **Relationships**: If multi-table, verify JOIN columns across tables

### Phase 3: Classify (AI Reasoning)
Use AI reasoning (not regex) to classify each column:
- **Time Dimensions**: DATE/TIMESTAMP types, `*_date`, `*_at` patterns
- **Dimensions**: Low-cardinality VARCHAR, booleans, entity names, categories, geographic codes
- **Facts**: Numeric aggregatable measures — assign `default_aggregation` (sum/avg/count/max)
- **Skip**: Surrogate keys (`*_key`), ETL columns, system columns

### Phase 4: Enrich (Synonyms + Descriptions)
For each column, generate:
- 2-5 business-friendly **synonyms** based on domain context and sample values
- A clear **description** (from schema.yml or AI-generated)
- **sample_values** from actual Snowflake data

### Phase 5: Verify (Generate + Test Queries)
Create 3-5 **verified queries** covering common patterns:
- Summary aggregation, time trends, top-N, dimensional breakdowns
- **Test each query** via MCP `run_sql` — fix and retry if it fails
- Record working SQL with `verified_by` and `verified_at`

### Phase 6: Assemble (Write YAML)
Write the complete YAML to `cortex-analyst-models/semantic_<name>.yaml` following the spec.
- `base_table.schema` must be `DBT_MARTS` (where data lives), NOT `SEMANTIC`
- Include: `custom_instructions` with domain rules for text-to-SQL accuracy

### Phase 7: Upload + Test
- Upload to `@DBT_DEV.SEMANTIC.CORTEX_ANALYST_MODELS` stage (SEMANTIC schema, not DBT_MARTS)
- Test with `CORTEX_ANALYST_MESSAGE()` using a verified query question

## Deterministic Fallback

For batch processing or when MCP is unavailable:
```bash
python scripts/generate_cortex_analyst_model.py --model <name>
python scripts/generate_cortex_analyst_model.py --batch
python scripts/upload_semantic_model_to_stage.py --all
```

## YAML Structure Checklist

When reviewing a Cortex Analyst YAML file:
- [ ] `name` is set and unique
- [ ] Each table has a `description` (multi-line, including grain and key features)
- [ ] `base_table` uses correct `database.schema.table`
- [ ] Every dimension has `description` and at least 2 `synonyms`
- [ ] Time dimensions are separate from regular dimensions
- [ ] Every fact has `description`, `default_aggregation`, and `synonyms`
- [ ] `sample_values` populated for each column (helps NL disambiguation)
- [ ] `primary_key.columns` correctly identifies grain columns
- [ ] 3-5 `verified_queries` with tested SQL
- [ ] `custom_instructions` cover edge cases and domain rules
- [ ] All SQL uses fully qualified table names (`database.schema.table`)

## Relationship to Snowflake Semantic Views

The same mart model can have BOTH:
1. A **Semantic View** (`ddl/semantic/sem_*_ddl.sql`) — simpler, database-native
2. A **Cortex Analyst YAML** (`cortex-analyst-models/semantic_*.yaml`) — richer NL metadata

The agentic workflow bridges existing Semantic View metadata → reuses dimension/metric
classifications to ensure consistency between both approaches.

## Column Classification Rules (Reference)

| Column Pattern | Classification | Aggregation |
|---------------|---------------|------------|
| DATE/TIMESTAMP types | `time_dimensions` | — |
| `*_status`, `*_type`, `*_category` | `dimensions` | — |
| `*_name`, `*_region`, `*_country` | `dimensions` | — |
| `*_sales`, `*_revenue`, `*_amount` | `facts` | SUM |
| `*_count`, `*_quantity` | `facts` | SUM |
| `*_avg`, `*_rate`, `*_percentage` | `facts` | AVG |
| `max_*`, `peak_*` | `facts` | MAX |
| `*_key` (surrogate hash) | Skip | — |
