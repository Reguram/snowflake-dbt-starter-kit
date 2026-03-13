with source as (
    select * from {{ source('us_census_data', '2019_RENT_PERCENTAGE_HOUSEHOLD_INCOME') }}
),

staged as (
    select
        census_block_group,
        "Total: Renter-occupied housing units",
        "50.0 percent or more: Renter-occupied housing units",
        "Not computed: Renter-occupied housing units",
        "Less than 10.0 percent: Renter-occupied housing units",
        "10.0 to 14.9 percent: Renter-occupied housing units",
        "15.0 to 19.9 percent: Renter-occupied housing units",
        "20.0 to 24.9 percent: Renter-occupied housing units",
        "25.0 to 29.9 percent: Renter-occupied housing units",
        "30.0 to 34.9 percent: Renter-occupied housing units",
        "35.0 to 39.9 percent: Renter-occupied housing units",
        "40.0 to 49.9 percent: Renter-occupied housing units"
    from source
)

select * from staged
