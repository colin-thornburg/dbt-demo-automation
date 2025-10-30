# Changelog

## [Unreleased] - 2025-10-30

### Added - dbt Cloud Automation & Repository Sync Fix

#### Major Features
- **dbt Cloud Terraform Integration**: Complete infrastructure-as-code provisioning of dbt Cloud projects
  - Automated creation of projects, environments, connections, and jobs
  - Full Snowflake connection configuration
  - GitHub App integration for repository access
  - Production and development environment setup
  
- **dbt Cloud Provisioning UI**: New Streamlit page for visual Terraform workflow
  - Live progress tracking with status updates
  - Snowflake configuration form with .env defaults
  - Real-time Terraform output display
  - Automatic job triggering after provisioning

- **Repository Metadata Sync**: Solution for GitHub App propagation delay
  - 30-second wait period for GitHub App to recognize new repositories
  - API-based repository metadata refresh via dbt Cloud Admin API
  - Graceful handling of sync timeouts with user guidance

#### New Files
- `src/dbt_cloud/api_client.py` - dbt Cloud API client with job triggering and project management
- `src/terraform_integration/` - Complete Terraform generation and execution module
  - `terraform_generator.py` - Generates .tfvars from demo scenarios
  - `terraform_executor.py` - Executes Terraform commands programmatically
- `src/ui/pages/dbt_cloud_provisioning.py` - UI for Terraform-based provisioning
- `src/ui/pages/final_success.py` - Comprehensive success page with all project links
- `terraform/` - Complete Terraform configuration
  - `main.tf` - Resource definitions (8+ resources)
  - `variables.tf` - Input variable definitions
  - `outputs.tf` - Output values for URLs and IDs
  - `providers.tf` - Provider configuration
  - `terraform.tfvars.template` - Configuration template

#### Documentation
- `TERRAFORM_INTEGRATION_SUMMARY.md` - Complete integration overview
- `INTEGRATION_COMPLETE.md` - Integration milestone documentation
- `docs/TERRAFORM_SETUP.md` - Detailed setup guide
- `docs/TERRAFORM_QUICKSTART.md` - 5-minute quickstart
- `docs/DBT_CLOUD_PROVISIONING_GUIDE.md` - Provisioning workflow guide
- `docs/ENV_VARIABLES_REFERENCE.md` - Complete environment variable reference
- `docs/WORKFLOW_DIAGRAM.md` - Visual workflow documentation

#### Configuration Enhancements
- Added `SnowflakeConfig` class for Snowflake connection settings
- Added `TerraformConfig` class for Terraform operations
- Extended `AppConfig` with Snowflake and Terraform environment variables
- Support for GitHub App installation ID configuration

### Changed
- Updated `requirements.md` and `requirements.txt` with new dependencies
- Enhanced `README.md` with Terraform setup instructions
- Updated `SETUP_GUIDE.md` with Terraform prerequisites
- Modified `.env.example` with Snowflake and Terraform variables
- Improved session state management for multi-page provisioning flow

### Fixed
- **Critical**: Resolved dbt Cloud job clone failures due to GitHub App propagation delay
  - Root cause: GitHub Apps take 30-60 seconds to recognize newly created repositories
  - Solution: Added wait period + API-based metadata refresh before job trigger
  - Jobs now succeed automatically instead of requiring manual retry
- Fixed `git_provider_webhook` trigger requirement in Terraform job configuration
- Improved error handling and user messaging throughout provisioning flow

### Technical Details

#### Repository Sync Solution
The primary challenge was that dbt Cloud jobs would fail immediately after provisioning with:
```
fatal: repository 'https://github.com/None.git/' not found
```

This occurred because:
1. Terraform creates repository link instantly
2. GitHub App installation takes 30-60s to propagate new repo access
3. dbt Cloud queries GitHub for metadata but gets nothing
4. Repository `full_name` remains `null`, causing clone URL to become `None.git`

Solution implemented:
1. Wait 30 seconds after Terraform apply
2. Call `POST /api/v2/accounts/{id}/projects/{id}/repository/` to force metadata refresh
3. Wait 10 more seconds for refresh to complete
4. Trigger job (now succeeds with proper clone URL)

#### API Integration
- Leverages dbt Cloud Admin API v2 for repository management
- Uses GitHub App authentication (`github_app` clone strategy)
- Supports both manual and programmatic Terraform execution

### Dependencies
- No new Python package dependencies required
- Terraform CLI 1.0+ required for provisioning features

### Migration Notes
- Existing users: Add new environment variables to `.env` (see `.env.example`)
- GitHub App installation ID required for automated provisioning
- Snowflake credentials needed for connection configuration

---

## Previous Changes
See git history for changes prior to this integration.

