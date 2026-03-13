# Task 1: Generate a Staging Model

## Prompt
Generate a dbt staging model for the `SUPPLIER` table from the `tpch` source (`SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`).

The model should:
1. Follow the `stg_<source>__<table>` naming convention
2. Rename all columns from UPPER_CASE to snake_case
3. Select from `{{ source('tpch', 'SUPPLIER') }}`
4. Use CTE structure (with source → renamed → select)
5. Include a complete `schema.yml` entry with:
   - Model description
   - Primary key test (unique + not_null on supplier_key)
   - Foreign key test (nation_key → stg_tpch__nations.nation_key)
   - Not null test on supplier_name

## Expected Output
- `models/staging/stg_tpch__supplier.sql`
- Updated `models/staging/schema.yml` entry

## Evaluation Dimensions
- dbt Model Generation (primary)
- Context Awareness
- Iteration Speed

## Scoring Notes
- 5 pts: All columns renamed correctly, all tests present, compiles on first try
- 4 pts: Minor naming issues but structurally correct
- 3 pts: Missing some tests or incorrect source reference
- 2 pts: Wrong naming pattern or uses hard-coded schema
- 1 pts: Does not compile or is completely wrong structure
