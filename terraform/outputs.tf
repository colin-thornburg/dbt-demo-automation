output "project_id" {
  description = "The ID of the created dbt Cloud project"
  value       = dbtcloud_project.demo_project.id
}

output "project_name" {
  description = "The name of the created dbt Cloud project"
  value       = dbtcloud_project.demo_project.name
}

output "repository_id" {
  description = "The ID of the connected repository"
  value       = dbtcloud_repository.demo_repo.id
}

output "connection_id" {
  description = "The ID of the Snowflake connection"
  value       = dbtcloud_connection.snowflake.connection_id
}

output "dev_environment_id" {
  description = "The ID of the development environment"
  value       = dbtcloud_environment.development.environment_id
}

output "prod_environment_id" {
  description = "The ID of the production environment"
  value       = dbtcloud_environment.production.environment_id
}

output "production_job_id" {
  description = "The ID of the production job (if enabled)"
  value       = var.enable_production_job ? dbtcloud_job.production_job[0].id : null
}

output "project_url" {
  description = "URL to access the project in dbt Cloud"
  value       = "https://cloud.getdbt.com/deploy/${var.dbt_cloud_account_id}/projects/${dbtcloud_project.demo_project.id}"
}

