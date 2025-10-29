"""
dbt Model Generator
Creates SQL files for staging, intermediate, and marts models
"""

from typing import Dict
from src.ai.scenario_generator import DemoScenario


def generate_dbt_models(scenario: DemoScenario) -> Dict[str, str]:
    """
    Generate all dbt model SQL files from the scenario

    Args:
        scenario: The demo scenario with model definitions

    Returns:
        Dictionary mapping filepath to SQL content
    """
    models = {}

    # Generate staging models
    for model in scenario.staging_models:
        filepath = f"models/staging/{model.name}.sql"
        sql_content = generate_staging_model_sql(model, scenario)
        models[filepath] = sql_content

    # Generate intermediate models
    for model in scenario.intermediate_models:
        filepath = f"models/intermediate/{model.name}.sql"
        sql_content = generate_intermediate_model_sql(model, scenario)
        models[filepath] = sql_content

    # Generate marts models
    for model in scenario.marts_models:
        filepath = f"models/marts/{model.name}.sql"
        sql_content = generate_mart_model_sql(model, scenario)
        models[filepath] = sql_content

    return models


def generate_staging_model_sql(model, scenario: DemoScenario) -> str:
    """Generate SQL for a staging model"""

    # Find the source definition
    source_table = model.source_table
    source_data = next((s for s in scenario.data_sources if s.name == source_table), None)

    if source_data:
        columns = source_data.columns
    else:
        # Fallback if source not found
        columns = ['id', 'created_at', 'updated_at']

    # Build column list with basic transformations
    column_sql_list = []
    for col in columns:
        # Apply common staging transformations
        if col.lower() in ['id', 'created_at', 'updated_at']:
            column_sql_list.append(f"    {col}")
        else:
            column_sql_list.append(f"    {col}")

    columns_sql = ",\n".join(column_sql_list)

    # Determine source reference
    source_name = source_table.split('.')[-1] if '.' in source_table else source_table

    sql = f"""{{{{
    config(
        materialized='view'
    )
}}}}

/*
    {model.description}
*/

with source as (

    select * from {{{{ ref('{source_name}') }}}}

),

renamed as (

    select
{columns_sql}

    from source

)

select * from renamed
"""

    return sql


def generate_intermediate_model_sql(model, scenario: DemoScenario) -> str:
    """Generate SQL for an intermediate model"""

    # Build CTEs for dependencies
    cte_list = []
    for i, dep in enumerate(model.depends_on):
        cte_name = dep.replace('stg_', '').replace('int_', '')
        cte_list.append(f"{cte_name} as (\n\n    select * from {{{{ ref('{dep}') }}}}\n\n)")

    ctes_sql = ",\n\n".join(cte_list)

    # Build basic join logic (simplified)
    if len(model.depends_on) > 1:
        base_table = model.depends_on[0].replace('stg_', '').replace('int_', '')
        join_tables = [dep.replace('stg_', '').replace('int_', '') for dep in model.depends_on[1:]]

        join_sql = f"    from {base_table}\n"
        for join_table in join_tables:
            join_sql += f"    left join {join_table} on {base_table}.id = {join_table}.id\n"

        final_select = "    select\n        *\n" + join_sql
    else:
        table_name = model.depends_on[0].replace('stg_', '').replace('int_', '')
        final_select = f"    select * from {table_name}"

    sql = f"""{{{{
    config(
        materialized='view'
    )
}}}}

/*
    {model.description}
*/

with {ctes_sql},

final as (

{final_select}

)

select * from final
"""

    return sql


def generate_mart_model_sql(model, scenario: DemoScenario) -> str:
    """Generate SQL for a marts model"""

    # Determine materialization
    if model.is_incremental:
        materialization = "materialized='incremental',\n        unique_key='id'"
    else:
        materialization = "materialized='table'"

    # Build CTEs for dependencies
    cte_list = []
    for dep in model.depends_on:
        cte_name = dep.replace('stg_', '').replace('int_', '').replace('fct_', '').replace('dim_', '')
        cte_list.append(f"{cte_name} as (\n\n    select * from {{{{ ref('{dep}') }}}}\n\n)")

    ctes_sql = ",\n\n".join(cte_list)

    # Build aggregation logic (simplified)
    if len(model.depends_on) > 1:
        base_table = model.depends_on[0].replace('stg_', '').replace('int_', '')
        agg_sql = f"""    select
        *
    from {base_table}"""
    else:
        table_name = model.depends_on[0].replace('stg_', '').replace('int_', '')
        agg_sql = f"    select * from {table_name}"

    # Add incremental logic if needed
    incremental_logic = ""
    if model.is_incremental:
        incremental_logic = """

    {% if is_incremental() %}
        -- Only include new/updated records
        where updated_at > (select max(updated_at) from {{ this }})
    {% endif %}
"""

    sql = f"""{{{{
    config(
        {materialization}
    )
}}}}

/*
    {model.description}
*/

with {ctes_sql},

final as (

{agg_sql}{incremental_logic}

)

select * from final
"""

    return sql
