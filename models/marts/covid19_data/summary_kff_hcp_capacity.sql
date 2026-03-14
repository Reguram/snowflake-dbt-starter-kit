-- Summary mart: auto-generated aggregations from KFF_HCP_CAPACITY
-- Dimensions: PROVINCE_STATE
-- Measures: TOTAL_HOSPITAL_BEDS, HOSPITAL_BEDS_PER_1000_POPULATION, TOTAL_CHCS, CHC_SERVICE_DELIVERY_SITES

with source as (
    select * from {{ ref('stg_covid19_data__kff_hcp_capacity') }}
)

select
    province_state,
    count(*) as record_count,
    sum(total_hospital_beds) as total_total_hospital_beds,
    avg(total_hospital_beds) as avg_total_hospital_beds,
    min(total_hospital_beds) as min_total_hospital_beds,
    max(total_hospital_beds) as max_total_hospital_beds,
    sum(hospital_beds_per_1000_population) as total_hospital_beds_per_1000_population,
    avg(hospital_beds_per_1000_population) as avg_hospital_beds_per_1000_population,
    min(hospital_beds_per_1000_population) as min_hospital_beds_per_1000_population,
    max(hospital_beds_per_1000_population) as max_hospital_beds_per_1000_population,
    sum(total_chcs) as total_total_chcs,
    avg(total_chcs) as avg_total_chcs,
    min(total_chcs) as min_total_chcs,
    max(total_chcs) as max_total_chcs,
    sum(chc_service_delivery_sites) as total_chc_service_delivery_sites,
    avg(chc_service_delivery_sites) as avg_chc_service_delivery_sites,
    min(chc_service_delivery_sites) as min_chc_service_delivery_sites,
    max(chc_service_delivery_sites) as max_chc_service_delivery_sites

from source
group by province_state
