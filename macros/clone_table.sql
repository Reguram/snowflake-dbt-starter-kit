{#
    Helper to create a Snowflake clone of a table for safe testing.
    Usage: {{ clone_table('my_database', 'my_schema', 'my_table', 'my_clone') }}
#}
{% macro clone_table(database, schema, source_table, clone_name) %}
    {% set sql %}
        CREATE OR REPLACE TABLE {{ database }}.{{ schema }}.{{ clone_name }}
        CLONE {{ database }}.{{ schema }}.{{ source_table }};
    {% endset %}
    {{ return(sql) }}
{% endmacro %}
