# Setup Guide - dbt Cloud Demo Automation Tool

Complete installation and configuration instructions.

---

## Prerequisites

### Required Accounts and Access

1. **GitHub Account**
   - Personal or organization account
   - Ability to create repositories
   - Personal Access Token with `repo` scope

2. **dbt Cloud Account**
   - Active dbt Cloud account
   - Admin or Project Creator permissions
   - Service Token access

3. **AI Provider** (choose one or both)
   - **Anthropic Claude**: API key from https://console.anthropic.com/
   - **OpenAI**: API key from https://platform.openai.com/

### System Requirements

- **Python**: 3.9 or higher
- **Node.js**: 18 or higher (for React frontend)
- **Git**: For repository operations
- **Internet Connection**: For API access

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd demo_automation
```

### 2. Create Python Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- FastAPI (backend framework)
- Anthropic and OpenAI clients for AI
- PyGithub (GitHub API)
- Pydantic (validation)
- Other supporting libraries

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your preferred text editor:

```bash
nano .env  # or vim, code, etc.
```

**Minimal configuration** (you can configure the rest in the UI):

```env
# Choose your default AI provider
DEFAULT_AI_PROVIDER=openai  # or claude

# Add your API key(s)
ANTHROPIC_API_KEY=sk-ant-xxxxx
# OR
OPENAI_API_KEY=sk-xxxxx

# Template repository (already set correctly)
DBT_TEMPLATE_REPO_URL=https://github.com/colin-thornburg/demo-automation-template.git
```

---

## API Key Setup

### GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a descriptive name: "dbt Demo Automation"
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again)
7. Add to `.env` as `GITHUB_TOKEN=ghp_xxxxx` OR enter in the UI

### Anthropic Claude API Key

1. Go to: https://console.anthropic.com/
2. Sign in or create an account
3. Navigate to "API Keys"
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)
6. Add to `.env` as `ANTHROPIC_API_KEY=sk-ant-xxxxx` OR enter in the UI

### OpenAI API Key

1. Go to: https://platform.openai.com/
2. Sign in or create an account
3. Navigate to "API Keys"
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)
6. Add to `.env` as `OPENAI_API_KEY=sk-xxxxx` OR enter in the UI

### dbt Cloud Service Token

1. Log into dbt Cloud
2. Go to Account Settings (gear icon)
3. Navigate to "Service Tokens"
4. Click "New Service Token"
5. Name it: "Demo Automation Tool"
6. Assign permissions: **Account Admin** or **Project Creator**
7. Copy the token
8. Add to `.env` as `DBT_CLOUD_SERVICE_TOKEN=xxxxx` OR enter in the UI

### dbt Cloud Account ID

1. While in dbt Cloud, look at your URL
2. It will be: `https://cloud.getdbt.com/accounts/{ACCOUNT_ID}/`
3. Copy the number after `/accounts/`
4. Add to `.env` as `DEFAULT_DBT_ACCOUNT_ID=12345` OR enter in the UI

---

## Running the Application

### Start the Backend (FastAPI)

```bash
# Activate virtual environment first
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Start the API server
./start_api.sh
# Or: uvicorn api.main:app --reload --port 8000
```

The API will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Start the Frontend (React)

In a new terminal:

```bash
cd frontend
npm run dev
```

The application will open in your browser at:
```
http://localhost:5173
```

### First Run

On first run, you'll see the Demo Setup page where you can:
1. Enter prospect information
2. Configure API settings (if not in `.env`)
3. Start generating demos

---

## Verification

### Test Your Installation

Run this Python snippet to verify configuration:

```bash
python -c "
from src.config import AppConfig
config = AppConfig()
print('✓ Configuration loaded successfully')
print(f'Default AI Provider: {config.default_ai_provider}')
print(f'Template Repo: {config.dbt_template_repo_url}')
"
```

### Test AI Connection

**For Claude:**
```bash
python -c "
from anthropic import Anthropic
client = Anthropic(api_key='your-key-here')
print('✓ Claude API connection successful')
"
```

**For OpenAI:**
```bash
python -c "
from openai import OpenAI
client = OpenAI(api_key='your-key-here')
print('✓ OpenAI API connection successful')
"
```

### Test GitHub Connection

```bash
python -c "
from github import Github
g = Github('your-token-here')
user = g.get_user()
print(f'✓ GitHub connected as: {user.login}')
"
```

---

## Configuration Options

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEFAULT_AI_PROVIDER` | No | `openai` | AI provider (claude/openai) |
| `ANTHROPIC_API_KEY` | If using Claude | - | Anthropic API key |
| `OPENAI_API_KEY` | If using OpenAI | - | OpenAI API key |
| `DEFAULT_CLAUDE_MODEL` | No | `claude-sonnet-4-5-20250929` | Claude model |
| `DEFAULT_OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model |
| `DEFAULT_GITHUB_ORG` | No | - | GitHub username/org |
| `GITHUB_TOKEN` | No* | - | GitHub PAT |
| `DBT_TEMPLATE_REPO_URL` | No | Pre-configured | Template repo |
| `DEFAULT_DBT_ACCOUNT_ID` | No* | - | dbt Cloud account |
| `DBT_CLOUD_SERVICE_TOKEN` | No* | - | dbt Cloud token |
| `DEFAULT_WAREHOUSE_TYPE` | No | `snowflake` | Warehouse type |
| `DEFAULT_DBT_CLOUD_PROJECT_ID` | No | - | dbt Cloud project ID for CLI |
| `DEFAULT_DBT_CLOUD_HOST` | No | `cloud.getdbt.com` | dbt Cloud host/region |
| `DBT_CLOUD_PAT_NAME` | No | - | Optional CLI token label |
| `DBT_CLOUD_PAT_VALUE` | No | - | Optional CLI Personal Access Token |
| `DBT_CLOUD_DEFER_ENV_ID` | No | - | Optional defer environment ID |
| `LOG_LEVEL` | No | `INFO` | Logging level |

*Can be provided in the UI instead

### dbt Cloud CLI Integration

To enable the optional Local Development workflow:

1. Open the **Configuration** section in the app and provide:
   - dbt Cloud Account ID
   - dbt Cloud Project ID
   - Host (for example, `cloud.getdbt.com` or your regional host)
   - (Optional) CLI Personal Access Token name and value
   - (Optional) Defer Environment ID
2. Confirm your scenario and navigate to the **Files Preview** page.
3. Download the generated project zip and, if provided, the auto-generated `dbt_cloud.yml` snippet.
4. Place the snippet in `~/.dbt/dbt_cloud.yml` to authenticate the dbt Cloud CLI.

The tool automatically adds a `dbt-cloud.project-id` block to `dbt_project.yml` when a project ID is supplied.

### Custom Prompt Guidance

- Add any `.txt` file to `templates/prompts/` (for example, `demo_guidelines.txt`).
- The contents are appended to the system prompt for every scenario generation.
- Remove or rename the file to stop applying the guidance.

### UI vs Environment Configuration

You can choose to:
- **Set everything in `.env`**: Fastest workflow, pre-filled forms
- **Set nothing in `.env`**: Most flexible, configure per demo
- **Hybrid approach**: Set defaults in `.env`, override in UI when needed

---

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Backend Won't Start

```bash
# Check if FastAPI is installed
pip show fastapi uvicorn

# Try running with explicit python
python -m uvicorn api.main:app --reload --port 8000
```

### Frontend Won't Start

```bash
# Check if node_modules exists
cd frontend
ls node_modules

# If not, install dependencies
npm install

# Start the dev server
npm run dev
```

### API Connection Errors

- **Invalid API Key**: Double-check the key format and regenerate if needed
- **Rate Limiting**: Wait a few minutes and try again
- **Network Issues**: Check your internet connection and firewall

### GitHub Permission Errors

Ensure your Personal Access Token has:
- ✅ `repo` scope enabled
- ✅ Not expired
- ✅ Correct username/org permissions

---

## Next Steps

Once installed and configured:

1. Read the [User Guide](USER_GUIDE.md) for usage instructions
2. Review [Example Scenarios](examples/) for inspiration
3. Check [API Reference](API_REFERENCE.md) for technical details
4. See [Troubleshooting Guide](TROUBLESHOOTING.md) for common issues

---

## Getting Help

If you encounter issues:

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) for known issues
3. Verify all prerequisites are met
4. Check API key validity and permissions

---

**Last Updated**: January 2025
