# dbt Cloud Automated Provisioning - User Guide

## Overview

The dbt Cloud Demo Automation Tool now includes **automated provisioning** of dbt Cloud projects using Terraform. After creating your GitHub repository, you can provision a complete dbt Cloud project with one click.

## Complete Workflow

### Phase 1-4: Demo Generation & Repository Creation
*(Existing functionality)*

1. **Demo Setup** - Enter company info
2. **Scenario Review** - AI generates scenario
3. **Files Preview** - Review generated dbt files
4. **Repository Success** - Push to GitHub

### Phase 5: dbt Cloud Provisioning ✨ NEW
*(Automated Terraform provisioning)*

5. **dbt Cloud Provisioning** - One-click setup:
   - Configure Snowflake credentials
   - Preview what will be created
   - Click "Provision dbt Cloud Project"
   - Watch progress in real-time
   - Get direct link to your project

### Phase 6: Final Success

6. **Final Success** - Complete setup ready:
   - GitHub repository ✅
   - dbt Cloud project ✅
   - Direct links to everything
   - Demo flow guide
   - Downloadable summary

---

## Setup Requirements

### 1. Environment Variables

Add these to your `.env` file:

```bash
# GitHub App Installation ID
GITHUB_APP_INSTALLATION_ID=12345678

# Snowflake Configuration
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

### 2. Get GitHub App Installation ID

1. Go to https://github.com/settings/installations
2. Find "dbt Cloud" app
3. Click "Configure"
4. Copy ID from URL: `https://github.com/settings/installations/[THIS_NUMBER]`

If you don't see dbt Cloud:
- Install it: https://github.com/apps/dbt-cloud
- Grant access to your repositories

### 3. Snowflake Setup

Create the required Snowflake resources:

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

### 4. Install Terraform

```bash
# macOS
brew install terraform

# Verify
terraform --version
```

---

## Using the Provisioning Feature

### In the Streamlit App

#### Step 1: After Repository Creation

After your GitHub repository is created, you'll see the **Repository Success** page with two options:

- **🏗️ Provision dbt Cloud** (if Snowflake config is available)
- **Skip to Success →** (if you want to set up manually)

#### Step 2: Configure Snowflake

On the **dbt Cloud Provisioning** page:

1. **Review Snowflake Configuration**
   - Form pre-fills with values from `.env`
   - You can override any value if needed
   - All fields are required

2. **Review What Will Be Created**
   - dbt Cloud project
   - Repository connection
   - Snowflake connection
   - Dev & Prod environments
   - Production job (daily at 6 AM)
   - CI job (runs on PRs)

3. **Optional: Advanced Settings**
   - Adjust thread counts
   - Modify job schedule
   - Toggle production job

#### Step 3: Provision

1. Click **"🚀 Provision dbt Cloud Project"**

2. **Watch Progress** (2-3 minutes):
   - ⚙️ Generating Terraform configuration...
   - 📝 Writing Terraform files...
   - 🔧 Initializing Terraform...
   - ✅ Validating configuration...
   - 📋 Creating execution plan...
   - 🚀 Provisioning dbt Cloud project...
   - 📊 Retrieving project information...
   - ✅ Provisioning complete!

3. **View Results**:
   - Project URL and ID
   - Environment IDs
   - Job IDs
   - Direct link to dbt Cloud IDE

#### Step 4: Success

Navigate to the **Final Success** page to see:

- Complete setup summary
- Links to GitHub repository
- Links to dbt Cloud project
- Suggested demo flow
- Quick reference links
- Downloadable summary

---

## What Gets Provisioned

### dbt Cloud Resources

| Resource | Description |
|----------|-------------|
| **Project** | New dbt Cloud project with your company name |
| **Repository** | GitHub repository connected via GitHub App |
| **Connection** | Snowflake connection configured and tested |
| **Dev Environment** | Development environment with dbt IDE access |
| **Prod Environment** | Production environment for deployments |
| **Dev Credentials** | Snowflake credentials for development (4 threads) |
| **Prod Credentials** | Snowflake credentials for production (8 threads) |
| **Production Job** | Scheduled daily job (6 AM): `dbt seed && dbt run && dbt test` |
| **CI Job** | Runs on PRs with deferral to production |

### Infrastructure as Code

All resources are created via Terraform:
- **Repeatable**: Create identical setups every time
- **Auditable**: Track changes in version control
- **Fast**: 2-3 minutes from start to finish
- **Reversible**: Can destroy and recreate easily

---

## User Experience

### With Snowflake Config (Recommended)

```
1. Demo Setup → Enter company info
2. Scenario Review → Review AI-generated scenario
3. Files Preview → Review dbt files
4. Create Repository → Push to GitHub
   ↓
5. Repository Success → Click "Provision dbt Cloud"
   ↓
6. dbt Cloud Provisioning:
   - Review/edit Snowflake config
   - Click "Provision"
   - Watch progress (2-3 min)
   - Get project URL
   ↓
7. Final Success → Complete setup ready!
   - Open dbt Cloud IDE
   - Run initial build
   - Start demo
```

### Without Snowflake Config (Manual)

```
1-4. Same as above
   ↓
5. Repository Success → Click "Skip to Success"
   ↓
6. Final Success → Manual setup instructions
   - Set up dbt Cloud manually
   - Or add Snowflake config and provision later
```

---

## Features

### Smart Defaults

- Pre-fills all fields from `.env`
- Shows which values come from environment
- Allows overrides for one-off demos

### Real-Time Progress

- Progress bar shows current step
- Status messages update in real-time
- Clear error messages if something fails

### Error Handling

- Validates all inputs before provisioning
- Shows detailed error messages
- Provides troubleshooting guidance
- Allows retry without starting over

### Flexibility

- Can skip provisioning and do manually
- Can provision later if skipped initially
- Can override any configuration value
- Can adjust thread counts and schedules

---

## Troubleshooting

### Issue: "Missing required field"

**Cause**: Snowflake configuration incomplete

**Fix**: Ensure all fields are filled:
- Account (format: `xy12345.us-east-1`)
- Database
- Warehouse
- Role
- User
- Password

### Issue: "GitHub Installation ID not found"

**Cause**: GitHub App not installed or incorrect ID

**Fix**:
1. Install dbt Cloud GitHub App
2. Get correct installation ID
3. Update `GITHUB_APP_INSTALLATION_ID` in `.env`
4. Restart Streamlit app

### Issue: "Invalid Snowflake credentials"

**Cause**: Wrong credentials or insufficient permissions

**Fix**:
1. Test credentials in Snowflake UI or SnowSQL
2. Verify user has been granted the role
3. Check role has necessary permissions
4. Update credentials in `.env` or form

### Issue: "Provisioning failed at stage: apply"

**Cause**: Terraform apply failed (various reasons)

**Fix**:
1. Read the error details in the expander
2. Common causes:
   - Repository already connected to another project
   - Insufficient dbt Cloud token permissions
   - Snowflake connection test failed
3. Fix the issue and click "Try Again"

### Issue: "Repository already connected"

**Cause**: Repo is already linked to a dbt Cloud project

**Fix**:
- Use a different repository, or
- Delete the existing dbt Cloud project first

---

## Advanced Usage

### Custom Thread Counts

In the "Advanced Options" section:

```
Development Threads: 4  (default)
Production Threads: 8   (default)
```

Adjust based on your warehouse size:
- Small warehouse: 4-8 threads
- Medium warehouse: 8-16 threads
- Large warehouse: 16-32 threads

### Custom Job Schedule

Modify the cron expression:

```
0 6 * * *    → Daily at 6 AM
0 8 * * 1-5  → Weekdays at 8 AM
0 */4 * * *  → Every 4 hours
0 0 * * 0    → Weekly on Sunday
```

### Skip Production Job

Uncheck "Enable Production Job" if:
- Demo doesn't need scheduled runs
- You'll configure jobs manually later
- Testing the provisioning process

---

## Best Practices

### Before Provisioning

1. ✅ Verify Snowflake credentials work
2. ✅ Check GitHub App has repository access
3. ✅ Ensure dbt Cloud token has correct permissions
4. ✅ Review configuration values
5. ✅ Understand what will be created

### After Provisioning

1. **Open dbt Cloud IDE immediately**
   - Verify connection works
   - Run `dbt debug` to test

2. **Run initial build**
   ```bash
   dbt deps
   dbt seed
   dbt run
   dbt test
   ```

3. **Test CI workflow**
   - Create a branch
   - Make a small change
   - Open PR
   - Verify CI job runs

4. **Customize as needed**
   - Adjust job schedules
   - Add notifications
   - Configure permissions

### For Multiple Demos

- Use descriptive project names
- Keep Snowflake credentials consistent
- Document which repos go with which projects
- Consider using separate Snowflake databases per demo

---

## Comparison: Manual vs Automated

| Aspect | Manual Setup | Automated (Terraform) |
|--------|-------------|----------------------|
| **Time** | 15-30 minutes | 2-3 minutes |
| **Errors** | Prone to mistakes | Consistent, validated |
| **Repeatability** | Manual each time | Identical every time |
| **Documentation** | Must document | Self-documenting code |
| **Cleanup** | Manual deletion | `terraform destroy` |
| **Auditing** | Not tracked | Version controlled |
| **Learning Curve** | Know dbt Cloud UI | Just fill a form |

---

## Resources

- **[Terraform Quickstart](./TERRAFORM_QUICKSTART.md)** - Manual Terraform usage
- **[Terraform Setup Guide](./TERRAFORM_SETUP.md)** - Complete Terraform docs
- **[Environment Variables](./ENV_VARIABLES_REFERENCE.md)** - All variables explained
- **[Main Setup Guide](./SETUP_GUIDE.md)** - Overall tool setup

---

## Feedback & Support

If you encounter issues:

1. Check error messages in the UI
2. Review [Troubleshooting](#troubleshooting) section above
3. Check Terraform logs in `terraform/` directory
4. Verify all prerequisites are met

---

**Ready to try it?** Add Snowflake credentials to your `.env` and start automating! 🚀

