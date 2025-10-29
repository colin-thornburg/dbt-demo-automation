"""
File Generation Orchestrator
Coordinates the generation of all dbt project files
"""

from typing import Dict, Optional
from src.ai.scenario_generator import DemoScenario
from .seed_generator import generate_seed_csvs
from .model_generator import generate_dbt_models
from .schema_generator import generate_schema_yml
from .project_generator import generate_dbt_project_yml
from .semantic_layer_generator import generate_semantic_models, generate_metrics_yml


class GeneratedFiles:
    """Container for all generated files"""

    def __init__(self):
        self.seeds: Dict[str, str] = {}
        self.models: Dict[str, str] = {}
        self.schemas: Dict[str, str] = {}
        self.semantic_models: Dict[str, str] = {}
        self.metrics_yml: str = ""
        self.project_yml: str = ""
        self.readme: str = ""

    def all_files(self) -> Dict[str, str]:
        """
        Get all files as a flat dictionary

        Returns:
            Dictionary mapping filepath to content
        """
        all_files = {}

        # Add seeds (in seeds/ directory)
        for filename, content in self.seeds.items():
            all_files[f"seeds/{filename}"] = content

        # Add models (already have full paths)
        all_files.update(self.models)

        # Add schemas (already have full paths)
        all_files.update(self.schemas)

        # Add semantic models (already have full paths)
        all_files.update(self.semantic_models)

        # Add metrics.yml
        if self.metrics_yml:
            all_files["models/metrics/metrics.yml"] = self.metrics_yml

        # Add project config
        if self.project_yml:
            all_files["dbt_project.yml"] = self.project_yml

        # Add README
        if self.readme:
            all_files["README.md"] = self.readme

        return all_files

    def get_summary(self) -> Dict[str, int]:
        """
        Get a summary of generated files

        Returns:
            Dictionary with counts of each file type
        """
        semantic_count = len(self.semantic_models) + (1 if self.metrics_yml else 0)
        return {
            "seeds": len(self.seeds),
            "models": len(self.models),
            "schemas": len(self.schemas),
            "semantic_layer": semantic_count,
            "config_files": 2 if self.project_yml and self.readme else 0,
            "total": len(self.all_files())
        }


def generate_all_files(
    scenario: DemoScenario,
    num_seed_rows: int = 20,
    dbt_cloud_project_id: Optional[str] = None,
    include_semantic_layer: bool = False
) -> GeneratedFiles:
    """
    Generate all dbt project files from a scenario

    Args:
        scenario: The demo scenario
        num_seed_rows: Number of rows to generate in seed files
        dbt_cloud_project_id: Optional dbt Cloud project ID for CLI integration
        include_semantic_layer: Whether to generate semantic layer files

    Returns:
        GeneratedFiles object containing all generated content
    """
    generated = GeneratedFiles()

    # Generate seed CSV files
    generated.seeds = generate_seed_csvs(scenario, num_rows=num_seed_rows)

    # Generate dbt model SQL files
    generated.models = generate_dbt_models(scenario)

    # Generate schema.yml files
    generated.schemas = generate_schema_yml(scenario)

    # Generate semantic layer files if requested
    if include_semantic_layer:
        generated.semantic_models = generate_semantic_models(scenario)
        generated.metrics_yml = generate_metrics_yml(scenario)

    # Generate dbt_project.yml
    generated.project_yml = generate_dbt_project_yml(
        scenario,
        dbt_cloud_project_id=dbt_cloud_project_id
    )

    # Generate README
    generated.readme = generate_readme(scenario)

    return generated


def generate_readme(scenario: DemoScenario) -> str:
    """
    Generate a README.md for the demo project

    Args:
        scenario: The demo scenario

    Returns:
        README content as markdown
    """
    project_name = scenario.company_name

    readme = f"""# {project_name} dbt Demo Project

## Overview

{scenario.demo_overview}

## Business Context

{scenario.business_context}

## Data Architecture

### Data Sources

"""

    # Add data sources
    for source in scenario.data_sources:
        readme += f"- **{source.name}**: {source.description}\n"

    readme += "\n### dbt Models\n\n"
    readme += "#### Staging Layer\n\n"
    for model in scenario.staging_models:
        readme += f"- **{model.name}**: {model.description}\n"

    readme += "\n#### Intermediate Layer\n\n"
    for model in scenario.intermediate_models:
        readme += f"- **{model.name}**: {model.description}\n"

    readme += "\n#### Marts Layer\n\n"
    for model in scenario.marts_models:
        incr_note = " (Incremental)" if model.is_incremental else ""
        readme += f"- **{model.name}**{incr_note}: {model.description}\n"

    readme += "\n## Key Metrics\n\n"
    for metric in scenario.key_metrics:
        readme += f"- **{metric.name}**: {metric.description}\n"
        readme += f"  - Calculation: `{metric.calculation}`\n"

    readme += "\n## Demo Talking Points\n\n"
    for i, point in enumerate(scenario.talking_points, 1):
        readme += f"{i}. {point}\n"

    readme += f"""

## Getting Started

### Prerequisites

- dbt Cloud account or dbt Core installed
- {scenario.industry} data warehouse (configured in your profile)

### Setup

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

### Project Structure

```
{project_name.lower().replace(' ', '_')}/
├── models/
│   ├── staging/       # Cleaned and renamed source data
│   ├── intermediate/  # Business logic transformations
│   └── marts/         # Analytics-ready tables
├── seeds/             # Sample data
├── tests/             # Custom data tests
└── dbt_project.yml    # Project configuration
```

## Demo Flow

1. **Show the DAG**: Demonstrate data lineage in dbt Cloud
2. **Review staging models**: Explain source data cleaning
3. **Walk through transformations**: Show intermediate logic
4. **Highlight marts**: Focus on final business-ready tables
5. **Run dbt**: Show build process and testing
6. **Explore results**: Query final tables in warehouse

---

**Generated with dbt Cloud Demo Automation Tool**
"""

    return readme
