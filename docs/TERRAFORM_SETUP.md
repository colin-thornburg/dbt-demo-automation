# Terraform Setup Guide

This guide explains how to use Terraform to automatically provision dbt Cloud projects after creating a GitHub repository with your demo content.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Initial Setup](#initial-setup)
4. [Configuration](#configuration)
5. [Running Terraform](#running-terraform)
6. [Integration with Demo Automation](#integration-with-demo-automation)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The Terraform integration automates the creation of:

- **dbt Cloud Project**: A new project in your dbt Cloud account
- **Repository Connection**: Links your GitHub repository to dbt Cloud
- **Snowflake Connection**: Configures Snowflake as the data warehouse
- **Environments**: Development and Production environments
- **Jobs**: Production job (daily run) and CI job (runs on PRs)
- **Credentials**: Separate credentials for dev and prod environments

### Architecture

```
GitHub Repository (your demo)
        ↓
    Terraform
        ↓
    ┌─────────────────┐
    │  dbt Cloud      │
    │                 │
    │  - Project      │
    │  - Repo Link    │
    │  - Environments │
    │  - Jobs         │
    └─────────────────┘
        ↓
    Snowflake
```

---

## Prerequisites

### 1. Terraform Installation

Install Terraform CLI (version 1.0 or higher):

```bash
# macOS
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Linux
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# Verify installation
terraform version
```

### 2. dbt Cloud Account

You need:
- **Account ID**: Found at Settings → Profile
- **Service Token or PAT**: Created at Settings → API Tokens
  - Required permissions: `Account Admin` or `Project Creator`

### 3. GitHub App Installation ID

To connect repositories to dbt Cloud:

1. Go to https://github.com/settings/installations
2. Find "dbt Cloud" in your installed apps
3. Click "Configure"
4. The Installation ID is in the URL:
   ```
   https://github.com/settings/installations/[INSTALLATION_ID]
   ```
5. Save this ID for configuration

**Note**: If you don't see dbt Cloud installed:
1. Install it from: https://github.com/apps/dbt-cloud
2. Grant access to the repositories you want to use

### 4. Snowflake Setup

Ensure you have:
- Snowflake account with appropriate permissions
- Database, warehouse, and role created for dbt
- User credentials with access to the database

Example setup SQL:

```sql
-- Create role
CREATE ROLE IF NOT EXISTS DBT_DEMO_ROLE;

-- Create warehouse
CREATE WAREHOUSE IF NOT EXISTS DBT_DEMO_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

-- Create database
CREATE DATABASE IF NOT EXISTS DBT_DEMO_DB;

-- Grant permissions
GRANT USAGE ON WAREHOUSE DBT_DEMO_WH TO ROLE DBT_DEMO_ROLE;
GRANT CREATE DATABASE ON ACCOUNT TO ROLE DBT_DEMO_ROLE;
GRANT USAGE ON DATABASE DBT_DEMO_DB TO ROLE DBT_DEMO_ROLE;
GRANT CREATE SCHEMA ON DATABASE DBT_DEMO_DB TO ROLE DBT_DEMO_ROLE;

-- Create user
CREATE USER IF NOT EXISTS DBT_DEMO_USER
  PASSWORD = 'your_secure_password'
  DEFAULT_ROLE = DBT_DEMO_ROLE
  DEFAULT_WAREHOUSE = DBT_DEMO_WH;

-- Grant role to user
GRANT ROLE DBT_DEMO_ROLE TO USER DBT_DEMO_USER;
```

---

## Initial Setup

### Step 1: Configure Environment Variables

Update your `.env` file with the required Terraform and Snowflake variables:

```bash
# dbt Cloud
DEFAULT_DBT_ACCOUNT_ID=123456
DBT_CLOUD_SERVICE_TOKEN=dbtc_xxxxx

# GitHub App
GITHUB_APP_INSTALLATION_ID=12345678

# Snowflake
SNOWFLAKE_ACCOUNT=xy12345.us-east-1
SNOWFLAKE_DATABASE=DBT_DEMO_DB
SNOWFLAKE_WAREHOUSE=DBT_DEMO_WH
SNOWFLAKE_ROLE=DBT_DEMO_ROLE
SNOWFLAKE_USER=DBT_DEMO_USER
SNOWFLAKE_PASSWORD=your_secure_password
SNOWFLAKE_SCHEMA=analytics

# Terraform
TERRAFORM_AUTO_APPROVE=false
```

### Step 2: Initialize Terraform

Navigate to the terraform directory and initialize:

```bash
cd terraform
terraform init
```

This downloads the dbt Cloud Terraform provider.

---

## Configuration

### Terraform Variables

The main configuration happens in `terraform.tfvars` (auto-generated) or manually:

```hcl
# dbt Cloud Configuration
dbt_cloud_account_id = "123456"
dbt_cloud_token      = "dbtc_xxxxx"
dbt_cloud_host_url   = "https://cloud.getdbt.com/api"

# Project Configuration
project_name        = "Acme Corp Demo"
project_description = "Demo project for Acme Corp"

# Repository Configuration
github_repo_url        = "https://github.com/username/demo-repo"
github_installation_id = "12345678"

# Snowflake Configuration
snowflake_account   = "xy12345.us-east-1"
snowflake_database  = "DBT_DEMO_DB"
snowflake_warehouse = "DBT_DEMO_WH"
snowflake_role      = "DBT_DEMO_ROLE"
snowflake_user      = "DBT_DEMO_USER"
snowflake_password  = "your_password"
snowflake_schema    = "analytics"

# Environment Configuration
dev_threads  = 4
prod_threads = 8

# Job Configuration
enable_production_job        = true
production_job_schedule_cron = "0 6 * * *"  # 6 AM daily

# Semantic Layer
enable_semantic_layer = false
```

### Customizing Resources

You can customize the Terraform configuration by editing files in the `terraform/` directory:

- **`variables.tf`**: Add new variables
- **`main.tf`**: Modify resources or add new ones
- **`outputs.tf`**: Add outputs you want to capture

---

## Running Terraform

### Manual Execution

#### 1. Plan

Preview what Terraform will create:

```bash
cd terraform
terraform plan
```

Review the output to ensure everything looks correct.

#### 2. Apply

Create the resources:

```bash
terraform apply
```

Type `yes` when prompted (or use `-auto-approve` flag for automation).

#### 3. View Outputs

After successful apply:

```bash
terraform output
```

Example output:
```
project_id = "12345"
project_name = "Acme Corp Demo"
project_url = "https://cloud.getdbt.com/deploy/123456/projects/12345"
dev_environment_id = "67890"
prod_environment_id = "67891"
production_job_id = "11111"
ci_job_id = "11112"
```

### Programmatic Execution

Use the Python integration:

```python
from pathlib import Path
from src.terraform_integration import apply_terraform_config

# Run Terraform
terraform_dir = Path("terraform")
results = apply_terraform_config(
    terraform_dir=terraform_dir,
    auto_approve=True  # Use with caution!
)

# Check results
if results['apply'].success:
    outputs = results['output'].outputs
    print(f"Project URL: {outputs['project_url']}")
else:
    print(f"Error: {results['apply'].stderr}")
```

---

## Integration with Demo Automation

### Automatic Workflow

The demo automation tool can automatically:

1. Generate demo scenario
2. Create dbt files
3. Create GitHub repository
4. **Generate Terraform configuration**
5. **Apply Terraform to provision dbt Cloud**

### Planned Integration

A future update will add a new page to the Streamlit UI:

**"dbt Cloud Provisioning" Page**
- Configure Snowflake credentials
- Review Terraform plan
- Apply configuration
- View provisioned project details

### Manual Integration (Current)

After creating a repository:

1. **Generate tfvars file**:

```python
from src.terraform_integration import generate_terraform_config, write_terraform_files
from pathlib import Path

# After repository creation
config = generate_terraform_config(
    scenario=scenario,
    github_repo_url=repo_info['repo_url'],
    dbt_cloud_account_id=dbt_account_id,
    dbt_cloud_token=dbt_token,
    github_installation_id=github_install_id,
    snowflake_account=snowflake_account,
    snowflake_database=snowflake_db,
    snowflake_warehouse=snowflake_wh,
    snowflake_role=snowflake_role,
    snowflake_user=snowflake_user,
    snowflake_password=snowflake_pass
)

# Write configuration
terraform_dir = Path("terraform")
write_terraform_files(config, terraform_dir)
```

2. **Run Terraform**:

```python
from src.terraform_integration import apply_terraform_config

results = apply_terraform_config(
    terraform_dir=terraform_dir,
    auto_approve=False  # Requires manual approval
)
```

---

## Troubleshooting

### Common Issues

#### 1. Provider Authentication Error

**Error**: `Error: Invalid credentials`

**Solution**: Verify your dbt Cloud token:
```bash
# Test token manually
curl -H "Authorization: Token $DBT_CLOUD_SERVICE_TOKEN" \
     https://cloud.getdbt.com/api/v2/accounts/$DBT_CLOUD_ACCOUNT_ID/projects/
```

#### 2. GitHub Installation ID Not Found

**Error**: `Error creating repository: github_installation_id not found`

**Solution**: 
- Verify the GitHub App is installed
- Check the installation ID is correct
- Ensure the app has access to your repositories

#### 3. Snowflake Connection Failed

**Error**: `Error testing connection: Invalid credentials`

**Solution**: Test Snowflake credentials:
```sql
-- Test connection with SnowSQL
snowsql -a xy12345.us-east-1 -u DBT_DEMO_USER -r DBT_DEMO_ROLE
```

#### 4. Repository Already Connected

**Error**: `Error: Repository is already connected to another project`

**Solution**: 
- Check if the repo is already used in dbt Cloud
- Delete the existing connection or use a different repo

#### 5. Insufficient Permissions

**Error**: `Error: User does not have permission to create projects`

**Solution**: Ensure your API token has appropriate permissions:
- Required: `Account Admin` or `Project Creator`
- Check at: Settings → API Tokens

### Debug Mode

Enable verbose Terraform logging:

```bash
export TF_LOG=DEBUG
export TF_LOG_PATH=./terraform-debug.log
terraform apply
```

### State Management

If you need to remove resources:

```bash
# View current state
terraform state list

# Remove specific resource
terraform state rm dbtcloud_job.production_job

# Destroy all resources
terraform destroy
```

**Warning**: `terraform destroy` will delete all provisioned resources in dbt Cloud!

---

## Advanced Topics

### Using Remote State

For team collaboration, use remote state:

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "dbt-demos/demo-project/terraform.tfstate"
    region = "us-east-1"
  }
}
```

### Multiple Environments

Create separate variable files for different environments:

```bash
# Development
terraform apply -var-file="dev.tfvars"

# Staging
terraform apply -var-file="staging.tfvars"

# Production
terraform apply -var-file="prod.tfvars"
```

### Importing Existing Resources

If you have existing dbt Cloud resources:

```bash
# Import project
terraform import dbtcloud_project.demo_project 12345

# Import environment
terraform import dbtcloud_environment.production 67890
```

---

## Next Steps

1. **Review Terraform Configuration**: Familiarize yourself with the files in `terraform/`
2. **Set Up Prerequisites**: Ensure all required accounts and credentials are ready
3. **Run First Deployment**: Try creating a test project
4. **Integrate with Workflow**: Add to your demo automation process

## Resources

- [Terraform dbt Cloud Provider Documentation](https://registry.terraform.io/providers/dbt-labs/dbtcloud/latest/docs)
- [dbt Cloud API Documentation](https://docs.getdbt.com/dbt-cloud/api-v2)
- [Snowflake Documentation](https://docs.snowflake.com/)
- [GitHub Apps Documentation](https://docs.github.com/en/developers/apps)

---

For questions or issues, please refer to the main [SETUP_GUIDE.md](./SETUP_GUIDE.md) or open an issue in the repository.

