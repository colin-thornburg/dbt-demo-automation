# dbt Cloud Demo Automation Tool

An AI-powered Streamlit application that enables Solution Architects to rapidly create customized, industry-specific dbt PLatform demo projects.

## Overview

This tool reduces demo preparation time from hours to minutes by:
- Generating industry-relevant data models using AI
- Creating synthetic seed data with proper relationships
- Automatically provisioning projects in dbt Cloud
- Producing ready-to-present demos with talking points

## Quick Start

### Prerequisites

- Python 3.9 or higher
- GitHub account with Personal Access Token
- dbt Cloud account with Service Token
- API key for Claude (Anthropic) or OpenAI

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd demo_automation
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

The app will open in your browser at `http://localhost:8501`

## Configuration

### Environment Variables

You can set defaults in `.env` or configure everything through the UI:

- **AI Provider**: Claude (Anthropic) or OpenAI
- **GitHub**: Personal Access Token with `repo` scope
- **dbt Cloud**: Account ID and Service Token

See [`.env.example`](.env.example) for all available options.

### API Keys Required

1. **Anthropic API Key** (for Claude)
   - Get it at: https://console.anthropic.com/

2. **GitHub Personal Access Token**
   - Generate at: https://github.com/settings/tokens
   - Required scope: `repo` (full control of private repositories)

3. **dbt Cloud Service Token**
   - Generate in: dbt Cloud > Account Settings > Service Tokens
   - Required permissions: Account Admin or Project Creator

## Usage

### 1. Demo Setup
- Enter prospect company name and industry
- Add discovery call notes and pain points
- Configure AI provider and API keys
- Set GitHub and dbt Cloud credentials

### 2. Review Demo Plan
- AI generates a detailed demo scenario
- Review proposed data architecture
- Confirm or regenerate with modifications

#### Add Custom Prompt Guidance
- Drop any `.txt` file into `templates/prompts/` to influence scenario generation
- Files are automatically appended to the model's instructions—no code changes required
- Use this to enforce internal demo guidelines, naming conventions, or required talking points

### 3. Project Generation
- Watch real-time progress as the tool:
  - Generates seed data and dbt models
  - Creates a GitHub repository
  - Provisions dbt Cloud project
  - Runs initial dbt build

### 4. Ready to Demo
- Access your GitHub repository
- Open the dbt Cloud project
- Review generated talking points

## Local Development & CLI Workflow

The Files Preview page now provides two quick actions for developers who want to iterate locally:

1. **Download Project Zip** – Grab a complete archive of the generated project to open directly in VS Code, PyCharm, or your editor of choice.
2. **dbt Cloud CLI Snippet** – When you provide your dbt Cloud account ID, project ID, and (optionally) a CLI PAT in the configuration sidebar, the app generates a ready-to-paste `~/.dbt/dbt_cloud.yml` snippet and also embeds the `dbt-cloud.project-id` block in `dbt_project.yml`.

Once downloaded, you can run the project locally with:

```bash
unzip <project>.zip
cd <project>
dbt deps
dbt seed
dbt run
dbt test
```

> The CLI snippet includes sensible placeholders if you omit optional values, so teams can share instructions without revealing secrets.

## Custom Prompt Guidelines

You can tailor the AI assistant without touching code:

- Place any additional `.txt` files in `templates/prompts/` (for example, `demo_guidelines.txt`).
- The file name becomes the section title, and its contents are appended to the system instructions for every generation.
- Remove or rename the file to disable the guidance.

This makes it easy to enforce internal storytelling standards, naming conventions, or demo-specific talking points.

## Project Structure

```
demo_automation/
├── app.py                      # Main Streamlit application
├── src/
│   ├── config/                 # Configuration management
│   ├── ai/                     # AI provider integration
│   ├── github_integration/     # GitHub API wrapper
│   ├── dbt_cloud/             # dbt Cloud API integration
│   ├── file_generation/       # dbt file generators
│   └── ui/                    # Streamlit UI components
├── templates/                  # Prompt templates
├── docs/                      # Documentation
├── tests/                     # Unit and integration tests
├── requirements.txt           # Python dependencies
└── .env.example              # Environment variable template
```

## Features

### AI-Powered Generation
- Industry-specific data models
- Realistic synthetic data with proper foreign keys
- dbt best practices automatically applied
- Semantic Layer support (optional)

### Automated Provisioning
- GitHub repository creation
- dbt Cloud project setup
- Environment and job configuration
- Initial dbt run execution

### Demo Enhancements
- Data quality scenarios (when requested)
- Incremental model examples
- Comprehensive testing examples
- Documentation and lineage ready to show

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black src/

# Type checking
mypy src/

# Linting
flake8 src/
```

## Documentation

- [Setup Guide](docs/SETUP_GUIDE.md) - Detailed installation and configuration
- [User Guide](docs/USER_GUIDE.md) - Step-by-step usage instructions
- [API Reference](docs/API_REFERENCE.md) - dbt Cloud and GitHub API details
- [Development Log](docs/DEVELOPMENT_LOG.md) - Build progress and testing notes
- [Local Development Guide](docs/LOCAL_DEVELOPMENT.md) - Work with the generated project and dbt Cloud CLI
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## Architecture

Built with:
- **Streamlit** - Interactive web interface
- **Pydantic** - Configuration validation
- **Anthropic/OpenAI** - AI model providers
- **PyGithub** - GitHub API integration
- **Requests** - dbt Cloud API integration

## Security

- API keys are never persisted to disk
- All sensitive inputs are masked
- Repositories default to private
- Session state cleared on app restart

## Support

For issues or questions:
1. Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
2. Review example scenarios in [`docs/examples/`](docs/examples/)
3. Open an issue in this repository

## License

[Your License Here]

## Acknowledgments

Built for dbt Labs Solutions Architects to create better demos faster.
