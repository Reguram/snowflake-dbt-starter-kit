{#
    Override built-in generic tests to accept extra keyword arguments.
    Snowflake's dbt runtime (1.9.4) passes an additional 'arguments' kwarg
    that the default macro signatures don't accept, causing:
      "macro 'dbt_macro__test_accepted_values' takes no keyword argument 'arguments'"
    Referencing `kwargs` in the macro body tells Jinja2 to accept any extra kwargs.
#}

{% test accepted_values(model, column_name, values, quote=True) %}
    {# Consume kwargs so Jinja doesn't reject unexpected keyword arguments #}
    {% set _extra = kwargs %}

    select *
    from {{ model }}
    {% if execute %}
    where {{ column_name }} not in (
        {% for value in values %}
            {% if quote %}'{{ value }}'{% else %}{{ value }}{% endif %}{% if not loop.last %},{% endif %}
        {% endfor %}
    )
    {% endif %}
{% endtest %}

{% test unique(model, column_name) %}
    {% set _extra = kwargs %}
    {% set macro = adapter.dispatch('test_unique', 'dbt') %}
    {{ macro(model, column_name) }}
{% endtest %}

{% test not_null(model, column_name) %}
    {% set _extra = kwargs %}
    {% set macro = adapter.dispatch('test_not_null', 'dbt') %}
    {{ macro(model, column_name) }}
{% endtest %}

{% test relationships(model, column_name, to, field) %}
    {% set _extra = kwargs %}
    {% set macro = adapter.dispatch('test_relationships', 'dbt') %}
    {{ macro(model, column_name, to, field) }}
{% endtest %}
