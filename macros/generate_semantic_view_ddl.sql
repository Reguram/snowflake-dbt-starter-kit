{#
    Generate Snowflake Semantic View DDL from dbt model metadata.
    
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

    {% set ddl %}
CREATE OR REPLACE SEMANTIC VIEW {{ target.database }}.{{ target.schema }}.{{ sv_name }}
  COMMENT = '{{ sv_desc }}'
AS SELECT * FROM {{ ref(model_name) }}
COLUMNS (
    {% for dim in dimensions %}
    {{ dim.name }} AS DIMENSION COMMENT '{{ dim.description }}'{{ "," if not loop.last }}
    {% endfor %}
)
METRICS (
    {% for metric in metrics %}
    {{ metric.name }} AS {{ metric.type | upper }}({{ metric.expression }}) COMMENT '{{ metric.description }}'{{ "," if not loop.last }}
    {% endfor %}
);
    {% endset %}

    {{ return(ddl) }}

{% endmacro %}
