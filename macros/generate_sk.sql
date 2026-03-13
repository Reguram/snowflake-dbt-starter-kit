{#
    Generate a surrogate key from one or more columns.
    Wrapper around dbt_utils.generate_surrogate_key for consistency.
#}
{% macro generate_sk(columns) %}
    {{ dbt_utils.generate_surrogate_key(columns) }}
{% endmacro %}
