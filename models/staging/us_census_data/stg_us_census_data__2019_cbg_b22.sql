with source as (
    select * from {{ source('us_census_data', '2019_CBG_B22') }}
),

staged as (
    select
        census_block_group,
        "B22010e1",
        "B22010m1",
        "B22010e2",
        "B22010m2",
        "B22010e3",
        "B22010m3",
        "B22010e4",
        "B22010m4",
        "B22010e5",
        "B22010m5",
        "B22010e6",
        "B22010m6",
        "B22010e7",
        "B22010m7"
    from source
)

select * from staged
