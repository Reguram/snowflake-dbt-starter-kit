# Snowflake Task DDL Reference

## CREATE TASK

```sql
CREATE [ OR REPLACE ] TASK [ IF NOT EXISTS ] <name>
  WAREHOUSE = <warehouse_name>
  [ SCHEDULE = 'USING CRON <cron_expr> <timezone>' | '<num> MINUTE' ]
  [ AFTER <predecessor_task_name> [, <predecessor_task_name>, ...] ]
  [ WHEN <boolean_expression> ]
  [ ERROR_INTEGRATION = <notification_integration_name> ]
  [ COMMENT = '<string>' ]
  [ ALLOW_OVERLAPPING_EXECUTION = { TRUE | FALSE } ]
  [ USER_TASK_TIMEOUT_MS = <num> ]
  [ SUSPEND_TASK_AFTER_NUM_FAILURES = <num> ]
  [ USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = '<size>' ]
AS
  <sql_statement> | CALL <procedure_name>()
;
```

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `WAREHOUSE` | Compute warehouse for task execution | Required |
| `SCHEDULE` | CRON or interval (root tasks only) | None |
| `AFTER` | Predecessor task(s) — makes this a child task | None |
| `WHEN` | Boolean condition; task skips if FALSE | Always runs |
| `ERROR_INTEGRATION` | Notification integration for failures | None |
| `ALLOW_OVERLAPPING_EXECUTION` | Allow concurrent runs | FALSE |
| `SUSPEND_TASK_AFTER_NUM_FAILURES` | Auto-suspend after N consecutive failures | 0 (never) |
| `USER_TASK_TIMEOUT_MS` | Max execution time in milliseconds | 3600000 (1hr) |

### SCHEDULE Syntax

```sql
-- CRON format: second minute hour day-of-month month day-of-week timezone
SCHEDULE = 'USING CRON 0 6 * * * UTC'       -- Daily at 6 AM UTC
SCHEDULE = 'USING CRON */15 * * * * UTC'     -- Every 15 minutes
SCHEDULE = 'USING CRON 0 8 * * 1-5 UTC'     -- Weekdays at 8 AM UTC

-- Interval format (minimum 1 minute)
SCHEDULE = '60 MINUTE'   -- Every 60 minutes
SCHEDULE = '1 MINUTE'    -- Every 1 minute (use sparingly)
```

## CREATE STREAM

```sql
CREATE [ OR REPLACE ] STREAM [ IF NOT EXISTS ] <name>
  ON TABLE <table_name>
  [ APPEND_ONLY = { TRUE | FALSE } ]
  [ INSERT_ONLY = { TRUE | FALSE } ]     -- external tables only
  [ SHOW_INITIAL_ROWS = { TRUE | FALSE } ]
  [ COMMENT = '<string>' ]
;
```

### Stream on Views
```sql
CREATE OR REPLACE STREAM <name>
  ON VIEW <view_name>;
```

### Consuming Streams
```sql
-- DML that reads from stream advances the offset
INSERT INTO target_table
SELECT * FROM my_stream WHERE METADATA$ACTION = 'INSERT';

-- Check if stream has data (for WHEN conditions)
SYSTEM$STREAM_HAS_DATA('<fully_qualified_stream_name>')
```

### Stream Metadata Columns
| Column | Description |
|--------|-------------|
| `METADATA$ACTION` | INSERT, DELETE |
| `METADATA$ISUPDATE` | TRUE if row is part of an UPDATE |
| `METADATA$ROW_ID` | Unique row identifier |

## ALTER TASK

```sql
-- Resume (activate) a task
ALTER TASK <name> RESUME;

-- Suspend (deactivate) a task
ALTER TASK <name> SUSPEND;

-- Modify schedule
ALTER TASK <name> SET SCHEDULE = 'USING CRON 0 7 * * * UTC';

-- Set error integration
ALTER TASK <name> SET ERROR_INTEGRATION = <integration_name>;

-- Change warehouse
ALTER TASK <name> SET WAREHOUSE = <new_warehouse>;
```

## NOTIFICATION INTEGRATION

```sql
-- Email notification
CREATE OR REPLACE NOTIFICATION INTEGRATION <name>
  TYPE = EMAIL
  ENABLED = TRUE
  ALLOWED_RECIPIENTS = ('<email1>', '<email2>');

-- Send notification manually
CALL SYSTEM$SEND_NOTIFICATIONS(
  '<integration_name>',
  '<subject>',
  '<body>'
);
```

## TASK_HISTORY Function

```sql
-- Query task execution history
SELECT *
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    TASK_NAME => '<task_name>',
    SCHEDULED_TIME_RANGE_START => DATEADD('day', -7, CURRENT_TIMESTAMP()),
    SCHEDULED_TIME_RANGE_END => CURRENT_TIMESTAMP(),
    RESULT_LIMIT => 100
));
```

### TASK_HISTORY Columns
| Column | Description |
|--------|-------------|
| `NAME` | Task name |
| `STATE` | SCHEDULED, EXECUTING, SUCCEEDED, FAILED, SKIPPED, CANCELLED |
| `SCHEDULED_TIME` | When the task was scheduled to run |
| `COMPLETED_TIME` | When execution completed |
| `ERROR_CODE` | Error code if FAILED |
| `ERROR_MESSAGE` | Error message if FAILED |
| `RETURN_VALUE` | Return value from stored procedure |

## DAG Lifecycle

1. **Create** all tasks (created SUSPENDED by default)
2. **Resume child tasks** bottom-up (leaves first)
3. **Resume root task** last (starts the schedule)
4. **Suspend root task** first to stop the DAG
5. **Drop** in any order after suspending
