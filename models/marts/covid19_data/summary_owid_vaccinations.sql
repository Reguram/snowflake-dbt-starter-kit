-- Summary mart: auto-generated aggregations from OWID_VACCINATIONS
-- Dimensions: COUNTRY_REGION, ISO3166_1, VACCINES, SOURCE_NAME, SOURCE_WEBSITE, LAST_REPORTED_FLAG
-- Measures: TOTAL_VACCINATIONS, PEOPLE_VACCINATED, PEOPLE_FULLY_VACCINATED, DAILY_VACCINATIONS_RAW, DAILY_VACCINATIONS, TOTAL_VACCINATIONS_PER_HUNDRED, PEOPLE_VACCINATED_PER_HUNDRED, PEOPLE_FULLY_VACCINATED_PER_HUNDRED, DAILY_VACCINATIONS_PER_MILLION

with source as (
    select * from {{ ref('stg_covid19_data__owid_vaccinations') }}
)

select
    country_region,
    iso3166_1,
    vaccines,
    source_name,
    source_website,
    last_reported_flag,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(total_vaccinations) as total_total_vaccinations,
    avg(total_vaccinations) as avg_total_vaccinations,
    min(total_vaccinations) as min_total_vaccinations,
    max(total_vaccinations) as max_total_vaccinations,
    sum(people_vaccinated) as total_people_vaccinated,
    avg(people_vaccinated) as avg_people_vaccinated,
    min(people_vaccinated) as min_people_vaccinated,
    max(people_vaccinated) as max_people_vaccinated,
    sum(people_fully_vaccinated) as total_people_fully_vaccinated,
    avg(people_fully_vaccinated) as avg_people_fully_vaccinated,
    min(people_fully_vaccinated) as min_people_fully_vaccinated,
    max(people_fully_vaccinated) as max_people_fully_vaccinated,
    sum(daily_vaccinations_raw) as total_daily_vaccinations_raw,
    avg(daily_vaccinations_raw) as avg_daily_vaccinations_raw,
    min(daily_vaccinations_raw) as min_daily_vaccinations_raw,
    max(daily_vaccinations_raw) as max_daily_vaccinations_raw,
    sum(daily_vaccinations) as total_daily_vaccinations,
    avg(daily_vaccinations) as avg_daily_vaccinations,
    min(daily_vaccinations) as min_daily_vaccinations,
    max(daily_vaccinations) as max_daily_vaccinations,
    sum(total_vaccinations_per_hundred) as total_total_vaccinations_per_hundred,
    avg(total_vaccinations_per_hundred) as avg_total_vaccinations_per_hundred,
    min(total_vaccinations_per_hundred) as min_total_vaccinations_per_hundred,
    max(total_vaccinations_per_hundred) as max_total_vaccinations_per_hundred,
    sum(people_vaccinated_per_hundred) as total_people_vaccinated_per_hundred,
    avg(people_vaccinated_per_hundred) as avg_people_vaccinated_per_hundred,
    min(people_vaccinated_per_hundred) as min_people_vaccinated_per_hundred,
    max(people_vaccinated_per_hundred) as max_people_vaccinated_per_hundred,
    sum(people_fully_vaccinated_per_hundred) as total_people_fully_vaccinated_per_hundred,
    avg(people_fully_vaccinated_per_hundred) as avg_people_fully_vaccinated_per_hundred,
    min(people_fully_vaccinated_per_hundred) as min_people_fully_vaccinated_per_hundred,
    max(people_fully_vaccinated_per_hundred) as max_people_fully_vaccinated_per_hundred,
    sum(daily_vaccinations_per_million) as total_daily_vaccinations_per_million,
    avg(daily_vaccinations_per_million) as avg_daily_vaccinations_per_million,
    min(daily_vaccinations_per_million) as min_daily_vaccinations_per_million,
    max(daily_vaccinations_per_million) as max_daily_vaccinations_per_million

from source
group by country_region, iso3166_1, vaccines, source_name, source_website, last_reported_flag, date_trunc('month', date), year(date)
