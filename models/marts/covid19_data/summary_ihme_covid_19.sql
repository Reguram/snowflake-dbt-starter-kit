-- Summary mart: auto-generated aggregations from IHME_COVID_19
-- Dimensions: LAST_REPORTED_FLAG, COUNTRY_REGION, ISO_3166_1, ISO_3166_2, PROVINCE_STATE
-- Measures: ALLBED_MEAN, ALLBED_LOWER, ALLBED_UPPER, ICUBED_MEAN, ICUBED_LOWER, ICUBED_UPPER, INVVEN_MEAN, INVVEN_LOWER, INVVEN_UPPER, DEATHS_MEAN, DEATHS_LOWER, DEATHS_UPPER, ADMIS_MEAN, ADMIS_LOWER, ADMIS_UPPER, NEWICU_MEAN, NEWICU_LOWER, NEWICU_UPPER, TOTDEA_MEAN, TOTDEA_LOWER, TOTDEA_UPPER, BEDOVER_MEAN, BEDOVER_LOWER, BEDOVER_UPPER, ICUOVER_MEAN, ICUOVER_LOWER, ICUOVER_UPPER

with source as (
    select * from {{ ref('stg_covid19_data__ihme_covid_19') }}
)

select
    last_reported_flag,
    country_region,
    iso_3166_1,
    iso_3166_2,
    province_state,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(allbed_mean) as total_allbed_mean,
    avg(allbed_mean) as avg_allbed_mean,
    min(allbed_mean) as min_allbed_mean,
    max(allbed_mean) as max_allbed_mean,
    sum(allbed_lower) as total_allbed_lower,
    avg(allbed_lower) as avg_allbed_lower,
    min(allbed_lower) as min_allbed_lower,
    max(allbed_lower) as max_allbed_lower,
    sum(allbed_upper) as total_allbed_upper,
    avg(allbed_upper) as avg_allbed_upper,
    min(allbed_upper) as min_allbed_upper,
    max(allbed_upper) as max_allbed_upper,
    sum(icubed_mean) as total_icubed_mean,
    avg(icubed_mean) as avg_icubed_mean,
    min(icubed_mean) as min_icubed_mean,
    max(icubed_mean) as max_icubed_mean,
    sum(icubed_lower) as total_icubed_lower,
    avg(icubed_lower) as avg_icubed_lower,
    min(icubed_lower) as min_icubed_lower,
    max(icubed_lower) as max_icubed_lower,
    sum(icubed_upper) as total_icubed_upper,
    avg(icubed_upper) as avg_icubed_upper,
    min(icubed_upper) as min_icubed_upper,
    max(icubed_upper) as max_icubed_upper,
    sum(invven_mean) as total_invven_mean,
    avg(invven_mean) as avg_invven_mean,
    min(invven_mean) as min_invven_mean,
    max(invven_mean) as max_invven_mean,
    sum(invven_lower) as total_invven_lower,
    avg(invven_lower) as avg_invven_lower,
    min(invven_lower) as min_invven_lower,
    max(invven_lower) as max_invven_lower,
    sum(invven_upper) as total_invven_upper,
    avg(invven_upper) as avg_invven_upper,
    min(invven_upper) as min_invven_upper,
    max(invven_upper) as max_invven_upper,
    sum(deaths_mean) as total_deaths_mean,
    avg(deaths_mean) as avg_deaths_mean,
    min(deaths_mean) as min_deaths_mean,
    max(deaths_mean) as max_deaths_mean

from source
group by last_reported_flag, country_region, iso_3166_1, iso_3166_2, province_state, date_trunc('month', date), year(date)
