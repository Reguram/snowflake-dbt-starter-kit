-- Summary mart: auto-generated aggregations from DEMOGRAPHICS
-- Dimensions: ISO3166_2, STATE
-- Measures: LATITUDE, LONGITUDE, TOTAL_POPULATION, TOTAL_MALE_POPULATION, TOTAL_FEMALE_POPULATION

with source as (
    select * from {{ ref('stg_covid19_data__demographics') }}
)

select
    iso3166_2,
    state,
    count(*) as record_count,
    sum(latitude) as total_latitude,
    avg(latitude) as avg_latitude,
    min(latitude) as min_latitude,
    max(latitude) as max_latitude,
    sum(longitude) as total_longitude,
    avg(longitude) as avg_longitude,
    min(longitude) as min_longitude,
    max(longitude) as max_longitude,
    sum(total_population) as total_total_population,
    avg(total_population) as avg_total_population,
    min(total_population) as min_total_population,
    max(total_population) as max_total_population,
    sum(total_male_population) as total_total_male_population,
    avg(total_male_population) as avg_total_male_population,
    min(total_male_population) as min_total_male_population,
    max(total_male_population) as max_total_male_population,
    sum(total_female_population) as total_total_female_population,
    avg(total_female_population) as avg_total_female_population,
    min(total_female_population) as min_total_female_population,
    max(total_female_population) as max_total_female_population

from source
group by iso3166_2, state
