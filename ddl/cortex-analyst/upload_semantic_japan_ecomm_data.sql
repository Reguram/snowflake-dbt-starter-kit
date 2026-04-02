-- =============================================================================
-- Upload semantic_japan_ecomm_data.yaml to @DBT_DEV.SEMANTIC.CORTEX_ANALYST_MODELS
-- Run this in a Snowflake Worksheet, Snowsight, or Cortex Code
-- =============================================================================

-- Step 1: Ensure the stage exists
CREATE STAGE IF NOT EXISTS DBT_DEV.SEMANTIC.CORTEX_ANALYST_MODELS
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  COMMENT = 'Internal stage for Cortex Analyst YAML semantic models';

-- Step 2: Create the upload procedure (one-time setup, idempotent)
CREATE OR REPLACE PROCEDURE DBT_DEV.SEMANTIC.UPLOAD_YAML_TO_STAGE(
    STAGE_PATH VARCHAR,
    FILE_NAME VARCHAR,
    YAML_CONTENT VARCHAR
)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'main'
AS
$$
import io

def main(session, stage_path, file_name, yaml_content):
    input_stream = io.BytesIO(yaml_content.encode('utf-8'))
    session.file.put_stream(
        input_stream,
        f'{stage_path}/{file_name}',
        auto_compress=False,
        overwrite=True
    )
    return f'Successfully uploaded {file_name} to {stage_path}'
$$;

-- Step 3: Upload the YAML file
CALL DBT_DEV.SEMANTIC.UPLOAD_YAML_TO_STAGE(
    '@DBT_DEV.SEMANTIC.CORTEX_ANALYST_MODELS',
    'semantic_japan_ecomm_data.yaml',
    $YAML_CONTENT$
name: SEM_JAPAN_ECOMM_DATA
tables:
  - name: FCT_SALES
    description: |
      Fact table containing daily e-commerce sales aggregated by date, maker, and item category.
      Grain: one row per (sales_date, maker, item_category) combination.
      Currently all data is Apple iPhones classified as Smartphone.
      Covers May 2025 with daily granularity.
      Key metrics: total sales revenue, average price, and transaction count.
    base_table:
      database: DBT_DEV
      schema: DBT_MARTS
      table: FCT_SALES
    dimensions:
      - name: MAKER
        synonyms:
          - manufacturer
          - brand
          - vendor
        description: The manufacturer or brand of the item sold.
        expr: MAKER
        data_type: VARCHAR
        sample_values:
          - "Apple"
      - name: ITEM_CATEGORY
        synonyms:
          - category
          - product category
          - product type
        description: Derived product category (Smartphone or Other).
        expr: ITEM_CATEGORY
        data_type: VARCHAR
        sample_values:
          - "Smartphone"
    time_dimensions:
      - name: SALES_DATE
        synonyms:
          - date
          - transaction date
          - order date
          - sale date
        description: The date of the sale.
        expr: SALES_DATE
        data_type: DATE
        sample_values:
          - "2025-05-01"
          - "2025-05-15"
          - "2025-05-31"
    facts:
      - name: TOTAL_SALES
        synonyms:
          - revenue
          - sales amount
          - total revenue
          - gross merchandise value
          - GMV
        description: Sum of item prices for this date/maker/category grouping.
        expr: TOTAL_SALES
        data_type: NUMBER
        default_aggregation: sum
        sample_values:
          - "59238110.00"
          - "92301229.00"
          - "123639921.00"
      - name: AVERAGE_PRICE
        synonyms:
          - avg price
          - mean price
          - unit price
          - price per item
        description: Average item price for this grouping.
        expr: AVERAGE_PRICE
        data_type: NUMBER
        default_aggregation: avg
        sample_values:
          - "39465.76"
          - "50000.00"
          - "57599.87"
      - name: TRANSACTION_COUNT
        synonyms:
          - number of transactions
          - order count
          - total transactions
          - sales volume
        description: Number of individual transactions in this grouping.
        expr: TRANSACTION_COUNT
        data_type: NUMBER
        default_aggregation: sum
        sample_values:
          - "1348"
          - "1800"
          - "2343"
    primary_key:
      columns:
        - SALES_KEY
  - name: FCT_MALL_MARKETS_YEARLY_REPORT
    description: |
      Detail fact table from the Japan e-commerce yearly report dataset.
      Contains per-item monthly data including price, listing counts, transaction counts,
      and month-over-month changes for GMV, listings, and transactions.
      Grain: one row per unique combination of month, website type, data source, item, model, condition, and volume.
      Covers January 2025 to May 2025. 45,034 rows.
    base_table:
      database: DBT_DEV
      schema: DBT_MARTS
      table: FCT_MALL_MARKETS_YEARLY_REPORT
    dimensions:
      - name: WEBSITE_TYPE
        synonyms:
          - platform type
          - site type
          - marketplace type
          - channel type
        description: "Type of e-commerce platform. \u30E2\u30FC\u30EB = Mall (marketplace),\
          \ \u30D5\u30EA\u30DE = Flea market (C2C)."
        expr: WEBSITE_TYPE
        data_type: VARCHAR
        sample_values:
          - "\u30E2\u30FC\u30EB"
          - "\u30D5\u30EA\u30DE"
      - name: DATA_SOURCE
        synonyms:
          - source
          - platform
          - marketplace
          - site name
        description: The specific e-commerce platform or marketplace where the listing originates.
        expr: DATA_SOURCE
        data_type: VARCHAR
        sample_values:
          - "MERCARI"
          - "RAKUTEN_ICHIBA"
          - "YAHOO_SHOPPING"
          - "YAHOO_AUCTIONS"
          - "AMAZON"
          - "MUSBI"
          - "RAKUMA"
      - name: MAKER
        synonyms:
          - manufacturer
          - brand
          - vendor
        description: Manufacturer or brand name of the product.
        expr: MAKER
        data_type: VARCHAR
        sample_values:
          - "Apple"
      - name: ITEM_NAME
        synonyms:
          - product name
          - phone model
          - iPhone model
          - device name
        description: Name of the product (e.g. iPhone model name).
        expr: ITEM_NAME
        data_type: VARCHAR
        sample_values:
          - "iPhone 16 Pro Max"
          - "iPhone 15 Pro"
          - "iPhone SE (\u7B2C3\u4E16\u4EE3)"
          - "iPhone 12"
          - "iPhone 14 Pro"
      - name: MODEL
        synonyms:
          - model number
          - SKU
          - part number
        description: Specific Apple model number (e.g. MGAC2J/A).
        expr: MODEL
        data_type: VARCHAR
        sample_values:
          - "MGAC2J/A"
          - "MNCJ2J/A"
          - "MPVW3J/A"
      - name: CONDITION
        synonyms:
          - item condition
          - product condition
          - quality grade
          - grade
        description: "Condition grade of the item: S=New/Mint, A=Excellent, B=Good, C=Fair,
          D=Poor, J=Junk."
        expr: CONDITION
        data_type: VARCHAR
        sample_values:
          - "S"
          - "A"
          - "B"
          - "C"
          - "D"
          - "J"
      - name: VOLUME
        synonyms:
          - storage
          - storage capacity
          - memory size
          - GB
          - capacity
        description: Storage capacity of the device (e.g. 64GB, 128GB, 256GB).
        expr: VOLUME
        data_type: VARCHAR
        sample_values:
          - "64GB"
          - "128GB"
          - "256GB"
          - "512GB"
          - "1TB"
    time_dimensions:
      - name: MONTH
        synonyms:
          - report month
          - period
          - date
        description: The month of the yearly report record.
        expr: MONTH
        data_type: DATE
        sample_values:
          - "2025-01-01"
          - "2025-03-01"
          - "2025-05-01"
      - name: RELEASE_DATE
        synonyms:
          - launch date
          - product release date
        description: The original release date of the product.
        expr: RELEASE_DATE
        data_type: DATE
        sample_values:
          - "2020-10-23"
          - "2024-09-20"
    facts:
      - name: SUM_PRICE
        synonyms:
          - total price
          - GMV
          - gross merchandise value
          - revenue
          - sales amount
        description: Total gross merchandise value (sum of prices) for this item/month combination.
        expr: SUM_PRICE
        data_type: NUMBER
        default_aggregation: sum
        sample_values:
          - "56000.00"
          - "92700.00"
          - "22720509.00"
      - name: LISTING_COUNT
        synonyms:
          - number of listings
          - total listings
          - active listings
          - inventory count
        description: Number of active listings for this item/month combination.
        expr: LISTING_COUNT
        data_type: NUMBER
        default_aggregation: sum
        sample_values:
          - "1"
          - "6"
          - "1251"
      - name: TRANSACTION_OUNT
        synonyms:
          - transaction count
          - number of transactions
          - sales count
          - units sold
        description: Number of transactions (sales) for this item/month combination.
        expr: TRANSACTION_OUNT
        data_type: NUMBER
        default_aggregation: sum
        sample_values:
          - "0"
          - "1"
          - "50"
      - name: MOM_CHANGE_IN_GMV
        synonyms:
          - month over month GMV change
          - GMV growth
          - revenue change
          - MoM GMV
        description: Month-over-month percentage change in gross merchandise value.
        expr: MOM_CHANGE_IN_GMV
        data_type: NUMBER
        default_aggregation: avg
        sample_values:
          - "0.00"
          - "56.17"
          - "109.32"
      - name: MOM_CHANGE_IN_LISTING_COUNT
        synonyms:
          - month over month listing change
          - listing growth
          - MoM listings
        description: Month-over-month percentage change in listing count.
        expr: MOM_CHANGE_IN_LISTING_COUNT
        data_type: NUMBER
        default_aggregation: avg
        sample_values:
          - "50.00"
          - "66.67"
          - "80.00"
      - name: MOM_CHANGE_IN_TRANSACTION_COUNT
        synonyms:
          - month over month transaction change
          - transaction growth
          - MoM transactions
        description: Month-over-month percentage change in transaction count.
        expr: MOM_CHANGE_IN_TRANSACTION_COUNT
        data_type: NUMBER
        default_aggregation: avg
        sample_values:
          - "0.00"
          - "50.00"
          - "100.00"
  - name: SUMMARY_MALL_MARKETS_MONTHLY_TRANSACTION
    description: |
      Aggregated summary of monthly e-commerce transactions.
      Grain: one row per combination of website type, data source, maker, item name, model, condition, volume, SIM status, and network restriction.
      Covers May 2025. 12,626 rows.
      Includes price aggregations and stock period metrics.
    base_table:
      database: DBT_DEV
      schema: DBT_MARTS
      table: SUMMARY_MALL_MARKETS_MONTHLY_TRANSACTION
    dimensions:
      - name: WEBSITE_TYPE
        synonyms:
          - platform type
          - site type
          - marketplace type
        description: "Type of e-commerce platform. \u30E2\u30FC\u30EB = Mall (marketplace),\
          \ \u30D5\u30EA\u30DE = Flea market (C2C)."
        expr: WEBSITE_TYPE
        data_type: VARCHAR
        sample_values:
          - "\u30E2\u30FC\u30EB"
          - "\u30D5\u30EA\u30DE"
      - name: DATA_SOURCE
        synonyms:
          - source
          - platform
          - marketplace
        description: The specific e-commerce platform.
        expr: DATA_SOURCE
        data_type: VARCHAR
        sample_values:
          - "MERCARI"
          - "RAKUTEN_ICHIBA"
          - "YAHOO_SHOPPING"
      - name: MAKER
        synonyms:
          - manufacturer
          - brand
        description: Manufacturer or brand name.
        expr: MAKER
        data_type: VARCHAR
        sample_values:
          - "Apple"
      - name: ITEM_NAME
        synonyms:
          - product name
          - phone model
          - iPhone model
        description: Name of the product.
        expr: ITEM_NAME
        data_type: VARCHAR
        sample_values:
          - "iPhone 16 Pro Max"
          - "iPhone 15 Pro"
          - "iPhone 12"
      - name: MODEL
        synonyms:
          - model number
          - SKU
        description: Specific Apple model number.
        expr: MODEL
        data_type: VARCHAR
        sample_values:
          - "MGAC2J/A"
          - "MNCJ2J/A"
      - name: CONDITION
        synonyms:
          - item condition
          - quality grade
          - grade
        description: "Condition grade: S=New/Mint, A=Excellent, B=Good, C=Fair, D=Poor,
          J=Junk."
        expr: CONDITION
        data_type: VARCHAR
        sample_values:
          - "S"
          - "A"
          - "B"
          - "C"
          - "D"
          - "J"
          - "unknown"
      - name: VOLUME
        synonyms:
          - storage
          - storage capacity
          - GB
        description: Storage capacity of the device.
        expr: VOLUME
        data_type: VARCHAR
        sample_values:
          - "64GB"
          - "128GB"
          - "256GB"
      - name: IS_SIM_FREE
        synonyms:
          - SIM unlocked
          - SIM free status
          - unlocked
          - SIM lock status
        description: Whether the device is SIM-free (unlocked) or SIM-locked.
        expr: IS_SIM_FREE
        data_type: VARCHAR
        sample_values:
          - "FREE"
          - "LOCKED"
      - name: NETWORK_RESTRICTION
        synonyms:
          - network status
          - carrier restriction
          - network lock
        description: "Network restriction status indicator: CIRCLE=No restriction, TRIANGLE=Partial,
          CROSS=Restricted."
        expr: NETWORK_RESTRICTION
        data_type: VARCHAR
        sample_values:
          - "CIRCLE"
          - "TRIANGLE"
          - "CROSS"
    time_dimensions:
      - name: MONTH_PERIOD
        synonyms:
          - month
          - period
          - date
          - transaction month
        description: Month of the transaction data (first day of month).
        expr: MONTH_PERIOD
        data_type: DATE
        sample_values:
          - "2025-05-01"
    facts:
      - name: RECORD_COUNT
        synonyms:
          - number of records
          - count
          - row count
        description: Number of individual transaction records in this grouping.
        expr: RECORD_COUNT
        data_type: NUMBER
        default_aggregation: sum
        sample_values:
          - "1"
          - "100"
          - "20834"
      - name: TOTAL_PRICE
        synonyms:
          - total sales
          - revenue
          - GMV
          - sales amount
        description: Total sum of prices for this grouping.
        expr: TOTAL_PRICE
        data_type: NUMBER
        default_aggregation: sum
        sample_values:
          - "2200.00"
          - "500000.00"
          - "14248909.00"
      - name: AVG_PRICE
        synonyms:
          - average price
          - mean price
          - unit price
        description: Average price across records in this grouping.
        expr: AVG_PRICE
        data_type: NUMBER
        default_aggregation: avg
        sample_values:
          - "25000.00"
          - "50000.00"
      - name: MIN_PRICE
        synonyms:
          - minimum price
          - lowest price
        description: Minimum price in this grouping.
        expr: MIN_PRICE
        data_type: NUMBER
        default_aggregation: min
        sample_values:
          - "2200.00"
          - "10000.00"
      - name: MAX_PRICE
        synonyms:
          - maximum price
          - highest price
        description: Maximum price in this grouping.
        expr: MAX_PRICE
        data_type: NUMBER
        default_aggregation: max
        sample_values:
          - "100000.00"
          - "500000.00"
      - name: TOTAL_STOCK_PERIOD
        synonyms:
          - total days on market
          - total stock days
        description: Total days items were in stock across this grouping.
        expr: TOTAL_STOCK_PERIOD
        data_type: NUMBER
        default_aggregation: sum
        sample_values:
          - "1"
          - "30"
          - "100"
      - name: AVG_STOCK_PERIOD
        synonyms:
          - average days on market
          - avg stock days
          - average listing duration
        description: Average number of days items were in stock.
        expr: AVG_STOCK_PERIOD
        data_type: NUMBER
        default_aggregation: avg
        sample_values:
          - "5"
          - "15"
          - "30"
  - name: SUMMARY_MALL_MARKETS_YEARLY_REPORT
    description: |
      Aggregated summary from the yearly report grouped by dimensions.
      Contains total, average, min, max aggregations for price, listing count,
      transaction count, and month-over-month changes.
      Grain: one row per combination of website type, data source, maker, item name, model, condition, volume, and month.
      Covers January 2025 to May 2025. 45,034 rows.
    base_table:
      database: DBT_DEV
      schema: DBT_MARTS
      table: SUMMARY_MALL_MARKETS_YEARLY_REPORT
    dimensions:
      - name: WEBSITE_TYPE
        synonyms:
          - platform type
          - site type
        description: "Type of e-commerce platform. \u30E2\u30FC\u30EB = Mall, \u30D5\u30EA\
          \u30DE = Flea market."
        expr: WEBSITE_TYPE
        data_type: VARCHAR
        sample_values:
          - "\u30E2\u30FC\u30EB"
          - "\u30D5\u30EA\u30DE"
      - name: DATA_SOURCE
        synonyms:
          - source
          - platform
          - marketplace
        description: The specific e-commerce platform.
        expr: DATA_SOURCE
        data_type: VARCHAR
        sample_values:
          - "MERCARI"
          - "RAKUTEN_ICHIBA"
          - "YAHOO_SHOPPING"
      - name: MAKER
        synonyms:
          - manufacturer
          - brand
        description: Manufacturer or brand name.
        expr: MAKER
        data_type: VARCHAR
        sample_values:
          - "Apple"
      - name: ITEM_NAME
        synonyms:
          - product name
          - phone model
          - iPhone model
        description: Name of the product.
        expr: ITEM_NAME
        data_type: VARCHAR
        sample_values:
          - "iPhone 16 Pro Max"
          - "iPhone 15 Pro"
          - "iPhone 12"
      - name: MODEL
        synonyms:
          - model number
          - SKU
        description: Specific Apple model number.
        expr: MODEL
        data_type: VARCHAR
        sample_values:
          - "MGAC2J/A"
      - name: CONDITION
        synonyms:
          - item condition
          - quality grade
          - grade
        description: "Condition grade: S=New/Mint, A=Excellent, B=Good, C=Fair, D=Poor,
          J=Junk."
        expr: CONDITION
        data_type: VARCHAR
        sample_values:
          - "S"
          - "A"
          - "B"
          - "C"
          - "D"
          - "J"
      - name: VOLUME
        synonyms:
          - storage
          - storage capacity
          - GB
        description: Storage capacity of the device.
        expr: VOLUME
        data_type: VARCHAR
        sample_values:
          - "64GB"
          - "128GB"
          - "256GB"
    time_dimensions:
      - name: MONTH_PERIOD
        synonyms:
          - month
          - period
          - date
        description: Month of the report data.
        expr: MONTH_PERIOD
        data_type: DATE
        sample_values:
          - "2025-01-01"
          - "2025-03-01"
          - "2025-05-01"
    facts:
      - name: RECORD_COUNT
        synonyms:
          - number of records
          - count
        description: Number of individual records in this grouping.
        expr: RECORD_COUNT
        data_type: NUMBER
        default_aggregation: sum
      - name: TOTAL_SUM_PRICE
        synonyms:
          - total GMV
          - total revenue
          - gross merchandise value
        description: Total gross merchandise value for this grouping.
        expr: TOTAL_SUM_PRICE
        data_type: NUMBER
        default_aggregation: sum
        sample_values:
          - "0.00"
          - "500000.00"
          - "22720509.00"
      - name: AVG_SUM_PRICE
        synonyms:
          - average GMV
          - average revenue
        description: Average gross merchandise value per record.
        expr: AVG_SUM_PRICE
        data_type: NUMBER
        default_aggregation: avg
      - name: TOTAL_LISTING_COUNT
        synonyms:
          - total listings
          - number of listings
          - inventory count
        description: Total number of listings for this grouping.
        expr: TOTAL_LISTING_COUNT
        data_type: NUMBER
        default_aggregation: sum
      - name: TOTAL_TRANSACTION_OUNT
        synonyms:
          - total transactions
          - number of transactions
          - units sold
        description: Total number of transactions for this grouping.
        expr: TOTAL_TRANSACTION_OUNT
        data_type: NUMBER
        default_aggregation: sum
  - name: DIM_ITEMS
    description: |
      Dimension table containing unique item details.
      One row per unique combination of listing ID, maker, model, volume, condition, and item name.
      59,320 rows. Currently all Apple iPhone products.
    base_table:
      database: DBT_DEV
      schema: DBT_MARTS
      table: DIM_ITEMS
    dimensions:
      - name: ITEM_ID
        synonyms:
          - item identifier
          - product ID
        description: Surrogate key (MD5 hash) uniquely identifying an item.
        expr: ITEM_ID
        data_type: VARCHAR
      - name: LISTING_ID
        synonyms:
          - listing identifier
          - listing number
        description: Original listing identifier from the source platform.
        expr: LISTING_ID
        data_type: VARCHAR
      - name: MAKER
        synonyms:
          - manufacturer
          - brand
        description: Manufacturer or brand name.
        expr: MAKER
        data_type: VARCHAR
        sample_values:
          - "Apple"
      - name: MODEL
        synonyms:
          - model number
          - SKU
          - part number
        description: Specific Apple model number.
        expr: MODEL
        data_type: VARCHAR
        sample_values:
          - "MGAC2J/A"
          - "MNCJ2J/A"
      - name: VOLUME
        synonyms:
          - storage
          - storage capacity
          - GB
          - capacity
        description: Storage capacity of the device.
        expr: VOLUME
        data_type: VARCHAR
        sample_values:
          - "64GB"
          - "128GB"
          - "256GB"
          - "512GB"
          - "1TB"
      - name: CONDITION
        synonyms:
          - item condition
          - quality grade
          - grade
        description: "Condition grade: S=New/Mint, A=Excellent, B=Good, C=Fair, D=Poor."
        expr: CONDITION
        data_type: VARCHAR
        sample_values:
          - "S"
          - "A"
          - "B"
          - "C"
          - "D"
      - name: ITEM_NAME
        synonyms:
          - product name
          - phone model
          - iPhone model
          - device name
        description: Name of the product (e.g. iPhone model name).
        expr: ITEM_NAME
        data_type: VARCHAR
        sample_values:
          - "iPhone 16 Pro Max"
          - "iPhone 15 Pro"
          - "iPhone SE (\u7B2C3\u4E16\u4EE3)"
          - "iPhone 12"
    primary_key:
      columns:
        - ITEM_ID
verified_queries:
  - name: daily_sales_trend
    question: "What are the total daily sales and transaction counts?"
    use_as_onboarding_question: true
    sql: |
      SELECT "SALES_DATE", SUM("TOTAL_SALES") AS total_revenue, SUM("TRANSACTION_COUNT") AS total_transactions FROM DBT_DEV.DBT_MARTS.FCT_SALES GROUP BY "SALES_DATE" ORDER BY "SALES_DATE" DESC LIMIT 10
    verified_by: cortex_code
    verified_at: 1743552000
  - name: monthly_gmv_trend
    question: "What is the monthly GMV trend across all platforms?"
    use_as_onboarding_question: true
    sql: |
      SELECT "MONTH", SUM("SUM_PRICE") AS total_gmv, SUM("LISTING_COUNT") AS total_listings, SUM("TRANSACTION_OUNT") AS total_transactions FROM DBT_DEV.DBT_MARTS.FCT_MALL_MARKETS_YEARLY_REPORT GROUP BY "MONTH" ORDER BY "MONTH"
    verified_by: cortex_code
    verified_at: 1743552000
  - name: top_iphone_models_by_revenue
    question: "What are the top 10 iPhone models by total revenue?"
    use_as_onboarding_question: true
    sql: |
      SELECT "ITEM_NAME", SUM("SUM_PRICE") AS total_gmv, SUM("TRANSACTION_OUNT") AS total_transactions FROM DBT_DEV.DBT_MARTS.FCT_MALL_MARKETS_YEARLY_REPORT GROUP BY "ITEM_NAME" ORDER BY total_gmv DESC LIMIT 10
    verified_by: cortex_code
    verified_at: 1743552000
  - name: sales_by_website_type
    question: "How do sales compare between mall and flea market platforms?"
    use_as_onboarding_question: true
    sql: |
      SELECT "WEBSITE_TYPE", SUM("TOTAL_PRICE") AS total_price, SUM("RECORD_COUNT") AS total_records FROM DBT_DEV.DBT_MARTS.SUMMARY_MALL_MARKETS_MONTHLY_TRANSACTION GROUP BY "WEBSITE_TYPE"
    verified_by: cortex_code
    verified_at: 1743552000
  - name: condition_breakdown
    question: "What is the revenue breakdown by item condition grade?"
    use_as_onboarding_question: true
    sql: |
      SELECT "CONDITION", SUM("SUM_PRICE") AS total_gmv, SUM("LISTING_COUNT") AS total_listings, SUM("TRANSACTION_OUNT") AS total_transactions FROM DBT_DEV.DBT_MARTS.FCT_MALL_MARKETS_YEARLY_REPORT GROUP BY "CONDITION" ORDER BY total_gmv DESC
    verified_by: cortex_code
    verified_at: 1743552000
  - name: platform_comparison
    question: "Which e-commerce platform has the highest GMV?"
    sql: |
      SELECT "DATA_SOURCE", SUM("SUM_PRICE") AS total_gmv, SUM("TRANSACTION_OUNT") AS total_transactions, SUM("LISTING_COUNT") AS total_listings FROM DBT_DEV.DBT_MARTS.FCT_MALL_MARKETS_YEARLY_REPORT GROUP BY "DATA_SOURCE" ORDER BY total_gmv DESC
    verified_by: cortex_code
    verified_at: 1743552000
  - name: storage_volume_analysis
    question: "What is the price breakdown by storage capacity?"
    sql: |
      SELECT "VOLUME", SUM("TOTAL_PRICE") AS total_price, SUM("RECORD_COUNT") AS total_records FROM DBT_DEV.DBT_MARTS.SUMMARY_MALL_MARKETS_MONTHLY_TRANSACTION GROUP BY "VOLUME" ORDER BY total_price DESC
    verified_by: cortex_code
    verified_at: 1743552000
custom_instructions: |
  This semantic model covers Japan e-commerce data for Apple iPhone products sold across multiple Japanese marketplaces (Mercari, Rakuten Ichiba, Yahoo Shopping, Yahoo Auctions, Amazon, Musbi, Rakuma).
  IMPORTANT COLUMN NOTES:
  - TRANSACTION_OUNT (not TRANSACTION_COUNT) is the column name in FCT_MALL_MARKETS_YEARLY_REPORT and SUMMARY_MALL_MARKETS_YEARLY_REPORT. This is a known typo in the source data.
  - WEBSITE_TYPE values are in Japanese: モール = Mall/Marketplace, フリマ = Flea Market/C2C.
  - CONDITION grades: S=New/Mint, A=Excellent, B=Good, C=Fair, D=Poor, J=Junk.
  - NETWORK_RESTRICTION: CIRCLE=No restriction, TRIANGLE=Partial restriction, CROSS=Fully restricted.
  - IS_SIM_FREE: FREE=Unlocked, LOCKED=Carrier locked.
  - All prices are in Japanese Yen (JPY).
  TABLE USAGE GUIDE:
  - For daily sales trends use FCT_SALES
  - For detailed item-level monthly analysis with MoM changes use FCT_MALL_MARKETS_YEARLY_REPORT
  - For transaction-level monthly aggregations with SIM/network info use SUMMARY_MALL_MARKETS_MONTHLY_TRANSACTION
  - For monthly aggregations with MoM metrics use SUMMARY_MALL_MARKETS_YEARLY_REPORT
  - For item dimension lookups use DIM_ITEMS
  QUERY PATTERNS:
  - When asked about revenue or GMV, use SUM(SUM_PRICE) from FCT_MALL_MARKETS_YEARLY_REPORT or SUM(TOTAL_SALES) from FCT_SALES.
  - When asked about platforms or marketplaces, group by DATA_SOURCE.
  - When asked about mall vs flea market, group by WEBSITE_TYPE.
  - When asked about popular or best selling phones, use SUM(TRANSACTION_OUNT) or SUM(SUM_PRICE).
  - For time trends, always ORDER BY the date column ASC.
  - Always use double-quoted column names in SQL.
  - Always use fully qualified table names: DBT_DEV.DBT_MARTS.<TABLE>.

$YAML_CONTENT$
);

-- Step 4: Verify the upload
LIST @DBT_DEV.SEMANTIC.CORTEX_ANALYST_MODELS;

-- Step 5: Validate the semantic model (optional)
SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_VALIDATE(
    BUILD_SCOPED_FILE_URL('@DBT_DEV.SEMANTIC.CORTEX_ANALYST_MODELS', 'semantic_japan_ecomm_data.yaml')
);

-- Step 6: Test with Cortex Analyst
-- SELECT SNOWFLAKE.CORTEX.CORTEX_ANALYST_MESSAGE(
--     '@DBT_DEV.SEMANTIC.CORTEX_ANALYST_MODELS/semantic_japan_ecomm_data.yaml',
--     [{'role': 'user', 'content': 'What are the total daily sales?'}]
-- );
