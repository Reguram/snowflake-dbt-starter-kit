# Task 5: Create an OpenFlow / Task Pipeline

## Prompt
Create a Snowflake OpenFlow pipeline (using Tasks and Streams) to refresh the marts layer daily:

1. **DAG structure**: 
   - Root task triggers at 6 AM UTC daily
   - Child tasks run in order: staging → intermediate → marts → semantic
2. **Error handling**: If any child task fails, send a notification and halt the DAG
3. **Warehouse**: Use `DBT_AGENT_WH` (size XS for staging, S for marts)
4. **Monitoring**: Include queries to check task run history and error logs

Requirements:
- Use Snowflake-native `CREATE TASK` syntax
- Set proper dependencies with `AFTER` clause
- Include `WHEN` conditions to skip if no new data
- Use Snowflake Streams to detect changes in source tables
- Configure notification integration for alerts

## Expected Output
- SQL script creating all tasks, streams, and notification integration
- Monitoring queries for task run history
- Diagram or description of the DAG

## Evaluation Dimensions
- Data Pipeline / OpenFlow (primary)
- Snowflake-native Integration
- Context Awareness

## Scoring Notes
- 5 pts: Complete DAG with error handling, streams, notifications, monitoring
- 4 pts: Working DAG with minor gaps in error handling
- 3 pts: Basic task chain but missing streams or notifications
- 2 pts: Incorrect task dependencies or wrong syntax
- 1 pts: Does not produce valid Snowflake Task SQL
