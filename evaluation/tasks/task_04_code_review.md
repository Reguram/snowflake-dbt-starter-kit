# Task 4: Code Review with Planted Bugs

## Prompt
Review the following SQL model for issues. This is meant to be a mart model at `models/marts/fct_shipments.sql`:

```sql
SELECT *
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM l
JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS o ON l.L_ORDERKEY = o.O_ORDERKEY
JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER c ON o.O_CUSTKEY = c.C_CUSTKEY
WHERE l.L_SHIPDATE > '2024-01-01'
LIMIT 1000
```

Identify all issues, categorize by severity, and provide a corrected version following project conventions.

## Planted Bugs
1. **SELECT * in a mart model** (should list columns explicitly)
2. **Hard-coded database.schema.table** (should use {{ ref() }})
3. **No CTE structure** (should use with blocks)
4. **LIMIT in production model** (not appropriate)
5. **No surrogate key** (marts need {{ dbt_utils.generate_surrogate_key() }})
6. **Columns not renamed** (still using L_, O_, C_ prefixes)
7. **Missing schema.yml** (no test definitions)
8. **No date parts** (should include date_trunc for analysis)

## Expected Output
- List of all 8 issues with severity and line numbers
- Corrected SQL using project conventions
- schema.yml entry for the corrected model

## Evaluation Dimensions
- Code Review (primary)
- Context Awareness
- dbt Model Generation

## Scoring Notes
- 5 pts: Finds all 8 issues, provides correct fix, proper schema.yml
- 4 pts: Finds 6-7 issues with good fixes
- 3 pts: Finds 4-5 issues
- 2 pts: Finds fewer than 4 issues or provides wrong fixes
- 1 pts: Misses critical issues or suggests non-standard patterns
