"""
Reusable UI components for Streamlit pages
"""

import streamlit as st
from typing import Optional, Callable


def render_page_header(title: str, subtitle: Optional[str] = None, show_reset: bool = True):
    """
    Render a consistent page header with optional reset button

    Args:
        title: Main page title
        subtitle: Optional subtitle/description
        show_reset: Whether to show the "Start Over" button in header
    """
    if show_reset:
        col1, col2 = st.columns([6, 1])
        with col1:
            st.title(title)
            if subtitle:
                st.markdown(f"*{subtitle}*")
        with col2:
            if st.button("🔄 Start Over", type="secondary", use_container_width=True, help="Clear all data and start a new demo"):
                # Clear all session state except input widgets
                keys_to_delete = [key for key in st.session_state.keys() if not key.startswith('input_')]
                for key in keys_to_delete:
                    del st.session_state[key]
                # Reset to demo setup page
                st.session_state['current_page'] = 'demo_setup'
                st.rerun()
    else:
        st.title(title)
        if subtitle:
            st.markdown(f"*{subtitle}*")
    st.divider()


def render_status_badge(label: str, is_complete: bool):
    """
    Render a status badge (checkmark or X)

    Args:
        label: Status label
        is_complete: Whether the status is complete
    """
    icon = "✅" if is_complete else "⚠️"
    color = "green" if is_complete else "orange"
    st.markdown(f":{color}[{icon} {label}]")


def render_collapsible_section(
    title: str,
    is_complete: bool,
    content_callback: Callable,
    expanded: bool = False
):
    """
    Render a collapsible section with status indicator

    Args:
        title: Section title
        is_complete: Whether section is configured
        content_callback: Function to render section content
        expanded: Whether to expand by default
    """
    status = "✅" if is_complete else "⚠️"
    with st.expander(f"{status} {title}", expanded=expanded):
        content_callback()


def render_info_box(message: str, type: str = "info"):
    """
    Render an info/warning/error box

    Args:
        message: Message to display
        type: Box type (info, warning, error, success)
    """
    if type == "info":
        st.info(message)
    elif type == "warning":
        st.warning(message)
    elif type == "error":
        st.error(message)
    elif type == "success":
        st.success(message)


def render_configuration_summary():
    """
    Render a summary of current configuration status
    """
    from src.ui.session_state import get_configuration_status

    st.subheader("Configuration Status")

    status = get_configuration_status()

    col1, col2 = st.columns(2)

    with col1:
        render_status_badge("Demo Inputs", status['demo_inputs'])
        render_status_badge("AI Configuration", status['ai_config'])

    with col2:
        render_status_badge("GitHub Configuration", status['github_config'])
        render_status_badge("dbt Cloud Configuration", status['dbt_config'])

    if status['all_ready']:
        st.success("🎉 All configuration complete! Ready to generate demo.")
    else:
        st.warning("⚠️ Please complete all configuration sections below.")


def render_api_key_input(
    label: str,
    key: str,
    help_text: Optional[str] = None,
    placeholder: str = "sk-..."
) -> str:
    """
    Render a password input for API keys with masking (shows last 5 digits)

    Args:
        label: Input label
        key: Session state key
        help_text: Optional help text
        placeholder: Placeholder text

    Returns:
        Input value
    """
    # Get the stored value
    stored_value = st.session_state.get(key, '')

    # Create a masked version showing last 5 digits
    if stored_value and len(stored_value) > 5:
        masked_value = '•' * (len(stored_value) - 5) + stored_value[-5:]
    else:
        masked_value = stored_value

    # Use a column layout to show masked value and edit button
    col1, col2 = st.columns([4, 1])

    with col1:
        # Show masked value or allow editing
        if st.session_state.get(f"{key}_editing", False):
            # Full edit mode with password input
            new_value = st.text_input(
                label,
                value='',
                type="password",
                help=help_text,
                placeholder=placeholder if not stored_value else "Enter new value or leave blank to keep current",
                key=f"input_{key}_edit"
            )
        else:
            # Display masked value
            st.text_input(
                label,
                value=masked_value,
                help=help_text,
                placeholder=placeholder,
                disabled=True,
                key=f"input_{key}_display"
            )

    with col2:
        # Edit/Save button
        if st.session_state.get(f"{key}_editing", False):
            if st.button("Save", key=f"save_{key}", use_container_width=True):
                # Only update if user entered a new value
                if st.session_state.get(f"input_{key}_edit", '').strip():
                    st.session_state[key] = st.session_state[f"input_{key}_edit"]
                st.session_state[f"{key}_editing"] = False
                st.rerun()
        else:
            if st.button("Edit", key=f"edit_{key}", use_container_width=True):
                st.session_state[f"{key}_editing"] = True
                st.rerun()

    return stored_value


def render_text_area_with_counter(
    label: str,
    key: str,
    height: int = 150,
    max_chars: Optional[int] = None,
    help: Optional[str] = None
) -> str:
    """
    Render a text area with optional character counter

    Args:
        label: Input label
        key: Session state key
        height: Text area height in pixels
        max_chars: Maximum characters (shows counter if set)
        help: Optional help text

    Returns:
        Input value
    """
    value = st.text_area(
        label,
        value=st.session_state.get(key, ''),
        height=height,
        max_chars=max_chars,
        help=help,
        key=f"input_{key}"
    )

    if max_chars:
        char_count = len(value)
        remaining = max_chars - char_count
        color = "green" if remaining > 100 else "orange" if remaining > 0 else "red"
        st.caption(f":{color}[{char_count}/{max_chars} characters]")

    return value


def render_loading_spinner(message: str = "Processing..."):
    """
    Render a loading spinner with message

    Args:
        message: Loading message
    """
    return st.spinner(message)


def render_progress_steps(steps: list[tuple[str, bool]]):
    """
    Render a list of progress steps with checkmarks

    Args:
        steps: List of (step_name, is_complete) tuples
    """
    for step_name, is_complete in steps:
        icon = "✅" if is_complete else "⏳"
        st.markdown(f"{icon} {step_name}")
