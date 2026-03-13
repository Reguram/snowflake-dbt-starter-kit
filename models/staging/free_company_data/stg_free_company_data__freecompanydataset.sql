with source as (
    select * from {{ source('free_company_data', 'FREECOMPANYDATASET') }}
),

renamed as (
    select
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
)

select * from renamed
