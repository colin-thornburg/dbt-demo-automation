"""
dbt_project.yml Generator
Creates customized dbt project configuration
"""

import yaml
from typing import Optional
from src.ai.scenario_generator import DemoScenario


def generate_dbt_project_yml(
    scenario: DemoScenario,
    dbt_cloud_project_id: Optional[str] = None
) -> str:
    """
    Generate dbt_project.yml configuration

    Args:
        scenario: The demo scenario

    Returns:
        YAML content as string
    """
    # Create project name from company name
    project_name = scenario.company_name.lower().replace(' ', '_').replace('-', '_')
    if not project_name[0].isalpha():
        project_name = 'demo_' + project_name

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

        'clean-targets': [
            'target',
            'dbt_packages'
        ],

        'models': {
            project_name: {
                'staging': {
                    '+materialized': 'view',
                    '+tags': ['staging']
                },
                'intermediate': {
                    '+materialized': 'view',
                    '+tags': ['intermediate']
                },
                'marts': {
                    '+materialized': 'table',
                    '+tags': ['marts']
                }
            }
        },

        'seeds': {
            project_name: {
                '+enabled': True,
                '+schema': 'seeds'
            }
        }
    }

    if dbt_cloud_project_id:
        project_dict['dbt-cloud'] = {
            'project-id': dbt_cloud_project_id
        }

    return yaml.dump(project_dict, default_flow_style=False, sort_keys=False)
