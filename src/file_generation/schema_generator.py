"""
Schema.yml Generator
Creates schema definitions with seeds, models, columns, and tests.

IMPORTANT: Seeds are defined in seeds/schema.yml (not as sources) so that
dbt tests resolve via ref() and honour the seed schema configuration in
dbt_project.yml.  Defining seeds as sources would cause tests to look in
a literal 'seeds' schema instead of '<target_schema>_seeds'.
"""

import yaml
from typing import Dict, List
from src.ai.scenario_generator import DemoScenario
from src.naming import identify_primary_key


def generate_schema_yml(scenario: DemoScenario) -> Dict[str, str]:
    """
    Generate schema.yml files for all layers.

    Returns:
        Dictionary mapping filepath to YAML content
    """
    return {
        # Seed-level tests (NOT sources — avoids schema mismatch)
        'seeds/schema.yml': _seeds_schema(scenario),
        # Model-level schemas
        'models/staging/schema.yml': _staging_schema(scenario),
        'models/intermediate/schema.yml': _intermediate_schema(scenario),
        'models/marts/schema.yml': _marts_schema(scenario),
    }


# ── internal helpers ────────────────────────────────────────────────


def _seeds_schema(scenario: DemoScenario) -> str:
    """
    Generate a seeds/schema.yml that defines properties and tests
    directly on the seed files.

    By using the ``seeds:`` key (instead of ``sources:``), dbt resolves
    these via ref() and always finds the correct schema regardless of
    the ``+schema`` config in dbt_project.yml.
    """
    seeds = []
    for ds in scenario.data_sources:
        table_name = ds.name.split('.')[-1]
        pk = identify_primary_key(ds.columns, ds.name)

        columns = []
        for col in ds.columns:
            col_def: dict = {
                'name': col,
                'description': col.replace('_', ' ').title() + ' column',
            }
            if col == pk:
                col_def['tests'] = ['unique', 'not_null']
            elif col.lower().endswith('_id'):
                col_def['tests'] = ['not_null']
            columns.append(col_def)

        seeds.append({
            'name': table_name,
            'description': ds.description,
            'config': {
                'quote_columns': False,
                'column_types': {col: 'varchar' for col in ds.columns},
            },
            'columns': columns,
        })

    return yaml.dump(
        {'version': 2, 'seeds': seeds},
        default_flow_style=False, sort_keys=False,
    )


def _staging_schema(scenario: DemoScenario) -> str:
    """Generate schema for staging models."""
    models = []
    for model in scenario.staging_models:
        source_data = next((s for s in scenario.data_sources if s.name == model.source_table), None)
        columns = []
        if source_data:
            pk = identify_primary_key(source_data.columns, source_data.name)
            for col in source_data.columns:
                col_def: dict = {'name': col, 'description': col.replace('_', ' ').title()}
                if col == pk:
                    col_def['tests'] = ['unique', 'not_null']
                columns.append(col_def)
        models.append({'name': model.name, 'description': model.description, 'columns': columns})

    return yaml.dump({'version': 2, 'models': models}, default_flow_style=False, sort_keys=False)


def _intermediate_schema(scenario: DemoScenario) -> str:
    """Generate schema for intermediate models (description only)."""
    models = [{'name': m.name, 'description': m.description} for m in scenario.intermediate_models]
    return yaml.dump({'version': 2, 'models': models}, default_flow_style=False, sort_keys=False)


def _marts_schema(scenario: DemoScenario) -> str:
    """Generate schema for marts models (description only)."""
    models = [{'name': m.name, 'description': m.description} for m in scenario.marts_models]
    return yaml.dump({'version': 2, 'models': models}, default_flow_style=False, sort_keys=False)
