# Task 7: Optimize a Slow Query

## Prompt
The following query runs on `fct_orders` (1.5M rows) and takes 45 seconds. Optimize it for Snowflake:

```sql
select
    dim_customers.market_segment,
    dim_customers.region_name,
    date_trunc('month', fct_orders.order_date) as order_month,
    count(*) as order_count,
    sum(fct_orders.net_revenue) as total_revenue,
    avg(fct_orders.net_revenue) as avg_revenue
from fct_orders
join dim_customers on fct_orders.customer_key = dim_customers.customer_key
where fct_orders.order_date between '1992-01-01' and '1998-12-31'
group by 1, 2, 3
order by total_revenue desc
```

Provide:
1. **Root cause analysis**: Why is this slow?
2. **Snowflake-specific optimizations**:
   - Clustering key recommendations
   - Warehouse sizing advice
   - Materialized view option
   - Result caching considerations
3. **dbt config changes**: Add clustering, materialization adjustments
4. **Rewritten query** if structural changes help

## Expected Output
- Analysis of performance bottlenecks
- dbt model config updates
- Snowflake-specific optimization recommendations
- Optionally: a pre-aggregated intermediate model

## Evaluation Dimensions
- Snowflake-native Integration (primary)
- Context Awareness
- Code Review

## Scoring Notes
- 5 pts: Identifies clustering, suggests warehouse sizing, considers materialized views, dbt config correct
- 4 pts: Good recommendations but misses one optimization
- 3 pts: Generic SQL optimization without Snowflake specifics
- 2 pts: Recommendations are wrong for Snowflake
- 1 pts: No useful optimization suggestions
