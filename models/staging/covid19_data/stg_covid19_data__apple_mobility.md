# Transformations — `stg_covid19_data__apple_mobility`

**Source:** `COVID19_EPIDEMIOLOGICAL_DATA.PUBLIC.APPLE_MOBILITY`
**Generated SQL:** [`stg_covid19_data__apple_mobility.sql`](./stg_covid19_data__apple_mobility.sql)
**Last updated:** 2026-05-05

> Default rule: any column NOT listed in the *Transformations* table or the
> *Excluded columns* list is moved through with a plain snake_case rename and
> no transformation.

## Transformations

<!-- This source is already published as cleanly-typed Snowflake columns, so
     no per-column transforms are required at the bronze layer. The full
     column list below is therefore moved as-is via lowercase rename. -->

| Source column | Output column | Type | SQL expression | Reason |
|---------------|---------------|------|----------------|--------|
| _none_        |               |      |                |        |

## Excluded columns

<!-- One bullet per column. Anything not listed here is INCLUDED. -->
- _none_

## As-is columns (informational)

- `COUNTRY_REGION`     → `country_region`
- `PROVINCE_STATE`     → `province_state`
- `DATE`               → `date`
- `TRANSPORTATION_TYPE` → `transportation_type`
- `DIFFERENCE`         → `difference`
- `ISO3166_1`          → `iso3166_1`
- `ISO3166_2`          → `iso3166_2`
- `LAST_UPDATED_DATE`  → `last_updated_date`
- `LAST_REPORTED_FLAG` → `last_reported_flag`
