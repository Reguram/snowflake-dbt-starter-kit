with source as (
    select * from {{ source('us_census_data', '2019_CBG_C16') }}
),

staged as (
    select
        census_block_group,
        "C16002e1",
        "C16002m1",
        "C16002e2",
        "C16002m2",
        "C16002e3",
        "C16002m3",
        "C16002e4",
        "C16002m4",
        "C16002e5",
        "C16002m5",
        "C16002e6",
        "C16002m6",
        "C16002e7",
        "C16002m7",
        "C16002e8",
        "C16002m8",
        "C16002e9",
        "C16002m9",
        "C16002e10",
        "C16002m10",
        "C16002e11",
        "C16002m11",
        "C16002e12",
        "C16002m12",
        "C16002e13",
        "C16002m13",
        "C16002e14",
        "C16002m14"
    from source
)

select * from staged
