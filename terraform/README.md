# Terraform Configuration for dbt Cloud

This directory contains Terraform configuration for automatically provisioning dbt Cloud projects with Snowflake connections.

## Quick Start

### 1. Install Terraform

```bash
# macOS
brew install terraform

# Verify
terraform version
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Create Configuration

Copy the template and fill in your values:

```bash
cp terraform.tfvars.template terraform.tfvars
# Edit terraform.tfvars with your values
```

### 4. Plan and Apply

```bash
# Preview changes
terraform plan

# Apply changes
terraform apply
```

## Files

- **`providers.tf`**: Terraform and provider configuration
- **`variables.tf`**: Input variable definitions
- **`main.tf`**: Main resource definitions (project, environments, jobs)
- **`outputs.tf`**: Output values (project ID, URLs, etc.)
- **`terraform.tfvars.template`**: Template for your configuration
- **`terraform.tfvars`**: Your actual configuration (gitignored)

## Resources Created

This configuration creates:

1. **dbt Cloud Project**: New project in your account
2. **GitHub Repository Connection**: Links your repo to dbt Cloud
3. **Snowflake Connection**: Database connection configuration
4. **Development Environment**: For development work
5. **Production Environment**: For production deployments
6. **Production Job**: Daily scheduled run (optional)
7. **CI Job**: Runs on pull requests
8. **Credentials**: Separate dev and prod Snowflake credentials

## Configuration Variables

### Required

- `dbt_cloud_account_id`: Your dbt Cloud account ID
- `dbt_cloud_token`: API token with project creation permissions
- `github_repo_url`: HTTPS URL of your GitHub repository
- `github_installation_id`: GitHub App installation ID for dbt Cloud
- `snowflake_account`: Snowflake account identifier
- `snowflake_database`: Database name
- `snowflake_warehouse`: Warehouse name
- `snowflake_role`: Role for dbt
- `snowflake_user`: Username
- `snowflake_password`: Password

### Optional

- `dbt_cloud_host_url`: API host (default: https://cloud.getdbt.com/api)
- `project_name`: Custom project name
- `project_description`: Project description
- `snowflake_schema`: Default schema (default: analytics)
- `dev_threads`: Dev environment threads (default: 4)
- `prod_threads`: Prod environment threads (default: 8)
- `enable_production_job`: Create production job (default: true)
- `production_job_schedule_cron`: Cron schedule (default: "0 6 * * *")
- `enable_semantic_layer`: Enable semantic layer (default: false)

## Outputs

After applying, you'll get:

```bash
terraform output
```

Example outputs:
- `project_id`: The ID of the created project
- `project_url`: Direct link to the project in dbt Cloud
- `dev_environment_id`: Development environment ID
- `prod_environment_id`: Production environment ID
- `production_job_id`: Production job ID
- `ci_job_id`: CI job ID

## Examples

### Basic Usage

```bash
# Initialize
terraform init

# See what will be created
terraform plan

# Create resources
terraform apply

# View outputs
terraform output project_url
```

### Using Variables from Environment

```bash
export TF_VAR_dbt_cloud_token="dbtc_xxxxx"
export TF_VAR_snowflake_password="xxxxx"
terraform apply
```

### Programmatic Usage (Python)

```python
from pathlib import Path
from src.terraform_integration import (
    generate_terraform_config,
    write_terraform_files,
    apply_terraform_config
)

# Generate configuration
config = generate_terraform_config(
    scenario=demo_scenario,
    github_repo_url="https://github.com/user/repo",
    dbt_cloud_account_id="123456",
    dbt_cloud_token="dbtc_xxxxx",
    github_installation_id="12345678",
    snowflake_account="xy12345.us-east-1",
    snowflake_database="DEMO_DB",
    snowflake_warehouse="DEMO_WH",
    snowflake_role="DBT_ROLE",
    snowflake_user="DBT_USER",
    snowflake_password="password"
)

# Write configuration files
terraform_dir = Path("terraform")
write_terraform_files(config, terraform_dir)

# Apply configuration
results = apply_terraform_config(
    terraform_dir=terraform_dir,
    auto_approve=True
)

# Check results
if results['apply'].success:
    print(f"✅ Project created: {results['output'].outputs['project_url']}")
else:
    print(f"❌ Error: {results['apply'].stderr}")
```

## Cleanup

To remove all created resources:

```bash
terraform destroy
```

**Warning**: This will delete your dbt Cloud project and all associated resources!

## Security Notes

1. **Never commit `terraform.tfvars`** - It contains sensitive credentials
2. **Use secure storage for state files** - Consider remote state with encryption
3. **Rotate credentials regularly** - Update Snowflake passwords and API tokens
4. **Use least-privilege tokens** - Only grant necessary permissions

## Troubleshooting

### Common Issues

**Invalid GitHub Installation ID**
```
Error: github_installation_id not found
```
Solution: Verify the GitHub App is installed and you have the correct installation ID

**Snowflake Connection Failed**
```
Error: Invalid Snowflake credentials
```
Solution: Test credentials with SnowSQL or Snowflake UI first

**Insufficient Permissions**
```
Error: User does not have permission to create projects
```
Solution: Ensure your dbt Cloud token has Account Admin or Project Creator permissions

### Debug Mode

Enable verbose logging:
```bash
export TF_LOG=DEBUG
terraform apply
```

## Additional Documentation

For detailed setup instructions, see:
- [TERRAFORM_SETUP.md](../docs/TERRAFORM_SETUP.md): Complete setup guide
- [SETUP_GUIDE.md](../docs/SETUP_GUIDE.md): Overall project setup

## Resources

- [dbt Cloud Terraform Provider](https://registry.terraform.io/providers/dbt-labs/dbtcloud/latest/docs)
- [Terraform Documentation](https://www.terraform.io/docs)
- [dbt Cloud API Docs](https://docs.getdbt.com/dbt-cloud/api-v2)








