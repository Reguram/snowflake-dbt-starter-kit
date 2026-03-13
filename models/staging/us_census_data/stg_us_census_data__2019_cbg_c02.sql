with source as (
    select * from {{ source('us_census_data', '2019_CBG_C02') }}
),

staged as (
    select
        census_block_group,
        "C02003e1",
        "C02003m1",
        "C02003e2",
        "C02003m2",
        "C02003e3",
        "C02003m3",
        "C02003e4",
        "C02003m4",
        "C02003e5",
        "C02003m5",
        "C02003e6",
        "C02003m6",
        "C02003e7",
        "C02003m7",
        "C02003e8",
        "C02003m8",
        "C02003e9",
        "C02003m9",
        "C02003e10",
        "C02003m10",
        "C02003e11",
        "C02003m11",
        "C02003e12",
        "C02003m12",
        "C02003e13",
        "C02003m13",
        "C02003e14",
        "C02003m14",
        "C02003e15",
        "C02003m15",
        "C02003e16",
        "C02003m16",
        "C02003e17",
        "C02003m17",
        "C02003e18",
        "C02003m18",
        "C02003e19",
        "C02003m19"
    from source
)

select * from staged
