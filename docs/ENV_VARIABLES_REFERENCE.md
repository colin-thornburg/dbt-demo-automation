# Environment Variables Reference

Complete reference for all environment variables used in the dbt Cloud Demo Automation Tool.

## Overview

Configuration can be provided via:
1. `.env` file (recommended for defaults)
2. UI configuration sidebar (overrides .env)
3. Programmatic configuration (Python code)

**Priority**: UI Input > .env file > Default values

## Required vs Optional

| Status | Description |
|--------|-------------|
| ✅ **Required** | Must be set to use the feature |
| 🔶 **Conditional** | Required for specific features |
| ⚙️ **Optional** | Has sensible defaults |

---

## AI Provider Configuration

### `DEFAULT_AI_PROVIDER`
- **Type**: String
- **Status**: ⚙️ Optional
- **Default**: `openai`
- **Values**: `claude` or `openai`
- **Description**: Which AI provider to use for scenario generation

### `ANTHROPIC_API_KEY`
- **Type**: String
- **Status**: 🔶 Conditional (required if using Claude)
- **Format**: `sk-ant-xxxxx`
- **Description**: Anthropic API key for Claude models
- **Get it**: https://console.anthropic.com/settings/keys

### `OPENAI_API_KEY`
- **Type**: String
- **Status**: 🔶 Conditional (required if using OpenAI)
- **Format**: `sk-xxxxx`
- **Description**: OpenAI API key for GPT models
- **Get it**: https://platform.openai.com/api-keys

### `DEFAULT_CLAUDE_MODEL`
- **Type**: String
- **Status**: ⚙️ Optional
- **Default**: `claude-sonnet-4-5-20250929`
- **Description**: Default Claude model to use

### `DEFAULT_OPENAI_MODEL`
- **Type**: String
- **Status**: ⚙️ Optional
- **Default**: `gpt-4o-mini`
- **Description**: Default OpenAI model to use

---

## GitHub Configuration

### `DEFAULT_GITHUB_ORG`
- **Type**: String
- **Status**: ⚙️ Optional
- **Description**: Default GitHub username or organization for repository creation
- **Example**: `my-github-username`

### `GITHUB_TOKEN`
- **Type**: String
- **Status**: ✅ Required (for repository creation)
- **Format**: `ghp_xxxxx`
- **Description**: GitHub Personal Access Token with `repo` scope
- **Get it**: https://github.com/settings/tokens
- **Required Scopes**: 
  - `repo` (full control of private repositories)
  - `workflow` (optional, for GitHub Actions)

### `DBT_TEMPLATE_REPO_URL`
- **Type**: String
- **Status**: ⚙️ Optional
- **Default**: `https://github.com/colin-thornburg/demo-automation-template.git`
- **Description**: Template repository to clone for new projects
- **Format**: Must be HTTPS URL ending in `.git`

### `GITHUB_APP_INSTALLATION_ID`
- **Type**: String
- **Status**: 🔶 Conditional (required for Terraform provisioning)
- **Format**: Numeric string (e.g., `12345678`)
- **Description**: GitHub App installation ID for dbt Cloud connection
- **Get it**: https://github.com/settings/installations → Configure dbt Cloud → ID in URL

---

## dbt Cloud Configuration

### `DEFAULT_DBT_ACCOUNT_ID`
- **Type**: String
- **Status**: ✅ Required (for dbt Cloud features)
- **Format**: Numeric string (e.g., `123456`)
- **Description**: Your dbt Cloud account ID
- **Get it**: dbt Cloud → Settings → Profile → Account ID

### `DBT_CLOUD_SERVICE_TOKEN`
- **Type**: String
- **Status**: ✅ Required (for dbt Cloud API)
- **Format**: `dbtc_xxxxx`
- **Description**: dbt Cloud Service Token for API access
- **Get it**: dbt Cloud → Account Settings → Service Tokens
- **Required Permissions**: 
  - Account Admin, or
  - Project Creator

### `DEFAULT_DBT_CLOUD_HOST`
- **Type**: String
- **Status**: ⚙️ Optional
- **Default**: `cloud.getdbt.com`
- **Description**: dbt Cloud host URL (change for single-tenant)
- **Examples**:
  - Multi-tenant: `cloud.getdbt.com`
  - Single-tenant: `your-company.getdbt.com`

### `DEFAULT_DBT_CLOUD_PROJECT_ID`
- **Type**: String
- **Status**: ⚙️ Optional
- **Description**: Default project ID (if reusing existing project)
- **Format**: Numeric string

### `DBT_CLOUD_PAT_NAME`
- **Type**: String
- **Status**: ⚙️ Optional
- **Description**: Name for Personal Access Token (for dbt Cloud CLI)
- **Example**: `demo_cli_token`

### `DBT_CLOUD_PAT_VALUE`
- **Type**: String
- **Status**: ⚙️ Optional
- **Description**: Personal Access Token value (for dbt Cloud CLI)
- **Format**: Alphanumeric string

### `DBT_CLOUD_DEFER_ENV_ID`
- **Type**: String
- **Status**: ⚙️ Optional
- **Description**: Environment ID to defer to for CI jobs
- **Format**: Numeric string

### `DEFAULT_WAREHOUSE_TYPE`
- **Type**: String
- **Status**: ⚙️ Optional
- **Default**: `snowflake`
- **Values**: `snowflake`, `bigquery`, `databricks`, `redshift`
- **Description**: Target data warehouse type

---

## Snowflake Configuration

### `SNOWFLAKE_ACCOUNT`
- **Type**: String
- **Status**: 🔶 Conditional (required for Terraform)
- **Format**: `[account].[region]` (e.g., `xy12345.us-east-1`)
- **Description**: Snowflake account identifier
- **Get it**: Snowflake URL or account admin

### `SNOWFLAKE_DATABASE`
- **Type**: String
- **Status**: 🔶 Conditional (required for Terraform)
- **Description**: Snowflake database name for dbt
- **Example**: `DBT_DEMO_DB`

### `SNOWFLAKE_WAREHOUSE`
- **Type**: String
- **Status**: 🔶 Conditional (required for Terraform)
- **Description**: Snowflake warehouse name for dbt
- **Example**: `DBT_DEMO_WH`

### `SNOWFLAKE_ROLE`
- **Type**: String
- **Status**: 🔶 Conditional (required for Terraform)
- **Description**: Snowflake role for dbt operations
- **Example**: `DBT_DEMO_ROLE`

### `SNOWFLAKE_USER`
- **Type**: String
- **Status**: 🔶 Conditional (required for Terraform)
- **Description**: Snowflake username for dbt Cloud
- **Example**: `DBT_DEMO_USER`

### `SNOWFLAKE_PASSWORD`
- **Type**: String
- **Status**: 🔶 Conditional (required for Terraform)
- **Description**: Snowflake password for dbt Cloud
- **Security**: Store securely, never commit to version control

### `SNOWFLAKE_SCHEMA`
- **Type**: String
- **Status**: ⚙️ Optional
- **Default**: `analytics`
- **Description**: Default Snowflake schema for dbt models

---

## Terraform Configuration

### `TERRAFORM_AUTO_APPROVE`
- **Type**: Boolean
- **Status**: ⚙️ Optional
- **Default**: `false`
- **Values**: `true` or `false`
- **Description**: Auto-approve Terraform applies (use with caution!)
- **Warning**: `true` will apply changes without confirmation

---

## Application Settings

### `LOG_LEVEL`
- **Type**: String
- **Status**: ⚙️ Optional
- **Default**: `INFO`
- **Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Description**: Logging verbosity level

---

## Configuration Examples

### Minimal Setup (GitHub only)

```bash
# AI
ANTHROPIC_API_KEY=sk-ant-xxxxx

# GitHub
GITHUB_TOKEN=ghp_xxxxx
DEFAULT_GITHUB_ORG=my-username

# dbt Cloud
DEFAULT_DBT_ACCOUNT_ID=123456
DBT_CLOUD_SERVICE_TOKEN=dbtc_xxxxx
```

### Full Setup (with Terraform)

```bash
# AI
ANTHROPIC_API_KEY=sk-ant-xxxxx
DEFAULT_AI_PROVIDER=openai

# GitHub
GITHUB_TOKEN=ghp_xxxxx
DEFAULT_GITHUB_ORG=my-org
GITHUB_APP_INSTALLATION_ID=12345678

# dbt Cloud
DEFAULT_DBT_ACCOUNT_ID=123456
DBT_CLOUD_SERVICE_TOKEN=dbtc_xxxxx
DEFAULT_DBT_CLOUD_HOST=cloud.getdbt.com

# Snowflake
SNOWFLAKE_ACCOUNT=xy12345.us-east-1
SNOWFLAKE_DATABASE=DBT_DEMO_DB
SNOWFLAKE_WAREHOUSE=DBT_DEMO_WH
SNOWFLAKE_ROLE=DBT_DEMO_ROLE
SNOWFLAKE_USER=DBT_DEMO_USER
SNOWFLAKE_PASSWORD=secure_password_here
SNOWFLAKE_SCHEMA=analytics

# Terraform
TERRAFORM_AUTO_APPROVE=false
```

### Multi-Provider AI Setup

```bash
# Both providers configured
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
DEFAULT_AI_PROVIDER=openai

# Models
DEFAULT_CLAUDE_MODEL=claude-sonnet-4-5-20250929
DEFAULT_OPENAI_MODEL=gpt-4o-mini
```

---

## Security Best Practices

### 1. Never Commit Secrets

```bash
# .gitignore should include:
.env
*.tfvars
terraform.tfstate*
```

### 2. Restrict File Permissions

```bash
chmod 600 .env
chmod 600 terraform/terraform.tfvars
```

### 3. Use Minimal Permissions

- **GitHub Token**: Only grant `repo` scope
- **dbt Cloud Token**: Use Service Token with minimal required permissions
- **Snowflake User**: Create dedicated user with limited privileges

### 4. Rotate Credentials Regularly

- Rotate API tokens every 90 days
- Update passwords quarterly
- Remove unused tokens immediately

### 5. Use Environment-Specific Configs

```bash
# Development
.env.dev

# Production
.env.prod

# Load appropriate file
cp .env.dev .env
```

---

## Validation

### Check Configuration

```python
from src.config.settings import load_config

config = load_config()
print(f"AI Provider: {config.default_ai_provider}")
print(f"GitHub Org: {config.default_github_org}")
print(f"dbt Account: {config.default_dbt_account_id}")
```

### Verify Required Variables

The application will warn you if required variables are missing based on the features you're using.

---

## Troubleshooting

### Issue: "Environment variable not found"

**Fix**: Ensure `.env` file exists in project root and is loaded:
```bash
ls -la .env  # Should exist
cat .env | grep VARIABLE_NAME  # Should show your value
```

### Issue: "Invalid API key format"

**Fix**: Verify format matches expected pattern:
- GitHub: `ghp_xxxxx`
- dbt Cloud: `dbtc_xxxxx`
- Anthropic: `sk-ant-xxxxx`
- OpenAI: `sk-xxxxx`

### Issue: Variables not loading

**Fix**: 
1. Check `.env` file encoding (UTF-8)
2. No spaces around `=` in `.env`
3. No quotes around values (unless value contains spaces)
4. Restart application after changing `.env`

---

For more information, see:
- [Setup Guide](./SETUP_GUIDE.md)
- [Terraform Setup](./TERRAFORM_SETUP.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
