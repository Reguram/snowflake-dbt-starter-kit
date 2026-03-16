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
    FROM {{ source('japan_ecomm_data', 'MALL_MARKETS_MONTHLY_TRANSACTION') }}
),
cleaned_data AS (
    SELECT
        LISTING_ID,
        WEBSITE_TYPE,
        DATA_SOURCE,
        SALES_DATE,
        MAKER,
        ITEM_NAME,
        MODEL,
        RELEASE_DATE,
        CASE
            WHEN CONDITION = 'A' THEN 'Excellent'
            WHEN CONDITION = 'B' THEN 'Good'
            WHEN CONDITION = 'C' THEN 'Fair'
            WHEN CONDITION = 'D' THEN 'Poor'
            ELSE 'Unknown'
        END AS CONDITION,
        VOLUME,
        IS_SIM_FREE,
        NETWORK_RESTRICTION,
        CAST(PRICE AS NUMBER(14,2)) AS PRICE,
        STOCK_PERIOD
    FROM source_data
)
SELECT * FROM cleaned_data