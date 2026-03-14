with source as (
    select * from {{ source('covid19_data', 'GOOG_GLOBAL_MOBILITY_REPORT') }}
),

staged as (
    select
        country_region,
        province_state,
        iso_3166_1,
        iso_3166_2,
        date,
        grocery_and_pharmacy_change_perc,
        parks_change_perc,
        residential_change_perc,
        retail_and_recreation_change_perc,
        transit_stations_change_perc,
        workplaces_change_perc,
        last_update_date,
        last_reported_flag,
        sub_region_2
    from source
)

select * from staged
