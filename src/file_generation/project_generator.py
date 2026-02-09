"""
dbt_project.yml Generator
Creates customized dbt project configuration with unique, privacy-safe names.

IMPORTANT – Snowflake seed loading:
We explicitly set ``+column_types`` for EVERY column in EVERY seed,
mapping them all to ``varchar``.  This bypasses agate's type-inference
(the #1 root cause of ``invalid identifier`` errors on Snowflake) and
forces dbt to emit a predictable ``CREATE TABLE … (col VARCHAR, …)``
statement.  Combined with ``+quote_columns: false`` the column names
are always unquoted → Snowflake stores them uppercase → references
always resolve.
"""

import yaml
from typing import Optional
from src.ai.scenario_generator import DemoScenario
from src.naming import make_unique_project_name


def generate_dbt_project_yml(
    scenario: DemoScenario,
    dbt_cloud_project_id: Optional[str] = None,
) -> str:
    """
    Generate dbt_project.yml configuration with a unique project name.

    The project name is derived from a privacy-safe alias of the company
    name so that real prospect names never appear in generated artifacts.

    Args:
        scenario: The demo scenario
        dbt_cloud_project_id: Optional dbt Cloud project ID for CLI integration

    Returns:
        YAML content as string
    """
    project_name = make_unique_project_name(scenario.company_name)

    # ── Build per-seed column_types config ─────────────────────────
    # Forces ALL columns to VARCHAR so agate never guesses types and
    # the adapter never emits ambiguous DDL.
    seed_config: dict = {
        '+enabled': True,
        '+schema': 'seeds',
        '+quote_columns': False,
    }
    for ds in scenario.data_sources:
        table_name = ds.name.split('.')[-1]
        col_types = {col: 'varchar' for col in ds.columns}
        seed_config[table_name] = {'+column_types': col_types}

    project_dict = {
        'name': project_name,
        'version': '1.0.0',
        'config-version': 2,
        'profile': project_name,
        'model-paths': ['models'],
        'analysis-paths': ['analyses'],
        'test-paths': ['tests'],
        'seed-paths': ['seeds'],
        'macro-paths': ['macros'],
        'snapshot-paths': ['snapshots'],
        'clean-targets': ['target', 'dbt_packages'],
        'models': {
            project_name: {
                'staging': {'+materialized': 'view', '+tags': ['staging']},
                'intermediate': {'+materialized': 'view', '+tags': ['intermediate']},
                'marts': {'+materialized': 'table', '+tags': ['marts']},
            }
        },
        'seeds': {
            project_name: seed_config,
        },
    }

    if dbt_cloud_project_id:
        project_dict['dbt-cloud'] = {'project-id': dbt_cloud_project_id}

    return yaml.dump(project_dict, default_flow_style=False, sort_keys=False)
