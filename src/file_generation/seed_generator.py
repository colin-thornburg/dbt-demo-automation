"""
Seed CSV Generator
Creates realistic seed data with foreign key integrity.

Column names are sanitised to be Snowflake-safe (lowercase, underscores only).

CSV files are written as PLAIN TEXT without the Python csv module to
eliminate any quoting / encoding quirks that can confuse dbt's agate
type-inference on Snowflake.  Every value is guaranteed to be free of
commas, quotes, newlines, and other special characters.
"""

import re
import random
from typing import Dict, List, Any
from datetime import datetime, timedelta

from src.ai.scenario_generator import DemoScenario, DataSource
from src.naming import identify_primary_key, identify_foreign_keys


# ---------------------------------------------------------------------------
# Column-name sanitisation
# ---------------------------------------------------------------------------

def _sanitize_column_name(name: str) -> str:
    """
    Clean a column name so it is safe for Snowflake and dbt seeds.

    - Strip whitespace
    - Lowercase
    - Replace spaces / special chars with underscores
    - Collapse consecutive underscores
    - Remove leading/trailing underscores
    - Ensure it starts with a letter or underscore
    """
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_") or "col"
    if not re.match(r"^[a-z_]", name):
        name = f"col_{name}"
    return name


def _sanitize_columns(columns: List[str]) -> List[str]:
    """Sanitise a list of column names, deduplicating if needed."""
    seen: Dict[str, int] = {}
    result: List[str] = []
    for raw in columns:
        clean = _sanitize_column_name(raw)
        if clean in seen:
            seen[clean] += 1
            clean = f"{clean}_{seen[clean]}"
        else:
            seen[clean] = 0
        result.append(clean)
    return result


def _safe_value(val: Any) -> str:
    """
    Convert *val* to a string that is safe for un-quoted CSV.

    Strips commas, double-quotes, single-quotes, newlines, carriage-
    returns, and any other characters that could break CSV parsing or
    Snowflake seed loading.
    """
    s = str(val)
    # Remove characters that would require CSV quoting
    for ch in (',', '"', "'", '\n', '\r', '\t'):
        s = s.replace(ch, '')
    return s


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


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
    Generate a single seed CSV file with realistic data and correct FK integrity.

    The CSV is built as a plain string (no Python csv module) so there is
    zero chance of hidden quoting or encoding artefacts.

    Args:
        source: Data source definition
        num_rows: Number of rows to generate
        generated_ids: Dictionary of previously generated IDs for FK relationships
        scenario: Full scenario for context

    Returns:
        CSV content as string
    """
    # Sanitise column names so they're safe for Snowflake
    clean_columns = _sanitize_columns(source.columns)

    # Identify primary key and foreign keys using the CLEAN column names
    all_table_names = [s.name for s in scenario.data_sources]
    pk_column = identify_primary_key(clean_columns, source.name)
    fk_map = identify_foreign_keys(clean_columns, pk_column, all_table_names)

    # Track primary key values for this table
    pk_values = []

    # ── Build rows as lists of safe strings ──────────────────────────
    lines: List[str] = []

    # Header line (plain column names, comma-separated, no quoting)
    lines.append(",".join(clean_columns))

    for i in range(num_rows):
        row_values: List[str] = []
        for column in clean_columns:
            if column == pk_column:
                pk_val = i + 1
                pk_values.append(pk_val)
                row_values.append(str(pk_val))
            elif column in fk_map:
                ref_table = fk_map[column]
                ref_table_base = ref_table.split('.')[-1]
                if ref_table_base in generated_ids and generated_ids[ref_table_base]:
                    row_values.append(str(random.choice(generated_ids[ref_table_base])))
                else:
                    row_values.append(str(random.randint(1, min(num_rows, 20))))
            else:
                val = generate_column_value(
                    column_name=column,
                    table_name=source.name,
                    row_index=i,
                    generated_ids=generated_ids,
                    scenario=scenario
                )
                row_values.append(_safe_value(val))

        lines.append(",".join(row_values))

    # Store this table's PK values so downstream tables can reference them
    table_key = source.name.split('.')[-1]
    generated_ids[table_key] = pk_values

    return "\n".join(lines)


def generate_column_value(
    column_name: str,
    table_name: str,
    row_index: int,
    generated_ids: Dict[str, List[Any]],
    scenario: DemoScenario
) -> Any:
    """
    Generate a realistic value for a column based on its name and context.

    IMPORTANT: Every returned value MUST be free of commas, double-quotes,
    single-quotes, and newlines so it can be safely placed into an un-quoted
    CSV cell.

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

    # Generic _id columns that weren't caught as FK above — treat as FK fallback
    if col_lower.endswith('_id'):
        # Try to find a matching table in generated_ids
        entity = col_lower[:-3]  # remove '_id'
        for table_key, ids in generated_ids.items():
            table_base = table_key.lower()
            for prefix in ('raw_', 'src_', 'source_', 'stg_'):
                if table_base.startswith(prefix):
                    table_base = table_base[len(prefix):]
            singular = table_base.rstrip('s') if table_base.endswith('s') and len(table_base) > 2 else table_base
            if entity == table_base or entity == singular:
                return random.choice(ids) if ids else 1
        # No match found — return ID in safe range
        return random.randint(1, min(20, max(1, row_index + 1)))

    # Email addresses — only alphanumeric in the domain part (no dots or @-related issues)
    if 'email' in col_lower:
        safe_domain = re.sub(r"[^a-z0-9]", "", scenario.company_name.lower())
        return f"user{row_index}@{safe_domain}.com"

    # Names (first, last, full)
    if 'first_name' in col_lower or col_lower == 'firstname':
        return random.choice(['John', 'Jane', 'Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank',
                              'Grace', 'Henry', 'Iris', 'James', 'Karen', 'Leo', 'Maria', 'Nathan',
                              'Olivia', 'Peter', 'Quinn', 'Rosa'])
    if 'last_name' in col_lower or col_lower == 'lastname':
        return random.choice(['Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller',
                              'Wilson', 'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson', 'White',
                              'Harris', 'Martin', 'Garcia', 'Clark', 'Lewis', 'Hall'])
    # Generic name columns — but NOT compound names like company_name, plan_name, etc.
    if col_lower == 'name' or 'full_name' in col_lower:
        first = random.choice(['John', 'Jane', 'Alice', 'Bob', 'Charlie', 'Diana'])
        last = random.choice(['Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis'])
        # Use underscore instead of space to avoid any CSV ambiguity
        return f"{first}_{last}"
    # Compound _name columns (company_name, plan_name, provider_name, etc.)
    if '_name' in col_lower:
        prefix = col_lower.replace('_name', '').replace('_', '_')
        suffix = random.choice(['alpha', 'beta', 'gamma', 'delta', 'omega', 'prime', 'plus', 'pro'])
        return f"{prefix}_{suffix}"

    # Dates and timestamps
    if any(term in col_lower for term in ['date', 'created_at', 'updated_at', 'timestamp', '_at']):
        base_date = datetime.now() - timedelta(days=365)
        random_days = random.randint(0, 365)
        return (base_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

    # Status/State columns
    if 'status' in col_lower:
        return random.choice(['active', 'pending', 'completed', 'cancelled'])
    if col_lower == 'state' or col_lower == 'region':
        return random.choice(['CA', 'NY', 'TX', 'FL', 'WA', 'IL', 'PA', 'OH'])

    # Boolean columns — lowercase string literals
    if col_lower.startswith('is_') or col_lower.startswith('has_'):
        return random.choice(['true', 'false'])

    # Amount/Price/Revenue columns
    if any(term in col_lower for term in ['amount', 'price', 'revenue', 'total', 'cost', 'value',
                                           'salary', 'budget', 'spend', 'fee', 'rate']):
        return round(random.uniform(10.0, 1000.0), 2)

    # Percentage/Score columns
    if any(term in col_lower for term in ['percent', 'pct', 'ratio', 'score', 'rating']):
        return round(random.uniform(0.0, 100.0), 2)

    # Quantity/Count columns
    if any(term in col_lower for term in ['quantity', 'count', 'qty', 'number', 'num_']):
        return random.randint(1, 100)

    # Description/Notes columns — no spaces, use underscores
    if any(term in col_lower for term in ['description', 'notes', 'comment', 'reason', 'details']):
        return f"sample_{column_name}_record_{row_index + 1}"

    # Category/Type columns — underscore-delimited
    if any(term in col_lower for term in ['category', 'type', 'class', 'tier', 'level', 'segment',
                                           'channel', 'source', 'medium', 'group']):
        return random.choice(['type_a', 'type_b', 'type_c', 'type_d'])

    # Country/City columns — no spaces
    if 'country' in col_lower:
        return random.choice(['US', 'UK', 'CA', 'DE', 'FR', 'AU', 'JP'])
    if 'city' in col_lower:
        return random.choice(['new_york', 'los_angeles', 'chicago', 'houston', 'phoenix', 'seattle'])

    # Phone columns — digits only (no dashes)
    if 'phone' in col_lower:
        return f"555{random.randint(1000000, 9999999)}"

    # URL columns
    if 'url' in col_lower or 'link' in col_lower or 'website' in col_lower:
        return f"https://example.com/{column_name}/{row_index}"

    # Year / vintage columns — plain integer year
    if 'year' in col_lower or 'vintage' in col_lower:
        return random.randint(2015, 2025)

    # Default: descriptive string value (underscores only)
    return f"{column_name}_{row_index + 1}"
