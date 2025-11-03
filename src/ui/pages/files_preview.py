"""
Files Preview Page - Review generated dbt project files
"""

import io
import zipfile
from typing import Optional

import streamlit as st
from src.ui.components import render_page_header, render_info_box
from src.ui.session_state import get_state, set_state
from src.file_generation import GeneratedFiles
from src.github_integration import (
    create_demo_repository,
    create_mesh_repositories,
    default_repo_name,
    sanitize_repo_name,
)


def render_files_preview_page():
    """
    Main render function for the Files Preview page
    """
    scenario = get_state('demo_scenario')
    generated_files = get_state('generated_files')

    # Handle repository creation if requested
    if get_state('create_repository_clicked', False):
        set_state('create_repository_clicked', False)

        with st.spinner("🚀 Creating GitHub repository and pushing files..."):
            try:
                # Get all required data
                github_token = get_state('github_token')
                github_username = get_state('github_username')
                template_repo_url = get_state('github_template_repo')
                requested_repo_name = get_state('repo_name', '').strip()
                is_mesh = get_state('is_mesh_demo', False)
                mesh_projects = get_state('mesh_projects', None)

                if is_mesh and mesh_projects:
                    # Create multiple repositories for mesh demo
                    base_repo_name = (
                        sanitize_repo_name(requested_repo_name)
                        if requested_repo_name
                        else None
                    )
                    
                    mesh_repos = create_mesh_repositories(
                        scenario=scenario,
                        mesh_projects=mesh_projects,
                        github_token=github_token,
                        github_username=github_username,
                        template_repo_url=template_repo_url,
                        base_repo_name=base_repo_name
                    )
                    
                    # Save all repository info
                    set_state('mesh_repositories', mesh_repos)
                    # For compatibility, save producer as main repo
                    if 'producer' in mesh_repos:
                        set_state('repo_info', mesh_repos['producer'])
                        set_state('repository_info', mesh_repos['producer'])
                        set_state('repo_name', mesh_repos['producer']['repo_name'])
                else:
                    # Create single repository
                    repo_name_override = (
                        sanitize_repo_name(requested_repo_name)
                        if requested_repo_name
                        else None
                    )

                    repo_info = create_demo_repository(
                        scenario=scenario,
                        generated_files=generated_files,
                        github_token=github_token,
                        github_username=github_username,
                        template_repo_url=template_repo_url,
                        repo_name=repo_name_override
                    )

                    # Save repository info to session state
                    set_state('repo_info', repo_info)  # Legacy key for compatibility
                    set_state('repository_info', repo_info)  # New key for provisioning
                    set_state('repo_name', repo_info['repo_name'])
                    if scenario:
                        set_state(
                            'repo_name_custom',
                            repo_info['repo_name'] != default_repo_name(scenario.company_name)
                        )

                # Navigate to success page
                set_state('current_page', 'repository_success')
                st.success("✅ Repository created successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to create repository: {str(e)}")
                render_info_box(
                    f"Error details: {str(e)}\n\n"
                    "Please check your GitHub token and permissions.",
                    type="error"
                )
                # Continue to show files below

    render_page_header(
        "Generated Files Preview",
        "Review the generated dbt project files before creating repository"
    )

    # Check if this is a mesh demo
    is_mesh = get_state('is_mesh_demo', False)
    mesh_projects = get_state('mesh_projects', None)

    if is_mesh and mesh_projects:
        # Show mesh projects
        st.subheader("🌐 dbt Mesh Demo - Multiple Projects")
        render_info_box(
            f"This is a mesh demo with {len(mesh_projects)} project(s): "
            f"1 producer and {len(mesh_projects) - 1} consumer(s).",
            type="info"
        )
        
        # Get producer project name from scenario
        producer_project_name = scenario.company_name.lower().replace(' ', '_').replace('-', '_')
        if not producer_project_name[0].isalpha():
            producer_project_name = 'demo_' + producer_project_name
        
        # Show mesh structure overview
        _render_mesh_structure_overview(mesh_projects, producer_project_name, scenario)
        
        st.divider()
        
        # Show project tabs
        project_tabs = st.tabs(['Producer'] + [f'Consumer {i}' for i in range(1, len(mesh_projects))])
        
        for idx, (project_key, project_files) in enumerate(mesh_projects.items()):
            with project_tabs[idx]:
                if project_key == 'producer':
                    st.markdown("### 📤 Producer Project")
                    st.caption("This project contains public models with contracts that can be referenced by consumer projects.")
                    
                    # Show which models have contracts
                    _render_producer_contracts_info(project_files, scenario)
                else:
                    consumer_num = project_key.replace('consumer_', '')
                    st.markdown(f"### 📥 Consumer Project {consumer_num}")
                    st.caption("This project references public models from the producer project using cross-project refs.")
                    
                    # Show cross-project refs
                    _render_consumer_refs_info(project_files, producer_project_name, consumer_num, scenario)
                
                # Display file summary for this project
                summary = project_files.get_summary()
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Seed Files", summary['seeds'])
                with col2:
                    st.metric("Model Files", summary['models'])
                with col3:
                    st.metric("Schema Files", summary['schemas'])
                with col4:
                    st.metric("Total Files", summary['total'])
                
                st.divider()
                
                # Show files for this project
                _render_project_files(project_files, project_key)
        
        # Use producer files for repository name default
        generated_files = mesh_projects['producer']
    else:
        # Single project mode
        # Get generated files from session state
        if not generated_files:
            render_info_box(
                "No generated files found. Please go back and confirm the scenario.",
                type="warning"
            )
            if st.button("← Back to Scenario"):
                set_state('current_page', 'scenario_review')
                st.rerun()
            return

        # Display file summary
        summary = generated_files.get_summary()
        st.subheader("📦 Files Generated")
        
        # Check if semantic layer is included
        has_semantic = summary.get('semantic_layer', 0) > 0

        if has_semantic:
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Seed Files", summary['seeds'])
            with col2:
                st.metric("Model Files", summary['models'])
            with col3:
                st.metric("Schema Files", summary['schemas'])
            with col4:
                st.metric("Semantic Layer", summary['semantic_layer'])
            with col5:
                st.metric("Total Files", summary['total'])
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Seed Files", summary['seeds'])
            with col2:
                st.metric("Model Files", summary['models'])
            with col3:
                st.metric("Schema Files", summary['schemas'])
            with col4:
                st.metric("Total Files", summary['total'])

        st.divider()
        
        _render_project_files(generated_files, 'single')

    st.divider()

    st.subheader("GitHub Repository Setup")
    
    if is_mesh and mesh_projects:
        render_info_box(
            f"This mesh demo will create {len(mesh_projects)} separate repositories: "
            "one for the producer project and one for each consumer project.",
            type="info"
        )

    # Get config for fallback values
    from src.config.settings import load_config
    app_config = load_config()
    
    # Get values from session state with .env fallback
    github_username = get_state('github_username', '') or app_config.default_github_org or ''
    github_token = get_state('github_token', '') or app_config.github_token or ''
    template_repo_url = get_state('github_template_repo', '') or app_config.dbt_template_repo_url or ''

    default_name = default_repo_name(scenario.company_name) if scenario else "dbt-demo-project"
    current_repo_name = get_state('repo_name', default_name) or default_name

    repo_name_input = st.text_input(
        "Repository Name *",
        value=current_repo_name,
        help="This will be the name of the GitHub repository created for the demo project.",
        key="input_repo_name"
    )

    raw_repo_name = repo_name_input.strip() or default_name
    sanitized_repo_name = sanitize_repo_name(raw_repo_name, fallback=default_name)
    set_state('repo_name', sanitized_repo_name)
    set_state('repo_name_custom', sanitized_repo_name != default_name)

    if sanitized_repo_name != raw_repo_name:
        st.caption(
            f"GitHub will create the repository as `{sanitized_repo_name}` (invalid characters were replaced)."
        )

    summary_col1, summary_col2 = st.columns(2)

    with summary_col1:
        if github_username:
            st.markdown(f"**Owner**: `{github_username}`")
        else:
            st.markdown(
                "⚠️ **Owner not set**\n\n"
                "Open your GitHub profile or organization (e.g., https://github.com/dbt-labs) "
                "and copy the value after the domain."
            )
        st.markdown(
            f"**Template Repo**: `{template_repo_url}`"
            if template_repo_url else "⚠️ **Template repository URL missing**"
        )

    with summary_col2:
        token_status = "✅ PAT configured" if github_token else "⚠️ PAT missing"
        st.markdown(f"**Personal Access Token**: {token_status}")
        st.markdown("**Visibility**: Private")

    missing_config = []
    if not github_username:
        missing_config.append("GitHub owner (username or organization — copy the value after https://github.com/ in your browser)")
    if not github_token:
        missing_config.append("GitHub Personal Access Token")
    if not sanitized_repo_name:
        missing_config.append("Repository name")
    if not template_repo_url:
        missing_config.append("Template repository URL")

    if missing_config:
        render_info_box(
            "Please complete the following before creating the repository:\n"
            + "\n".join(f"- {item}" for item in missing_config),
            type="warning"
        )
        
        # Debug expander to help troubleshoot
        with st.expander("🔍 Debug: View Current Configuration Values", expanded=False):
            st.write("**GitHub Username:**", github_username if github_username else "(not set)")
            st.write("**GitHub Token:**", "✅ Present" if github_token else "❌ Not set")
            st.write("**Repository Name:**", sanitized_repo_name if sanitized_repo_name else "(not set)")
            st.write("**Template Repo URL:**", template_repo_url if template_repo_url else "(not set)")
            st.write("\n**How to fix:** Go back to Demo Setup page and check the GitHub Configuration section in the sidebar.")
    elif github_username:
        st.caption(
            f"Repository will be created at "
            f"`https://github.com/{github_username}/{sanitized_repo_name}`"
        )

    st.markdown("---")

    st.subheader("Local Development Setup")

    if generated_files:
        project_zip = build_project_zip(generated_files)
        zip_name = f"{(default_repo_name(scenario.company_name) if scenario else 'dbt-demo-project')}.zip"
        st.download_button(
            "⬇️ Download Project Zip",
            data=project_zip.getvalue(),
            file_name=zip_name,
            mime="application/zip",
            help="Download the generated project to open locally in your IDE."
        )

    account_id = get_state('dbt_account_id', '').strip()
    project_id = get_state('dbt_cloud_project_id', '').strip()
    host = get_state('dbt_cloud_host', 'cloud.getdbt.com').strip() or 'cloud.getdbt.com'
    pat_name = get_state('dbt_cloud_pat_name', '').strip()
    pat_value = get_state('dbt_cloud_pat_value', '').strip()
    defer_env_id = get_state('dbt_cloud_defer_env_id', '').strip()

    cli_yaml = build_dbt_cloud_cli_yaml(
        project_name=scenario.company_name if scenario else "Demo Project",
        project_id=project_id,
        account_id=account_id,
        host=host,
        token_name=pat_name,
        token_value=pat_value,
        defer_env_id=defer_env_id
    )

    if cli_yaml:
        st.markdown("**dbt Cloud CLI Profile**")
        st.write(
            "Copy the snippet below into `~/.dbt/dbt_cloud.yml` (or download it) to use this project "
            "with the dbt Cloud CLI."
        )
        st.code(cli_yaml, language="yaml")
        st.download_button(
            "⬇️ Download dbt_cloud.yml snippet",
            data=cli_yaml.encode("utf-8"),
            file_name="dbt_cloud.yml",
            mime="application/x-yaml"
        )
    else:
        render_info_box(
            "Provide your dbt Cloud Account ID and Project ID (plus optional CLI token) to generate a "
            "dbt Cloud CLI configuration snippet.",
            type="info"
        )

    st.divider()

    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if missing_config:
            st.error(f"❌ Cannot create repository - {len(missing_config)} item(s) missing (see warning box above)")
        else:
            st.success("✅ Files look good? Review the settings above, then create the repository.")

    with col2:
        if st.button("← Back to Scenario", type="secondary", use_container_width=True):
            set_state('current_page', 'scenario_review')
            st.rerun()

    with col3:
        disable_create = bool(missing_config)
        button_label = "Create Repository →" if not disable_create else f"Missing {len(missing_config)} Config(s)"
        if st.button(
            button_label,
            type="primary",
            use_container_width=True,
            disabled=disable_create
        ):
            set_state('create_repository_clicked', True)
            st.rerun()


def _render_mesh_structure_overview(mesh_projects: dict, producer_project_name: str, scenario):
    """Render overview of mesh structure with contracts and refs"""
    with st.expander("🔍 **Mesh Structure Overview** - Contracts & Cross-Project Refs", expanded=True):
        # Producer contracts
        st.markdown("#### 📤 Producer Project - Public Models with Contracts")
        if scenario.marts_models:
            producer_model = scenario.marts_models[0].name
            st.markdown(f"- **`{producer_model}`** and other marts models")
            st.markdown("  - ✅ `access: public`")
            st.markdown("  - ✅ `contract.enforced: true`")
            st.markdown("  - ✅ All columns have `not_null` tests")
        
        # Consumer refs
        st.markdown("#### 📥 Consumer Projects - Cross-Project References")
        consumer_types = [
            ("Marketing Channels", "marketing_roi_by_channel"),
            ("Regions", "regional_performance"),
            ("Product Categories", "category_analysis")
        ]
        
        for i in range(1, len(mesh_projects)):
            consumer_type, model_name = consumer_types[i - 1]
            producer_model = scenario.marts_models[0].name if scenario.marts_models else 'monthly_revenue'
            
            st.markdown(f"**Consumer {i}** (`{model_name}`):")
            st.code(f"{{{{ ref('{producer_project_name}', '{producer_model}') }}}}", language="sql")
            st.caption(f"References producer model via two-argument ref() syntax")


def _render_producer_contracts_info(project_files: GeneratedFiles, scenario):
    """Show which models have contracts in producer project"""
    # Find marts schema file
    marts_schema = None
    for filepath in project_files.schemas.keys():
        if 'marts' in filepath and 'schema' in filepath:
            marts_schema = project_files.schemas[filepath]
            break
    
    if marts_schema:
        import yaml
        try:
            schema_dict = yaml.safe_load(marts_schema)
            if 'models' in schema_dict:
                public_models = [m for m in schema_dict['models'] if m.get('access') == 'public']
                if public_models:
                    st.markdown("**✅ Public Models with Contracts:**")
                    for model in public_models:
                        has_contract = 'contract' in model and model.get('contract', {}).get('enforced', False)
                        contract_badge = "✅ Contract Enforced" if has_contract else "⚠️ No Contract"
                        st.markdown(f"- **`{model['name']}`** - {contract_badge}")
                        if has_contract:
                            st.caption(f"  Contract ensures stable API for downstream consumers")
        except:
            pass


def _render_consumer_refs_info(project_files: GeneratedFiles, producer_project_name: str, consumer_num: str, scenario):
    """Show cross-project references in consumer project"""
    # Find dependencies.yml
    dependencies_content = None
    for filepath, content in project_files.schemas.items():
        if 'dependencies.yml' in filepath:
            dependencies_content = content
            break
    
    if dependencies_content:
        st.markdown("**📋 Project Dependencies:**")
        st.code(dependencies_content, language="yaml")
    
    # Find consumer model with cross-project ref
    consumer_types = [
        ("Marketing Channels", "marketing_roi_by_channel"),
        ("Regions", "regional_performance"),
        ("Product Categories", "category_analysis")
    ]
    
    consumer_idx = int(consumer_num) - 1
    if 0 <= consumer_idx < len(consumer_types):
        _, model_name = consumer_types[consumer_idx]
        model_path = f"models/marts/{model_name}.sql"
        
        if model_path in project_files.models:
            model_content = project_files.models[model_path]
            # Extract the ref() call
            import re
            ref_pattern = r"ref\('([^']+)',\s*'([^']+)'\)"
            matches = re.findall(ref_pattern, model_content)
            
            if matches:
                st.markdown("**🔗 Cross-Project Reference:**")
                for proj_name, model_name_ref in matches:
                    st.code(f"{{{{ ref('{proj_name}', '{model_name_ref}') }}}}", language="sql")
                    st.caption(f"References `{model_name_ref}` from `{proj_name}` project")


def _render_project_files(generated_files: GeneratedFiles, project_key: str):
    """Helper function to render files for a single project"""
    # File categories
    st.subheader("📁 File Browser")

    # Seed files
    with st.expander("**Seeds/** (Sample Data CSVs)", expanded=True):
        for filename, content in generated_files.seeds.items():
            render_file_preview(f"seeds/{filename}", content, language="csv")

    # Model files by layer
    with st.expander("**Models/Staging/** (Source Data Cleaning)", expanded=True):
        staging_models = {k: v for k, v in generated_files.models.items() if 'staging' in k}
        for filepath, content in staging_models.items():
            render_file_preview(filepath, content, language="sql")

    with st.expander("**Models/Intermediate/** (Business Logic)", expanded=False):
        int_models = {k: v for k, v in generated_files.models.items() if 'intermediate' in k}
        for filepath, content in int_models.items():
            render_file_preview(filepath, content, language="sql")

    with st.expander("**Models/Marts/** (Final Analytics Tables)", expanded=False):
        marts_models = {k: v for k, v in generated_files.models.items() if 'marts' in k}
        for filepath, content in marts_models.items():
            render_file_preview(filepath, content, language="sql")

    # Schema files and dependencies.yml
    with st.expander("**Schema Files** (Documentation & Tests)", expanded=False):
        for filepath, content in generated_files.schemas.items():
            if filepath == 'dependencies.yml':
                st.markdown("**`dependencies.yml`** (Project Dependencies)")
                st.caption("Defines cross-project dependencies for dbt Mesh")
                st.code(content, language="yaml", line_numbers=True)
                st.divider()
            else:
                render_file_preview(filepath, content, language="yaml")

    # Semantic Layer files (if generated)
    if generated_files.semantic_models or generated_files.metrics_yml:
        with st.expander("**Semantic Layer** (Metrics & Semantic Models)", expanded=True):
            # Show semantic models
            for filepath, content in generated_files.semantic_models.items():
                render_file_preview(filepath, content, language="yaml")
            # Show metrics.yml
            if generated_files.metrics_yml:
                render_file_preview("models/metrics/metrics.yml", generated_files.metrics_yml, language="yaml")

    # Project config
    with st.expander("**Project Configuration**", expanded=False):
        render_file_preview("dbt_project.yml", generated_files.project_yml, language="yaml")
        render_file_preview("README.md", generated_files.readme, language="markdown")


def render_file_preview(filepath: str, content: str, language: str = "text"):
    """
    Render a preview of a single file

    Args:
        filepath: Path to the file
        content: File content
        language: Syntax highlighting language
    """
    st.markdown(f"**`{filepath}`**")

    # Show file size
    file_size = len(content)
    st.caption(f"Size: {file_size:,} bytes | Lines: {content.count(chr(10)) + 1}")

    # Show content with syntax highlighting
    with st.container():
        st.code(content, language=language, line_numbers=True)

    st.divider()


def build_project_zip(generated_files: GeneratedFiles) -> io.BytesIO:
    """Create an in-memory ZIP archive of generated project files."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for path, content in generated_files.all_files().items():
            zip_file.writestr(path, content)
    buffer.seek(0)
    return buffer


def build_dbt_cloud_cli_yaml(
    project_name: str,
    project_id: str,
    account_id: str,
    host: str,
    token_name: str,
    token_value: str,
    defer_env_id: str,
) -> Optional[str]:
    """Construct dbt Cloud CLI YAML snippet if required fields are present."""
    if not project_id or not account_id:
        return None

    token_name = token_name or "<pat-name>"
    token_value = token_value or "<pat-value>"
    account_name = f"{project_name} Account" if project_name else "dbt Cloud Account"
    host = host or "cloud.getdbt.com"

    lines = ["version: \"1\"", "context:"]
    lines.append(f"  active-project: \"{project_id}\"")
    lines.append(f"  active-host: \"{host}\"")
    if defer_env_id:
        lines.append(f"  defer-env-id: \"{defer_env_id}\"")
    lines.append("projects:")
    lines.append("  - project-name: \"{}\"".format(project_name or "demo-project"))
    lines.append(f"    project-id: \"{project_id}\"")
    lines.append(f"    account-name: \"{account_name}\"")
    lines.append(f"    account-id: \"{account_id}\"")
    lines.append(f"    account-host: \"{host}\"")
    lines.append(f"    token-name: \"{token_name}\"")
    lines.append(f"    token-value: \"{token_value}\"")

    return "\n".join(lines) + "\n"
