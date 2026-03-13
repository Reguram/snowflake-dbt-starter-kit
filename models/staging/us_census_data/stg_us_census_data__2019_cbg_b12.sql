with source as (
    select * from {{ source('us_census_data', '2019_CBG_B12') }}
),

staged as (
    select
        census_block_group,
        "B12001e1",
        "B12001m1",
        "B12001e2",
        "B12001m2",
        "B12001e3",
        "B12001m3",
        "B12001e4",
        "B12001m4",
        "B12001e5",
        "B12001m5",
        "B12001e6",
        "B12001m6",
        "B12001e7",
        "B12001m7",
        "B12001e8",
        "B12001m8",
        "B12001e9",
        "B12001m9",
        "B12001e10",
        "B12001m10",
        "B12001e11",
        "B12001m11",
        "B12001e12",
        "B12001m12",
        "B12001e13",
        "B12001m13",
        "B12001e14",
        "B12001m14",
        "B12001e15",
        "B12001m15",
        "B12001e16",
        "B12001m16",
        "B12001e17",
        "B12001m17",
        "B12001e18",
        "B12001m18",
        "B12001e19",
        "B12001m19"
    from source
)

select * from staged
