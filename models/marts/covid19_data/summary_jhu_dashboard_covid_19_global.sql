-- Summary mart: auto-generated aggregations from JHU_DASHBOARD_COVID_19_GLOBAL
-- Dimensions: ISO3166_1, ISO3166_2, LAST_REPORTED_FLAG
-- Measures: ACTIVE, PEOPLE_TESTED, CONFIRMED, PEOPLE_HOSPITALIZED, DEATHS, RECOVERED, INCIDENT_RATE, TESTING_RATE, HOSPITALIZATION_RATE, MORTALITY_RATE, LONG, LAT

with source as (
    select * from {{ ref('stg_covid19_data__jhu_dashboard_covid_19_global') }}
)

select
    iso3166_1,
    iso3166_2,
    last_reported_flag,
    date_trunc('month', date) as month_period,
    year(date) as year_period,
    count(*) as record_count,
    sum(active) as total_active,
    avg(active) as avg_active,
    min(active) as min_active,
    max(active) as max_active,
    sum(people_tested) as total_people_tested,
    avg(people_tested) as avg_people_tested,
    min(people_tested) as min_people_tested,
    max(people_tested) as max_people_tested,
    sum(confirmed) as total_confirmed,
    avg(confirmed) as avg_confirmed,
    min(confirmed) as min_confirmed,
    max(confirmed) as max_confirmed,
    sum(people_hospitalized) as total_people_hospitalized,
    avg(people_hospitalized) as avg_people_hospitalized,
    min(people_hospitalized) as min_people_hospitalized,
    max(people_hospitalized) as max_people_hospitalized,
    sum(deaths) as total_deaths,
    avg(deaths) as avg_deaths,
    min(deaths) as min_deaths,
    max(deaths) as max_deaths,
    sum(recovered) as total_recovered,
    avg(recovered) as avg_recovered,
    min(recovered) as min_recovered,
    max(recovered) as max_recovered,
    sum(incident_rate) as total_incident_rate,
    avg(incident_rate) as avg_incident_rate,
    min(incident_rate) as min_incident_rate,
    max(incident_rate) as max_incident_rate,
    sum(testing_rate) as total_testing_rate,
    avg(testing_rate) as avg_testing_rate,
    min(testing_rate) as min_testing_rate,
    max(testing_rate) as max_testing_rate,
    sum(hospitalization_rate) as total_hospitalization_rate,
    avg(hospitalization_rate) as avg_hospitalization_rate,
    min(hospitalization_rate) as min_hospitalization_rate,
    max(hospitalization_rate) as max_hospitalization_rate,
    sum(mortality_rate) as total_mortality_rate,
    avg(mortality_rate) as avg_mortality_rate,
    min(mortality_rate) as min_mortality_rate,
    max(mortality_rate) as max_mortality_rate

from source
group by iso3166_1, iso3166_2, last_reported_flag, date_trunc('month', date), year(date)
