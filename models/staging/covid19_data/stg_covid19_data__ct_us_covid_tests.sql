with source as (
    select * from {{ source('covid19_data', 'CT_US_COVID_TESTS') }}
),

staged as (
    select
        country_region,
        province_state,
        date,
        positive,
        positive_since_previous_day,
        negative,
        negative_since_previous_day,
        pending,
        pending_since_previous_day,
        death,
        death_since_previous_day,
        hospitalized,
        hospitalized_since_previous_day,
        total,
        total_since_previous_day,
        iso3166_1,
        iso3166_2,
        last_updated_date,
        last_reported_flag,
        hospitalizedcurrently,
        hospitalizedcurrentlyincrease,
        hospitalizedcumulative,
        hospitalizedcumulativeincrease,
        inicucurrently,
        inicucurrentlyincrease,
        inicucumulative,
        inicucumulativeincrease,
        onventilatorcurrently,
        onventilatorcurrentlyincrease,
        onventilatorcumulative,
        onventilatorcumulativeincrease
    from source
)

select * from staged
