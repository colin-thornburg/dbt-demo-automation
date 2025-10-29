"""
Demo Setup Page - Main input form for demo generation
"""

import streamlit as st
from src.ui.components import (
    render_page_header,
    render_configuration_summary,
    render_api_key_input,
    render_text_area_with_counter,
    render_info_box
)
from src.ui.session_state import (
    get_state,
    set_state,
    has_demo_inputs,
    has_ai_config,
    has_github_config,
    has_dbt_config
)
from src.config import load_config
from src.ai import get_ai_provider, generate_demo_scenario
from src.github_integration import default_repo_name


def render_demo_inputs_section():
    """Render the demo inputs form section"""
    st.subheader("1. Demo Context")

    render_info_box(
        "Provide information about the prospect and their use case. "
        "This will be used to generate a customized demo scenario.",
        type="info"
    )

    # Default values for easier testing
    default_company = "Jaffle Shop"
    default_industry = "Candy Retailer"
    # Empty defaults for discovery notes and pain points - users should provide their own
    default_discovery = ""
    default_pain_points = ""

    # Initialize defaults BEFORE rendering components (only for required fields)
    if 'company_name' not in st.session_state or not st.session_state.get('company_name'):
        st.session_state['company_name'] = default_company
    if 'industry' not in st.session_state or not st.session_state.get('industry'):
        st.session_state['industry'] = default_industry
    # Don't set defaults for optional fields - let them be empty unless user fills them
    if 'discovery_notes' not in st.session_state:
        st.session_state['discovery_notes'] = default_discovery
    if 'pain_points' not in st.session_state:
        st.session_state['pain_points'] = default_pain_points

    # Company Name
    company = st.text_input(
        "Company Name *",
        value=get_state('company_name', default_company),
        placeholder="e.g., Acme Corporation",
        help="The prospect's company name",
        key="input_company_name"
    )
    set_state('company_name', company)

    # Industry
    industry = st.text_input(
        "Industry / Vertical *",
        value=get_state('industry', default_industry),
        placeholder="e.g., E-commerce, Healthcare, Financial Services",
        help="The industry or vertical this prospect operates in",
        key="input_industry"
    )
    set_state('industry', industry)

    # Discovery Notes
    st.markdown("---")
    st.markdown("**Optional: Additional Context**")

    discovery = render_text_area_with_counter(
        "Discovery Call Notes",
        key='discovery_notes',
        height=150,
        help="Key insights from your discovery call (current data challenges, business goals, etc.)"
    )
    set_state('discovery_notes', discovery)

    # Pain Points
    pain_points = render_text_area_with_counter(
        "Technical Pain Points",
        key='pain_points',
        height=150,
        help="Specific pain points with their current data tooling or processes"
    )
    set_state('pain_points', pain_points)

    # Semantic Layer
    semantic = st.checkbox(
        "Include Semantic Layer in Demo",
        value=get_state('include_semantic_layer', False),
        help="Generate Semantic Layer metrics and examples",
        key="input_semantic_layer"
    )
    set_state('include_semantic_layer', semantic)


def render_ai_config_section():
    """Render the AI configuration section"""
    config = load_config()

    # Only show subheader if not in sidebar (check for smaller width)
    import inspect
    # Check if being called from sidebar by looking at call stack
    in_sidebar = 'render_configuration_sidebar' in str(inspect.stack())

    if not in_sidebar:
        st.subheader("2. AI Provider Configuration")

    # Check if we have defaults from .env
    has_env_claude = bool(config.anthropic_api_key)
    has_env_openai = bool(config.openai_api_key)

    # Provider selection
    provider = st.selectbox(
        "AI Provider *",
        options=['claude', 'openai'],
        index=0 if get_state('ai_provider', config.default_ai_provider) == 'claude' else 1,
        help="Select which AI provider to use for demo generation",
        key="input_ai_provider"
    )
    set_state('ai_provider', provider)

    # Check if using .env default for current provider
    using_env_key = (provider == 'claude' and has_env_claude) or (provider == 'openai' and has_env_openai)

    if using_env_key:
        st.markdown(
            '<p style="color: #888; font-size: 0.9em; font-style: italic;">🔑 Using API key from .env file</p>',
            unsafe_allow_html=True
        )

    # API Key input - use provider-specific keys
    api_key_state_key = f'{provider}_api_key'  # e.g., 'claude_api_key' or 'openai_api_key'

    api_key_placeholder = "Using .env default..." if using_env_key else "sk-..."

    api_key = render_api_key_input(
        f"{provider.capitalize()} API Key *",
        key=api_key_state_key,
        help_text=f"Your {provider.capitalize()} API key. Leave blank to use .env default." if using_env_key else f"Your {provider.capitalize()} API key",
        placeholder=api_key_placeholder
    )

    # Use env value if input is empty, then set the active key
    if not api_key:
        if provider == 'claude' and has_env_claude:
            set_state(api_key_state_key, config.anthropic_api_key)
            set_state('ai_api_key', config.anthropic_api_key)
        elif provider == 'openai' and has_env_openai:
            set_state(api_key_state_key, config.openai_api_key)
            set_state('ai_api_key', config.openai_api_key)
    else:
        set_state(api_key_state_key, api_key)
        set_state('ai_api_key', api_key)

    # Model selection
    if provider == 'claude':
        model_options = [
            {
                "value": "claude-haiku-4-5-20251001",
                "label": "claude-haiku-4.5 (Oct 2025) — Lowest latency and cost"
            },
            {
                "value": "claude-sonnet-4-5-20250929",
                "label": "claude-sonnet-4.5 (Sep 2025) — Balanced quality vs. speed (recommended)"
            },
            {
                "value": "claude-opus-4-1-20250805",
                "label": "claude-opus-4.1 (Aug 2025) — Highest reasoning depth"
            },
            {
                "value": "claude-opus-4-20250514",
                "label": "claude-opus-4 (May 2025) — Advanced reasoning, earlier release"
            },
            {
                "value": "claude-sonnet-4-20250514",
                "label": "claude-sonnet-4 (May 2025) — Reliable general-purpose option"
            },
        ]
        claude_model_values = [option["value"] for option in model_options]
        default_model = (
            config.default_claude_model
            if config.default_claude_model in claude_model_values
            else 'claude-sonnet-4-5-20250929'
        )

        current_model = get_state('ai_model', default_model)
        selected_index = next(
            (index for index, option in enumerate(model_options) if option["value"] == current_model),
            1  # default to sonnet 4.5
        )
        model_labels = [option["label"] for option in model_options]
        selected_label = st.selectbox(
            "Model",
            options=model_labels,
            index=selected_index,
            help=(
                "Choose the Claude model that best matches your needs. "
                "Haiku minimizes latency/cost, Sonnet offers balanced performance, "
                "and Opus maximizes reasoning depth."
            ),
            key="input_ai_model"
        )
        model_lookup = {option["label"]: option["value"] for option in model_options}
        set_state('ai_model', model_lookup[selected_label])
    else:
        model_options = [
            {
                "value": "gpt-5",
                "label": "gpt-5 — Deepest reasoning, highest cost"
            },
            {
                "value": "gpt-4o",
                "label": "gpt-4o — Balanced quality and speed (recommended)"
            },
            {
                "value": "gpt-4o-mini",
                "label": "gpt-4o-mini — Fastest responses, lowest cost"
            },
        ]
        openai_model_values = [option["value"] for option in model_options]
        default_model = (
            config.default_openai_model
            if config.default_openai_model in openai_model_values
            else 'gpt-4o'
        )

        current_model = get_state('ai_model', default_model)
        selected_index = next(
            (index for index, option in enumerate(model_options) if option["value"] == current_model),
            1  # default to gpt-4o
        )
        model_labels = [option["label"] for option in model_options]
        selected_label = st.selectbox(
            "Model",
            options=model_labels,
            index=selected_index,
            help=(
                "Choose the OpenAI model best suited for your demo. "
                "gpt-5 provides the most capable reasoning, "
                "gpt-4o balances quality and price, "
                "and gpt-4o-mini keeps costs lowest with rapid responses."
            ),
            key="input_ai_model"
        )
        model_lookup = {option["label"]: option["value"] for option in model_options}
        set_state('ai_model', model_lookup[selected_label])

    # API key generation links
    st.caption(
        f"Don't have an API key? "
        f"[Get {provider.capitalize()} API Key]"
        f"({'https://console.anthropic.com/' if provider == 'claude' else 'https://platform.openai.com/'})"
    )


def render_github_config_section():
    """Render the GitHub configuration section"""
    config = load_config()

    # Only show subheader if not in sidebar
    import inspect
    in_sidebar = 'render_configuration_sidebar' in str(inspect.stack())

    if not in_sidebar:
        st.subheader("3. GitHub Configuration")

    has_env_token = bool(config.github_token)
    has_env_org = bool(config.default_github_org)

    # Show indicators for .env defaults
    env_indicators = []
    if has_env_token:
        env_indicators.append("token")
    if has_env_org:
        env_indicators.append("username")

    if env_indicators:
        st.markdown(
            f'<p style="color: #888; font-size: 0.9em; font-style: italic;">🔑 Using {", ".join(env_indicators)} from .env file</p>',
            unsafe_allow_html=True
        )

    # Username/Org
    username_placeholder = (
        f"Using .env: {config.default_github_org}"
        if has_env_org else "e.g. dbt-labs or your-username"
    )
    username = st.text_input(
        "GitHub Owner (Username or Organization) *",
        value=get_state('github_username', config.default_github_org or ''),
        placeholder=username_placeholder,
        help=(
            "The account that will own the repository. This is the text immediately after "
            "'https://github.com/' in the address bar. Example: https://github.com/dbt-labs "
            "➡ owner is 'dbt-labs'."
        ),
        key="input_github_username"
    )
    username_clean = username.strip()
    set_state('github_username', username_clean)

    if not has_env_org:
        st.caption(
            "Tip: Open GitHub in your browser and copy the value that appears right after "
            "'https://github.com/' on your profile or organization page."
        )

    # Personal Access Token
    token_placeholder = "Using .env default..." if has_env_token else "ghp_..."
    token = render_api_key_input(
        "Personal Access Token *",
        key='github_token',
        help_text="GitHub PAT with 'repo' scope. Leave blank to use .env default." if has_env_token else "GitHub PAT with 'repo' scope",
        placeholder=token_placeholder
    )

    # Use env value if input is empty
    if not token and has_env_token:
        set_state('github_token', config.github_token)
    else:
        set_state('github_token', token)

    # Template repo (usually don't need to change)
    template = st.text_input(
        "Template Repository URL",
        value=get_state('github_template_repo', config.dbt_template_repo_url),
        help="dbt project template to clone (usually don't need to change)",
        key="input_github_template"
    )
    set_state('github_template_repo', template)

    st.caption(
        "Need a token? [Generate GitHub Personal Access Token](https://github.com/settings/tokens) "
        "(requires 'repo' scope)"
    )


def render_dbt_config_section():
    """Render the dbt Cloud configuration section"""
    config = load_config()

    # Only show subheader if not in sidebar
    import inspect
    in_sidebar = 'render_configuration_sidebar' in str(inspect.stack())

    if not in_sidebar:
        st.subheader("4. dbt Cloud Configuration")

    has_env_token = bool(config.dbt_cloud_service_token)
    has_env_account = bool(config.default_dbt_account_id)
    has_env_project = bool(config.default_dbt_cloud_project_id)
    has_env_host = bool(config.default_dbt_cloud_host)
    has_env_pat_name = bool(config.dbt_cloud_pat_name)
    has_env_pat_value = bool(config.dbt_cloud_pat_value)
    has_env_defer = bool(config.dbt_cloud_defer_env_id)

    # Show indicators for .env defaults
    env_indicators = []
    if has_env_token:
        env_indicators.append("service token")
    if has_env_account:
        env_indicators.append("account ID")
    if has_env_project:
        env_indicators.append("project ID")
    if has_env_host:
        env_indicators.append("host")
    if has_env_pat_value:
        env_indicators.append("CLI PAT")

    if env_indicators:
        st.markdown(
            f'<p style="color: #888; font-size: 0.9em; font-style: italic;">🔑 Using {", ".join(env_indicators)} from .env file</p>',
            unsafe_allow_html=True
        )

    # Account ID
    account_placeholder = f"Using .env: {config.default_dbt_account_id}" if has_env_account else "12345"
    account_id = st.text_input(
        "dbt Cloud Account ID *",
        value=get_state('dbt_account_id', config.default_dbt_account_id or ''),
        placeholder=account_placeholder,
        help="Your dbt Cloud Account ID (found in the URL: cloud.getdbt.com/accounts/{ID}/)",
        key="input_dbt_account_id"
    )
    set_state('dbt_account_id', account_id)

    # Service Token
    token_placeholder = "Using .env default..." if has_env_token else "dbt_cloud_token_..."
    service_token = render_api_key_input(
        "Service Token *",
        key='dbt_service_token',
        help_text="dbt Cloud Service Token (requires Account Admin or Project Creator permissions). Leave blank to use .env default." if has_env_token else "dbt Cloud Service Token (requires Account Admin or Project Creator permissions)",
        placeholder=token_placeholder
    )

    # Use env value if input is empty
    if not service_token and has_env_token:
        set_state('dbt_service_token', config.dbt_cloud_service_token)
    else:
        set_state('dbt_service_token', service_token)

    # Warehouse Type
    warehouse_options = ['snowflake', 'bigquery', 'databricks', 'redshift']
    current_warehouse = get_state('dbt_warehouse_type', config.default_warehouse_type)
    warehouse_index = warehouse_options.index(current_warehouse) if current_warehouse in warehouse_options else 0

    warehouse = st.selectbox(
        "Target Warehouse",
        options=warehouse_options,
        index=warehouse_index,
        help="Target data warehouse for the demo",
        key="input_dbt_warehouse"
    )
    set_state('dbt_warehouse_type', warehouse)

    st.caption(
        "Need a token? Go to dbt Cloud > Account Settings > Service Tokens"
    )

    st.markdown("---")

    project_placeholder = (
        f"Using .env: {config.default_dbt_cloud_project_id}"
        if has_env_project else "Enter your dbt Cloud Project ID"
    )
    project_id = st.text_input(
        "dbt Cloud Project ID",
        value=get_state('dbt_cloud_project_id', config.default_dbt_cloud_project_id or ''),
        placeholder=project_placeholder,
        help="Project ID found in dbt Cloud under Deploy > Environments. Used for dbt Cloud CLI profiles.",
        key="input_dbt_project_id"
    )
    project_value = project_id.strip()
    if not project_value and has_env_project:
        project_value = config.default_dbt_cloud_project_id or ''
    set_state('dbt_cloud_project_id', project_value)

    host_placeholder = (
        f"Using .env: {config.default_dbt_cloud_host}"
        if has_env_host else "cloud.getdbt.com"
    )
    host_input = st.text_input(
        "dbt Cloud Host",
        value=get_state('dbt_cloud_host', config.default_dbt_cloud_host or 'cloud.getdbt.com'),
        placeholder=host_placeholder,
        help="Hostname for your dbt Cloud region (e.g., cloud.getdbt.com, emea.dbt.com).",
        key="input_dbt_host"
    )
    host_fallback = config.default_dbt_cloud_host or 'cloud.getdbt.com'
    host_clean = host_input.strip() if host_input else ''
    if not host_clean:
        host_clean = host_fallback
    set_state('dbt_cloud_host', host_clean)

    pat_name_placeholder = (
        f"Using .env: {config.dbt_cloud_pat_name}"
        if has_env_pat_name else "e.g. cloud-cli-demo"
    )
    pat_name = st.text_input(
        "CLI Token Name (Optional)",
        value=get_state('dbt_cloud_pat_name', config.dbt_cloud_pat_name or ''),
        placeholder=pat_name_placeholder,
        help="Optional: A friendly label for this token (e.g., 'cloud-cli-demo'). This is just a reference name you choose - it's not from dbt Cloud. If you already have a dbt_cloud.yml file, you can use your existing token-name value (e.g., 'cloud-cli-95ea').",
        key="input_dbt_pat_name"
    )
    pat_name_value = pat_name.strip()
    if not pat_name_value and has_env_pat_name:
        pat_name_value = config.dbt_cloud_pat_name or ''
    set_state('dbt_cloud_pat_name', pat_name_value)

    pat_placeholder = "Using .env default..." if has_env_pat_value else "dbtu_..."
    pat_value = render_api_key_input(
        "CLI Token Value (Optional)",
        key='dbt_cloud_pat_value',
        help_text="Optional: Personal Access Token from dbt Cloud (starts with 'dbtu_'). Create one in dbt Cloud under Account Settings > API Access > Personal Access Tokens. Leave blank to use .env default." if has_env_pat_value else "Optional: Personal Access Token from dbt Cloud (starts with 'dbtu_'). Create one in dbt Cloud under Account Settings > API Access > Personal Access Tokens.",
        placeholder=pat_placeholder
    )
    if not pat_value and has_env_pat_value:
        set_state('dbt_cloud_pat_value', config.dbt_cloud_pat_value)
    else:
        set_state('dbt_cloud_pat_value', pat_value)

    defer_placeholder = (
        f"Using .env: {config.dbt_cloud_defer_env_id}"
        if has_env_defer else "Optional environment ID for defer runs"
    )
    defer_env_id = st.text_input(
        "Defer Environment ID (optional)",
        value=get_state('dbt_cloud_defer_env_id', config.dbt_cloud_defer_env_id or ''),
        placeholder=defer_placeholder,
        help="Optional: Environment ID to use with dbt Cloud CLI defer functionality.",
        key="input_dbt_defer_env_id"
    )
    defer_value = defer_env_id.strip()
    if not defer_value and has_env_defer:
        defer_value = config.dbt_cloud_defer_env_id or ''
    set_state('dbt_cloud_defer_env_id', defer_value)

    st.caption(
        "Need a CLI token? Go to dbt Cloud > Account Settings > Personal Access Tokens."
    )


def render_demo_setup_page():
    """
    Main render function for the Demo Setup page
    """
    # Handle demo generation if requested
    if get_state('generate_demo_clicked', False):
        set_state('generate_demo_clicked', False)

        # Show loading state
        with st.spinner("🤖 Generating custom demo scenario with AI..."):
            try:
                # Get AI provider
                ai_provider = get_ai_provider(
                    provider_type=get_state('ai_provider'),
                    api_key=get_state('ai_api_key'),
                    model=get_state('ai_model')
                )

                # Generate new scenario
                # Debug: Log what we're sending to AI
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Generating scenario with discovery_notes: {get_state('discovery_notes')[:100]}...")
                logger.info(f"Generating scenario with pain_points: {get_state('pain_points')[:100]}...")
                
                scenario = generate_demo_scenario(
                    company_name=get_state('company_name'),
                    industry=get_state('industry'),
                    ai_provider=ai_provider,
                    discovery_notes=get_state('discovery_notes'),
                    pain_points=get_state('pain_points'),
                    include_semantic_layer=get_state('include_semantic_layer', False)
                )

                # Save scenario to session state
                set_state('demo_scenario', scenario)
                set_state('repo_name', default_repo_name(scenario.company_name))
                set_state('repo_name_custom', False)
                set_state('regeneration_summary', [])
                set_state('regeneration_feedback', '')
                if 'regeneration_feedback_input' in st.session_state:
                    del st.session_state['regeneration_feedback_input']
                set_state('scroll_to_top', True)

                # Navigate to review page
                set_state('current_page', 'scenario_review')
                st.success("✅ Demo scenario generated successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to generate demo scenario: {str(e)}")
                render_info_box(
                    "Please check your API key and try again. If the problem persists, "
                    "try a different model or provider.",
                    type="error"
                )
                return

    render_page_header(
        "Demo Setup",
        "Configure your prospect demo and API settings",
        show_reset=False  # Don't show reset on the setup page since this is the starting point
    )

    # Configuration status summary
    render_configuration_summary()

    st.markdown("---")

    # Required demo inputs (always visible)
    render_demo_inputs_section()

    st.markdown("---")

    render_info_box(
        "Need to adjust AI, GitHub, or dbt Cloud settings? Open the sidebar and expand "
        "the **⚙️ Configuration** panel to make updates without leaving this page.",
        type="info"
    )
    st.markdown("---")
    
    # Debug: Show what will be sent to AI
    with st.expander("🔍 Debug: View Inputs Being Sent to AI", expanded=False):
        st.write("**Company:**", get_state('company_name', 'Not set'))
        st.write("**Industry:**", get_state('industry', 'Not set'))
        discovery = get_state('discovery_notes', '')
        st.write("**Discovery Notes:**", discovery if discovery else "(empty)")
        pain = get_state('pain_points', '')
        st.write("**Pain Points:**", pain if pain else "(empty)")
        st.write("**Semantic Layer:**", get_state('include_semantic_layer', False))

    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if not has_demo_inputs():
            st.warning("⚠️ Please fill in Company Name and Industry to continue")

    with col2:
        if st.button("Clear Form", type="secondary", use_container_width=True):
            # Clear all session state
            for key in list(st.session_state.keys()):
                if key.startswith('input_'):
                    continue  # Let Streamlit handle input widgets
                del st.session_state[key]
            st.rerun()

    with col3:
        all_configs = has_demo_inputs() and has_ai_config() and has_github_config() and has_dbt_config()

        if st.button(
            "Generate Demo →",
            type="primary",
            disabled=not all_configs,
            use_container_width=True
        ):
            # Trigger scenario generation
            set_state('generate_demo_clicked', True)
            st.rerun()


def render_configuration_sidebar():
    """
    Render configuration controls inside the sidebar expander
    """
    from src.ui.session_state import has_ai_config, has_github_config, has_dbt_config

    # AI Configuration
    ai_status = "✅" if has_ai_config() else "⚠️"
    st.markdown(f"### {ai_status} AI Provider")
    render_ai_config_section()
    st.markdown("---")

    # GitHub Configuration
    github_status = "✅" if has_github_config() else "⚠️"
    st.markdown(f"### {github_status} GitHub")
    render_github_config_section()
    st.markdown("---")

    # dbt Cloud Configuration
    dbt_status = "✅" if has_dbt_config() else "⚠️"
    st.markdown(f"### {dbt_status} dbt Cloud")
    render_dbt_config_section()

    st.markdown("---")

    # Quick action: Test configuration
    if has_ai_config() and has_github_config():
        if st.button("✓ All Set! Close Sidebar", use_container_width=True, type="primary"):
            st.info("Configuration complete! You can now generate your demo.")
            st.balloons()
