# Terraform Integration - Summary

## What Was Added

A complete Terraform-based infrastructure-as-code solution for automatically provisioning dbt Cloud projects on Snowflake after repository creation.

## New Files Created

### Terraform Configuration (`terraform/`)
```
terraform/
├── providers.tf                    # Terraform & dbt Cloud provider setup
├── variables.tf                    # All input variables with descriptions
├── main.tf                        # Resource definitions (project, environments, jobs)
├── outputs.tf                     # Output values (URLs, IDs, etc.)
├── terraform.tfvars.template      # Configuration template
├── .gitignore                     # Ignores sensitive files
└── README.md                      # Quick reference guide
```

### Python Integration (`src/terraform_integration/`)
```
src/terraform_integration/
├── __init__.py                    # Module exports
├── terraform_generator.py         # Generates .tfvars from demo scenario
└── terraform_executor.py          # Executes Terraform commands
```

### Documentation (`docs/`)
```
docs/
├── TERRAFORM_SETUP.md             # Complete setup & troubleshooting guide
├── TERRAFORM_QUICKSTART.md        # 5-minute quickstart guide
└── ENV_VARIABLES_REFERENCE.md     # All environment variables documented
```

### Configuration Updates
- **`src/config/settings.py`**: Added `SnowflakeConfig` and `TerraformConfig` classes
- **`README.md`**: Updated with Terraform features and documentation links

## What It Does

### Resources Provisioned

When you run `terraform apply`, it creates:

1. **dbt Cloud Project** - New project in your account
2. **GitHub Repository Connection** - Links repo via GitHub App
3. **Snowflake Connection** - Configures data warehouse
4. **Development Environment** - For dev work in IDE
5. **Production Environment** - For production deployments
6. **Snowflake Credentials** - Separate for dev and prod
7. **Production Job** - Daily scheduled run (6 AM)
8. **CI Job** - Runs on pull requests with deferral

### Infrastructure as Code Benefits

- **Repeatable**: Create identical projects every time
- **Auditable**: Track all infrastructure changes in git
- **Fast**: Provision complete project in ~2 minutes
- **Consistent**: No manual UI clicks, no mistakes
- **Scalable**: Create multiple demo projects easily

## How to Use It

### Option 1: Manual (Traditional)

```bash
# 1. Setup environment variables in .env
vim .env  # Add Snowflake & Terraform vars

# 2. Create Terraform config manually
cd terraform
cp terraform.tfvars.template terraform.tfvars
vim terraform.tfvars  # Fill in your values

# 3. Run Terraform
terraform init
terraform plan
terraform apply
```

### Option 2: Programmatic (Automated)

```python
from pathlib import Path
from src.terraform_integration import (
    generate_terraform_config,
    write_terraform_files,
    apply_terraform_config
)
from src.config.settings import load_config

# After repository creation...
app_config = load_config()

# Generate config from demo scenario
config = generate_terraform_config(
    scenario=demo_scenario,
    github_repo_url=repo_info['repo_url'],
    dbt_cloud_account_id=app_config.default_dbt_account_id,
    dbt_cloud_token=app_config.dbt_cloud_service_token,
    github_installation_id=app_config.github_app_installation_id,
    snowflake_account=app_config.snowflake_account,
    snowflake_database=app_config.snowflake_database,
    snowflake_warehouse=app_config.snowflake_warehouse,
    snowflake_role=app_config.snowflake_role,
    snowflake_user=app_config.snowflake_user,
    snowflake_password=app_config.snowflake_password,
)

# Write files
terraform_dir = Path("terraform")
write_terraform_files(config, terraform_dir)

# Apply
results = apply_terraform_config(
    terraform_dir=terraform_dir,
    auto_approve=True  # Use carefully!
)

# Get project URL
if results['apply'].success:
    project_url = results['output'].outputs['project_url']
    print(f"✅ Project ready: {project_url}")
```

## Required Setup

### 1. Install Terraform

```bash
# macOS
brew install terraform

# Verify
terraform --version
```

### 2. Get GitHub App Installation ID

1. Go to: https://github.com/settings/installations
2. Find "dbt Cloud"
3. Click "Configure"
4. Copy ID from URL: `https://github.com/settings/installations/[ID]`

### 3. Add to .env

```bash
# GitHub App
GITHUB_APP_INSTALLATION_ID=12345678

# Snowflake
SNOWFLAKE_ACCOUNT=xy12345.us-east-1
SNOWFLAKE_DATABASE=DBT_DEMO_DB
SNOWFLAKE_WAREHOUSE=DBT_DEMO_WH
SNOWFLAKE_ROLE=DBT_DEMO_ROLE
SNOWFLAKE_USER=DBT_DEMO_USER
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_SCHEMA=analytics

# Terraform
TERRAFORM_AUTO_APPROVE=false
```

## Workflow Integration

### Current Demo Flow

1. ✅ Generate demo scenario (AI)
2. ✅ Create dbt files
3. ✅ Create GitHub repository
4. **NEW**: Provision dbt Cloud project (Terraform)
5. Ready to demo!

### Future Enhancement

Plan to add a new Streamlit page: **"dbt Cloud Provisioning"**

Features:
- Configure Snowflake credentials in UI
- Preview Terraform plan
- One-click apply
- View provisioned project details
- Direct link to dbt Cloud IDE

## Documentation

### For Users

- **[Quickstart](docs/TERRAFORM_QUICKSTART.md)** - Get started in 5 minutes
- **[Setup Guide](docs/TERRAFORM_SETUP.md)** - Complete documentation
- **[Terraform README](terraform/README.md)** - Configuration reference
- **[Environment Variables](docs/ENV_VARIABLES_REFERENCE.md)** - All variables documented

### For Developers

- **Python Module**: `src/terraform_integration/`
- **Config Models**: `src/config/settings.py` (SnowflakeConfig, TerraformConfig)
- **Terraform Files**: `terraform/*.tf`

## Security Notes

### Secrets Management

✅ **Protected**:
- `terraform.tfvars` is gitignored
- `.env` is gitignored
- Snowflake passwords are marked sensitive
- API tokens are SecretStr types

⚠️ **Important**:
- Never commit `.tfvars` files
- Use `chmod 600 .env`
- Rotate credentials regularly
- Use minimal API token permissions

## Testing

### Validate Configuration

```bash
cd terraform
terraform init
terraform validate
terraform plan  # Should show 8+ resources to create
```

### Test Python Integration

```python
from src.terraform_integration import TerraformConfig

config = TerraformConfig(
    dbt_cloud_account_id="123456",
    dbt_cloud_token="dbtc_test",
    github_repo_url="https://github.com/user/repo",
    github_installation_id="12345678",
    snowflake_account="test.us-east-1",
    snowflake_database="TEST_DB",
    snowflake_warehouse="TEST_WH",
    snowflake_role="TEST_ROLE",
    snowflake_user="test_user",
    snowflake_password="test_pass",
    project_name="Test Project"
)

print(config.model_dump())  # Should validate successfully
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| GitHub Installation ID not found | Install dbt Cloud GitHub App |
| Invalid Snowflake credentials | Test in SnowSQL first |
| Insufficient dbt Cloud permissions | Use Account Admin token |
| Repository already connected | Use different repo or delete existing project |

### Debug Commands

```bash
# Enable Terraform debug logging
export TF_LOG=DEBUG
terraform apply

# Check state
terraform state list

# View specific resource
terraform state show dbtcloud_project.demo_project

# Remove resource from state (if needed)
terraform state rm dbtcloud_project.demo_project
```

## Next Steps

### Immediate

1. ✅ Configure environment variables
2. ✅ Get GitHub App installation ID
3. ✅ Setup Snowflake resources
4. ✅ Run first Terraform apply

### Future Enhancements

1. **UI Integration**: Add Terraform provisioning page to Streamlit app
2. **Remote State**: Configure S3/Azure backend for team collaboration
3. **Multi-Warehouse**: Support BigQuery, Databricks, Redshift
4. **Advanced Jobs**: Add more sophisticated job configurations
5. **Monitoring**: Add Terraform drift detection

## Resources

### External Links

- [dbt Cloud Terraform Provider](https://registry.terraform.io/providers/dbt-labs/dbtcloud/latest/docs)
- [Terraform Documentation](https://www.terraform.io/docs)
- [dbt Cloud API](https://docs.getdbt.com/dbt-cloud/api-v2)
- [GitHub Apps](https://docs.github.com/en/developers/apps)

### Internal Links

- [Main README](README.md)
- [Setup Guide](docs/SETUP_GUIDE.md)
- [Terraform Setup](docs/TERRAFORM_SETUP.md)
- [Terraform Quickstart](docs/TERRAFORM_QUICKSTART.md)

---

## Questions?

For issues or questions:
1. Check [Troubleshooting](docs/TERRAFORM_SETUP.md#troubleshooting)
2. Review [Environment Variables](docs/ENV_VARIABLES_REFERENCE.md)
3. Open an issue in the repository

**Happy provisioning! 🚀**

