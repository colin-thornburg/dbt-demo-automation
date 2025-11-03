# dbt Cloud Configuration
variable "dbt_cloud_account_id" {
  description = "dbt Cloud Account ID"
  type        = string
}

variable "dbt_cloud_token" {
  description = "dbt Cloud API Token (Service Token or Personal Access Token)"
  type        = string
  sensitive   = true
}

variable "dbt_cloud_host_url" {
  description = "dbt Cloud API Host URL"
  type        = string
  default     = "https://cloud.getdbt.com/api"
}

# Project Configuration
variable "project_name" {
  description = "Name for the dbt Cloud project"
  type        = string
}

variable "project_description" {
  description = "Description for the dbt Cloud project"
  type        = string
  default     = ""
}

# Repository Configuration
variable "github_repo_url" {
  description = "GitHub repository URL (HTTPS format)"
  type        = string
}

variable "github_installation_id" {
  description = "GitHub App Installation ID for dbt Cloud"
  type        = string
}

# Snowflake Configuration
variable "snowflake_account" {
  description = "Snowflake account identifier"
  type        = string
}

variable "snowflake_database" {
  description = "Snowflake database name"
  type        = string
}

variable "snowflake_warehouse" {
  description = "Snowflake warehouse name"
  type        = string
}

variable "snowflake_role" {
  description = "Snowflake role for dbt"
  type        = string
}

variable "snowflake_user" {
  description = "Snowflake user for dbt Cloud connection"
  type        = string
}

variable "snowflake_password" {
  description = "Snowflake password for dbt Cloud connection"
  type        = string
  sensitive   = true
}

variable "snowflake_schema" {
  description = "Default Snowflake schema for dbt"
  type        = string
  default     = "analytics"
}

# Environment Configuration
variable "dev_threads" {
  description = "Number of threads for development environment"
  type        = number
  default     = 4
}

variable "prod_threads" {
  description = "Number of threads for production environment"
  type        = number
  default     = 8
}

# Job Configuration
variable "enable_production_job" {
  description = "Whether to create a production job"
  type        = bool
  default     = true
}

variable "production_job_schedule_cron" {
  description = "Cron schedule for production job"
  type        = string
  default     = "0 6 * * *"  # 6 AM daily
}

# Optional: Semantic Layer
variable "enable_semantic_layer" {
  description = "Whether to enable the semantic layer for this project"
  type        = bool
  default     = false
}


