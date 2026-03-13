{#
    Limit data in development for faster iteration.
    Usage: {{ limit_data_in_dev('order_date', 365) }}
#}
{% macro limit_data_in_dev(date_column, days=365) %}
    {% if target.name == 'dev' %}
        where {{ date_column }} >= dateadd('day', -{{ days }}, current_date())
    {% endif %}
{% endmacro %}
