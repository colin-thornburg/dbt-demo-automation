"""
dbt Cloud Provisioning Page
Terraform-based provisioning of dbt Cloud projects
"""

import streamlit as st
from pathlib import Path
import time
from typing import Optional, Dict
from src.ui.session_state import get_state, set_state
from src.config.settings import load_config
from src.terraform_integration import (
    generate_terraform_config,
    write_terraform_files,
    apply_terraform_config,
    TerraformExecutor
)


def render_snowflake_config_form() -> Dict[str, str]:
    """
    Render Snowflake configuration form with .env defaults
    
    Returns:
        Dictionary of Snowflake configuration
    """
    st.subheader("Snowflake Configuration")
    
    app_config = load_config()
    
    col1, col2 = st.columns(2)
    
    with col1:
        account = st.text_input(
            "Snowflake Account",
            value=app_config.snowflake_account or "",
            help="Modern format: ORGNAME-ACCOUNTNAME (e.g., CMVGRNF-ZNA84829) or Legacy: account.region (e.g., xy12345.us-west-2)",
            placeholder="CMVGRNF-ZNA84829 or xy12345.us-west-2"
        )
        
        database = st.text_input(
            "Database",
            value=app_config.snowflake_database or "",
            help="Database name for dbt",
            placeholder="DBT_DEMO_DB"
        )
        
        warehouse = st.text_input(
            "Warehouse",
            value=app_config.snowflake_warehouse or "",
            help="Warehouse name for dbt",
            placeholder="DBT_DEMO_WH"
        )
        
        role = st.text_input(
            "Role",
            value=app_config.snowflake_role or "",
            help="Role for dbt operations",
            placeholder="DBT_DEMO_ROLE"
        )
    
    with col2:
        user = st.text_input(
            "User",
            value=app_config.snowflake_user or "",
            help="Snowflake username",
            placeholder="DBT_DEMO_USER"
        )
        
        password = st.text_input(
            "Password",
            value=app_config.snowflake_password or "",
            type="password",
            help="Snowflake password"
        )
        
        schema = st.text_input(
            "Schema",
            value=app_config.snowflake_schema or "analytics",
            help="Default schema for models",
            placeholder="analytics"
        )
    
    # Show status
    has_env_defaults = bool(app_config.snowflake_account)
    if has_env_defaults:
        st.info("ℹ️ Using defaults from .env file. You can override them above.")
    else:
        st.warning("⚠️ No Snowflake configuration found in .env. Please enter credentials above.")
    
    return {
        'account': account,
        'database': database,
        'warehouse': warehouse,
        'role': role,
        'user': user,
        'password': password,
        'schema': schema
    }


def validate_snowflake_config(config: Dict[str, str]) -> tuple[bool, Optional[str]]:
    """
    Validate Snowflake configuration
    
    Args:
        config: Snowflake configuration dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['account', 'database', 'warehouse', 'role', 'user', 'password']
    
    for field in required_fields:
        if not config.get(field):
            return False, f"Missing required field: {field}"
    
    # Validate account format (accept both legacy and modern formats)
    # Legacy format: xy12345.us-west-2 or xy12345.us-west-2.aws
    # Modern format: ORGNAME-ACCOUNTNAME (e.g., CMVGRNF-ZNA84829)
    account = config['account']
    
    # Basic check: should have either a dot (legacy) or hyphen (modern)
    if '.' not in account and '-' not in account:
        return False, "Account should be in format: 'ORGNAME-ACCOUNTNAME' (modern) or 'account.region' (legacy)"
    
    return True, None


def render_provision_preview():
    """Render preview of what will be provisioned"""
    st.subheader("What Will Be Created")
    
    scenario = get_state('demo_scenario')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**dbt Cloud Resources**")
        st.markdown(f"""
        - 🏗️ Project: `{scenario.company_name} Demo`
        - 📦 Repository Connection
        - 🔗 Snowflake Connection
        - 👨‍💻 Development Environment
        - 🚀 Production Environment
        - 🔐 Separate credentials (dev & prod)
        """)
    
    with col2:
        st.markdown("**Jobs & Automation**")
        st.markdown("""
        - 📅 Production Job (daily at 6 AM)
        - 🏗️ Runs `dbt build` command
        - 📊 Generates documentation
        - ✨ Creates all artifacts for demo
        """)
    
    st.info("""
    **What happens next:**
    1. Terraform will create these resources in your dbt Cloud account
    2. Your GitHub repository will be connected
    3. Snowflake connection will be configured and tested
    4. You'll get a direct link to your new project
    
    This typically takes 2-3 minutes.
    """)


def run_terraform_provisioning(
    snowflake_config: Dict[str, str]
) -> Dict:
    """
    Execute Terraform provisioning with progress updates
    
    Args:
        snowflake_config: Snowflake configuration
    
    Returns:
        Dictionary with results
    """
    # Get required data from session state
    scenario = get_state('demo_scenario')
    repo_info = get_state('repository_info')
    app_config = load_config()
    
    # Progress container
    progress_container = st.container()
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # Output log container
    with st.expander("🔍 View Terraform Output (Live)", expanded=False):
        output_log = st.empty()
    
    try:
        # Step 1: Generate Terraform configuration
        status_text.text("⚙️ Generating Terraform configuration...")
        progress_bar.progress(10)
        
        # Handle SecretStr vs plain string for tokens
        dbt_token = app_config.dbt_cloud_service_token
        if hasattr(dbt_token, 'get_secret_value'):
            dbt_token = dbt_token.get_secret_value()
        
        # Construct proper host URL for Terraform provider
        # Terraform provider expects: https://host.com/api
        dbt_host = app_config.default_dbt_cloud_host
        if not dbt_host.startswith('http'):
            dbt_host = f"https://{dbt_host}"
        if not dbt_host.endswith('/api'):
            dbt_host = f"{dbt_host}/api"
        
        config = generate_terraform_config(
            scenario=scenario,
            github_repo_url=repo_info['repo_url'],
            dbt_cloud_account_id=app_config.default_dbt_account_id,
            dbt_cloud_token=dbt_token,
            dbt_cloud_host_url=dbt_host,
            github_installation_id=app_config.github_app_installation_id,
            snowflake_account=snowflake_config['account'],
            snowflake_database=snowflake_config['database'],
            snowflake_warehouse=snowflake_config['warehouse'],
            snowflake_role=snowflake_config['role'],
            snowflake_user=snowflake_config['user'],
            snowflake_password=snowflake_config['password'],
            snowflake_schema=snowflake_config.get('schema', 'analytics')
        )
        
        progress_bar.progress(20)
        
        # Step 2: Write Terraform files
        status_text.text("📝 Writing Terraform files...")
        terraform_dir = Path("terraform")
        write_terraform_files(config, terraform_dir)
        progress_bar.progress(30)
        
        # Step 3: Terraform init
        status_text.text("🔧 Initializing Terraform...")
        executor = TerraformExecutor(terraform_dir)
        init_result = executor.init()
        
        if not init_result.success:
            return {
                'success': False,
                'error': f"Terraform init failed: {init_result.stderr}",
                'stage': 'init'
            }
        
        progress_bar.progress(45)
        
        # Step 4: Terraform validate
        status_text.text("✅ Validating configuration...")
        validate_result = executor.validate()
        
        if not validate_result.success:
            return {
                'success': False,
                'error': f"Validation failed: {validate_result.stderr}",
                'stage': 'validate'
            }
        
        progress_bar.progress(55)
        
        # Step 5: Terraform plan
        status_text.text("📋 Creating execution plan...")
        plan_result = executor.plan()
        
        if not plan_result.success:
            # Check if it's a lock error
            if 'state lock' in plan_result.stderr.lower():
                # Try to remove the lock file and retry once
                lock_file = terraform_dir / '.terraform.tfstate.lock.info'
                if lock_file.exists():
                    lock_file.unlink()
                    status_text.text("🔓 Removing stale lock and retrying...")
                    plan_result = executor.plan()
                    if not plan_result.success:
                        return {
                            'success': False,
                            'error': f"Planning failed after removing lock: {plan_result.stderr}",
                            'stage': 'plan'
                        }
                else:
                    return {
                        'success': False,
                        'error': f"State lock error (lock file not found): {plan_result.stderr}",
                        'stage': 'plan'
                    }
            else:
                return {
                    'success': False,
                    'error': f"Planning failed: {plan_result.stderr}",
                    'stage': 'plan'
                }
        
        progress_bar.progress(65)
        
        # Step 6: Terraform apply with detailed progress
        status_text.text("🚀 Starting provisioning... (this may take 2-3 minutes)")
        
        # Resource creation steps to show
        resources_to_create = [
            ("dbtcloud_project", "🏗️ Creating dbt Cloud project...", 68),
            ("dbtcloud_repository", "📦 Connecting GitHub repository...", 72),
            ("dbtcloud_connection", "🔗 Configuring Snowflake connection...", 76),
            ("dbtcloud_snowflake_credential", "🔐 Setting up credentials...", 80),
            ("dbtcloud_environment", "👨‍💻 Creating development environment...", 84),
            ("dbtcloud_environment", "🚀 Creating production environment...", 88),
            ("dbtcloud_job", "📅 Configuring production job...", 92)
        ]
        
        # Always auto-approve when running from UI (user already clicked provision button)
        # Start the apply
        import subprocess
        import threading
        
        cmd = ['terraform', 'apply', '-auto-approve']
        
        process = subprocess.Popen(
            cmd,
            cwd=terraform_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Track which resources we've created
        created_resources = set()
        current_step = 0
        
        # Read output line by line
        output_lines = []
        for line in process.stdout:
            output_lines.append(line)
            line_lower = line.lower()
            
            # Update live output log
            output_log.code(''.join(output_lines[-30:]))  # Show last 30 lines
            
            # Detect resource creation
            if 'creating...' in line_lower or 'creation complete' in line_lower:
                for resource_type, message, progress in resources_to_create:
                    if resource_type in line and resource_type not in created_resources:
                        status_text.text(message)
                        progress_bar.progress(progress)
                        created_resources.add(resource_type)
                        break
        
        # Wait for completion
        return_code = process.wait()
        
        if return_code != 0:
            return {
                'success': False,
                'error': ''.join(output_lines[-50:]),  # Last 50 lines
                'stage': 'apply'
            }
        
        progress_bar.progress(90)
        
        # Step 7: Get outputs
        status_text.text("📊 Retrieving project information...")
        output_result = executor.output()
        
        progress_bar.progress(92)
        
        # Step 7.5: Wait briefly and force repository metadata refresh via API
        status_text.text("⏳ Waiting for GitHub App to recognize repository (30s)...")
        
        try:
            import time
            from src.dbt_cloud import DbtCloudApiClient
            
            # Wait 30 seconds for GitHub App propagation
            time.sleep(30)
            
            progress_bar.progress(93)
            status_text.text("🔄 Refreshing repository metadata via dbt Cloud API...")
            
            # Get project details to extract repository info
            project_id = str(output_result.outputs.get('project_id', ''))
            repo_url = repo_info.get('repo_url', '')
            
            # Create API client
            client = DbtCloudApiClient(
                account_id=app_config.default_dbt_account_id,
                api_token=dbt_token,
                host=app_config.default_dbt_cloud_host
            )
            
            # Get current project state
            project_data = client.get_project(project_id)
            repository = project_data.get('data', {}).get('repository', {})
            
            if repository and repository.get('id'):
                # Force update the repository via API to trigger metadata refresh
                client.update_project_repository(
                    project_id=project_id,
                    repository_id=repository['id'],
                    remote_url=repo_url,
                    github_installation_id=int(app_config.github_app_installation_id)
                )
                
                status_text.text("✅ Repository metadata refresh triggered!")
                
                # Wait another 10 seconds for the refresh to complete
                time.sleep(10)
            else:
                st.warning("⚠️ Could not find repository to refresh")
                
        except Exception as e:
            # Don't fail provisioning if this doesn't work
            st.warning(f"⚠️ Repository refresh failed: {e}")
            st.info("The initial job run may fail. Please wait 2-3 minutes and manually re-run the job.")
        
        progress_bar.progress(95)
        
        # Step 8: Trigger initial job run (if production job was created)
        job_triggered = False
        job_run_info = None
        
        if output_result.outputs and output_result.outputs.get('production_job_id'):
            status_text.text("🚀 Triggering initial production build...")
            
            try:
                from src.dbt_cloud import trigger_initial_job_run
                
                job_run_info = trigger_initial_job_run(
                    account_id=app_config.default_dbt_account_id,
                    api_token=dbt_token,
                    job_id=str(output_result.outputs['production_job_id']),
                    wait_for_completion=False,  # Don't wait, let it run in background
                    host=app_config.default_dbt_cloud_host
                )
                
                job_triggered = True
                status_text.text("✅ Production job triggered! Building models and artifacts...")
                
            except Exception as e:
                # Don't fail the whole provisioning if job trigger fails
                job_run_info = {'error': str(e), 'status': 'failed'}
        
        progress_bar.progress(100)
        status_text.text("✅ Provisioning complete!")
        
        return {
            'success': True,
            'outputs': output_result.outputs if output_result.success else {},
            'apply_output': ''.join(output_lines),
            'job_triggered': job_triggered,
            'job_run_info': job_run_info
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'stage': 'exception'
        }


def check_terraform_installed() -> bool:
    """Check if Terraform CLI is installed"""
    import shutil
    return shutil.which('terraform') is not None


def render_dbt_cloud_provisioning_page():
    """Main page renderer for dbt Cloud provisioning"""
    
    st.title("🏗️ dbt Cloud Provisioning")
    
    # Check if Terraform is installed
    if not check_terraform_installed():
        st.error("❌ Terraform CLI is not installed")
        st.markdown("""
        ### Install Terraform
        
        Terraform is required for automated dbt Cloud provisioning.
        
        **macOS:**
        ```bash
        brew install terraform
        ```
        
        **Linux (Ubuntu/Debian):**
        ```bash
        wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt update && sudo apt install terraform
        ```
        
        **Windows:**
        ```bash
        choco install terraform
        ```
        
        **Or download from:** https://www.terraform.io/downloads
        
        After installation, restart your terminal and this app.
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Repository"):
                set_state('current_page', 'repository_success')
                st.rerun()
        with col2:
            if st.button("Skip to Success"):
                set_state('current_page', 'final_success')
                st.rerun()
        return
    
    # Check prerequisites
    repo_info = get_state('repository_info')
    if not repo_info:
        st.error("❌ No repository information found. Please create a repository first.")
        if st.button("← Back to Demo Setup"):
            set_state('current_page', 'demo_setup')
            st.rerun()
        return
    
    # Check if already provisioned
    provisioning_result = get_state('provisioning_result')
    if provisioning_result and provisioning_result.get('success'):
        st.success("✅ dbt Cloud project already provisioned!")
        
        outputs = provisioning_result.get('outputs', {})
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(f"""
            **Project URL:** {outputs.get('project_url', 'N/A')}
            
            **Project ID:** {outputs.get('project_id', 'N/A')}
            """)
        
        with col2:
            if st.button("🎉 View Success Page", type="primary", use_container_width=True):
                set_state('current_page', 'final_success')
                st.rerun()
            
            if st.button("🔄 Provision Another Project"):
                set_state('provisioning_result', None)
                st.rerun()
        
        return
    
    # Show repository info
    st.success(f"""
    ✅ **Repository Created:** [{repo_info['repo_name']}]({repo_info['repo_url']})
    
    Now let's provision your dbt Cloud project!
    """)
    
    st.divider()
    
    # Snowflake Configuration
    with st.form("snowflake_config_form", clear_on_submit=False):
        snowflake_config = render_snowflake_config_form()
        
        st.divider()
        
        # Preview
        render_provision_preview()
        
        st.divider()
        
        # Advanced options
        with st.expander("⚙️ Advanced Options", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                dev_threads = st.number_input(
                    "Development Threads",
                    min_value=1,
                    max_value=16,
                    value=4,
                    help="Number of threads for development environment"
                )
            
            with col2:
                prod_threads = st.number_input(
                    "Production Threads",
                    min_value=1,
                    max_value=32,
                    value=8,
                    help="Number of threads for production environment"
                )
            
            enable_prod_job = st.checkbox(
                "Enable Production Job",
                value=True,
                help="Create a daily scheduled production job"
            )
            
            if enable_prod_job:
                cron_schedule = st.text_input(
                    "Production Job Schedule (Cron)",
                    value="0 6 * * *",
                    help="Cron expression for job schedule. Default: 6 AM daily"
                )
        
        # Submit button
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            submit_button = st.form_submit_button(
                "🚀 Provision dbt Cloud Project",
                type="primary",
                use_container_width=True
            )
    
    # Handle form submission
    if submit_button:
        # Store config in session state for reliability
        set_state('_temp_snowflake_config', snowflake_config)
        # Validate configuration
        is_valid, error_msg = validate_snowflake_config(snowflake_config)
        
        if not is_valid:
            st.error(f"❌ Configuration Error: {error_msg}")
            return
        
        # Run provisioning
        with st.spinner("Provisioning dbt Cloud project..."):
            result = run_terraform_provisioning(snowflake_config)
        
        if result['success']:
            st.success("🎉 dbt Cloud project provisioned successfully!")
            
            # Store result in session state
            set_state('provisioning_result', result)
            
            # Show outputs
            outputs = result.get('outputs', {})
            
            st.balloons()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🎯 Your dbt Cloud Project")
                st.info(f"""
                **Project Name:** {outputs.get('project_name', 'N/A')}
                
                **Project ID:** {outputs.get('project_id', 'N/A')}
                
                **Project URL:** {outputs.get('project_url', 'N/A')}
                """)
            
            with col2:
                st.markdown("### 📊 Environment Details")
                st.info(f"""
                **Dev Environment ID:** {outputs.get('dev_environment_id', 'N/A')}
                
                **Prod Environment ID:** {outputs.get('prod_environment_id', 'N/A')}
                
                **Production Job ID:** {outputs.get('production_job_id', 'N/A')}
                """)
            
            # Show job run status if triggered
            if result.get('job_triggered'):
                job_info = result.get('job_run_info', {})
                
                if job_info.get('status') == 'triggered':
                    st.success(f"""
                    ### 🏗️ Initial Build Started!
                    
                    The production job has been triggered and is now running in the background.
                    
                    **Run ID:** {job_info.get('run_id', 'N/A')}
                    
                    This will:
                    - Load seed data
                    - Build all models
                    - Run tests
                    - Generate documentation
                    - Create artifacts for your demo
                    
                    The build typically takes 2-5 minutes depending on your data volume.
                    """)
                    
                    if job_info.get('run_url'):
                        st.markdown(f"[📊 View Run Progress in dbt Cloud]({job_info['run_url']})")
                elif job_info.get('error'):
                    st.warning(f"""
                    ⚠️ **Job trigger failed:** {job_info.get('error')}
                    
                    You can manually trigger the job from dbt Cloud.
                    """)
            
            st.divider()
            
            # Next steps
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### 🎯 Next Steps")
                
                if result.get('job_triggered'):
                    st.markdown(f"""
                    1. **Monitor the build:** [View run progress in dbt Cloud]({outputs.get('project_url', '#')})
                    2. **Wait for completion:** The initial build is running (2-5 minutes)
                    3. **Open IDE:** Once complete, [open the IDE]({outputs.get('project_url', '#')}/develop)
                    4. **Explore results:**
                       - View the lineage graph
                       - Check documentation
                       - Review test results
                    5. **Start demoing!** All artifacts are ready
                    """)
                else:
                    st.markdown(f"""
                    1. **Open dbt Cloud IDE:** [Click here]({outputs.get('project_url', '#')})
                    2. **Initialize your project:** The repository is already connected
                    3. **Run your first build:**
                       ```bash
                       dbt seed
                       dbt run
                       dbt test
                       ```
                    4. **Review results** in the lineage and documentation tabs
                    """)
            
            with col2:
                if st.button("🎉 Continue to Success Page", type="primary", use_container_width=True):
                    set_state('current_page', 'final_success')
                    st.rerun()
        
        else:
            st.error(f"❌ Provisioning failed at stage: {result.get('stage', 'unknown')}")
            
            with st.expander("🔍 Error Details", expanded=True):
                st.code(result.get('error', 'Unknown error'))
            
            st.markdown("### 🛠️ Troubleshooting")
            st.markdown("""
            Common issues:
            - **Invalid Snowflake credentials:** Verify username/password
            - **GitHub App not installed:** Install dbt Cloud GitHub App
            - **Insufficient permissions:** Check dbt Cloud token permissions
            - **Repository already connected:** Use a different repository
            
            See the [Terraform Setup Guide](docs/TERRAFORM_SETUP.md#troubleshooting) for more help.
            """)
            
            if st.button("🔄 Try Again"):
                st.rerun()
    
    # Bottom navigation
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Back to Files"):
            set_state('current_page', 'repository_success')
            st.rerun()
    
    with col3:
        if st.button("Skip Provisioning →"):
            st.warning("⚠️ You'll need to manually set up dbt Cloud project")
            time.sleep(2)
            set_state('current_page', 'final_success')
            st.rerun()

