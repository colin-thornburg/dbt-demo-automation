# Terraform Quickstart Guide

Get your dbt Cloud project provisioned in 5 minutes!

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Terraform installed (`brew install terraform` on macOS)
- [ ] dbt Cloud account with Account ID and Service Token
- [ ] GitHub App installation ID for dbt Cloud
- [ ] Snowflake account with database, warehouse, and credentials ready
- [ ] GitHub repository already created (via the demo automation tool)

## 5-Minute Setup

### Step 1: Get Your GitHub App Installation ID (2 minutes)

1. Go to: https://github.com/settings/installations
2. Find "dbt Cloud" in the list
3. Click "Configure"
4. Look at the URL: `https://github.com/settings/installations/[THIS_IS_YOUR_ID]`
5. Copy that number

**Don't see dbt Cloud?**
- Install it: https://github.com/apps/dbt-cloud
- Grant access to your repositories

### Step 2: Configure Environment Variables (2 minutes)

Add these to your `.env` file:

```bash
# dbt Cloud
DEFAULT_DBT_ACCOUNT_ID=123456
DBT_CLOUD_SERVICE_TOKEN=dbtc_xxxxx

# GitHub App
GITHUB_APP_INSTALLATION_ID=12345678

# Snowflake
# Modern format (ORGNAME-ACCOUNTNAME): CMVGRNF-ZNA84829
# Legacy format (account.region): xy12345.us-west-2
SNOWFLAKE_ACCOUNT=CMVGRNF-ZNA84829
SNOWFLAKE_DATABASE=DBT_DEMO_DB
SNOWFLAKE_WAREHOUSE=DBT_DEMO_WH
SNOWFLAKE_ROLE=DBT_DEMO_ROLE
SNOWFLAKE_USER=DBT_DEMO_USER
SNOWFLAKE_PASSWORD=your_password
```

### Step 3: Run Terraform (1 minute)

```bash
cd terraform
terraform init
terraform apply
```

Type `yes` when prompted.

### Step 4: Access Your Project

After completion, get your project URL:

```bash
terraform output project_url
```

Open that URL in your browser! 🎉

## What Gets Created?

Your new dbt Cloud project includes:

✅ **Project**: Named after your demo company  
✅ **Repository**: Connected to your GitHub repo  
✅ **Snowflake Connection**: Configured and tested  
✅ **Dev Environment**: Ready for development  
✅ **Prod Environment**: Ready for deployments  
✅ **Production Job**: Scheduled to run daily at 6 AM  
✅ **CI Job**: Automatically runs on pull requests  

## Using with Demo Automation Tool

### After Creating Repository

Once you've created a GitHub repository with the demo automation tool:

1. **Note the repository URL** from the success page
2. **Run the Python integration**:

```python
from pathlib import Path
from src.terraform_integration import (
    generate_terraform_config,
    write_terraform_files,
    apply_terraform_config
)
from src.config.settings import load_config

# Load configuration from .env
app_config = load_config()

# Generate Terraform config
config = generate_terraform_config(
    scenario=your_scenario,  # From the demo generation
    github_repo_url="https://github.com/user/your-demo-repo",
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

# Write Terraform files
terraform_dir = Path("terraform")
write_terraform_files(config, terraform_dir)

# Apply (requires manual approval unless auto_approve=True)
results = apply_terraform_config(
    terraform_dir=terraform_dir,
    auto_approve=False
)

# Check results
if results['apply'].success:
    outputs = results['output'].outputs
    print(f"✅ Success! Project URL: {outputs['project_url']}")
    print(f"   Project ID: {outputs['project_id']}")
else:
    print(f"❌ Error: {results['apply'].stderr}")
```

## Common Scenarios

### Scenario 1: First Time Setup

```bash
# Clone repo, setup environment
git clone <your-repo>
cd demo_automation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure .env
cp .env.example .env
# Edit .env with your credentials

# Initialize Terraform
cd terraform
terraform init

# Create project
terraform apply
```

### Scenario 2: Update Existing Project

```bash
# Make changes to terraform files or variables
cd terraform

# Preview changes
terraform plan

# Apply changes
terraform apply
```

### Scenario 3: Create Multiple Projects

```bash
# Use different .tfvars files
terraform apply -var-file="project1.tfvars"
terraform apply -var-file="project2.tfvars"
```

### Scenario 4: Tear Down Project

```bash
cd terraform
terraform destroy
```

**Warning**: This permanently deletes the project!

## Troubleshooting

### Issue: "GitHub Installation ID not found"

**Cause**: GitHub App not installed or incorrect ID

**Fix**:
1. Install GitHub App: https://github.com/apps/dbt-cloud
2. Verify installation ID from URL
3. Ensure app has access to your repository

### Issue: "Invalid Snowflake credentials"

**Cause**: Wrong credentials or insufficient permissions

**Fix**:
```sql
-- Test in Snowflake UI or SnowSQL
SHOW GRANTS TO ROLE DBT_DEMO_ROLE;
SHOW GRANTS TO USER DBT_DEMO_USER;
```

### Issue: "Insufficient permissions"

**Cause**: API token lacks permissions

**Fix**:
1. Go to dbt Cloud Settings → API Tokens
2. Verify token has "Account Admin" or "Project Creator" permission
3. Create new token if needed

### Issue: "Repository already connected"

**Cause**: Repo is already linked to another dbt Cloud project

**Fix**:
- Use a different repository, or
- Delete the existing project in dbt Cloud first

## Next Steps

After provisioning:

1. **Open dbt Cloud IDE**
   - Navigate to project URL
   - Click "Develop" to open the IDE

2. **Initialize dbt**
   - IDE will automatically connect to your repo
   - Run `dbt debug` to verify connection

3. **Run Your Project**
   - `dbt seed` - Load seed data
   - `dbt run` - Build models
   - `dbt test` - Run tests

4. **Set Up CI/CD**
   - Create a pull request
   - CI job will automatically run
   - Review results in dbt Cloud

## Advanced Configuration

### Custom Job Schedule

Change production job timing:

```hcl
# terraform.tfvars
production_job_schedule_cron = "0 8 * * 1-5"  # 8 AM weekdays only
```

### Different Thread Counts

Optimize for your warehouse:

```hcl
# terraform.tfvars
dev_threads  = 8   # More threads for development
prod_threads = 16  # Even more for production
```

### Enable Semantic Layer

If your demo includes semantic models:

```hcl
# terraform.tfvars
enable_semantic_layer = true
```

## Resources

- **Full Documentation**: [TERRAFORM_SETUP.md](./TERRAFORM_SETUP.md)
- **Main Setup Guide**: [SETUP_GUIDE.md](./SETUP_GUIDE.md)
- **dbt Cloud Provider**: https://registry.terraform.io/providers/dbt-labs/dbtcloud/latest/docs
- **Terraform Docs**: https://www.terraform.io/docs

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review detailed docs in [TERRAFORM_SETUP.md](./TERRAFORM_SETUP.md)
3. Check Terraform logs: `export TF_LOG=DEBUG`
4. Verify all credentials and permissions

---

**Happy provisioning! 🚀**

