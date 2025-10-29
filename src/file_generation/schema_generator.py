"""
Schema.yml Generator
Creates schema definitions with sources, models, columns, and tests
"""

import yaml
from typing import Dict, List, Any
from src.ai.scenario_generator import DemoScenario


def generate_schema_yml(scenario: DemoScenario) -> Dict[str, str]:
    """
    Generate schema.yml files for all layers

    Args:
        scenario: The demo scenario

    Returns:
        Dictionary mapping filepath to YAML content
    """
    schema_files = {}

    # Generate sources schema (in staging)
    sources_schema = generate_sources_schema(scenario)
    schema_files['models/staging/schema.yml'] = sources_schema

    # Generate staging models schema
    staging_schema = generate_staging_schema(scenario)
    schema_files['models/staging/models_schema.yml'] = staging_schema

    # Generate intermediate models schema
    intermediate_schema = generate_intermediate_schema(scenario)
    schema_files['models/intermediate/schema.yml'] = intermediate_schema

    # Generate marts models schema
    marts_schema = generate_marts_schema(scenario)
    schema_files['models/marts/schema.yml'] = marts_schema

    return schema_files


def generate_sources_schema(scenario: DemoScenario) -> str:
    """Generate sources schema for seed data"""
    sources = []

    for data_source in scenario.data_sources:
        table_name = data_source.name.split('.')[-1]

        columns = []
        for col in data_source.columns:
            column_def = {
                'name': col,
                'description': f'{col.replace("_", " ").title()} column'
            }

            # Add tests for common columns
            tests = []
            if col.lower() == 'id':
                tests = ['unique', 'not_null']
            elif col.lower().endswith('_id'):
                tests = ['not_null']
            elif 'email' in col.lower():
                tests = ['not_null']

            if tests:
                column_def['tests'] = tests

            columns.append(column_def)

        sources.append({
            'name': table_name,
            'description': data_source.description,
            'columns': columns
        })

    schema_dict = {
        'version': 2,
        'sources': [{
            'name': 'seeds',
            'description': 'Seed data for demo',
            'tables': sources
        }]
    }

    return yaml.dump(schema_dict, default_flow_style=False, sort_keys=False)


def generate_staging_schema(scenario: DemoScenario) -> str:
    """Generate schema for staging models"""
    models = []

    for model in scenario.staging_models:
        # Get source columns
        source_table = model.source_table
        source_data = next((s for s in scenario.data_sources if s.name == source_table), None)

        columns = []
        if source_data:
            for col in source_data.columns[:5]:  # Limit to first 5 columns for brevity
                column_def = {
                    'name': col,
                    'description': f'{col.replace("_", " ").title()}'
                }
                columns.append(column_def)

        models.append({
            'name': model.name,
            'description': model.description,
            'columns': columns
        })

    schema_dict = {
        'version': 2,
        'models': models
    }

    return yaml.dump(schema_dict, default_flow_style=False, sort_keys=False)


def generate_intermediate_schema(scenario: DemoScenario) -> str:
    """Generate schema for intermediate models"""
    models = []

    for model in scenario.intermediate_models:
        # Basic column documentation
        columns = [
            {'name': 'id', 'description': 'Primary key'},
            {'name': 'created_at', 'description': 'Creation timestamp'},
            {'name': 'updated_at', 'description': 'Last update timestamp'}
        ]

        models.append({
            'name': model.name,
            'description': model.description,
            'columns': columns
        })

    schema_dict = {
        'version': 2,
        'models': models
    }

    return yaml.dump(schema_dict, default_flow_style=False, sort_keys=False)


def generate_marts_schema(scenario: DemoScenario) -> str:
    """Generate schema for marts models with comprehensive tests"""
    models = []

    for model in scenario.marts_models:
        # Build columns with tests
        columns = [
            {
                'name': 'id',
                'description': 'Primary key',
                'tests': ['unique', 'not_null']
            }
        ]

        # Add metric columns if applicable
        for metric in scenario.key_metrics[:2]:  # Add first 2 metrics as example columns
            metric_col_name = metric.name.lower().replace(' ', '_')
            columns.append({
                'name': metric_col_name,
                'description': metric.description
            })

        # Add timestamp columns
        columns.extend([
            {
                'name': 'created_at',
                'description': 'Creation timestamp',
                'tests': ['not_null']
            },
            {
                'name': 'updated_at',
                'description': 'Last update timestamp'
            }
        ])

        model_def = {
            'name': model.name,
            'description': model.description,
            'columns': columns
        }

        # Add model-level tests
        if model.is_incremental:
            model_def['tests'] = [
                'dbt_utils.unique_combination_of_columns:\n            combination_of_columns:\n              - id\n              - updated_at'
            ]

        models.append(model_def)

    schema_dict = {
        'version': 2,
        'models': models
    }

    return yaml.dump(schema_dict, default_flow_style=False, sort_keys=False)
