{#
    Generate Snowflake Semantic View DDL from dbt model metadata.
    Uses current Snowflake syntax: TABLES / DIMENSIONS / METRICS.
    
    Usage in a run-operation or post-hook:
    {{ generate_semantic_view_ddl('sem_revenue_analysis') }}
#}
{% macro generate_semantic_view_ddl(model_name) %}

    {% set model_node = graph.nodes.get('model.' ~ project_name ~ '.' ~ model_name) %}
    {% if model_node is none %}
        {{ exceptions.raise_compiler_error("Model '" ~ model_name ~ "' not found in graph") }}
    {% endif %}

    {% set meta = model_node.meta.get('snowflake_semantic_view', {}) %}
    {% set sv_name = meta.get('name', model_name | upper) %}
    {% set sv_desc = meta.get('description', '') %}
    {% set dimensions = meta.get('dimensions', []) %}
    {% set metrics = meta.get('metrics', []) %}
    {% set table_alias = model_name | replace('sem_', '') %}

    {% set ddl %}
CREATE OR REPLACE SEMANTIC VIEW {{ target.database }}.{{ target.schema }}.{{ sv_name }}
  TABLES (
    {{ table_alias }} AS {{ ref(model_name) }}
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
