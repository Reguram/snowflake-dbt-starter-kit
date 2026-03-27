CREATE OR REPLACE SEMANTIC VIEW DBT_DEV.SEMANTIC.SEM_CDC_PATIENT_IMPACT
  TABLES (
    patient_impact AS DBT_DEV.DBT_MARTS.FCT_CDC_REPORTED_PATIENT_IMPACT
  )
  DIMENSIONS (
    patient_impact.state AS state
      COMMENT = 'US state abbreviation',
    patient_impact.iso3166_1 AS iso3166_1
      COMMENT = 'ISO 3166-1 country code',
    patient_impact.iso3166_2 AS iso3166_2
      COMMENT = 'ISO 3166-2 state/region code',
    patient_impact.last_reported_flag AS last_reported_flag
      COMMENT = 'True if this is the most recent report for this state',
    patient_impact.report_date AS CAST(date AS DATE)
      COMMENT = 'Date of the report',
    patient_impact.report_month AS DATE_TRUNC('month', CAST(date AS DATE))
      COMMENT = 'Report month derived from date',
    patient_impact.report_year AS EXTRACT(YEAR FROM CAST(date AS DATE))
      COMMENT = 'Report year derived from date'
  )
  METRICS (
    patient_impact.total_inpatient_beds AS SUM(inpatient_beds)
      COMMENT = 'Total staffed inpatient beds',
    patient_impact.total_inpatient_beds_used AS SUM(inpatient_beds_used)
      COMMENT = 'Total inpatient beds currently in use',
    patient_impact.total_inpatient_beds_used_covid AS SUM(inpatient_beds_used_covid)
      COMMENT = 'Total inpatient beds occupied by COVID patients',
    patient_impact.total_hospital_onset_covid AS SUM(hospital_onset_covid)
      COMMENT = 'Total patients with hospital-onset COVID',
    patient_impact.total_adult_covid_hospitalized AS SUM(total_adult_patients_hospitalized_confirmed_covid)
      COMMENT = 'Total adult patients hospitalized with confirmed COVID',
    patient_impact.total_adult_covid_suspected_hospitalized AS SUM(total_adult_patients_hospitalized_confirmed_and_suspected_covid)
      COMMENT = 'Total adult patients hospitalized with confirmed and suspected COVID',
    patient_impact.total_pediatric_covid_hospitalized AS SUM(total_pediatric_patients_hospitalized_confirmed_covid)
      COMMENT = 'Total pediatric patients hospitalized with confirmed COVID',
    patient_impact.total_staffed_icu_beds AS SUM(total_staffed_adult_icu_beds)
      COMMENT = 'Total staffed adult ICU beds',
    patient_impact.total_icu_bed_occupancy AS SUM(staffed_adult_icu_bed_occupancy)
      COMMENT = 'Total occupied adult ICU beds',
    patient_impact.total_icu_covid_patients AS SUM(staffed_icu_adult_patients_confirmed_covid)
      COMMENT = 'Total adult ICU patients with confirmed COVID',
    patient_impact.total_prev_day_adult_admissions AS SUM(previous_day_admission_adult_covid_confirmed)
      COMMENT = 'Total previous-day adult COVID confirmed admissions',
    patient_impact.total_prev_day_pediatric_admissions AS SUM(previous_day_admission_pediatric_covid_confirmed)
      COMMENT = 'Total previous-day pediatric COVID confirmed admissions',
    patient_impact.total_staffing_shortage_yes AS SUM(critical_staffing_shortage_today_yes)
      COMMENT = 'Count of facilities reporting critical staffing shortage today',
    patient_impact.total_staffing_shortage_no AS SUM(critical_staffing_shortage_today_no)
      COMMENT = 'Count of facilities reporting no critical staffing shortage today',
    patient_impact.avg_inpatient_bed_utilization AS AVG(inpatient_beds_utilization)
      COMMENT = 'Average inpatient bed utilization rate',
    patient_impact.avg_inpatient_bed_covid_utilization AS AVG(inpatient_bed_covid_utilization)
      COMMENT = 'Average inpatient bed COVID utilization rate',
    patient_impact.avg_adult_icu_bed_utilization AS AVG(adult_icu_bed_utilization)
      COMMENT = 'Average adult ICU bed utilization rate',
    patient_impact.avg_adult_icu_bed_covid_utilization AS AVG(adult_icu_bed_covid_utilization)
      COMMENT = 'Average adult ICU bed COVID utilization rate',
    patient_impact.avg_pct_inpatients_with_covid AS AVG(percent_of_inpatients_with_covid)
      COMMENT = 'Average percentage of inpatients with COVID'
  )
  COMMENT = 'CDC reported hospital patient impact — inpatient beds, ICU utilization, staffing, and COVID admissions by US state and date';
