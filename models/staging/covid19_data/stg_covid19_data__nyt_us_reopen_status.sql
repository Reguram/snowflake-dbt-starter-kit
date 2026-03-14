with source as (
    select * from {{ source('covid19_data', 'NYT_US_REOPEN_STATUS') }}
),

staged as (
    select
        state_code,
        state,
        status_description,
        date_details_description,
        restriction_start,
        restriction_end,
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
        last_update_date
    from source
)

select * from staged
