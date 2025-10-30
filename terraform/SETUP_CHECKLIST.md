# Terraform Setup Checklist

Use this checklist to ensure you have everything configured correctly before running Terraform.

## Prerequisites ✓

### 1. Software Installation
- [ ] Terraform CLI installed (`terraform --version`)
- [ ] Python 3.9+ installed
- [ ] Virtual environment activated

### 2. Accounts & Access
- [ ] dbt Cloud account with admin access
- [ ] GitHub account with dbt Cloud app installed
- [ ] Snowflake account with appropriate permissions

## Configuration Steps ✓

### Step 1: dbt Cloud Setup
- [ ] Get dbt Cloud Account ID
  - Location: dbt Cloud → Settings → Profile
  - Add to `.env`: `DEFAULT_DBT_ACCOUNT_ID=123456`

- [ ] Create Service Token
  - Location: dbt Cloud → Account Settings → Service Tokens
  - Required permission: Account Admin or Project Creator
  - Add to `.env`: `DBT_CLOUD_SERVICE_TOKEN=dbtc_xxxxx`

### Step 2: GitHub App Setup
- [ ] Install dbt Cloud GitHub App
  - URL: https://github.com/apps/dbt-cloud
  - Grant access to repositories

- [ ] Get Installation ID
  - Go to: https://github.com/settings/installations
  - Click "Configure" on dbt Cloud
  - Copy ID from URL: `https://github.com/settings/installations/[ID]`
  - Add to `.env`: `GITHUB_APP_INSTALLATION_ID=12345678`

### Step 3: Snowflake Setup
- [ ] Create Snowflake resources (or verify they exist):
  ```sql
  -- Database
  CREATE DATABASE IF NOT EXISTS DBT_DEMO_DB;
  
  -- Warehouse
  CREATE WAREHOUSE IF NOT EXISTS DBT_DEMO_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60;
  
  -- Role
  CREATE ROLE IF NOT EXISTS DBT_DEMO_ROLE;
  
  -- User
  CREATE USER IF NOT EXISTS DBT_DEMO_USER
    PASSWORD = 'secure_password'
    DEFAULT_ROLE = DBT_DEMO_ROLE;
  
  -- Grants
  GRANT USAGE ON WAREHOUSE DBT_DEMO_WH TO ROLE DBT_DEMO_ROLE;
  GRANT USAGE ON DATABASE DBT_DEMO_DB TO ROLE DBT_DEMO_ROLE;
  GRANT CREATE SCHEMA ON DATABASE DBT_DEMO_DB TO ROLE DBT_DEMO_ROLE;
  GRANT ROLE DBT_DEMO_ROLE TO USER DBT_DEMO_USER;
  ```

- [ ] Add credentials to `.env`:
  ```bash
  SNOWFLAKE_ACCOUNT=xy12345.us-east-1
  SNOWFLAKE_DATABASE=DBT_DEMO_DB
  SNOWFLAKE_WAREHOUSE=DBT_DEMO_WH
  SNOWFLAKE_ROLE=DBT_DEMO_ROLE
  SNOWFLAKE_USER=DBT_DEMO_USER
  SNOWFLAKE_PASSWORD=your_secure_password
  ```

- [ ] Test Snowflake connection:
  ```bash
  snowsql -a xy12345.us-east-1 -u DBT_DEMO_USER -r DBT_DEMO_ROLE
  ```

### Step 4: Repository Setup
- [ ] Create repository using demo automation tool
- [ ] Note the repository URL (HTTPS format)
- [ ] Verify repository exists on GitHub
- [ ] Ensure GitHub App has access to the repository

## Terraform Configuration ✓

### Step 5: Initialize Terraform
- [ ] Navigate to terraform directory:
  ```bash
  cd terraform
  ```

- [ ] Initialize Terraform:
  ```bash
  terraform init
  ```

- [ ] Verify providers downloaded:
  ```
  ✓ Terraform has been successfully initialized!
  ✓ Provider dbt-labs/dbtcloud installed
  ```

### Step 6: Configure Variables
- [ ] Copy template:
  ```bash
  cp terraform.tfvars.template terraform.tfvars
  ```

- [ ] Edit `terraform.tfvars` with your values:
  - dbt Cloud credentials
  - GitHub repository URL
  - GitHub installation ID
  - Snowflake credentials
  
- [ ] Verify no syntax errors:
  ```bash
  terraform validate
  ```

### Step 7: Review Plan
- [ ] Run Terraform plan:
  ```bash
  terraform plan
  ```

- [ ] Review planned changes:
  - [ ] 1 dbt Cloud project
  - [ ] 1 repository connection
  - [ ] 1 Snowflake connection
  - [ ] 2 credentials (dev & prod)
  - [ ] 2 environments (dev & prod)
  - [ ] 2 jobs (production & CI)

- [ ] Verify all resource names and configurations look correct

## Apply Configuration ✓

### Step 8: Apply Terraform
- [ ] Apply configuration:
  ```bash
  terraform apply
  ```

- [ ] Review summary one more time

- [ ] Type `yes` to confirm

- [ ] Wait for completion (typically 1-2 minutes)

- [ ] Verify success message:
  ```
  Apply complete! Resources: 8 added, 0 changed, 0 destroyed.
  ```

### Step 9: Verify Deployment
- [ ] Get project URL:
  ```bash
  terraform output project_url
  ```

- [ ] Open URL in browser

- [ ] Verify in dbt Cloud:
  - [ ] Project exists
  - [ ] Repository is connected
  - [ ] Snowflake connection is configured
  - [ ] Development environment is ready
  - [ ] Production environment is ready
  - [ ] Jobs are configured

- [ ] Test IDE access:
  - [ ] Click "Develop" in dbt Cloud
  - [ ] IDE opens successfully
  - [ ] Repository files are visible

### Step 10: Test Connection
- [ ] In dbt Cloud IDE, run:
  ```bash
  dbt debug
  ```

- [ ] Verify all checks pass:
  ```
  ✓ Connection test: OK
  ✓ dbt project: OK
  ✓ Profile: OK
  ```

- [ ] Run initial build (optional):
  ```bash
  dbt seed
  dbt run
  dbt test
  ```

## Post-Deployment ✓

### Step 11: Save Outputs
- [ ] Save project details:
  ```bash
  terraform output > project_details.txt
  ```

- [ ] Record important IDs:
  - Project ID: _______________
  - Dev Environment ID: _______________
  - Prod Environment ID: _______________
  - Production Job ID: _______________
  - CI Job ID: _______________

### Step 12: Security Review
- [ ] Verify `.env` is not committed:
  ```bash
  git status  # Should show .env as ignored
  ```

- [ ] Verify `terraform.tfvars` is not committed:
  ```bash
  git status  # Should show .tfvars as ignored
  ```

- [ ] Set proper file permissions:
  ```bash
  chmod 600 .env
  chmod 600 terraform/terraform.tfvars
  ```

- [ ] Review state file security:
  - [ ] Consider using remote state (S3, Azure, etc.)
  - [ ] Ensure state file is not committed to git

### Step 13: Documentation
- [ ] Document project details for your team
- [ ] Note any custom configurations
- [ ] Save credentials in team password manager
- [ ] Share project URL with stakeholders

## Troubleshooting ✓

If you encounter issues, verify:

### Common Issue Checklist
- [ ] All environment variables are set correctly
- [ ] GitHub App has access to the repository
- [ ] Snowflake credentials are valid
- [ ] dbt Cloud token has correct permissions
- [ ] Repository URL is in HTTPS format
- [ ] Terraform is initialized
- [ ] No typos in variable values

### Debug Commands
```bash
# Check Terraform version
terraform --version

# Validate configuration
terraform validate

# Check provider installation
terraform version

# Enable debug logging
export TF_LOG=DEBUG
terraform plan
```

## Next Steps ✓

After successful deployment:

- [ ] Create a pull request in your repository
- [ ] Verify CI job runs automatically
- [ ] Test production job manually
- [ ] Configure job notifications (in dbt Cloud UI)
- [ ] Add team members to project
- [ ] Set up Slack/email notifications
- [ ] Schedule demo with prospect

## Resources

- **Quickstart**: [docs/TERRAFORM_QUICKSTART.md](../docs/TERRAFORM_QUICKSTART.md)
- **Detailed Guide**: [docs/TERRAFORM_SETUP.md](../docs/TERRAFORM_SETUP.md)
- **Environment Variables**: [docs/ENV_VARIABLES_REFERENCE.md](../docs/ENV_VARIABLES_REFERENCE.md)
- **Troubleshooting**: [docs/TERRAFORM_SETUP.md#troubleshooting](../docs/TERRAFORM_SETUP.md#troubleshooting)

## Support

Need help?
1. Check [Troubleshooting](../docs/TERRAFORM_SETUP.md#troubleshooting)
2. Review [Common Issues](../docs/TERRAFORM_SETUP.md#common-issues)
3. Verify environment variables
4. Open an issue in the repository

---

**Ready to provision?** Make sure all checkboxes above are ✓ before running `terraform apply`!

