terraform {
  required_version = ">= 1.0"

  required_providers {
    dbtcloud = {
      source  = "dbt-labs/dbtcloud"
      version = "~> 0.3"
    }
  }
}

provider "dbtcloud" {
  account_id = var.dbt_cloud_account_id
  token      = var.dbt_cloud_token
  host_url   = var.dbt_cloud_host_url
}

