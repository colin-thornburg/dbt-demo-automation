"""
dbt Cloud Demo Automation Tool
Main Streamlit Application Entry Point
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.ui.session_state import initialize_session_state, get_state
from src.ui.pages.demo_setup import render_demo_setup_page, render_configuration_sidebar
from src.ui.pages.scenario_review import render_scenario_review_page
from src.ui.pages.files_preview import render_files_preview_page
from src.ui.pages.repository_success import render_repository_success_page
from src.ui.pages.dbt_cloud_provisioning import render_dbt_cloud_provisioning_page
from src.ui.pages.final_success import render_final_success_page

# Page configuration
st.set_page_config(
    page_title="dbt Cloud Demo Automation",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main content area */
    .main {
        padding: 2rem;
    }

    /* Headers */
    h1 {
        color: #FF6347;
        padding-bottom: 1rem;
    }

    h2 {
        color: #FF6347;
        padding-top: 1rem;
    }

    h3 {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    /* Status badges */
    .stAlert {
        padding: 1rem;
        margin: 1rem 0;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
    }

    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1.1rem;
    }

    /* Input fields */
    .stTextInput > label, .stTextArea > label, .stSelectbox > label {
        font-weight: 500;
        font-size: 0.9rem;
    }

    /* Divider */
    hr {
        margin: 2rem 0;
    }

    /* Sidebar specific styles */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }

    section[data-testid="stSidebar"] .stProgress > div > div {
        background-color: #28a745;
    }

    section[data-testid="stSidebar"] h3 {
        font-size: 0.95rem;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }

    section[data-testid="stSidebar"] .stTextInput input,
    section[data-testid="stSidebar"] .stSelectbox select {
        font-size: 0.85rem;
    }

    /* Compact spacing in sidebar */
    section[data-testid="stSidebar"] .stTextInput,
    section[data-testid="stSidebar"] .stSelectbox {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """
    Main application entry point
    """
    # Initialize session state on first run
    initialize_session_state()

    # Sidebar (for future navigation)
    with st.sidebar:
        st.title("🚀 dbt Demo")

        # Configuration Status Summary (Always visible)
        from src.ui.session_state import get_configuration_status
        status = get_configuration_status()

        # Progress bar
        completed = sum([status['demo_inputs'], status['ai_config'],
                        status['github_config'], status['dbt_config']])
        progress = completed / 4
        st.progress(progress)

        # Status indicators
        st.markdown(f"""
        <div style="font-size: 0.85em; padding: 0.5rem 0;">
            {'✅' if status['demo_inputs'] else '⭕'} Demo Inputs<br>
            {'✅' if status['ai_config'] else '⭕'} AI Provider<br>
            {'✅' if status['github_config'] else '⭕'} GitHub<br>
            {'✅' if status['dbt_config'] else '⭕'} dbt Cloud
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Navigation with page indicator
        current_page = get_state('current_page', 'demo_setup')
        page_names = {
            'demo_setup': '📝 Setup',
            'scenario_review': '👀 Review',
            'files_preview': '📁 Files',
            'repository_success': '🎯 Repository',
            'dbt_cloud_provisioning': '🏗️ Provision',
            'final_success': '✅ Success'
        }

        st.markdown(f"**Current:** {page_names.get(current_page, 'Setup')}")

        st.divider()

        # Configuration section - expanded by default if incomplete
        config_expanded = not status['all_ready']
        with st.expander("⚙️ Configuration", expanded=config_expanded):
            render_configuration_sidebar()

        st.divider()

        # Help section
        with st.expander("❓ Quick Help", expanded=False):
            st.markdown("""
            **Workflow:**
            1. Fill demo context
            2. Configure APIs (sidebar)
            3. Generate scenario
            4. Review & confirm
            5. Push to GitHub

            **Tips:**
            - Use .env for default values
            - Gray text = using .env
            - Edit button = change keys
            """)

        # About section
        with st.expander("ℹ️ About", expanded=False):
            st.markdown("""
            **dbt Demo Automation**

            v0.1.0

            Rapidly create customized dbt Cloud demos using AI.

            Built for dbt Labs SAs
            """)

    # Main content area - route to appropriate page
    current_page = get_state('current_page', 'demo_setup')

    if current_page == 'scenario_review':
        render_scenario_review_page()
    elif current_page == 'files_preview':
        render_files_preview_page()
    elif current_page == 'repository_success':
        render_repository_success_page()
    elif current_page == 'dbt_cloud_provisioning':
        render_dbt_cloud_provisioning_page()
    elif current_page == 'final_success':
        render_final_success_page()
    else:
        render_demo_setup_page()

    # Footer
    st.divider()
    st.caption(
        "dbt Cloud Demo Automation Tool v0.1.0 | "
        "Built for dbt Labs Solutions Architects | "
        "[Documentation](docs/SETUP_GUIDE.md)"
    )


if __name__ == "__main__":
    main()
