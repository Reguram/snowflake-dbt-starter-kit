with source as (
    select * from {{ source('us_census_data', '2020_CBG_B02') }}
),

staged as (
    select
        census_block_group,
        "B02001e1",
        "B02001m1",
        "B02001e2",
        "B02001m2",
        "B02001e3",
        "B02001m3",
        "B02001e4",
        "B02001m4",
        "B02001e5",
        "B02001m5",
        "B02001e6",
        "B02001m6",
        "B02001e7",
        "B02001m7",
        "B02001e8",
        "B02001m8",
        "B02001e9",
        "B02001m9",
        "B02001e10",
        "B02001m10",
        "B02008e1",
        "B02008m1",
        "B02009e1",
        "B02009m1",
        "B02010e1",
        "B02010m1",
        "B02011e1",
        "B02011m1",
        "B02012e1",
        "B02012m1",
        "B02013e1",
        "B02013m1"
    from source
)

select * from staged
