"""
Configuration models using Pydantic for validation
Handles all configuration across AI providers, GitHub, and dbt Cloud
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings
import os


class AIConfig(BaseModel):
    """Configuration for AI provider"""
    provider: Literal["claude", "openai"] = Field(
        default="openai",
        description="AI provider to use for generation"
    )
    api_key: SecretStr = Field(
        description="API key for the selected provider"
    )
    model: str = Field(
        description="Model identifier to use"
    )

    @field_validator('model')
    @classmethod
    def validate_model(cls, v: str, info) -> str:
        """Validate model based on provider"""
        provider = info.data.get('provider')
        if provider == 'claude' and not v.startswith('claude'):
            raise ValueError("Claude provider requires a model starting with 'claude'")
        elif provider == 'openai' and not (v.startswith('gpt') or v.startswith('o1') or v.startswith('o3') or v.startswith('o4')):
            raise ValueError("OpenAI provider requires a GPT or O-series model")
        return v


class GitHubConfig(BaseModel):
    """Configuration for GitHub integration"""
    username: str = Field(
        description="GitHub username or organization"
    )
    access_token: SecretStr = Field(
        description="GitHub Personal Access Token with repo scope"
    )
    template_repo_url: str = Field(
        default="https://github.com/colin-thornburg/demo-automation-template.git",
        description="Template repository to clone"
    )

    @field_validator('template_repo_url')
    @classmethod
    def validate_repo_url(cls, v: str) -> str:
        """Validate GitHub repository URL format"""
        if not v.startswith('https://github.com/'):
            raise ValueError("Repository URL must start with https://github.com/")
        if not v.endswith('.git'):
            v = v + '.git'
        return v


class DbtCloudConfig(BaseModel):
    """Configuration for dbt Cloud API integration"""
    account_id: str = Field(
        description="dbt Cloud Account ID"
    )
    service_token: SecretStr = Field(
        description="dbt Cloud Service Token with appropriate permissions"
    )
    warehouse_type: Literal["snowflake", "bigquery", "databricks", "redshift"] = Field(
        default="snowflake",
        description="Target warehouse type"
    )
    api_base_url: str = Field(
        default="https://cloud.getdbt.com/api",
        description="dbt Cloud API base URL"
    )


class SnowflakeConfig(BaseModel):
    """Configuration for Snowflake connection"""
    account: str = Field(
        description="Snowflake account identifier (e.g., xy12345.us-east-1)"
    )
    database: str = Field(
        description="Snowflake database name"
    )
    warehouse: str = Field(
        description="Snowflake warehouse name"
    )
    role: str = Field(
        description="Snowflake role for dbt"
    )
    user: str = Field(
        description="Snowflake username"
    )
    password: SecretStr = Field(
        description="Snowflake password"
    )
    schema: str = Field(
        default="analytics",
        description="Default Snowflake schema"
    )


class TerraformConfig(BaseModel):
    """Configuration for Terraform operations"""
    github_installation_id: str = Field(
        description="GitHub App Installation ID for dbt Cloud"
    )
    auto_approve: bool = Field(
        default=False,
        description="Whether to auto-approve Terraform apply"
    )


class DemoInputs(BaseModel):
    """User inputs for demo generation"""
    company_name: str = Field(
        min_length=1,
        description="Prospect company name"
    )
    industry: str = Field(
        min_length=1,
        description="Industry or vertical"
    )
    discovery_notes: str = Field(
        default="",
        description="Notes from discovery call"
    )
    pain_points: str = Field(
        default="",
        description="Technical pain points with current tooling"
    )
    include_semantic_layer: bool = Field(
        default=False,
        description="Whether to include Semantic Layer in demo"
    )


class AppConfig(BaseSettings):
    """
    Application-level configuration loaded from environment variables
    Provides defaults that can be overridden in the UI
    """

    # AI Provider Defaults
    default_ai_provider: str = Field(
        default="openai",
        alias="DEFAULT_AI_PROVIDER"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        alias="ANTHROPIC_API_KEY"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        alias="OPENAI_API_KEY"
    )
    default_claude_model: str = Field(
        default="claude-opus-4-6",
        alias="DEFAULT_CLAUDE_MODEL"
    )
    default_openai_model: str = Field(
        default="gpt-4o-mini",
        alias="DEFAULT_OPENAI_MODEL"
    )

    # GitHub Defaults
    default_github_org: Optional[str] = Field(
        default=None,
        alias="DEFAULT_GITHUB_ORG"
    )
    github_token: Optional[str] = Field(
        default=None,
        alias="GITHUB_TOKEN"
    )
    dbt_template_repo_url: str = Field(
        default="https://github.com/colin-thornburg/demo-automation-template.git",
        alias="DBT_TEMPLATE_REPO_URL"
    )

    # dbt Cloud Defaults
    default_dbt_account_id: Optional[str] = Field(
        default=None,
        alias="DEFAULT_DBT_ACCOUNT_ID"
    )
    dbt_cloud_service_token: Optional[str] = Field(
        default=None,
        alias="DBT_CLOUD_SERVICE_TOKEN"
    )
    default_warehouse_type: str = Field(
        default="snowflake",
        alias="DEFAULT_WAREHOUSE_TYPE"
    )
    default_dbt_cloud_project_id: Optional[str] = Field(
        default=None,
        alias="DEFAULT_DBT_CLOUD_PROJECT_ID"
    )
    default_dbt_cloud_host: str = Field(
        default="cloud.getdbt.com",
        alias="DEFAULT_DBT_CLOUD_HOST"
    )
    dbt_cloud_pat_name: Optional[str] = Field(
        default=None,
        alias="DBT_CLOUD_PAT_NAME"
    )
    dbt_cloud_pat_value: Optional[str] = Field(
        default=None,
        alias="DBT_CLOUD_PAT_VALUE"
    )
    dbt_cloud_defer_env_id: Optional[str] = Field(
        default=None,
        alias="DBT_CLOUD_DEFER_ENV_ID"
    )

    # Snowflake Defaults
    snowflake_account: Optional[str] = Field(
        default=None,
        alias="SNOWFLAKE_ACCOUNT"
    )
    snowflake_database: Optional[str] = Field(
        default=None,
        alias="SNOWFLAKE_DATABASE"
    )
    snowflake_warehouse: Optional[str] = Field(
        default=None,
        alias="SNOWFLAKE_WAREHOUSE"
    )
    snowflake_role: Optional[str] = Field(
        default=None,
        alias="SNOWFLAKE_ROLE"
    )
    snowflake_user: Optional[str] = Field(
        default=None,
        alias="SNOWFLAKE_USER"
    )
    snowflake_password: Optional[str] = Field(
        default=None,
        alias="SNOWFLAKE_PASSWORD"
    )
    snowflake_schema: str = Field(
        default="analytics",
        alias="SNOWFLAKE_SCHEMA"
    )

    # Terraform Defaults
    github_app_installation_id: Optional[str] = Field(
        default=None,
        alias="GITHUB_APP_INSTALLATION_ID"
    )
    terraform_auto_approve: bool = Field(
        default=False,
        alias="TERRAFORM_AUTO_APPROVE"
    )

    # Application Settings
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def load_config() -> AppConfig:
    """
    Load application configuration from environment variables
    Returns AppConfig instance with defaults
    """
    return AppConfig()
