WITH countries AS (
    SELECT DISTINCT
        COUNTRY
    FROM {{ ref('stg_free_company_data__freecompanydataset') }}
    WHERE COUNTRY IS NOT NULL
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['COUNTRY']) }} AS country_id,
    COUNTRY
FROM countries