"""
Semantic Layer Generator
Generates semantic model and metrics YAML files for dbt Semantic Layer
"""

from typing import Dict, List
from src.ai.scenario_generator import DemoScenario, MartModel, Metric


def generate_semantic_models(scenario: DemoScenario) -> Dict[str, str]:
    """
    Generate semantic model YAML files for marts

    Args:
        scenario: The demo scenario

    Returns:
        Dictionary mapping filepath to YAML content
    """
    semantic_files = {}

    # Generate one semantic model per mart model
    for mart in scenario.marts_models:
        semantic_yaml = generate_semantic_model_for_mart(mart, scenario)
        # Store in models/metrics/ directory
        filename = f"models/metrics/{mart.name}_semantic.yml"
        semantic_files[filename] = semantic_yaml

    return semantic_files


def generate_semantic_model_for_mart(mart: MartModel, scenario: DemoScenario) -> str:
    """
    Generate a semantic model YAML for a specific mart model

    Args:
        mart: The mart model to create semantic model for
        scenario: The demo scenario for context

    Returns:
        YAML content as string
    """
    # Infer entity from mart name (typically ends with "s" like orders, customers)
    entity_name = mart.name.replace('fct_', '').replace('dim_', '').rstrip('s')
    if not entity_name:
        entity_name = 'record'

    # Create semantic model YAML
    yaml_content = f"""# Semantic model for {mart.name}
# Generated for dbt Semantic Layer

semantic_models:
  - name: {mart.name}_semantic
    description: |
      {mart.description}
    model: ref('{mart.name}')
    defaults:
      agg_time_dimension: created_at

    # Entities are the join keys
    entities:
      - name: {entity_name}_id
        type: primary
        expr: {entity_name}_id
"""

    # Add foreign key entities if this mart depends on other models
    if mart.depends_on:
        for dep in mart.depends_on[:2]:  # Limit to 2 foreign keys
            fk_entity = dep.replace('stg_', '').replace('int_', '').rstrip('s')
            if fk_entity != entity_name:
                yaml_content += f"""      - name: {fk_entity}_id
        type: foreign
        expr: {fk_entity}_id
"""

    # Add time dimension
    yaml_content += """
    # Dimensions are attributes for grouping and filtering
    dimensions:
      - name: created_at
        type: time
        type_params:
          time_granularity: day
      - name: status
        type: categorical
"""

    # Add measures based on common patterns
    yaml_content += """
    # Measures are aggregations
    measures:
      - name: total_amount
        description: "Sum of transaction amounts"
        agg: sum
        expr: amount

      - name: record_count
        description: "Count of records"
        agg: count_distinct
        expr: """ + f"{entity_name}_id" + """

      - name: avg_amount
        description: "Average transaction amount"
        agg: average
        expr: amount
"""

    return yaml_content


def generate_metrics_yml(scenario: DemoScenario) -> str:
    """
    Generate metrics.yml file with metrics defined from semantic models

    Args:
        scenario: The demo scenario containing key metrics

    Returns:
        YAML content as string
    """
    yaml_content = """# Metrics for dbt Semantic Layer
# Generated from demo scenario

metrics:
"""

    # Generate metrics from the scenario's key_metrics
    for i, metric in enumerate(scenario.key_metrics):
        metric_name = metric.name.lower().replace(' ', '_').replace('-', '_')

        # Determine metric type based on calculation
        metric_type = "simple"
        type_params = ""

        if '/' in metric.calculation or 'ratio' in metric.calculation.lower():
            metric_type = "ratio"
            # For ratio metrics, we need numerator and denominator
            type_params = """    type_params:
      numerator:
        name: total_amount
      denominator:
        name: record_count
"""
        elif 'sum' in metric.calculation.lower() or 'total' in metric.calculation.lower():
            metric_type = "simple"
            type_params = """    type_params:
      measure:
        name: total_amount
"""
        elif 'count' in metric.calculation.lower():
            metric_type = "simple"
            type_params = """    type_params:
      measure:
        name: record_count
"""
        elif 'average' in metric.calculation.lower() or 'avg' in metric.calculation.lower():
            metric_type = "simple"
            type_params = """    type_params:
      measure:
        name: avg_amount
"""
        else:
            # Default to simple with total_amount
            type_params = """    type_params:
      measure:
        name: total_amount
"""

        yaml_content += f"""  - name: {metric_name}
    description: "{metric.description}"
    type: {metric_type}
    label: "{metric.name}"
{type_params}
"""

    # Add some standard derived metrics
    yaml_content += """  - name: average_transaction_value
    description: "Average value per transaction"
    type: ratio
    label: "Average Transaction Value"
    type_params:
      numerator:
        name: total_amount
      denominator:
        name: record_count

  - name: transaction_growth_rate
    description: "Period over period growth rate"
    type: derived
    label: "Transaction Growth Rate"
    type_params:
      expr: (current_period_total - prior_period_total) / prior_period_total
      metrics:
        - name: total_amount
          alias: current_period_total
        - name: total_amount
          alias: prior_period_total
          offset_window: 1 month
"""

    return yaml_content
