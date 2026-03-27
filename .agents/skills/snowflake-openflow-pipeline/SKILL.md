---
name: snowflake-openflow-pipeline
description: >
  Create Snowflake OpenFlow data pipelines using Tasks, Streams, and DAGs for orchestrating
  dbt model refreshes and CDC-based incremental processing. Generates CREATE TASK / CREATE STREAM
  DDL with proper DAG dependencies, error handling, notification integrations, and monitoring queries.
  Use when building Snowflake-native orchestration pipelines, scheduling dbt layer refreshes,
  detecting change data capture (CDC) with Streams, or setting up task-based DAGs.
user-invocable: true
metadata:
  author: snowflake-dbt-starter-kit
  version: "1.0"
---

# Snowflake OpenFlow Pipeline Creator

> **This skill creates Snowflake-native OpenFlow pipelines** using `CREATE TASK`, `CREATE STREAM`,
> and DAG orchestration. This is for **Snowflake-native scheduling and CDC** — not dbt Cloud job
> scheduling or external orchestrators like Airflow.

## What is Snowflake OpenFlow?

OpenFlow is Snowflake's native data pipeline framework built on:
- **Tasks** — Scheduled or event-driven SQL/procedure execution units
- **Streams** — Change Data Capture (CDC) objects that track DML changes on tables/views
- **Task DAGs** — Directed Acyclic Graphs of tasks with `AFTER` dependencies
- **Notification Integrations** — Email/webhook alerts for pipeline failures

Together, these enable fully serverless ELT pipelines inside Snowflake without external orchestration.

## When to Invoke This Skill

- User asks to "create a pipeline" or "schedule dbt refreshes" in Snowflake
- User wants to orchestrate staging → intermediate → marts → semantic layer refreshes
- User needs CDC / change detection on source tables
- User asks about Snowflake Tasks, Streams, or DAGs
- User wants monitoring/alerting for pipeline runs
- User is working on evaluation task 5 (OpenFlow pipeline)

## End-to-End Workflow

### 1. Identify Pipeline Scope

Determine what the pipeline should orchestrate:
- **Which layers?** staging, intermediate, marts, semantic (or a subset)
- **Which sources?** One source schema or multiple
- **Trigger type?** Scheduled (CRON) or event-driven (Stream-based)
- **Error handling?** Halt on failure, retry, or skip

Read existing models to understand the DAG:
```bash
# List all models by layer
ls models/staging/ models/intermediate/ models/marts/ models/semantic/
```

### 2. Create Streams for CDC (Optional)

Streams track INSERT, UPDATE, DELETE changes on source tables. Create streams when the pipeline should only process **new or changed data**.

```sql
-- Stream on a source table to detect new rows
CREATE OR REPLACE STREAM <schema>.stream_<source_table>
  ON TABLE <database>.<schema>.<source_table>
  APPEND_ONLY = TRUE    -- only track INSERTs (lighter weight)
  SHOW_INITIAL_ROWS = FALSE;
```

**Stream naming convention**: `stream_<source_table_name>`

**Stream types:**
| Type | Use Case | Syntax |
|------|----------|--------|
| Standard | Track INSERT + UPDATE + DELETE | `ON TABLE ...` (default) |
| Append-only | Track INSERTs only (logs, events) | `APPEND_ONLY = TRUE` |
| Insert-only | Track INSERTs on external tables | `INSERT_ONLY = TRUE` |

**Key behavior:**
- `SYSTEM$STREAM_HAS_DATA('<stream_name>')` returns TRUE if stream has unconsumed rows
- Consuming a stream (SELECT in a DML) advances the offset automatically
- Streams are transactional — if the consuming DML fails, the offset does not advance

### 3. Design the Task DAG

A Task DAG has:
- **One root task** with a schedule (CRON or interval)
- **Child tasks** with `AFTER` dependencies on parent tasks
- Optional `WHEN` conditions to skip execution

**DAG design pattern for dbt layers:**
```
root_task (6 AM UTC daily)
  ├── task_refresh_staging      (AFTER root_task)
  │     ├── task_refresh_intermediate  (AFTER task_refresh_staging)
  │     │     └── task_refresh_marts   (AFTER task_refresh_intermediate)
  │     │           └── task_refresh_semantic  (AFTER task_refresh_marts)
```

### 4. Generate Task DDL

#### Root Task (Scheduled)
```sql
CREATE OR REPLACE TASK <schema>.task_dbt_pipeline_root
  WAREHOUSE = '<warehouse_name>'
  SCHEDULE = 'USING CRON 0 6 * * * UTC'  -- 6 AM UTC daily
  COMMENT = 'Root task for dbt pipeline DAG — triggers daily refresh'
AS
  SELECT 1;  -- Root task is a no-op; children do the work
```

#### Child Tasks (Layer Refresh)
```sql
-- Staging refresh
CREATE OR REPLACE TASK <schema>.task_refresh_staging
  WAREHOUSE = '<warehouse_xs>'
  AFTER <schema>.task_dbt_pipeline_root
  WHEN SYSTEM$STREAM_HAS_DATA('<schema>.stream_<source_table>')
  COMMENT = 'Refresh staging models when new source data detected'
AS
  CALL SYSTEM$EXECUTE_PIPELINE('<pipeline_name>')  -- or inline SQL / stored procedure
;

-- Intermediate refresh
CREATE OR REPLACE TASK <schema>.task_refresh_intermediate
  WAREHOUSE = '<warehouse_xs>'
  AFTER <schema>.task_refresh_staging
  COMMENT = 'Refresh intermediate models after staging completes'
AS
  CALL <schema>.sp_refresh_intermediate()
;

-- Marts refresh
CREATE OR REPLACE TASK <schema>.task_refresh_marts
  WAREHOUSE = '<warehouse_s>'
  AFTER <schema>.task_refresh_intermediate
  COMMENT = 'Refresh mart models after intermediate completes'
AS
  CALL <schema>.sp_refresh_marts()
;

-- Semantic refresh (optional)
CREATE OR REPLACE TASK <schema>.task_refresh_semantic
  WAREHOUSE = '<warehouse_xs>'
  AFTER <schema>.task_refresh_marts
  COMMENT = 'Refresh semantic views after marts completes'
AS
  CALL <schema>.sp_refresh_semantic()
;
```

### 5. Error Handling and Notifications

#### Notification Integration
```sql
-- Create email notification integration (requires ACCOUNTADMIN)
CREATE OR REPLACE NOTIFICATION INTEGRATION pipeline_failure_notify
  TYPE = EMAIL
  ENABLED = TRUE
  ALLOWED_RECIPIENTS = ('team@example.com');
```

#### Error Handling in Stored Procedures
```sql
CREATE OR REPLACE PROCEDURE <schema>.sp_refresh_staging()
  RETURNS VARCHAR
  LANGUAGE SQL
  EXECUTE AS CALLER
AS
BEGIN
  BEGIN
    -- Refresh staging models
    EXECUTE IMMEDIATE 'INSERT OVERWRITE INTO <target> SELECT ... FROM <stream>';
    RETURN 'SUCCESS';
  EXCEPTION
    WHEN OTHER THEN
      -- Send failure notification
      CALL SYSTEM$SEND_NOTIFICATIONS(
        'pipeline_failure_notify',
        'dbt Pipeline Failure',
        'Staging refresh failed: ' || SQLERRM
      );
      -- Re-raise to halt downstream tasks
      RAISE;
  END;
END;
```

#### Task-Level Error Config
```sql
-- Set error integration on root task (applies to entire DAG)
ALTER TASK <schema>.task_dbt_pipeline_root
  SET ERROR_INTEGRATION = pipeline_failure_notify;

-- Suspend downstream tasks on failure (default behavior)
-- When a task fails, subsequent AFTER tasks are skipped for that run
```

### 6. Activate the DAG

Tasks are created in **suspended** state. Resume them bottom-up:

```sql
-- Resume child tasks FIRST (bottom-up)
ALTER TASK <schema>.task_refresh_semantic RESUME;
ALTER TASK <schema>.task_refresh_marts RESUME;
ALTER TASK <schema>.task_refresh_intermediate RESUME;
ALTER TASK <schema>.task_refresh_staging RESUME;

-- Resume root task LAST (starts the schedule)
ALTER TASK <schema>.task_dbt_pipeline_root RESUME;
```

**To suspend the entire DAG:**
```sql
-- Suspend root task FIRST (stops the schedule)
ALTER TASK <schema>.task_dbt_pipeline_root SUSPEND;
```

### 7. Monitoring Queries

#### Task Run History
```sql
-- Last 20 task runs across the DAG
SELECT
    name,
    state,
    scheduled_time,
    completed_time,
    DATEDIFF('second', scheduled_time, completed_time) AS duration_seconds,
    error_code,
    error_message
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    SCHEDULED_TIME_RANGE_START => DATEADD('day', -1, CURRENT_TIMESTAMP()),
    RESULT_LIMIT => 20
))
ORDER BY scheduled_time DESC;
```

#### Failed Runs Only
```sql
SELECT name, scheduled_time, error_code, error_message
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    SCHEDULED_TIME_RANGE_START => DATEADD('day', -7, CURRENT_TIMESTAMP())
))
WHERE state = 'FAILED'
ORDER BY scheduled_time DESC;
```

#### Stream Status Check
```sql
-- Check if streams have unconsumed data
SELECT
    stream_name,
    stale,
    stale_after,
    SYSTEM$STREAM_HAS_DATA(CONCAT(table_catalog, '.', table_schema, '.', stream_name)) AS has_data
FROM INFORMATION_SCHEMA.STREAMS
WHERE table_schema = '<schema>';
```

#### Task DAG Visualization
```sql
-- Show all tasks and their dependencies
SHOW TASKS IN SCHEMA <database>.<schema>;

-- Show task graph (predecessors)
SELECT name, predecessors, schedule, state, warehouse
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));
```

## Project-Specific Conventions

### Naming
| Object | Pattern | Example |
|--------|---------|---------|
| Root task | `task_<pipeline>_root` | `task_dbt_pipeline_root` |
| Layer task | `task_refresh_<layer>` | `task_refresh_staging` |
| Stream | `stream_<source_table>` | `stream_raw_orders` |
| Stored procedure | `sp_refresh_<layer>` | `sp_refresh_marts` |
| Notification | `<pipeline>_failure_notify` | `pipeline_failure_notify` |

### Warehouse Sizing
| Layer | Warehouse Size | Rationale |
|-------|---------------|-----------|
| Staging | XS | Light transforms, column renames |
| Intermediate | XS–S | Joins, business logic |
| Marts | S–M | Heavy aggregations, surrogate keys |
| Semantic | XS | DDL execution only |

### File Location
- Pipeline DDL scripts: `ddl/openflow/`
- Monitoring queries: `ddl/openflow/monitoring/`
- Stored procedures: `ddl/openflow/procedures/`

## CRON Schedule Reference

| Schedule | CRON Expression |
|----------|----------------|
| Every day at 6 AM UTC | `0 6 * * * UTC` |
| Every hour | `0 * * * * UTC` |
| Weekdays at 7 AM UTC | `0 7 * * 1-5 UTC` |
| Every 15 minutes | `*/15 * * * * UTC` |
| First day of month at midnight | `0 0 1 * * UTC` |

## Common Patterns

### Pattern 1: Full Daily Refresh
Schedule-based, refreshes all layers sequentially.
Best for: batch ELT with predictable data landing times.

### Pattern 2: CDC-Triggered Refresh
Stream-based, only processes when new data arrives.
Best for: near real-time pipelines with unpredictable ingestion.

### Pattern 3: Hybrid (Schedule + CDC)
Root task scheduled, but child tasks check streams before executing.
Best for: batched processing of change data at fixed intervals.

## Distinction from External Orchestrators

| Aspect | Snowflake OpenFlow | Airflow / dbt Cloud |
|--------|-------------------|---------------------|
| Runs on | Snowflake-native (serverless) | External scheduler |
| Trigger | CRON or Stream (CDC) | CRON, API, or sensor |
| Cost | Warehouse compute only | Compute + orchestrator infra |
| Monitoring | TASK_HISTORY / Snowsight | Airflow UI / dbt Cloud UI |
| Best for | Snowflake-only pipelines | Multi-system orchestration |
| dbt integration | `EXECUTE TASK` / stored procs | Native `dbt build` |
