-- Summary mart: auto-generated aggregations from HS_BULK_DATA
-- Dimensions: HEALTHCARE_PROVIDER_TYPE, OPERATOR
-- Measures: LONG, LAT, BEDS, STAFF_MEDICAL, STAFF_NURSING

with source as (
    select * from {{ ref('stg_covid19_data__hs_bulk_data') }}
)

select
    healthcare_provider_type,
    operator,
    count(*) as record_count,
    sum(long) as total_long,
    avg(long) as avg_long,
    min(long) as min_long,
    max(long) as max_long,
    sum(lat) as total_lat,
    avg(lat) as avg_lat,
    min(lat) as min_lat,
    max(lat) as max_lat,
    sum(beds) as total_beds,
    avg(beds) as avg_beds,
    min(beds) as min_beds,
    max(beds) as max_beds,
    sum(staff_medical) as total_staff_medical,
    avg(staff_medical) as avg_staff_medical,
    min(staff_medical) as min_staff_medical,
    max(staff_medical) as max_staff_medical,
    sum(staff_nursing) as total_staff_nursing,
    avg(staff_nursing) as avg_staff_nursing,
    min(staff_nursing) as min_staff_nursing,
    max(staff_nursing) as max_staff_nursing

from source
group by healthcare_provider_type, operator
