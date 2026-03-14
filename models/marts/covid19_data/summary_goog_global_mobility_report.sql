-- Summary mart: auto-generated aggregations from GOOG_GLOBAL_MOBILITY_REPORT
-- Dimensions: PROVINCE_STATE, ISO_3166_1, ISO_3166_2, LAST_REPORTED_FLAG, SUB_REGION_2
-- Measures: GROCERY_AND_PHARMACY_CHANGE_PERC, PARKS_CHANGE_PERC, RESIDENTIAL_CHANGE_PERC, RETAIL_AND_RECREATION_CHANGE_PERC, TRANSIT_STATIONS_CHANGE_PERC, WORKPLACES_CHANGE_PERC

with source as (
    select * from {{ ref('stg_covid19_data__goog_global_mobility_report') }}
)

select
    province_state,
    iso_3166_1,
    iso_3166_2,
    last_reported_flag,
    sub_region_2,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(grocery_and_pharmacy_change_perc) as total_grocery_and_pharmacy_change_perc,
    avg(grocery_and_pharmacy_change_perc) as avg_grocery_and_pharmacy_change_perc,
    min(grocery_and_pharmacy_change_perc) as min_grocery_and_pharmacy_change_perc,
    max(grocery_and_pharmacy_change_perc) as max_grocery_and_pharmacy_change_perc,
    sum(parks_change_perc) as total_parks_change_perc,
    avg(parks_change_perc) as avg_parks_change_perc,
    min(parks_change_perc) as min_parks_change_perc,
    max(parks_change_perc) as max_parks_change_perc,
    sum(residential_change_perc) as total_residential_change_perc,
    avg(residential_change_perc) as avg_residential_change_perc,
    min(residential_change_perc) as min_residential_change_perc,
    max(residential_change_perc) as max_residential_change_perc,
    sum(retail_and_recreation_change_perc) as total_retail_and_recreation_change_perc,
    avg(retail_and_recreation_change_perc) as avg_retail_and_recreation_change_perc,
    min(retail_and_recreation_change_perc) as min_retail_and_recreation_change_perc,
    max(retail_and_recreation_change_perc) as max_retail_and_recreation_change_perc,
    sum(transit_stations_change_perc) as total_transit_stations_change_perc,
    avg(transit_stations_change_perc) as avg_transit_stations_change_perc,
    min(transit_stations_change_perc) as min_transit_stations_change_perc,
    max(transit_stations_change_perc) as max_transit_stations_change_perc,
    sum(workplaces_change_perc) as total_workplaces_change_perc,
    avg(workplaces_change_perc) as avg_workplaces_change_perc,
    min(workplaces_change_perc) as min_workplaces_change_perc,
    max(workplaces_change_perc) as max_workplaces_change_perc

from source
group by province_state, iso_3166_1, iso_3166_2, last_reported_flag, sub_region_2, date_trunc('month', date), year(date)
