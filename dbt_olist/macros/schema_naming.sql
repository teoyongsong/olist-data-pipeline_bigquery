{% macro generate_schema_name(custom_schema_name, node) -%}
    {# For BigQuery, use the custom schema (dataset) directly when provided,
       otherwise fall back to the target dataset from the profile. #}
    {%- if custom_schema_name is none -%}
        {{ target.dataset }}
    {%- else -%}
        {{ custom_schema_name }}
    {%- endif -%}
{%- endmacro %}

