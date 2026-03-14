-- Summary mart: auto-generated aggregations from METADATA
-- Dimensions: TYPE
-- Measures: count only

with source as (
    select * from {{ ref('stg_covid19_data__metadata') }}
)

select
    type,
    count(*) as record_count

from source
group by type
