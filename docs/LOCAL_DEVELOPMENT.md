# Local Development Guide

This guide explains how to work with generated demo projects on your own machine using the dbt Cloud CLI.

## Prerequisites

- dbt Cloud CLI installed (`pip install dbt-cloud-cli` or via Homebrew)
- dbt Cloud Account ID and Project ID
- dbt Cloud Personal Access Token (PAT) with appropriate permissions

## Generate a Project

1. Launch the Streamlit app (`streamlit run app.py`).
2. Configure the **dbt Cloud** section in the sidebar:
   - Account ID
   - Project ID
   - Host (for example, `cloud.getdbt.com`)
   - Optional CLI token name/value and defer environment ID
3. Confirm the AI-generated scenario and proceed to the **Files Preview** page.
4. Download the project zip and the `dbt_cloud.yml` snippet.

## Configure the CLI

1. Create (or update) `~/.dbt/dbt_cloud.yml` with the snippet provided.
2. Verify connectivity:
   ```bash
   dbt-cloud --version
   dbt-cloud list projects
   ```

## Run the Project Locally

```bash
unzip <project>.zip
cd <project>
dbt deps
dbt seed
dbt run
dbt test
```

> The project zip already contains the correct `dbt-cloud.project-id` configuration inside `dbt_project.yml`.

## Custom Prompt Guidance

To enforce additional modelling standards, add `.txt` files to `templates/prompts/`. The tool automatically folds their content into the AI instructions.

