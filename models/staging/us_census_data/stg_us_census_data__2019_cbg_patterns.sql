with source as (
    select * from {{ source('us_census_data', '2019_CBG_PATTERNS') }}
),

staged as (
    select
        census_block_group,
        date_range_start,
        date_range_end,
        raw_visit_count,
        raw_visitor_count,
        visitor_home_cbgs,
        visitor_work_cbgs,
        distance_from_home,
        related_same_day_brand,
        related_same_month_brand,
        top_brands,
        popularity_by_hour,
        popularity_by_day
    from source
)

select * from staged
