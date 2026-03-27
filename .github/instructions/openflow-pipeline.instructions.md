---
applyTo: "ddl/openflow/**,scripts/snowflake_setup.sql"
description: "Snowflake OpenFlow pipeline design — Tasks, Streams, DAGs, error handling, notification integrations, and monitoring. Auto-activates when editing pipeline DDL or Snowflake setup scripts."
---

# Skill: Snowflake OpenFlow Pipeline Design

> **This skill is for Snowflake-native orchestration** using Tasks, Streams, and DAGs. For external orchestration (Airflow, dbt Cloud jobs), use standard scheduling tools.

## When to Use
- Creating Snowflake Task DAGs for dbt layer refresh orchestration
- Setting up Streams for CDC-based incremental processing
- Configuring error handling and notification integrations
- Writing monitoring queries for task run history
- Designing pipeline architecture (schedule vs CDC vs hybrid)

## Active Behavior
When this skill activates on `ddl/openflow/**` files:
1. Validate Task DDL syntax and DAG dependencies
2. Check that child tasks reference valid predecessor tasks
3. Ensure WHEN conditions use `SYSTEM$STREAM_HAS_DATA()` correctly
4. Verify warehouse sizing follows project conventions (XS for staging, S for marts)
5. Confirm error integration is configured on the root task

## Key Conventions

### Task Naming
- Root task: `task_<pipeline>_root`
- Layer tasks: `task_refresh_<layer>` (staging, intermediate, marts, semantic)
- Streams: `stream_<source_table>`
- Stored procedures: `sp_refresh_<layer>`

### DAG Order
```
root → staging → intermediate → marts → semantic
```

### Warehouse Sizing
| Layer | Size |
|-------|------|
| Staging | XS |
| Intermediate | XS–S |
| Marts | S–M |
| Semantic | XS |

### Error Handling Checklist
- [ ] Notification integration created
- [ ] `ERROR_INTEGRATION` set on root task
- [ ] Stored procedures use BEGIN/EXCEPTION blocks
- [ ] Failed tasks halt downstream execution (default behavior)

### Resume/Suspend Order
- **Resume**: children first (bottom-up), root last
- **Suspend**: root first, then children

## File Organization
```
ddl/openflow/
  ├── pipeline_setup.sql       -- Streams, notification integration
  ├── task_dag.sql             -- All CREATE TASK statements
  ├── procedures/              -- Stored procedures for each layer
  │   ├── sp_refresh_staging.sql
  │   ├── sp_refresh_intermediate.sql
  │   ├── sp_refresh_marts.sql
  │   └── sp_refresh_semantic.sql
  └── monitoring/
      └── task_monitoring.sql  -- TASK_HISTORY queries
```
