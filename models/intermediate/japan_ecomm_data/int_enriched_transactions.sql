WITH source_data AS (
    SELECT
        LISTING_ID,
        WEBSITE_TYPE,
        DATA_SOURCE,
        SALES_DATE,
        MAKER,
        ITEM_NAME,
        MODEL,
        RELEASE_DATE,
        CONDITION,
        VOLUME,
        IS_SIM_FREE,
        NETWORK_RESTRICTION,
        PRICE,
        STOCK_PERIOD
    FROM {{ ref('int_cleaned_transactions') }}
),
enriched_data AS (
    SELECT
        LISTING_ID,
        WEBSITE_TYPE,
        DATA_SOURCE,
        SALES_DATE,
        MAKER,
        ITEM_NAME,
        MODEL,
        RELEASE_DATE,
        CONDITION,
        VOLUME,
        IS_SIM_FREE,
        NETWORK_RESTRICTION,
        PRICE,
        STOCK_PERIOD,
        DATEDIFF('year', RELEASE_DATE, SALES_DATE) AS ITEM_AGE,
        CASE
            WHEN ITEM_NAME LIKE '%iPhone%' THEN 'Smartphone'
            ELSE 'Other'
        END AS ITEM_CATEGORY
    FROM source_data
)
SELECT * FROM enriched_data