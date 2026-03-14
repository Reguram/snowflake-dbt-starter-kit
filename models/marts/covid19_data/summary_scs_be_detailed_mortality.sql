-- Summary mart: auto-generated aggregations from SCS_BE_DETAILED_MORTALITY
-- Dimensions: SEX, AGEGROUP, ISO3166_1, ISO3166_2
-- Measures: DEATHS

with source as (
    select * from {{ ref('stg_covid19_data__scs_be_detailed_mortality') }}
)

select
    sex,
    agegroup,
    iso3166_1,
    iso3166_2,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(deaths) as total_deaths,
    avg(deaths) as avg_deaths,
    min(deaths) as min_deaths,
    max(deaths) as max_deaths

from source
group by sex, agegroup, iso3166_1, iso3166_2, date_trunc('month', date), year(date)
