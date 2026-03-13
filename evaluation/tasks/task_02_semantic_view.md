# Task 2: Create a Semantic View

## Prompt
Create a Snowflake Semantic View for **supply chain analysis** based on data from `SUPPLIER`, `PARTSUPP`, `PART`, and `NATION` tables.

Requirements:
1. Create a dbt model `sem_supply_chain_analysis` in `models/semantic/` that joins:
   - stg_tpch__supplier (or create if needed)
   - Parts and part-supplier data
   - Nation for geography
2. Define the Semantic View YAML metadata in `schema.yml` with:
   - Dimensions: nation_name, supplier_name, part_type, part_size
   - Metrics: total_supply_cost (SUM of supplycost * availqty), supplier_count (COUNT DISTINCT), avg_supply_cost (AVG)
3. Generate the Snowflake Semantic View DDL

## Expected Output
- `models/semantic/sem_supply_chain_analysis.sql`
- `models/semantic/schema.yml` updated with semantic metadata
- DDL script for CREATE SEMANTIC VIEW

## Evaluation Dimensions
- Semantic View Creation (primary)
- dbt Model Generation
- Snowflake-native Integration

## Scoring Notes
- 5 pts: Valid DDL, correct metric aggregations, proper joins, dimensions well-chosen
- 4 pts: Minor metric issues but valid structure
- 3 pts: Missing some dimensions/metrics, DDL needs fixes
- 2 pts: Invalid DDL or wrong joins
- 1 pts: Does not produce valid Semantic View structure
