-- Summary mart: auto-generated aggregations from SCS_BE_DETAILED_HOSPITALISATIONS
-- Dimensions: REGION, ISO3166_1, ISO3166_2, ISO3166_3
-- Measures: NR_REPORTING, TOTAL_IN, TOTAL_IN_ICU, TOTAL_IN_RESP, TOTAL_IN_ECMO, NEW_IN, NEW_OUT

with source as (
    select * from {{ ref('stg_covid19_data__scs_be_detailed_hospitalisations') }}
)

select
    region,
    iso3166_1,
    iso3166_2,
    iso3166_3,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(nr_reporting) as total_nr_reporting,
    avg(nr_reporting) as avg_nr_reporting,
    min(nr_reporting) as min_nr_reporting,
    max(nr_reporting) as max_nr_reporting,
    sum(total_in) as total_total_in,
    avg(total_in) as avg_total_in,
    min(total_in) as min_total_in,
    max(total_in) as max_total_in,
    sum(total_in_icu) as total_total_in_icu,
    avg(total_in_icu) as avg_total_in_icu,
    min(total_in_icu) as min_total_in_icu,
    max(total_in_icu) as max_total_in_icu,
    sum(total_in_resp) as total_total_in_resp,
    avg(total_in_resp) as avg_total_in_resp,
    min(total_in_resp) as min_total_in_resp,
    max(total_in_resp) as max_total_in_resp,
    sum(total_in_ecmo) as total_total_in_ecmo,
    avg(total_in_ecmo) as avg_total_in_ecmo,
    min(total_in_ecmo) as min_total_in_ecmo,
    max(total_in_ecmo) as max_total_in_ecmo,
    sum(new_in) as total_new_in,
    avg(new_in) as avg_new_in,
    min(new_in) as min_new_in,
    max(new_in) as max_new_in,
    sum(new_out) as total_new_out,
    avg(new_out) as avg_new_out,
    min(new_out) as min_new_out,
    max(new_out) as max_new_out

from source
group by region, iso3166_1, iso3166_2, iso3166_3, date_trunc('month', date), year(date)
