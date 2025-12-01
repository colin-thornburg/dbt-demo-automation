# dbt Cloud Project
resource "dbtcloud_project" "demo_project" {
  name = var.project_name
  dbt_project_subdirectory = ""
}

# GitHub Repository Connection
resource "dbtcloud_repository" "demo_repo" {
  project_id            = dbtcloud_project.demo_project.id
  remote_url            = var.github_repo_url
  github_installation_id = var.github_installation_id
  git_clone_strategy    = "github_app"
}

# Link repository to project so dbt Cloud recognizes it during setup
resource "dbtcloud_project_repository" "demo_project_repo" {
  project_id    = dbtcloud_project.demo_project.id
  repository_id = dbtcloud_repository.demo_repo.repository_id
}

# Snowflake Connection (deprecated but still works in v0.3.26)
resource "dbtcloud_connection" "snowflake" {
  project_id = dbtcloud_project.demo_project.id
  name       = "Snowflake"
  type       = "snowflake"
  
  account   = var.snowflake_account
  database  = var.snowflake_database
  warehouse = var.snowflake_warehouse
  role      = var.snowflake_role
  
  allow_sso = false
  allow_keep_alive = false
}

# Link Snowflake connection to project to make it available in environments
resource "dbtcloud_project_connection" "demo_project_connection" {
  project_id    = dbtcloud_project.demo_project.id
  connection_id = dbtcloud_connection.snowflake.connection_id
}

# Snowflake Credentials
resource "dbtcloud_snowflake_credential" "dev_credentials" {
  project_id  = dbtcloud_project.demo_project.id
  auth_type   = "password"
  num_threads = var.dev_threads
  schema      = var.snowflake_schema
  user        = var.snowflake_user
  password    = var.snowflake_password
  is_active   = true
}

# Development Environment
resource "dbtcloud_environment" "development" {
  project_id        = dbtcloud_project.demo_project.id
  name              = "Development"
  dbt_version       = "versionless"
  type              = "development"
  use_custom_branch = false
  
  connection_id = dbtcloud_connection.snowflake.connection_id
  credential_id = dbtcloud_snowflake_credential.dev_credentials.credential_id

  depends_on = [
    dbtcloud_project_repository.demo_project_repo,
    dbtcloud_project_connection.demo_project_connection
  ]
}

# Production Credentials (separate for security)
resource "dbtcloud_snowflake_credential" "prod_credentials" {
  project_id  = dbtcloud_project.demo_project.id
  auth_type   = "password"
  num_threads = var.prod_threads
  schema      = var.snowflake_schema
  user        = var.snowflake_user
  password    = var.snowflake_password
  is_active   = true
}

# Production Environment
resource "dbtcloud_environment" "production" {
  project_id        = dbtcloud_project.demo_project.id
  name              = "Production"
  dbt_version       = "versionless"
  type              = "deployment"
  deployment_type   = "production"
  use_custom_branch = false
  custom_branch     = "main"
  
  connection_id = dbtcloud_connection.snowflake.connection_id
  credential_id = dbtcloud_snowflake_credential.prod_credentials.credential_id

  depends_on = [
    dbtcloud_project_repository.demo_project_repo,
    dbtcloud_project_connection.demo_project_connection
  ]
}

# Production Job - Builds everything and generates artifacts
resource "dbtcloud_job" "production_job" {
  count = var.enable_production_job ? 1 : 0
  
  project_id       = dbtcloud_project.demo_project.id
  environment_id   = dbtcloud_environment.production.environment_id
  name             = "Production Build"
  description      = "Daily production dbt build - generates all artifacts"
  execute_steps    = [
    "dbt build"
  ]
  
  triggers = {
    schedule = true
    github_webhook = false
    git_provider_webhook = false
  }
  
  schedule_type = "custom_cron"
  schedule_cron = var.production_job_schedule_cron
  
  run_generate_sources = false
  generate_docs        = true
}
