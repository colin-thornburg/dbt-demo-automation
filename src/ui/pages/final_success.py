"""
Final Success Page - Show complete demo setup including dbt Cloud provisioning
"""

import streamlit as st
from src.ui.components import render_page_header
from src.ui.session_state import get_state, set_state


def render_final_success_page():
    """
    Main render function for the Final Success page
    Shows both GitHub repository and dbt Cloud project info
    """
    render_page_header(
        "🎉 Demo Setup Complete!",
        "Your dbt Cloud demo is ready to present"
    )

    # Get all relevant info from session state
    scenario = get_state('demo_scenario')
    repo_info = get_state('repository_info') or get_state('repo_info')
    provisioning_result = get_state('provisioning_result')
    
    if not repo_info:
        st.error("❌ No repository information found.")
        if st.button("← Back to Setup"):
            set_state('current_page', 'demo_setup')
            st.rerun()
        return
    
    # Success banner
    if provisioning_result and provisioning_result.get('success'):
        st.balloons()
        st.success("""
        ### ✅ Complete End-to-End Setup Successful!
        
        Your demo is fully configured and ready to present:
        - ✅ GitHub repository created with dbt project
        - ✅ dbt Cloud project provisioned
        - ✅ Snowflake connection configured
        - ✅ Environments and jobs ready
        """)
    else:
        st.success("""
        ### ✅ GitHub Repository Created!
        
        Your dbt project is ready in GitHub. You can now set up dbt Cloud manually or use Terraform provisioning.
        """)
    
    st.divider()
    
    # Main content - Two columns for GitHub and dbt Cloud
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📦 GitHub Repository")
        
        st.markdown(f"""
        **Repository:** [{repo_info['repo_name']}]({repo_info['repo_url']})
        
        **Company:** {scenario.company_name}
        
        **Industry:** {scenario.industry}
        
        **Visibility:** Private
        """)
        
        if st.button("🔗 Open Repository", type="secondary", use_container_width=True):
            st.markdown(f"[Click here to open]({repo_info['repo_url']})")
        
        # Quick stats
        st.divider()
        summary = get_state('generated_files').get_summary()
        
        st.markdown("**Project Stats:**")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Models", summary['models'])
            st.metric("Seeds", summary['seeds'])
        with col_b:
            st.metric("Schemas", summary['schemas'])
            st.metric("Total Files", summary['total'])
    
    with col2:
        st.markdown("### 🏗️ dbt Cloud Project")
        
        if provisioning_result and provisioning_result.get('success'):
            outputs = provisioning_result.get('outputs', {})
            project_url = outputs.get('project_url', '')
            
            st.markdown(f"""
            **Project:** {outputs.get('project_name', 'N/A')}
            
            **Project ID:** `{outputs.get('project_id', 'N/A')}`
            
            **Status:** ✅ Provisioned and ready
            
            **Connection:** Snowflake configured
            """)
            
            if st.button("🚀 Open dbt Cloud", type="primary", use_container_width=True):
                st.markdown(f"[Click here to open]({project_url})")
            
            # Environment details
            st.divider()
            st.markdown("**Environments:**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.caption("Development")
                st.code(outputs.get('dev_environment_id', 'N/A'))
            with col_b:
                st.caption("Production")
                st.code(outputs.get('prod_environment_id', 'N/A'))
            
            st.markdown("**Jobs:**")
            st.caption("Production Job")
            st.code(outputs.get('production_job_id', 'N/A'))
        else:
            st.info("""
            **Not yet provisioned**
            
            You can:
            - Set up dbt Cloud manually
            - Use Terraform provisioning
            - Go back to provision now
            """)
            
            if st.button("🏗️ Provision Now", type="primary", use_container_width=True):
                set_state('current_page', 'dbt_cloud_provisioning')
                st.rerun()
    
    st.divider()
    
    # Demo Overview
    st.markdown("### 📋 Demo Overview")
    
    with st.expander("View Full Demo Context", expanded=False):
        st.markdown("**Business Context:**")
        st.write(scenario.business_context)
        
        st.markdown("**Demo Overview:**")
        st.info(scenario.demo_overview)
        
        st.markdown("**Key Features:**")
        if hasattr(scenario, 'data_architecture') and scenario.data_architecture:
            st.markdown(f"""
            - **Sources:** {len(scenario.data_architecture.sources)} data sources
            - **Staging Models:** {len(scenario.data_architecture.staging_models)} models
            - **Marts:** {len(scenario.data_architecture.marts)} mart models
            - **Semantic Layer:** {'Enabled' if scenario.include_semantic_layer else 'Disabled'}
            """)
    
    # Next Steps
    st.divider()
    st.markdown("### 🎯 Next Steps")
    
    if provisioning_result and provisioning_result.get('success'):
        outputs = provisioning_result.get('outputs', {})
        project_url = outputs.get('project_url', '')
        
        tab1, tab2, tab3 = st.tabs(["🚀 Get Started", "📊 Demo Flow", "🛠️ Advanced"])
        
        with tab1:
            st.markdown(f"""
            ### Open dbt Cloud IDE
            1. [Open your project]({project_url})
            2. Click **"Develop"** to open the IDE
            3. The repository is already connected
            
            ### Initialize Your Project
            Run these commands in the IDE:
            ```bash
            # Install dependencies
            dbt deps
            
            # Load seed data
            dbt seed
            
            # Build all models
            dbt run
            
            # Run all tests
            dbt test
            
            # Generate documentation
            dbt docs generate
            ```
            
            ### Verify Setup
            - Check the **Lineage** tab to see model relationships
            - Review the **Documentation** for generated docs
            - Verify data in Snowflake
            """)
        
        with tab2:
            st.markdown("""
            ### Suggested Demo Flow
            
            1. **Introduction** (2 min)
               - Show business context from README
               - Explain data architecture
            
            2. **Source Data** (3 min)
               - Show seed files (sample data)
               - Run `dbt seed` to load data
               - Check data in Snowflake
            
            3. **Data Transformation** (5 min)
               - Show staging models (cleaning & standardization)
               - Show intermediate models (business logic)
               - Run `dbt run` to build models
            
            4. **Data Quality** (3 min)
               - Show test definitions
               - Run `dbt test`
               - Show test results
            
            5. **Lineage & Documentation** (3 min)
               - Show DAG in dbt Cloud
               - Explore lineage graph
               - View generated documentation
            
            6. **Production Deployment** (2 min)
               - Show production job configuration
               - Explain scheduling
               - Show CI/CD workflow
            
            7. **Q&A** (5 min)
            """)
        
        with tab3:
            st.markdown(f"""
            ### Advanced Features
            
            **Environment IDs:**
            - Dev: `{outputs.get('dev_environment_id', 'N/A')}`
            - Prod: `{outputs.get('prod_environment_id', 'N/A')}`
            
            **Job ID:**
            - Production: `{outputs.get('production_job_id', 'N/A')}`
            
            **Customize Your Demo:**
            - Modify models in the IDE
            - Add custom tests
            - Configure job schedules
            - Set up Slack notifications
            
            **CI/CD Workflow:**
            1. Create a branch in the IDE
            2. Make changes to models
            3. Commit and push
            4. Open a pull request on GitHub
            5. CI job runs automatically
            6. Review results before merging
            """)
    
    else:
        st.markdown("""
        1. **Set up dbt Cloud** (if not already done)
           - Manually or via Terraform provisioning
        
        2. **Connect repository** to dbt Cloud
           - Use the GitHub URL above
        
        3. **Run initial build:**
           ```bash
           dbt seed
           dbt run
           dbt test
           ```
        
        4. **Start your demo!**
        """)
    
    st.divider()
    
    # Quick Reference
    st.markdown("### 📚 Quick Reference")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        **Repository Links:**
        - [Repository]({repo_info['repo_url']})
        - [README]({repo_info['repo_url']}/blob/main/README.md)
        - [Models]({repo_info['repo_url']}/tree/main/models)
        - [Seeds]({repo_info['repo_url']}/tree/main/seeds)
        """)
    
    with col2:
        if provisioning_result and provisioning_result.get('success'):
            outputs = provisioning_result.get('outputs', {})
            st.markdown(f"""
            **dbt Cloud Links:**
            - [Project]({outputs.get('project_url', '#')})
            - [IDE]({outputs.get('project_url', '#')}/develop)
            - [Jobs]({outputs.get('project_url', '#')}/jobs)
            - [Docs]({outputs.get('project_url', '#')}/docs)
            """)
        else:
            st.markdown("""
            **dbt Cloud:**
            - [dbt Cloud Login](https://cloud.getdbt.com)
            - [Create Project](https://cloud.getdbt.com/projects/new)
            """)
    
    with col3:
        st.markdown("""
        **Documentation:**
        - [dbt Docs](https://docs.getdbt.com/)
        - [Best Practices](https://docs.getdbt.com/best-practices)
        - [Semantic Layer](https://docs.getdbt.com/docs/use-dbt-semantic-layer/dbt-sl)
        """)
    
    st.divider()
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Create Another Demo", type="secondary", use_container_width=True):
            # Clear state and start over
            set_state('current_page', 'demo_setup')
            set_state('demo_scenario', None)
            set_state('generated_files', None)
            set_state('repository_info', None)
            set_state('repo_info', None)
            set_state('provisioning_result', None)
            st.rerun()
    
    with col2:
        if not provisioning_result or not provisioning_result.get('success'):
            if st.button("🏗️ Provision dbt Cloud", type="primary", use_container_width=True):
                set_state('current_page', 'dbt_cloud_provisioning')
                st.rerun()
    
    with col3:
        if st.button("📥 Download Summary", type="secondary", use_container_width=True):
            # Generate summary text
            summary_text = f"""
# Demo Setup Summary

## Project Details
- Company: {scenario.company_name}
- Industry: {scenario.industry}
- Repository: {repo_info['repo_url']}

## GitHub Repository
- Name: {repo_info['repo_name']}
- URL: {repo_info['repo_url']}
- Clone URL: {repo_info.get('clone_url', 'N/A')}

"""
            
            if provisioning_result and provisioning_result.get('success'):
                outputs = provisioning_result.get('outputs', {})
                summary_text += f"""
## dbt Cloud Project
- Project Name: {outputs.get('project_name', 'N/A')}
- Project ID: {outputs.get('project_id', 'N/A')}
- Project URL: {outputs.get('project_url', 'N/A')}
- Dev Environment: {outputs.get('dev_environment_id', 'N/A')}
- Prod Environment: {outputs.get('prod_environment_id', 'N/A')}
- Production Job: {outputs.get('production_job_id', 'N/A')}
"""
            
            summary_text += f"""
## Demo Overview
{scenario.demo_overview}

## Business Context
{scenario.business_context}

## Next Steps
1. Open dbt Cloud IDE
2. Run: dbt seed && dbt run && dbt test
3. Review lineage and documentation
4. Start your demo!
"""
            
            st.download_button(
                label="📄 Download Summary",
                data=summary_text,
                file_name=f"{repo_info['repo_name']}_summary.md",
                mime="text/markdown"
            )

