-- Summary mart: auto-generated aggregations from NYT_US_REOPEN_STATUS
-- Dimensions: STATE, STATUS_DESCRIPTION, STATUS_DETAILS, EXTERNAL_LINK, OPENED_PERSONAL_CARE, CLOSED_OUTDOOR_AND_RECREATION, CLOSED_ENTERTAINMENT, OPENED_OUTDOOR_AND_RECREATION, CLOSED_FOOD_AND_DRINK, OPENED_HOUSES_OF_WORSHIP, OPENED_ENTERTAINMENT, OPENED_FOOD_AND_DRINK, OPENED_RETAIL, OPENED_INDUSTRIES, POPULATION
-- Measures: count only

with source as (
    select * from {{ ref('stg_covid19_data__nyt_us_reopen_status') }}
)

select
    state,
    status_description,
    status_details,
    external_link,
    opened_personal_care,
    closed_outdoor_and_recreation,
    closed_entertainment,
    opened_outdoor_and_recreation,
    closed_food_and_drink,
    opened_houses_of_worship,
    opened_entertainment,
    opened_food_and_drink,
    opened_retail,
    opened_industries,
    population,
    date_trunc('month', restriction_start) as month_period,
    year(restriction_start) as year_period,
    count(*) as record_count

from source
group by state, status_description, status_details, external_link, opened_personal_care, closed_outdoor_and_recreation, closed_entertainment, opened_outdoor_and_recreation, closed_food_and_drink, opened_houses_of_worship, opened_entertainment, opened_food_and_drink, opened_retail, opened_industries, population, date_trunc('month', restriction_start), year(restriction_start)
