"""
Repository Success Page - Show created repository details
"""

import streamlit as st
from src.ui.components import render_page_header, render_info_box
from src.ui.session_state import get_state, set_state


def render_repository_success_page():
    """
    Main render function for the Repository Success page
    """
    render_page_header(
        "🎉 Repository Created Successfully!",
        "Your dbt demo project has been created and pushed to GitHub"
    )

    # Get repository info from session state
    repo_info = get_state('repo_info')
    scenario = get_state('demo_scenario')

    if not repo_info:
        render_info_box(
            "No repository information found. Please try creating the repository again.",
            type="warning"
        )
        if st.button("← Back to Files"):
            set_state('current_page', 'files_preview')
            st.rerun()
        return

    # Display success information
    st.success(f"✅ Repository '{repo_info['repo_name']}' has been created and all files have been pushed!")

    # Repository details
    st.subheader("📦 Repository Details")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Repository Name:**")
        st.code(repo_info['repo_name'])

        st.markdown("**Company:**")
        st.code(scenario.company_name)

        st.markdown("**Industry:**")
        st.code(scenario.industry)

    with col2:
        st.markdown("**Repository URL:**")
        st.markdown(f"[{repo_info['repo_url']}]({repo_info['repo_url']})")

        st.markdown("**Clone URL:**")
        st.code(repo_info['clone_url'], language="bash")

        st.markdown("**Visibility:**")
        st.code("Private")

    st.divider()

    # Next steps
    st.subheader("📋 Next Steps")

    st.markdown("""
    ### 1. View Your Repository
    Click the link above to view your repository on GitHub.

    ### 2. dbt Cloud Setup (Manual - Phase 6 Coming Soon)
    For now, you'll need to manually set up dbt Cloud:

    1. Go to [dbt Cloud](https://cloud.getdbt.com/)
    2. Create a new project
    3. Connect your GitHub repository:
       - Use the repository URL above
       - dbt Cloud will detect it's a dbt project
    4. Set up a connection to your warehouse
    5. Run `dbt seed` to load sample data
    6. Run `dbt run` to build models
    7. Run `dbt test` to run tests

    ### 3. Demo Talking Points
    Use the generated README.md in your repository for talking points during the demo!
    """)

    st.divider()

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("View on GitHub", type="primary", use_container_width=True):
            st.markdown(f"[Open Repository]({repo_info['repo_url']})")

    with col2:
        if st.button("← Back to Files", type="secondary", use_container_width=True):
            set_state('current_page', 'files_preview')
            st.rerun()

    with col3:
        if st.button("🔄 New Demo", type="secondary", use_container_width=True):
            # Clear all state and start over
            set_state('current_page', 'demo_setup')
            set_state('demo_scenario', None)
            set_state('generated_files', None)
            set_state('repo_info', None)
            st.rerun()

    st.divider()

    # Quick links
    st.subheader("📚 Quick Links")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        **Repository**
        - [View Repo]({repo_info['repo_url']})
        - [README.md]({repo_info['repo_url']}/blob/main/README.md)
        - [dbt_project.yml]({repo_info['repo_url']}/blob/main/dbt_project.yml)
        """)

    with col2:
        st.markdown(f"""
        **Models**
        - [Staging]({repo_info['repo_url']}/tree/main/models/staging)
        - [Intermediate]({repo_info['repo_url']}/tree/main/models/intermediate)
        - [Marts]({repo_info['repo_url']}/tree/main/models/marts)
        """)

    with col3:
        st.markdown(f"""
        **Data**
        - [Seeds]({repo_info['repo_url']}/tree/main/seeds)
        - [Tests]({repo_info['repo_url']}/tree/main/tests)
        """)

    # Repository summary
    st.divider()
    st.subheader("📊 What Was Created")

    summary = get_state('generated_files').get_summary()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Seed Files", summary['seeds'])
    with col2:
        st.metric("Model Files", summary['models'])
    with col3:
        st.metric("Schema Files", summary['schemas'])
    with col4:
        st.metric("Total Files", summary['total'])

    # Show demo overview
    st.divider()
    st.subheader("📋 Demo Overview")
    st.info(scenario.demo_overview)

    st.markdown("**Business Context:**")
    st.write(scenario.business_context)
