-- Summary mart: auto-generated aggregations from FREECOMPANYDATASET
-- Dimensions: COUNTRY, INDUSTRY, LOCALITY, REGION, SIZE
-- Measures: FOUNDED

with source as (
    select * from {{ ref('stg_free_company_data__freecompanydataset') }}
)

select
    country,
    industry,
    locality,
    region,
    size,
    count(*) as record_count,
    sum(founded) as total_founded,
    avg(founded) as avg_founded,
    min(founded) as min_founded,
    max(founded) as max_founded

from source
group by country, industry, locality, region, size
