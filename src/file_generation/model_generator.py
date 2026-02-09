"""
dbt Model Generator
Creates SQL files for staging, intermediate, and marts models.

IMPORTANT: Joined models use explicit column lists (not SELECT *)
to avoid duplicate column names (e.g. both tables having 'id').

JOIN DIRECTION:
  - Forward FK:  base table has a FK to the join table
                 e.g. orders.customer_id → customers.id
                 ON orders.customer_id = customers.id
  - Reverse FK:  join table has a FK to the base (or any prior table)
                 e.g. claim_lines.claim_id → claims.id
                 ON claims.id = claim_lines.claim_id
"""

from typing import Dict, List, Optional, Tuple
from src.ai.scenario_generator import DemoScenario


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_model_columns(model_name: str, scenario: DemoScenario) -> List[str]:
    """
    Resolve the output columns for a model by tracing back to source data.

    Works for staging models (via their source table) and makes a best-effort
    attempt for intermediate models (union of dependency columns).
    Returns an empty list if columns can't be resolved.
    """
    # Staging model → source columns
    stg = next((s for s in scenario.staging_models if s.name == model_name), None)
    if stg:
        source = next(
            (s for s in scenario.data_sources if s.name == stg.source_table), None
        )
        if source:
            return list(source.columns)

    # Intermediate model → union of dependency columns (minus duplicates)
    intm = next((m for m in scenario.intermediate_models if m.name == model_name), None)
    if intm:
        seen: set = set()
        cols: List[str] = []
        for dep in intm.depends_on:
            for c in _get_model_columns(dep, scenario):
                if c.lower() not in seen:
                    seen.add(c.lower())
                    cols.append(c)
        return cols

    return []


def _entity_name(model_name: str) -> str:
    """
    Derive the singular entity name from a model name.

    stg_claim_lines → claim_line
    int_orders → order
    stg_raw_claims → raw_claim
    """
    base = model_name.replace("stg_", "").replace("int_", "").replace("fct_", "").replace("dim_", "")
    # Strip trailing 's' only if the word isn't too short (avoid stripping e.g. 'us')
    if base.endswith("s") and len(base) > 3:
        base = base[:-1]
    return base


def _find_join_columns(
    base_dep: str,
    join_dep: str,
    scenario: DemoScenario,
) -> Tuple[str, str]:
    """
    Determine the (base_column, join_column) pair for joining two models.

    Returns:
        (base_col, join_col) so the ON clause is:
            ON base_alias.base_col = join_alias.join_col
    """
    base_cols = [c.lower() for c in _get_model_columns(base_dep, scenario)]
    join_cols = [c.lower() for c in _get_model_columns(join_dep, scenario)]

    join_entity = _entity_name(join_dep)
    base_entity = _entity_name(base_dep)

    # ── Strategy 1: base has FK to join entity ──
    # e.g. orders has customer_id → join customers on orders.customer_id = customers.id
    fk_in_base = f"{join_entity}_id"
    if fk_in_base in base_cols:
        return (fk_in_base, "id")

    # ── Strategy 2: join has FK to base entity ──
    # e.g. claim_lines has claim_id → join on claims.id = claim_lines.claim_id
    fk_in_join = f"{base_entity}_id"
    if fk_in_join in join_cols:
        return ("id", fk_in_join)

    # ── Strategy 3: shared _id column (same name on both sides) ──
    base_id_cols = {c for c in base_cols if c.endswith("_id")}
    join_id_cols = {c for c in join_cols if c.endswith("_id")}
    shared = base_id_cols & join_id_cols
    if shared:
        col = sorted(shared)[0]
        return (col, col)

    # ── Strategy 4: both have 'id' ──
    if "id" in base_cols and "id" in join_cols:
        return ("id", "id")

    return ("id", "id")


def _build_join_select(
    base_alias: str,
    base_dep: str,
    join_aliases: List[str],
    join_deps: List[str],
    scenario: DemoScenario,
) -> str:
    """
    Build an explicit SELECT clause for a model with joins, avoiding
    duplicate column names.

    - All columns from the *base* table are included.
    - For each joined table, only columns that don't already appear are included.
    """
    base_columns = _get_model_columns(base_dep, scenario)

    if not base_columns:
        # Can't resolve columns — safe fallback: only base columns
        return f"{base_alias}.*"

    selected: set = {c.lower() for c in base_columns}
    parts: List[str] = [f"{base_alias}.*"]

    for j_alias, j_dep in zip(join_aliases, join_deps):
        j_columns = _get_model_columns(j_dep, scenario)
        if not j_columns:
            continue
        new_cols = [c for c in j_columns if c.lower() not in selected]
        for c in new_cols:
            parts.append(f"{j_alias}.{c}")
            selected.add(c.lower())

    return ",\n        ".join(parts)


def _build_join_clauses(
    base_alias: str,
    base_dep: str,
    join_aliases: List[str],
    join_deps: List[str],
    scenario: DemoScenario,
) -> str:
    """
    Build LEFT JOIN clauses with correct FK→PK relationships.

    Supports both directions:
      - Forward:  available_table.entity_id = join_table.id
      - Reverse:  available_table.id = join_table.entity_id

    Also supports transitive joins through previously joined tables.
    """
    clauses: List[str] = []

    # Track all available tables and their columns for transitive lookups.
    # Entries: (alias, dep_name, columns_lower)
    available_tables: List[tuple] = [
        (base_alias, base_dep, [c.lower() for c in _get_model_columns(base_dep, scenario)])
    ]

    for j_alias, j_dep in zip(join_aliases, join_deps):
        j_cols_lower = [c.lower() for c in _get_model_columns(j_dep, scenario)]
        join_entity = _entity_name(j_dep)
        matched = False

        # ── Forward FK: does any available table have a FK to this join table? ──
        # e.g. available 'orders' has 'customer_id' → join customers on orders.customer_id = customers.id
        fk_col = f"{join_entity}_id"
        for avail_alias, avail_dep, avail_cols in available_tables:
            if fk_col in avail_cols:
                clauses.append(
                    f"left join {j_alias}\n"
                    f"        on {avail_alias}.{fk_col} = {j_alias}.id"
                )
                matched = True
                break

        # ── Reverse FK: does the join table have a FK to any available table? ──
        # e.g. join 'claim_lines' has 'claim_id' → join on claims.id = claim_lines.claim_id
        if not matched:
            for avail_alias, avail_dep, avail_cols in available_tables:
                avail_entity = _entity_name(avail_dep)
                reverse_fk = f"{avail_entity}_id"
                if reverse_fk in j_cols_lower:
                    clauses.append(
                        f"left join {j_alias}\n"
                        f"        on {avail_alias}.id = {j_alias}.{reverse_fk}"
                    )
                    matched = True
                    break

        # ── Fallback: use _find_join_columns against the base ──
        if not matched:
            base_col, join_col = _find_join_columns(base_dep, j_dep, scenario)
            clauses.append(
                f"left join {j_alias}\n"
                f"        on {base_alias}.{base_col} = {j_alias}.{join_col}"
            )

        # Add this joined table to the available set for subsequent joins
        available_tables.append((j_alias, j_dep, j_cols_lower))

    return "\n    ".join(clauses)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_dbt_models(scenario: DemoScenario) -> Dict[str, str]:
    """
    Generate all dbt model SQL files from the scenario.

    Returns:
        Dictionary mapping filepath to SQL content
    """
    models = {}

    for model in scenario.staging_models:
        models[f"models/staging/{model.name}.sql"] = generate_staging_model_sql(model, scenario)

    for model in scenario.intermediate_models:
        models[f"models/intermediate/{model.name}.sql"] = generate_intermediate_model_sql(model, scenario)

    for model in scenario.marts_models:
        models[f"models/marts/{model.name}.sql"] = generate_mart_model_sql(model, scenario)

    return models


def generate_staging_model_sql(model, scenario: DemoScenario) -> str:
    """Generate SQL for a staging model."""

    source_table = model.source_table
    source_data = next((s for s in scenario.data_sources if s.name == source_table), None)

    columns = source_data.columns if source_data else ['id', 'created_at', 'updated_at']
    columns_sql = ",\n    ".join(f"{col}" for col in columns)
    source_name = source_table.split('.')[-1] if '.' in source_table else source_table

    return f"""{{{{
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


def generate_intermediate_model_sql(model, scenario: DemoScenario) -> str:
    """Generate SQL for an intermediate model (join-safe)."""

    # Build CTEs
    cte_aliases: List[str] = []
    cte_parts: List[str] = []
    for dep in model.depends_on:
        alias = dep.replace('stg_', '').replace('int_', '')
        cte_aliases.append(alias)
        cte_parts.append(f"{alias} as (\n\n    select * from {{{{ ref('{dep}') }}}}\n\n)")

    ctes_sql = ",\n\n".join(cte_parts)

    # Build final SELECT
    if len(model.depends_on) > 1:
        base_alias = cte_aliases[0]
        base_dep = model.depends_on[0]
        join_aliases = cte_aliases[1:]
        join_deps = model.depends_on[1:]

        select_cols = _build_join_select(base_alias, base_dep, join_aliases, join_deps, scenario)
        join_sql = _build_join_clauses(base_alias, base_dep, join_aliases, join_deps, scenario)

        final_select = (
            f"    select\n"
            f"        {select_cols}\n"
            f"    from {base_alias}\n"
            f"    {join_sql}"
        )
    else:
        final_select = f"    select * from {cte_aliases[0]}"

    return f"""{{{{
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


def generate_mart_model_sql(model, scenario: DemoScenario) -> str:
    """Generate SQL for a marts model (join-safe)."""

    materialization = (
        "materialized='incremental',\n        unique_key='id'"
        if model.is_incremental
        else "materialized='table'"
    )

    # Build CTEs
    cte_aliases: List[str] = []
    cte_parts: List[str] = []
    for dep in model.depends_on:
        alias = dep.replace('stg_', '').replace('int_', '').replace('fct_', '').replace('dim_', '')
        cte_aliases.append(alias)
        cte_parts.append(f"{alias} as (\n\n    select * from {{{{ ref('{dep}') }}}}\n\n)")

    ctes_sql = ",\n\n".join(cte_parts)

    # Build final SELECT
    if len(model.depends_on) > 1:
        base_alias = cte_aliases[0]
        base_dep = model.depends_on[0]
        join_aliases = cte_aliases[1:]
        join_deps = model.depends_on[1:]

        select_cols = _build_join_select(base_alias, base_dep, join_aliases, join_deps, scenario)
        join_sql = _build_join_clauses(base_alias, base_dep, join_aliases, join_deps, scenario)

        agg_select = (
            f"    select\n"
            f"        {select_cols}\n"
            f"    from {base_alias}\n"
            f"    {join_sql}"
        )
    else:
        agg_select = f"    select * from {cte_aliases[0]}"

    incremental_logic = ""
    if model.is_incremental:
        incremental_logic = """

    {% if is_incremental() %}
        -- Only include new/updated records
        where updated_at > (select max(updated_at) from {{ this }})
    {% endif %}
"""

    return f"""{{{{
    config(
        {materialization}
    )
}}}}

/*
    {model.description}
*/

with {ctes_sql},

final as (

{agg_select}{incremental_logic}

)

select * from final
"""
