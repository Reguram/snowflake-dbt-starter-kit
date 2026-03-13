-- Fact table: auto-generated from FREECOMPANYDATASET
with source as (
    select * from {{ ref('stg_free_company_data__freecompanydataset') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['id']) }} as freecompanydataset_id,
    country,
    founded,
    id,
    industry,
    linkedin_url,
    locality,
    name,
    region,
    size,
    website

from source
