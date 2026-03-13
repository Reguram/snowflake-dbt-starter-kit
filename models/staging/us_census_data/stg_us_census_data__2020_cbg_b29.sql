with source as (
    select * from {{ source('us_census_data', '2020_CBG_B29') }}
),

staged as (
    select
        census_block_group,
        "B29001e1",
        "B29001m1",
        "B29001e2",
        "B29001m2",
        "B29001e3",
        "B29001m3",
        "B29001e4",
        "B29001m4",
        "B29001e5",
        "B29001m5",
        "B29002e1",
        "B29002m1",
        "B29002e2",
        "B29002m2",
        "B29002e3",
        "B29002m3",
        "B29002e4",
        "B29002m4",
        "B29002e5",
        "B29002m5",
        "B29002e6",
        "B29002m6",
        "B29002e7",
        "B29002m7",
        "B29002e8",
        "B29002m8",
        "B29003e1",
        "B29003m1",
        "B29003e2",
        "B29003m2",
        "B29003e3",
        "B29003m3",
        "B29004e1",
        "B29004m1"
    from source
)

select * from staged
