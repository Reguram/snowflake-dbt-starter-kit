with source as (
    select * from {{ source('covid19_data', 'HDX_ACAPS') }}
),

staged as (
    select
        country_state,
        admin_2,
        region,
        category,
        measure,
        targeted_pop_group,
        comments,
        non_compliance,
        date_implemented,
        source,
        source_type,
        link,
        entry_date,
        iso3166_1,
        last_updated_date,
        log_type
    from source
)

select * from staged
