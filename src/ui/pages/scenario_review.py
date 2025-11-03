"""
Scenario Review Page - Review and confirm AI-generated demo scenario
"""

from typing import List

import streamlit as st
import streamlit.components.v1 as components
from src.ui.components import (
    render_page_header,
    render_info_box
)
from src.ui.session_state import get_state, set_state
from src.ai.scenario_generator import DemoScenario
from src.github_integration import default_repo_name


def render_scenario_overview(scenario: DemoScenario):
    """Render the demo overview section"""
    st.subheader("📋 Demo Overview")
    st.info(scenario.demo_overview)

    st.subheader("🎯 Business Context")
    st.write(scenario.business_context)


def render_data_architecture(scenario: DemoScenario):
    """Render the data architecture section"""
    st.subheader("🗄️ Data Architecture")

    # Data Sources
    with st.expander("**Source Tables**", expanded=True):
        for source in scenario.data_sources:
            st.markdown(f"**`{source.name}`**")
            st.caption(source.description)
            st.caption(f"Columns: {', '.join(source.columns)}")
            st.divider()

    # Staging Models
    with st.expander("**Staging Models (stg_)**", expanded=True):
        for model in scenario.staging_models:
            st.markdown(f"**`{model.name}`**")
            st.caption(model.description)
            st.caption(f"Source: `{model.source_table}`")
            st.divider()

    # Intermediate Models
    with st.expander("**Intermediate Models (int_)**", expanded=True):
        for model in scenario.intermediate_models:
            st.markdown(f"**`{model.name}`**")
            st.caption(model.description)
            st.caption(f"Depends on: {', '.join([f'`{dep}`' for dep in model.depends_on])}")
            st.divider()

    # Marts Models
    with st.expander("**Marts Models (final analytics tables)**", expanded=True):
        for model in scenario.marts_models:
            incremental_badge = " 🔄 **INCREMENTAL**" if model.is_incremental else ""
            st.markdown(f"**`{model.name}`**{incremental_badge}")
            st.caption(model.description)
            st.caption(f"Depends on: {', '.join([f'`{dep}`' for dep in model.depends_on])}")
            st.divider()


def render_metrics_and_talking_points(scenario: DemoScenario):
    """Render metrics and talking points"""
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Key Metrics")
        for metric in scenario.key_metrics:
            st.markdown(f"**{metric.name}**")
            st.caption(metric.description)
            st.caption(f"Calculation: `{metric.calculation}`")
            st.divider()

    with col2:
        st.subheader("💡 Demo Talking Points")
        for i, point in enumerate(scenario.talking_points, 1):
            st.markdown(f"{i}. {point}")


def render_mesh_demo_overview(scenario: DemoScenario, num_downstream: int):
    """Render mesh demo structure overview"""
    st.markdown("---")
    st.subheader("🌐 dbt Mesh Demo Structure")
    
    # Get producer project name
    producer_project_name = scenario.company_name.lower().replace(' ', '_').replace('-', '_')
    if not producer_project_name[0].isalpha():
        producer_project_name = 'demo_' + producer_project_name
    
    render_info_box(
        f"This mesh demo will create **{num_downstream + 1} projects**: "
        f"1 producer project and {num_downstream} consumer project(s). "
        "The producer exposes public models with contracts, and consumers reference them via cross-project refs.",
        type="info"
    )
    
    # Producer Project Details
    with st.expander("📤 **Producer Project** - Public Models & Contracts", expanded=True):
        st.markdown(f"**Project Name:** `{producer_project_name}`")
        st.markdown("**Purpose:** Contains public models that downstream projects can reference")
        
        st.markdown("**Public Models (with Contracts):**")
        if scenario.marts_models:
            for model in scenario.marts_models[:3]:  # Show first 3 marts models
                st.markdown(f"- **`{model.name}`**")
                st.caption(f"  {model.description}")
                st.caption(f"  ✅ Will have `access: public` and `contract.enforced: true`")
        
        st.markdown("**Contract Requirements:**")
        st.markdown("""
        - All public models will have model contracts enabled
        - Contracts enforce column data types and constraints
        - Ensures stable API for downstream consumers
        - All columns marked as `not_null` for contract compliance
        """)
    
    # Consumer Projects Details
    consumer_types = [
        ("Marketing Channels", "marketing_channels.csv", "marketing_roi_by_channel"),
        ("Regions", "regions.csv", "regional_performance"),
        ("Product Categories", "product_categories.csv", "category_analysis")
    ]
    
    for i in range(1, num_downstream + 1):
        consumer_type, seed_file, model_name = consumer_types[i - 1]
        consumer_project_name = f"{producer_project_name}_consumer_{i}"
        
        with st.expander(f"📥 **Consumer Project {i}** - Cross-Project References", expanded=True):
            st.markdown(f"**Project Name:** `{consumer_project_name}`")
            st.markdown(f"**Focus:** {consumer_type} analysis")
            
            st.markdown("**What's Included:**")
            st.markdown(f"- **Seed Data:** `{seed_file}`")
            st.markdown(f"  - Reference data for {consumer_type.lower()}")
            
            # Get producer model name for reference
            producer_model = scenario.marts_models[0].name if scenario.marts_models else 'monthly_revenue'
            
            st.markdown(f"- **Model:** `{model_name}`")
            st.markdown(f"  - Combines local seed data with producer model")
            st.markdown(f"  - Uses cross-project reference: `{{{{ ref('{producer_project_name}', '{producer_model}') }}}}`")
            
            st.markdown("**Cross-Project Reference Syntax:**")
            st.code(f"{{{{ ref('{producer_project_name}', '{producer_model}') }}}}", language="sql")
            st.caption("Two-argument ref() syntax: (project_name, model_name)")
            
            st.markdown("**Dependencies Configuration:**")
            st.code(f"""projects:
  - name: {producer_project_name}""", language="yaml")
            st.caption("Defined in `dependencies.yml`")
    
    st.markdown("---")


def summarize_scenario_changes(old: DemoScenario, new: DemoScenario) -> List[str]:
    """Generate a human-friendly summary of differences between two scenarios."""

    def _format_backtick(names: List[str]) -> str:
        return ", ".join(f"`{name}`" for name in names)

    def _format_quotes(items: List[str]) -> str:
        return ", ".join(f'"{item}"' for item in items)

    def _map_by_name(items):
        return {item.name: item for item in (items or [])}

    def _summarize_named_section(old_items, new_items, label: str) -> List[str]:
        messages = []
        old_map = _map_by_name(old_items)
        new_map = _map_by_name(new_items)

        added = [name for name in new_map if name not in old_map]
        removed = [name for name in old_map if name not in new_map]
        updated = []

        for name in set(old_map).intersection(new_map):
            old_item = old_map[name]
            new_item = new_map[name]
            old_dump = old_item.model_dump()
            new_dump = new_item.model_dump()

            if hasattr(old_item, "is_incremental") and getattr(old_item, "is_incremental") != getattr(new_item, "is_incremental"):
                if getattr(new_item, "is_incremental"):
                    messages.append(f"Marked `{name}` as incremental in the marts layer.")
                else:
                    messages.append(f"Removed incremental materialization from `{name}` in the marts layer.")

            if old_dump != new_dump:
                updated.append(name)

        if added:
            messages.append(f"Added {label}: {_format_backtick(added)}.")
        if removed:
            messages.append(f"Removed {label}: {_format_backtick(removed)}.")
        if updated:
            messages.append(f"Updated {label} definitions for {_format_backtick(updated)}.")

        return messages

    if old is None:
        return ["Generated a brand-new scenario."]

    changes: List[str] = []

    if old.demo_overview.strip() != new.demo_overview.strip():
        changes.append("Refined the demo overview narrative.")

    if old.business_context.strip() != new.business_context.strip():
        changes.append("Updated the business context to reflect your feedback.")

    changes.extend(_summarize_named_section(old.data_sources, new.data_sources, "data sources"))
    changes.extend(_summarize_named_section(old.staging_models, new.staging_models, "staging models"))
    changes.extend(_summarize_named_section(old.intermediate_models, new.intermediate_models, "intermediate models"))
    changes.extend(_summarize_named_section(old.marts_models, new.marts_models, "marts models"))

    # Metrics
    old_metrics = _map_by_name(old.key_metrics)
    new_metrics = _map_by_name(new.key_metrics)
    added_metrics = [name for name in new_metrics if name not in old_metrics]
    removed_metrics = [name for name in old_metrics if name not in new_metrics]
    updated_metrics = [
        name for name in set(old_metrics).intersection(new_metrics)
        if old_metrics[name].model_dump() != new_metrics[name].model_dump()
    ]
    if added_metrics:
        changes.append(f"Added key metrics: {_format_backtick(added_metrics)}.")
    if removed_metrics:
        changes.append(f"Removed key metrics: {_format_backtick(removed_metrics)}.")
    if updated_metrics:
        changes.append(f"Updated metric definitions for {_format_backtick(updated_metrics)}.")

    # Talking points (order matters, so use sequence comparison)
    old_points = old.talking_points or []
    new_points = new.talking_points or []
    added_points = [point for point in new_points if point not in old_points]
    removed_points = [point for point in old_points if point not in new_points]
    if added_points:
        changes.append(f"Added demo talking points: {_format_quotes(added_points)}.")
    if removed_points:
        changes.append(f"Removed demo talking points: {_format_quotes(removed_points)}.")

    if not changes:
        changes.append("Refined wording while keeping the overall plan intact.")

    return changes


def render_regeneration_section(scenario: DemoScenario):
    """Render the regeneration feedback section"""
    st.markdown("---")
    st.subheader("🔄 Want to Adjust This Scenario?")

    feedback = st.text_area(
        "Provide feedback for regeneration",
        placeholder="E.g., 'Add more focus on data quality', 'Include customer churn metrics', 'Simplify the model structure'",
        height=100,
        key="regeneration_feedback_input",
        value=get_state('regeneration_feedback', '')
    )

    col1, col2 = st.columns([3, 1])

    with col2:
        if st.button("🔄 Regenerate", type="secondary", use_container_width=True, disabled=not feedback):
            if feedback:
                set_state('regeneration_requested', True)
                set_state('regeneration_feedback', feedback)
                st.rerun()


def render_scenario_review_page():
    """
    Main render function for the Scenario Review page
    """
    # Handle file generation if confirmed
    if get_state('confirm_scenario_clicked', False):
        set_state('confirm_scenario_clicked', False)

        with st.spinner("📁 Generating dbt project files..."):
            try:
                from src.file_generation import generate_all_files, generate_mesh_projects

                # Get scenario
                scenario = get_state('demo_scenario')
                mesh_demo = get_state('mesh_demo', False)
                num_downstream = get_state('num_downstream_projects', 1)

                if mesh_demo:
                    # Generate mesh projects
                    mesh_projects = generate_mesh_projects(
                        scenario,
                        num_downstream_projects=num_downstream,
                        num_seed_rows=20,
                        dbt_cloud_project_id=get_state('dbt_cloud_project_id', '').strip() or None,
                        include_semantic_layer=get_state('include_semantic_layer', False)
                    )
                    
                    # Save to session state
                    set_state('generated_files', mesh_projects['producer'])  # Legacy - use producer for compatibility
                    set_state('mesh_projects', mesh_projects)
                    set_state('is_mesh_demo', True)
                else:
                    # Generate single project
                    generated_files = generate_all_files(
                        scenario,
                        num_seed_rows=20,
                        dbt_cloud_project_id=get_state('dbt_cloud_project_id', '').strip() or None,
                        include_semantic_layer=get_state('include_semantic_layer', False)
                    )
                    
                    # Save to session state
                    set_state('generated_files', generated_files)
                    set_state('mesh_projects', None)
                    set_state('is_mesh_demo', False)

                # Navigate to files preview page
                set_state('current_page', 'files_preview')
                st.success("✅ Files generated successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to generate files: {str(e)}")
                render_info_box(
                    f"Error details: {str(e)}",
                    type="error"
                )
                # Continue to show scenario below

    # Handle regeneration if requested
    if get_state('regeneration_requested', False):
        set_state('regeneration_requested', False)

        with st.spinner("🤖 Regenerating scenario with your feedback..."):
            try:
                from src.ai import get_ai_provider
                from src.ai.scenario_generator import regenerate_scenario

                # Get AI provider
                ai_provider = get_ai_provider(
                    provider_type=get_state('ai_provider'),
                    api_key=get_state('ai_api_key'),
                    model=get_state('ai_model')
                )

                # Regenerate with feedback
                original_scenario = get_state('demo_scenario')
                scenario = regenerate_scenario(
                    original_scenario=original_scenario,
                    feedback=get_state('regeneration_feedback', ''),
                    ai_provider=ai_provider,
                    discovery_notes=get_state('discovery_notes'),
                    pain_points=get_state('pain_points'),
                    include_semantic_layer=get_state('include_semantic_layer', False)
                )

                change_summary = summarize_scenario_changes(original_scenario, scenario)

                # Save updated scenario
                set_state('demo_scenario', scenario)
                if not get_state('repo_name_custom', False):
                    set_state('repo_name', default_repo_name(scenario.company_name))
                set_state('regeneration_summary', change_summary)
                set_state('regeneration_feedback', '')
                set_state('scroll_to_top', True)
                if 'regeneration_feedback_input' in st.session_state:
                    del st.session_state['regeneration_feedback_input']
                st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to regenerate scenario: {str(e)}")
                render_info_box(
                    "Please check your API key and try again.",
                    type="error"
                )
                # Continue to show the original scenario below

    render_page_header(
        "Demo Scenario Review",
        "Review the AI-generated demo scenario and proceed or regenerate"
    )

    # Get scenario from session state
    scenario = get_state('demo_scenario')

    if not scenario:
        render_info_box(
            "No demo scenario found. Please go back to Demo Setup and generate a scenario.",
            type="warning"
        )
        if st.button("← Back to Setup"):
            set_state('current_page', 'demo_setup')
            st.rerun()
        return

    change_summary = get_state('regeneration_summary', [])
    if get_state('scroll_to_top', False):
        components.html(
            "<script>window.parent.scrollTo({top: 0, behavior: 'auto'});</script>",
            height=0
        )
        set_state('scroll_to_top', False)
        if not change_summary:
            st.success("✅ Demo scenario ready! Start with the overview below.")

    if change_summary:
        st.success("Scenario regenerated with your feedback. Key updates:")
        for item in change_summary:
            st.markdown(f"- {item}")
        set_state('regeneration_summary', [])

    # Display prospect info
    st.markdown(f"**Company:** {scenario.company_name} | **Industry:** {scenario.industry}")
    
    # Check if this is a mesh demo and show mesh structure
    is_mesh = get_state('mesh_demo', False)
    num_downstream = get_state('num_downstream_projects', 1)
    
    if is_mesh:
        render_mesh_demo_overview(scenario, num_downstream)
    
    st.divider()

    # Render scenario sections
    render_scenario_overview(scenario)
    st.markdown("---")
    render_data_architecture(scenario)
    st.markdown("---")
    render_metrics_and_talking_points(scenario)

    # Regeneration section
    render_regeneration_section(scenario)

    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.success("✅ Scenario looks good? Click Confirm to proceed with file generation.")

    with col2:
        if st.button("← Back to Setup", type="secondary", use_container_width=True):
            set_state('current_page', 'demo_setup')
            set_state('demo_scenario', None)
            st.rerun()

    with col3:
        if st.button("Confirm Scenario →", type="primary", use_container_width=True):
            set_state('confirm_scenario_clicked', True)
            st.rerun()
