with source as (
    select * from {{ source('us_census_data', '2020_CBG_C17') }}
),

staged as (
    select
        census_block_group,
        "C17002e1",
        "C17002m1",
        "C17002e2",
        "C17002m2",
        "C17002e3",
        "C17002m3",
        "C17002e4",
        "C17002m4",
        "C17002e5",
        "C17002m5",
        "C17002e6",
        "C17002m6",
        "C17002e7",
        "C17002m7",
        "C17002e8",
        "C17002m8"
    from source
)

select * from staged
