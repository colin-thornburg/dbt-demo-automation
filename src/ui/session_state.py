"""
Session state management for Streamlit application
Handles persistent state across page interactions
"""

import streamlit as st
from typing import Any, Optional


def initialize_session_state():
    """
    Initialize all session state variables with defaults
    Call this at the start of the app
    """
    defaults = {
        # Navigation
        'current_page': 'demo_setup',

        # Demo Inputs
        'company_name': '',
        'industry': '',
        'discovery_notes': '',
        'pain_points': '',
        'include_semantic_layer': False,

        # AI Configuration
        'ai_provider': 'claude',
        'ai_api_key': '',
        'ai_model': '',

        # GitHub Configuration
        'github_username': '',
        'github_token': '',
        'github_template_repo': 'https://github.com/colin-thornburg/demo-automation-template.git',

        # dbt Cloud Configuration
        'dbt_account_id': '',
        'dbt_service_token': '',
        'dbt_warehouse_type': 'snowflake',
        'dbt_cloud_project_id': '',
        'dbt_cloud_host': 'cloud.getdbt.com',
        'dbt_cloud_pat_name': '',
        'dbt_cloud_pat_value': '',
        'dbt_cloud_defer_env_id': '',

        # Generated Content (will be populated later)
        'demo_scenario': None,
        'generated_files': None,
        'github_repo_url': None,
        'dbt_project_url': None,
        'regeneration_feedback': '',
        'regeneration_summary': [],
        'scroll_to_top': False,
        'repo_name': '',
        'repo_name_custom': False,

        # UI State
        'show_ai_config': False,
        'show_github_config': False,
        'show_dbt_config': False,
        'generation_in_progress': False,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def get_state(key: str, default: Any = None) -> Any:
    """
    Get a value from session state

    Args:
        key: Session state key
        default: Default value if key doesn't exist

    Returns:
        Value from session state or default
    """
    return st.session_state.get(key, default)


def set_state(key: str, value: Any):
    """
    Set a value in session state

    Args:
        key: Session state key
        value: Value to set
    """
    st.session_state[key] = value


def clear_generated_content():
    """
    Clear all generated content from session state
    Used when user wants to start a new demo
    """
    keys_to_clear = [
        'demo_scenario',
        'generated_files',
        'github_repo_url',
        'dbt_project_url'
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            st.session_state[key] = None


def validate_required_fields() -> tuple[bool, list[str]]:
    """
    Validate that all required fields are filled

    Returns:
        Tuple of (is_valid, list_of_missing_fields)
    """
    required_fields = {
        'company_name': 'Company Name',
        'industry': 'Industry',
        'ai_api_key': 'AI API Key',
        'github_username': 'GitHub Username',
        'github_token': 'GitHub Token',
        'dbt_account_id': 'dbt Cloud Account ID',
        'dbt_service_token': 'dbt Cloud Service Token',
    }

    missing = []
    for key, display_name in required_fields.items():
        value = st.session_state.get(key, '')
        if not value or (isinstance(value, str) and not value.strip()):
            missing.append(display_name)

    return len(missing) == 0, missing


def has_demo_inputs() -> bool:
    """
    Check if minimum demo inputs are provided

    Returns:
        True if company name and industry are filled
    """
    return (
        bool(st.session_state.get('company_name', '').strip()) and
        bool(st.session_state.get('industry', '').strip())
    )


def has_ai_config() -> bool:
    """
    Check if AI configuration is complete
    Checks both session state and .env defaults

    Returns:
        True if AI provider and API key are set
    """
    from src.config import load_config

    # Check session state first
    if (bool(st.session_state.get('ai_provider')) and
        bool(st.session_state.get('ai_api_key', '').strip())):
        return True

    # Check .env as fallback
    try:
        config = load_config()
        provider = st.session_state.get('ai_provider', config.default_ai_provider)

        if provider == 'claude':
            return bool(config.anthropic_api_key)
        elif provider == 'openai':
            return bool(config.openai_api_key)
    except:
        pass

    return False


def has_github_config() -> bool:
    """
    Check if GitHub configuration is complete
    Checks both session state and .env defaults

    Returns:
        True if GitHub username and token are set
    """
    from src.config import load_config

    # Check session state first
    if (bool(st.session_state.get('github_username', '').strip()) and
        bool(st.session_state.get('github_token', '').strip())):
        return True

    # Check .env as fallback
    try:
        config = load_config()
        return bool(config.github_token) and bool(config.default_github_org)
    except:
        pass

    return False


def has_dbt_config() -> bool:
    """
    Check if dbt Cloud configuration is complete
    Checks both session state and .env defaults

    Returns:
        True if account ID and service token are set
    """
    from src.config import load_config

    # Check session state first
    if (bool(st.session_state.get('dbt_account_id', '').strip()) and
        bool(st.session_state.get('dbt_service_token', '').strip())):
        return True

    # Check .env as fallback
    try:
        config = load_config()
        return bool(config.dbt_cloud_service_token) and bool(config.default_dbt_account_id)
    except:
        pass

    return False


def get_configuration_status() -> dict:
    """
    Get the status of all configuration sections

    Returns:
        Dictionary with boolean flags for each config section
    """
    return {
        'demo_inputs': has_demo_inputs(),
        'ai_config': has_ai_config(),
        'github_config': has_github_config(),
        'dbt_config': has_dbt_config(),
        'all_ready': (
            has_demo_inputs() and
            has_ai_config() and
            has_github_config() and
            has_dbt_config()
        )
    }
