"""
Seed CSV Generator
Creates realistic seed data with foreign key integrity
"""

import csv
import random
from typing import Dict, List, Any
from io import StringIO
from datetime import datetime, timedelta

from src.ai.scenario_generator import DemoScenario, DataSource


def generate_seed_csvs(scenario: DemoScenario, num_rows: int = 20) -> Dict[str, str]:
    """
    Generate seed CSV files for all data sources in the scenario

    Args:
        scenario: The demo scenario with data sources
        num_rows: Number of rows to generate per seed file (default: 20)

    Returns:
        Dictionary mapping filename to CSV content
    """
    seed_files = {}
    generated_ids = {}  # Track generated IDs for FK relationships

    # Generate CSVs in order to maintain FK integrity
    for source in scenario.data_sources:
        csv_content = generate_single_seed_csv(
            source=source,
            num_rows=num_rows,
            generated_ids=generated_ids,
            scenario=scenario
        )

        # Filename: source name without schema prefix
        filename = f"{source.name.split('.')[-1]}.csv"
        seed_files[filename] = csv_content

    return seed_files


def generate_single_seed_csv(
    source: DataSource,
    num_rows: int,
    generated_ids: Dict[str, List[Any]],
    scenario: DemoScenario
) -> str:
    """
    Generate a single seed CSV file with realistic data

    Args:
        source: Data source definition
        num_rows: Number of rows to generate
        generated_ids: Dictionary of previously generated IDs for FK relationships
        scenario: Full scenario for context

    Returns:
        CSV content as string
    """
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=source.columns)
    writer.writeheader()

    # Track IDs from this table
    table_ids = []

    for i in range(num_rows):
        row = {}
        for column in source.columns:
            row[column] = generate_column_value(
                column_name=column,
                table_name=source.name,
                row_index=i,
                generated_ids=generated_ids,
                scenario=scenario
            )

        # Track ID column values
        if 'id' in column.lower() and not any(fk in column.lower() for fk in ['_id', 'fk_']):
            table_ids.append(row[column])

        writer.writerow(row)

    # Store generated IDs for this table
    if table_ids:
        table_key = source.name.split('.')[-1]
        generated_ids[table_key] = table_ids

    # Remove trailing newline so dbt seed tests don't treat it as an empty row
    return output.getvalue().rstrip('\r\n')


def generate_column_value(
    column_name: str,
    table_name: str,
    row_index: int,
    generated_ids: Dict[str, List[Any]],
    scenario: DemoScenario
) -> Any:
    """
    Generate a realistic value for a column based on its name and context

    Args:
        column_name: Name of the column
        table_name: Name of the table
        row_index: Current row index
        generated_ids: Previously generated IDs
        scenario: Demo scenario for context

    Returns:
        Generated value for the column
    """
    col_lower = column_name.lower()

    # Primary ID columns
    if col_lower == 'id' or col_lower.endswith('_id') and not any(
        ref in col_lower for ref in ['user', 'customer', 'product', 'order', 'account']
    ):
        return row_index + 1

    # Foreign key columns (look for referenced table IDs)
    if '_id' in col_lower or col_lower.startswith('fk_'):
        # Try to find matching table
        for table_key, ids in generated_ids.items():
            if table_key.lower() in col_lower.lower():
                return random.choice(ids) if ids else 1
        # Fallback: random ID between 1-50
        return random.randint(1, 50)

    # Email addresses
    if 'email' in col_lower:
        return f"user{row_index}@{scenario.company_name.lower().replace(' ', '')}.com"

    # Names (first, last, full)
    if 'first_name' in col_lower or col_lower == 'firstname':
        return random.choice(['John', 'Jane', 'Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank'])
    if 'last_name' in col_lower or col_lower == 'lastname':
        return random.choice(['Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson'])
    if col_lower == 'name' or 'full_name' in col_lower:
        first = random.choice(['John', 'Jane', 'Alice', 'Bob'])
        last = random.choice(['Smith', 'Johnson', 'Williams', 'Jones'])
        return f"{first} {last}"

    # Dates
    if 'date' in col_lower or col_lower in ['created_at', 'updated_at', 'timestamp']:
        base_date = datetime.now() - timedelta(days=365)
        random_days = random.randint(0, 365)
        return (base_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

    # Status/State columns
    if 'status' in col_lower:
        return random.choice(['active', 'pending', 'completed', 'cancelled'])
    if 'state' in col_lower:
        return random.choice(['CA', 'NY', 'TX', 'FL', 'WA', 'IL'])

    # Boolean columns
    if col_lower.startswith('is_') or col_lower.startswith('has_'):
        return random.choice([True, False])

    # Amount/Price/Revenue columns
    if any(term in col_lower for term in ['amount', 'price', 'revenue', 'total', 'cost']):
        return round(random.uniform(10.0, 1000.0), 2)

    # Quantity/Count columns
    if any(term in col_lower for term in ['quantity', 'count', 'qty', 'number']):
        return random.randint(1, 100)

    # Description/Notes columns
    if any(term in col_lower for term in ['description', 'notes', 'comment']):
        return f"Sample {column_name} for row {row_index}"

    # Category/Type columns
    if any(term in col_lower for term in ['category', 'type', 'class']):
        return random.choice(['Type A', 'Type B', 'Type C', 'Type D'])

    # Default: string value
    return f"{column_name}_{row_index}"
