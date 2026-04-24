{% macro publish_verified_queries() %}
{#-
  Generic post-hook macro for any semantic view model.
  Reads verified_queries from the model's own meta config (in its .yml file),
  appends them to the current semantic view YAML, and recreates the view.

  Usage — in the model's .yml:
    config:
      meta:
        verified_queries:
          - name: my_query
            question: "What is ...?"
            verified_at: 1744070400
            verified_by: author
            sql: "SELECT ... FROM __table_alias ..."

  Then in the model's .sql config block:
    post_hook = ["{{ publish_verified_queries() }}"]

  Single quotes in SQL are auto-escaped — write normal SQL in the YAML.
-#}

{%- set meta    = model.config.meta or {} -%}
{%- set queries = meta.get('verified_queries', []) -%}

{%- if queries | length == 0 -%}

  SELECT 1 /* no verified queries configured for {{ this.identifier }} */

{%- else -%}

  {%- set ns = namespace(yaml = '\nverified_queries:') -%}

  {%- for vq in queries %}
    {%- set escaped_question = vq.question | replace("'", "''") -%}
    {%- set escaped_sql      = vq.sql      | replace("'", "''") -%}
    {%- set ns.yaml = ns.yaml
        ~ '\n  - name: '        ~ vq.name
        ~ '\n    question: "'   ~ escaped_question ~ '"'
        ~ '\n    verified_at: ' ~ vq.verified_at
        ~ '\n    verified_by: ' ~ vq.verified_by
        ~ '\n    sql: |' -%}
    {%- for sql_line in escaped_sql.strip().split('\n') %}
      {%- set ns.yaml = ns.yaml ~ '\n      ' ~ sql_line -%}
    {%- endfor %}
  {%- endfor %}

  CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML(
    '{{ this.database }}.{{ this.schema }}',
    SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('{{ this }}')
    || '{{ ns.yaml }}'
  )

{%- endif -%}

{% endmacro %}
