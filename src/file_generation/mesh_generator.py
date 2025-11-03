"""
dbt Mesh Generator
Creates producer and consumer projects for dbt Mesh demos
"""

import yaml
from typing import Dict, List, Optional
from src.ai.scenario_generator import DemoScenario
from .project_generator import generate_dbt_project_yml
from .schema_generator import generate_schema_yml
from .model_generator import generate_dbt_models
from .seed_generator import generate_seed_csvs


def generate_producer_project(
    scenario: DemoScenario,
    dbt_cloud_project_id: Optional[str] = None,
    include_semantic_layer: bool = False
) -> Dict[str, str]:
    """
    Generate a producer project with public models and contracts
    
    Args:
        scenario: The demo scenario
        dbt_cloud_project_id: Optional dbt Cloud project ID
        include_semantic_layer: Whether to include semantic layer
        
    Returns:
        Dictionary mapping filepath to content for producer project
    """
    from .orchestrator import generate_all_files
    
    # Generate base files
    generated = generate_all_files(
        scenario,
        num_seed_rows=20,
        dbt_cloud_project_id=dbt_cloud_project_id,
        include_semantic_layer=include_semantic_layer
    )
    
    # Get project name
    project_name = scenario.company_name.lower().replace(' ', '_').replace('-', '_')
    if not project_name[0].isalpha():
        project_name = 'demo_' + project_name
    
    # Update schema files to mark marts models as public with contracts
    updated_schemas = _add_public_access_and_contracts(
        generated.schemas,
        scenario,
        project_name
    )
    
    # Combine all files
    all_files = {}
    
    # Add seeds
    for filename, content in generated.seeds.items():
        all_files[f"seeds/{filename}"] = content
    
    # Add models
    all_files.update(generated.models)
    
    # Add updated schemas with public access
    all_files.update(updated_schemas)
    
    # Add semantic layer if requested
    if include_semantic_layer:
        all_files.update(generated.semantic_models)
        if generated.metrics_yml:
            all_files["models/metrics/metrics.yml"] = generated.metrics_yml
    
    # Add project config
    all_files["dbt_project.yml"] = generated.project_yml
    
    # Add README
    all_files["README.md"] = _generate_producer_readme(scenario, project_name)
    
    return all_files


def generate_consumer_project(
    producer_scenario: DemoScenario,
    consumer_index: int,
    producer_project_name: str,
    dbt_cloud_project_id: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate a consumer project that references the producer project
    
    Args:
        producer_scenario: The producer scenario (for context)
        consumer_index: Index of this consumer (1, 2, or 3)
        producer_project_name: Name of the producer project
        dbt_cloud_project_id: Optional dbt Cloud project ID
        
    Returns:
        Dictionary mapping filepath to content for consumer project
    """
    # Create consumer project name
    consumer_project_name = f"{producer_project_name}_consumer_{consumer_index}"
    
    # Generate simple seed data for consumer
    consumer_seeds = _generate_consumer_seeds(consumer_index)
    
    # Generate consumer models that reference producer
    consumer_models = _generate_consumer_models(
        producer_scenario,
        producer_project_name,
        consumer_index
    )
    
    # Generate schema files
    consumer_schemas = _generate_consumer_schemas(consumer_index)
    
    # Generate dependencies.yml
    dependencies_yml = _generate_dependencies_yml(producer_project_name)
    
    # Generate dbt_project.yml
    project_yml = _generate_consumer_project_yml(
        consumer_project_name,
        dbt_cloud_project_id
    )
    
    # Generate README
    readme = _generate_consumer_readme(
        producer_scenario,
        consumer_project_name,
        producer_project_name,
        consumer_index
    )
    
    # Combine all files
    all_files = {}
    
    # Add seeds
    for filename, content in consumer_seeds.items():
        all_files[f"seeds/{filename}"] = content
    
    # Add models
    all_files.update(consumer_models)
    
    # Add schemas
    all_files.update(consumer_schemas)
    
    # Add dependencies.yml
    all_files["dependencies.yml"] = dependencies_yml
    
    # Add project config
    all_files["dbt_project.yml"] = project_yml
    
    # Add README
    all_files["README.md"] = readme
    
    return all_files


def _add_public_access_and_contracts(
    schemas: Dict[str, str],
    scenario: DemoScenario,
    project_name: str
) -> Dict[str, str]:
    """
    Update schema files to add public access and contracts to marts models
    """
    import yaml
    
    updated_schemas = {}
    
    # Find the marts schema file
    marts_schema_path = 'models/marts/schema.yml'
    
    if marts_schema_path in schemas:
        # Parse the YAML
        schema_dict = yaml.safe_load(schemas[marts_schema_path])
        
        # Update each marts model to be public with contract
        if 'models' in schema_dict:
            for model in schema_dict['models']:
                # Mark as public
                model['access'] = 'public'
                
                # Add contract (required for cross-project refs)
                if 'columns' in model and len(model['columns']) > 0:
                    # Ensure contract is enabled
                    model['contract'] = {
                        'enforced': True
                    }
                    # Mark columns as required (contract requirement)
                    for col in model['columns']:
                        if 'tests' not in col:
                            col['tests'] = []
                        if 'not_null' not in col['tests']:
                            col['tests'].append('not_null')
        
        # Dump back to YAML
        updated_schemas[marts_schema_path] = yaml.dump(
            schema_dict,
            default_flow_style=False,
            sort_keys=False
        )
    
    # Copy other schema files as-is
    for path, content in schemas.items():
        if path != marts_schema_path:
            updated_schemas[path] = content
    
    return updated_schemas


def _generate_consumer_seeds(consumer_index: int) -> Dict[str, str]:
    """Generate simple seed data for consumer project"""
    seeds = {}
    
    # Generate a simple reference/lookup table
    if consumer_index == 1:
        # Consumer 1: Marketing channels
        seeds['marketing_channels.csv'] = """channel_id,channel_name,budget
1,Email,50000
2,Social Media,30000
3,Paid Search,40000
4,Display Ads,25000
"""
    elif consumer_index == 2:
        # Consumer 2: Regions
        seeds['regions.csv'] = """region_id,region_name,country
1,North America,USA
2,Europe,UK
3,Asia Pacific,Japan
4,Latin America,Brazil
"""
    else:  # consumer_index == 3
        # Consumer 3: Product categories
        seeds['product_categories.csv'] = """category_id,category_name,department
1,Electronics,Technology
2,Clothing,Retail
3,Food & Beverage,Grocery
4,Home & Garden,Retail
"""
    
    return seeds


def _generate_consumer_models(
    producer_scenario: DemoScenario,
    producer_project_name: str,
    consumer_index: int
) -> Dict[str, str]:
    """Generate consumer models that reference producer models"""
    models = {}
    
    # Pick a marts model from producer to reference
    producer_marts_model = producer_scenario.marts_models[0].name if producer_scenario.marts_models else 'monthly_revenue'
    
    # Generate a simple model that combines seed data with producer model
    if consumer_index == 1:
        # Consumer 1: Marketing ROI analysis
        model_name = 'marketing_roi_by_channel'
        model_sql = f"""{{{{ config(materialized='table') }}}}

/*
    Marketing ROI analysis combining channel budgets with revenue data
    Demonstrates cross-project reference to {producer_project_name}
*/

with producer_revenue as (
    select * from {{{{ ref('{producer_project_name}', '{producer_marts_model}') }}}}
),

channels as (
    select * from {{{{ ref('marketing_channels') }}}}
),

combined as (
    select
        c.channel_name,
        c.budget,
        coalesce(sum(r.revenue), 0) as total_revenue,
        coalesce(sum(r.revenue), 0) - c.budget as roi
    from channels c
    left join producer_revenue r on 1=1  -- Simplified join for demo
    group by c.channel_id, c.channel_name, c.budget
)

select * from combined
"""
    elif consumer_index == 2:
        # Consumer 2: Regional analysis
        model_name = 'regional_performance'
        model_sql = f"""{{{{ config(materialized='table') }}}}

/*
    Regional performance analysis combining region data with revenue
    Demonstrates cross-project reference to {producer_project_name}
*/

with producer_revenue as (
    select * from {{{{ ref('{producer_project_name}', '{producer_marts_model}') }}}}
),

regions as (
    select * from {{{{ ref('regions') }}}}
),

combined as (
    select
        r.region_name,
        r.country,
        coalesce(sum(pr.revenue), 0) as total_revenue
    from regions r
    left join producer_revenue pr on 1=1  -- Simplified join for demo
    group by r.region_id, r.region_name, r.country
)

select * from combined
"""
    else:  # consumer_index == 3
        # Consumer 3: Category analysis
        model_name = 'category_analysis'
        model_sql = f"""{{{{ config(materialized='table') }}}}

/*
    Product category analysis combining category data with revenue
    Demonstrates cross-project reference to {producer_project_name}
*/

with producer_revenue as (
    select * from {{{{ ref('{producer_project_name}', '{producer_marts_model}') }}}}
),

categories as (
    select * from {{{{ ref('product_categories') }}}}
),

combined as (
    select
        c.category_name,
        c.department,
        coalesce(sum(pr.revenue), 0) as total_revenue
    from categories c
    left join producer_revenue pr on 1=1  -- Simplified join for demo
    group by c.category_id, c.category_name, c.department
)

select * from combined
"""
    
    models[f"models/marts/{model_name}.sql"] = model_sql
    
    return models


def _generate_consumer_schemas(consumer_index: int) -> Dict[str, str]:
    """Generate schema files for consumer project"""
    schemas = {}
    
    if consumer_index == 1:
        model_name = 'marketing_roi_by_channel'
        columns = [
            {'name': 'channel_name', 'description': 'Marketing channel name'},
            {'name': 'budget', 'description': 'Channel budget'},
            {'name': 'total_revenue', 'description': 'Total revenue attributed to channel'},
            {'name': 'roi', 'description': 'Return on investment'}
        ]
    elif consumer_index == 2:
        model_name = 'regional_performance'
        columns = [
            {'name': 'region_name', 'description': 'Region name'},
            {'name': 'country', 'description': 'Country'},
            {'name': 'total_revenue', 'description': 'Total revenue for region'}
        ]
    else:  # consumer_index == 3
        model_name = 'category_analysis'
        columns = [
            {'name': 'category_name', 'description': 'Product category name'},
            {'name': 'department', 'description': 'Department'},
            {'name': 'total_revenue', 'description': 'Total revenue for category'}
        ]
    
    schema_dict = {
        'version': 2,
        'models': [{
            'name': model_name,
            'description': f'Consumer model demonstrating cross-project reference',
            'columns': columns
        }]
    }
    
    schemas['models/marts/schema.yml'] = yaml.dump(
        schema_dict,
        default_flow_style=False,
        sort_keys=False
    )
    
    return schemas


def _generate_dependencies_yml(producer_project_name: str) -> str:
    """Generate dependencies.yml with project dependency"""
    dependencies_dict = {
        'projects': [
            {
                'name': producer_project_name
            }
        ]
    }
    
    return yaml.dump(dependencies_dict, default_flow_style=False, sort_keys=False)


def _generate_consumer_project_yml(
    consumer_project_name: str,
    dbt_cloud_project_id: Optional[str] = None
) -> str:
    """Generate dbt_project.yml for consumer project"""
    project_dict = {
        'name': consumer_project_name,
        'version': '1.0.0',
        'config-version': 2,
        'profile': consumer_project_name,
        
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
            consumer_project_name: {
                'marts': {
                    '+materialized': 'table',
                    '+tags': ['marts']
                }
            }
        },
        
        'seeds': {
            consumer_project_name: {
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


def _generate_producer_readme(scenario: DemoScenario, project_name: str) -> str:
    """Generate README for producer project"""
    return f"""# {scenario.company_name} dbt Producer Project

## Overview

This is the **producer** project in a dbt Mesh demo. It contains public models with contracts that are referenced by downstream consumer projects.

## Public Models

The following marts models are marked as `public` and can be referenced by other projects:

{chr(10).join([f"- `{model.name}`: {model.description}" for model in scenario.marts_models[:3]])}

## Model Contracts

All public models have contracts enforced to ensure stable interfaces for downstream consumers.

## Getting Started

1. Install dependencies:
   ```bash
   dbt deps
   ```

2. Load seed data:
   ```bash
   dbt seed
   ```

3. Run models:
   ```bash
   dbt run
   ```

4. Test models:
   ```bash
   dbt test
   ```

## Cross-Project References

Downstream projects can reference public models using:
```sql
select * from {{{{ ref('{project_name}', 'model_name') }}}}
```

---

**Generated with dbt Cloud Demo Automation Tool**
"""


def _generate_consumer_readme(
    producer_scenario: DemoScenario,
    consumer_project_name: str,
    producer_project_name: str,
    consumer_index: int
) -> str:
    """Generate README for consumer project"""
    return f"""# {consumer_project_name.replace('_', ' ').title()} - Consumer Project

## Overview

This is a **consumer** project that demonstrates dbt Mesh cross-project references. It references public models from the `{producer_project_name}` producer project.

## Project Dependencies

This project depends on:
- **{producer_project_name}**: Producer project with public models

See `dependencies.yml` for configuration.

## Cross-Project References

This project uses cross-project `ref()` syntax:
```sql
select * from {{{{ ref('{producer_project_name}', 'model_name') }}}}
```

## Models

The models in this project combine local seed data with public models from the producer project to demonstrate cross-project data integration.

## Getting Started

1. Install dependencies:
   ```bash
   dbt deps
   ```
   This will resolve the project dependency on `{producer_project_name}`.

2. Load seed data:
   ```bash
   dbt seed
   ```

3. Run models:
   ```bash
   dbt run
   ```

## Requirements

The producer project (`{producer_project_name}`) must:
- Have public models defined
- Have model contracts enabled
- Be deployed to a production environment in dbt Cloud

---

**Generated with dbt Cloud Demo Automation Tool**
"""

