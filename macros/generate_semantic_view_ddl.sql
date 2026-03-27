{#
    Generate Snowflake Semantic View DDL from dbt model metadata.
    Uses current Snowflake syntax: TABLES / DIMENSIONS / METRICS.
    
    Usage in a run-operation:
    {{ generate_semantic_view_ddl('sem_revenue_analysis', base_model='fct_sales') }}
    
    Parameters:
      model_name: The semantic model name (reads metadata from schema.yml)
      base_model:  (Optional) The upstream mart model to reference in TABLES clause.
                   If not provided, defaults to the semantic model itself.
                   Use this when the semantic model is disabled (enabled: false).
#}
{% macro generate_semantic_view_ddl(model_name, base_model=none) %}

    {% set model_node = graph.nodes.get('model.' ~ project_name ~ '.' ~ model_name) %}
    {% if model_node is none %}
        {{ exceptions.raise_compiler_error("Model '" ~ model_name ~ "' not found in graph. If the model is disabled (enabled: false), pass base_model parameter to reference the upstream mart model.") }}
    {% endif %}

    {% set meta = model_node.meta.get('snowflake_semantic_view', {}) %}
    {% set sv_name = meta.get('name', model_name | upper) %}
    {% set sv_desc = meta.get('description', '') %}
    {% set dimensions = meta.get('dimensions', []) %}
    {% set metrics = meta.get('metrics', []) %}
    {% set table_alias = model_name | replace('sem_', '') %}

    {# Determine the base table reference #}
    {% if base_model is not none %}
        {% set base_ref = ref(base_model) %}
    {% else %}
        {% set base_ref = ref(model_name) %}
    {% endif %}

    {% set ddl %}
CREATE OR REPLACE SEMANTIC VIEW {{ target.database }}.{{ target.schema }}.{{ sv_name }}
  TABLES (
    {{ table_alias }} AS {{ base_ref }}
  )
  DIMENSIONS (
    {% for dim in dimensions %}
    {{ table_alias }}.{{ dim.name }} AS {{ dim.expression if dim.expression is defined else dim.name }}
      COMMENT = '{{ dim.description }}'{{ "," if not loop.last }}
    {% endfor %}
  )
  METRICS (
    {% for metric in metrics %}
    {{ table_alias }}.{{ metric.name }} AS {{ metric.type | upper }}({{ metric.expression }})
      COMMENT = '{{ metric.description }}'{{ "," if not loop.last }}
    {% endfor %}
  )
  COMMENT = '{{ sv_desc }}';
    {% endset %}

    {{ return(ddl) }}

{% endmacro %}
