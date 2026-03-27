{#
  ======================================================================
  Semantic View: SEM_CDC_PATIENT_IMPACT
  ======================================================================
  This model is DISABLED (enabled: false in dbt_project.yml).
  It does NOT run during `dbt build`.

  The Snowflake Semantic View DDL is maintained in:
    ddl/semantic/sem_cdc_patient_impact_ddl.sql

  To execute the DDL, run it directly in Snowflake:
    USE ROLE ACCOUNTADMIN;
    -- then paste/execute the DDL from ddl/semantic/sem_cdc_patient_impact_ddl.sql

  The DDL references FCT_CDC_REPORTED_PATIENT_IMPACT (in DBT_MARTS) directly.

  Original base SELECT (kept for reference):
  --------------------------------------------------------------------------
  with base as (
      select * from {{ ref('fct_cdc_reported_patient_impact') }}
  )
  select
      state, iso3166_1, iso3166_2, last_reported_flag,
      cast(date as date) as report_date,
      date_trunc('month', cast(date as date)) as report_month,
      extract(year from cast(date as date)) as report_year,
      inpatient_beds, inpatient_beds_used, inpatient_beds_used_covid,
      hospital_onset_covid, total_adult_patients_hospitalized_confirmed_covid,
      total_pediatric_patients_hospitalized_confirmed_covid,
      total_staffed_adult_icu_beds, staffed_adult_icu_bed_occupancy,
      staffed_icu_adult_patients_confirmed_covid,
      previous_day_admission_adult_covid_confirmed,
      previous_day_admission_pediatric_covid_confirmed,
      critical_staffing_shortage_today_yes, critical_staffing_shortage_today_no,
      inpatient_beds_utilization, inpatient_bed_covid_utilization,
      adult_icu_bed_utilization, adult_icu_bed_covid_utilization,
      percent_of_inpatients_with_covid
  from base
  --------------------------------------------------------------------------
#}

-- This model is disabled. See comment block above for details.
select 1 as _placeholder
