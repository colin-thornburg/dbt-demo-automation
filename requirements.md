# dbt Cloud Demo Automation Tool - Requirements Document

## Project Overview

Build an application that enables dbt Labs Sales Engineers to rapidly create customized, industry-specific dbt Cloud demo projects using AI. The tool will generate appropriate data models, seed files with synthetic data, and automatically provision the demo in dbt Cloud via API integration.

## Target Users

Primary: dbt Labs Sales Engineers and Solutions Architects
Secondary: Account Executives (for self-service demos)

## Core Objectives

1. Reduce demo preparation time from hours to minutes
2. Create industry-relevant, use-case-specific demonstrations
3. Automatically provision working dbt Cloud projects
4. Scale high-quality, personalized demos across the sales organization

---

## Application Architecture

### Technology Stack

- **Frontend**: React (Vite + Tailwind CSS)
- **Backend**: FastAPI (Python REST API)
- **AI Models**: User-configurable (Claude, GPT-4, etc.)
- **Version Control**: GitHub API for repository management
- **Platform Integration**: dbt Cloud Admin API (v2 and v3)
- **Infrastructure**: Terraform for dbt Cloud provisioning
- **Language**: Python 3.9+, Node.js 18+

### Key Dependencies

- `fastapi` - Backend API framework
- `uvicorn` - ASGI server
- `anthropic` - Claude API client
- `openai` - OpenAI API client
- `requests` - API interactions
- `PyGithub` - GitHub API wrapper
- `pydantic` - Data validation
- `pyyaml` - dbt YAML file generation
- `jinja2` - Template rendering for dbt models

---

## User Flow

### Phase 1: Initial Context Gathering

**Page: "Demo Setup"**

User inputs:
1. Prospect company name (text input)
2. Industry/vertical (text input or dropdown)
3. Discovery call notes (large text area) - free-form context about:
   - Specific use case or initiative
   - Business objectives
   - Timeline/urgency
4. Major technical pain points with current tooling (large text area)
5. Semantic Layer requirement (checkbox: "Include Semantic Layer")

**AI Model Configuration (collapsible section):**
- AI Provider dropdown (Claude, OpenAI, etc.)
- API Key input (masked, with validation)
- Model selection dropdown (based on provider)

**Technical Configuration (collapsible section):**
- Sales Engineer's GitHub username/org
- GitHub Personal Access Token (masked)
- dbt Cloud Account ID
- dbt Cloud Service Token (masked)
- Target warehouse type (Snowflake, BigQuery, Databricks, Redshift)

**Action Button**: "Generate Demo Scenario"

### Phase 2: AI-Generated Scenario Review

**Page: "Review Demo Plan"**

The AI returns a detailed, text-based plan including:

**Section 1: Business Context Summary**
- Restated understanding of prospect's industry and use case
- Key business objectives the demo will address

**Section 2: Proposed Data Architecture**
- Description of 3-5 source datasets (tables in seed files)
- Brief description of what each source represents
- Example: "orders.csv - Customer order transactions with order_id, customer_id, order_date, amount"

**Section 3: dbt Model Structure**
- **Staging Layer**: List of staging models (stg_* models)
  - Purpose of each staging model
- **Intermediate Layer**: List of intermediate models (int_* models)
  - Transformations and business logic applied
- **Marts Layer**: Final analytics models (fct_* and dim_* models)
  - Specifically note which model will be incremental
  - Business questions these models answer

**Section 4: Semantic Layer (if applicable)**
- List of key metrics that will be defined
- Entity relationships

**Section 5: Pain Point Demonstrations**
- How dbt features address the prospect's technical pain points
- Specific features to highlight during demo (e.g., testing, lineage, documentation)

**Section 6: Data Quality Scenarios (if pain point mentioned)**
- Specific data quality issues embedded in seed data
- Which dbt tests will catch these issues
- Expected outcomes to demonstrate during demo

**User Actions:**
- "Confirm and Build" button
- "Regenerate with modifications" - Opens text area for additional instructions
- "Edit specific section" - Allow inline edits to the plan

### Phase 3: Project Generation & Provisioning

**Page: "Building Demo Project"**

Display real-time progress with status indicators:

1. ✓ Cloning template repository
2. ✓ Generating seed data files
3. ✓ Creating staging models
4. ✓ Creating intermediate models
5. ✓ Creating marts models
6. ✓ Generating schema.yml files
7. ✓ Creating Semantic Layer configuration (if applicable)
8. ✓ Committing to new GitHub repository
9. ✓ Creating dbt Cloud project via API
10. ✓ Connecting GitHub repository
11. ✓ Configuring warehouse connection
12. ✓ Running initial dbt run

**Final Output:**
- Link to GitHub repository
- Link to dbt Cloud project
- Summary artifact with demo talking points
- (Optional) Data quality scenario guide if applicable

---

## Technical Implementation Details

### 1. Template Repository Structure

The application expects a base template repository with this structure:

```
dbt-demo-template/
├── dbt_project.yml
├── packages.yml
├── models/
│   ├── staging/
│   │   └── .gitkeep
│   ├── intermediate/
│   │   └── .gitkeep
│   └── marts/
│       └── .gitkeep
├── seeds/
│   └── .gitkeep
├── tests/
│   └── .gitkeep
└── README.md
```

### 2. AI Prompt Engineering Strategy

**For Initial Scenario Generation:**

The prompt to the AI should include:
- Company name and industry context
- Discovery call notes
- Technical pain points
- Instruction to output in structured format with clear sections
- Constraint: 3-5 source tables maximum
- Constraint: Easy to medium complexity models
- Requirement: One incremental model in marts layer
- Requirement: Ensure foreign key relationships are consistent

**For Code Generation (Seed Files):**

The prompt should:
- Specify exactly 10 rows per dataset
- Emphasize ID consistency for joins
- Request CSV format
- Include column names and data types
- Request realistic but simple data for the use case

**For Code Generation (dbt Models):**

The prompt should:
- Reference the seed file structures
- Request proper dbt conventions (naming, folder structure)
- Include appropriate dbt configurations (materialization, tags)
- Request schema.yml with tests and descriptions
- Specify that marts layer should have one incremental model
- Include sample documentation in descriptions

**For Semantic Layer (if applicable):**

The prompt should:
- Request semantic_models.yml structure
- Define metrics based on business use case
- Reference the marts models

### 3. File Generation Logic

**Process for each file type:**

**Seed CSV Files:**
- Parse AI response for seed data
- Validate CSV structure
- Ensure foreign key integrity across files
- Write to `seeds/` directory with descriptive names

**Staging Models:**
- One `.sql` file per source in `models/staging/`
- Naming: `stg_{source_name}__{table_name}.sql`
- Use `{{ source() }}` macro
- Include basic column renaming and type casting
- Materialization: view

**Intermediate Models:**
- `.sql` files in `models/intermediate/`
- Naming: `int_{entity}_{description}.sql`
- Include `{{ ref() }}` to staging models
- Business logic transformations
- Materialization: view or ephemeral

**Marts Models:**
- `.sql` files in `models/marts/`
- Naming: `fct_{entity}.sql` or `dim_{entity}.sql`
- Include `{{ ref() }}` to intermediate models
- One model configured as incremental with unique_key
- Materialization: table (or incremental)

**Schema YAML Files:**
- Generate `schema.yml` in each subdirectory
- Include model descriptions
- Add column-level descriptions
- Include generic tests (unique, not_null, relationships)
- Add custom test recommendations for data quality issues

**dbt_project.yml Updates:**
- Configure model paths and materializations
- Set project name to `{company_name}_demo`
- Configure seeds schema

### 4. GitHub Integration

**Repository Creation:**
- Use PyGithub to create new repository
- Naming convention: `{company_name}-dbt-demo-{timestamp}`
- Initialize with README containing demo context
- Set repository to private
- Clone template repository content
- Add generated files
- Commit with meaningful message: "Initial demo project for {company_name}"
- Push to main branch

**Authentication:**
- Use GitHub Personal Access Token with repo scope
- Validate token before proceeding

### 5. dbt Cloud API Integration

**Create Project (API v3):**
```
POST /api/v3/accounts/{account_id}/projects/
```
Payload:
- name: "{Company Name} Demo"
- dbt_project_subdirectory: "" (root)
- connection_id: (from warehouse connection)

**Connect Repository (API v2):**
```
POST /api/v2/accounts/{account_id}/projects/{project_id}/repository/
```
Payload:
- git_clone_strategy: "github_app"
- repository_url: GitHub repo URL
- github_installation_id: (from SE's GitHub app)

**Create Environment (API v3):**
```
POST /api/v3/accounts/{account_id}/projects/{project_id}/environments/
```
Create both:
1. Development environment
2. Production environment (deployment)

**Create Job (API v3):**
```
POST /api/v3/accounts/{account_id}/projects/{project_id}/jobs/
```
Configure:
- dbt build command
- Schedule: manual trigger
- Environment: production

**Trigger Initial Run (API v2):**
```
POST /api/v2/accounts/{account_id}/jobs/{job_id}/run/
```

**Error Handling:**
- Validate all API responses
- Provide clear error messages if provisioning fails
- Offer rollback option (delete created resources)
- Log all API interactions for debugging

### 6. Data Quality Scenario Generation

**When user mentions data quality pain points:**

AI should generate:
1. Specific data anomalies in seed files (e.g., null values, duplicates, orphaned records)
2. dbt test definitions to catch these issues
3. A separate markdown artifact explaining:
   - What data quality issues exist
   - Where they are in the data
   - Which dbt tests will fail
   - How to demonstrate fixing them
   - Talking points about dbt's testing framework

**Output Format:**
- Save as `data_quality_demo_guide.md` in repository
- Also display in the app as downloadable artifact

### 7. State Management

Use server-side session state to maintain:
- User inputs across pages
- AI-generated scenario
- Current build progress
- Generated file contents for review
- API tokens (encrypted in memory)

**Session State Keys:**
```
company_name
industry
discovery_notes
pain_points
ai_scenario
github_repo_url
dbt_cloud_project_url
build_status
```

---

## Security Considerations

1. **API Key Storage**: Never persist API keys to disk, only in session state
2. **Token Masking**: All sensitive inputs should use `type="password"`
3. **Validation**: Validate all tokens before use
4. **Repository Access**: Default to private repositories
5. **Error Messages**: Don't expose sensitive info in error messages
6. **Cleanup**: Clear session state on logout or app restart

---

## Error Handling Strategy

### User Input Validation
- Validate all required fields before proceeding
- Test API tokens with simple API calls
- Check GitHub token scopes
- Verify dbt Cloud account access

### AI Generation Errors
- Retry logic for API timeouts
- Fallback prompts if initial generation fails
- Validate AI output structure before proceeding
- Allow manual editing if AI output is unsatisfactory

### GitHub Errors
- Check for repository name conflicts
- Handle rate limiting
- Verify write permissions
- Provide rollback if commit fails

### dbt Cloud API Errors
- Validate account ID exists
- Check service token permissions
- Handle resource creation failures gracefully
- Provide partial success feedback (e.g., "Repo created but dbt Cloud setup failed")

---

## UI/UX Guidelines

### Best Practices
- Show loading indicators for long-running operations
- Use clear success, error, and warning notifications for feedback
- Collapsible sections for configuration groups
- Tabs for organizing different configuration sections
- Progress bars for build progress
- Download buttons for artifact downloads

### Layout
- Wide layout mode for better readability
- Sidebar for navigation and configuration
- Main area for content and forms
- Clear visual hierarchy with headers and dividers

### Copy and Messaging
- Use dbt terminology consistently
- Provide helpful tooltips for technical fields
- Include examples for text inputs
- Success messages should include next steps

---

## Future Enhancement Considerations

While not in initial scope, document these for future iterations:
1. CRM integration (Salesforce) for auto-population
2. Demo template library (save successful demos)
3. Multi-user collaboration (review/approve workflow)
4. Analytics on demo effectiveness
5. Version control for demo iterations
6. Advanced Semantic Layer with multiple metrics layers
7. Include dbt Mesh examples for large organizations
8. Automated demo video generation with talking points

---

## Testing Requirements

### Unit Tests
- Test seed data generation with correct ID relationships
- Validate dbt model SQL syntax
- Test YAML generation structure
- Verify GitHub API interaction logic
- Test dbt Cloud API payload construction

### Integration Tests
- Test full flow with mock APIs
- Verify file structure matches dbt conventions
- Test repository creation and cleanup
- Validate dbt Cloud project setup

### User Acceptance Criteria
- SE can generate a working demo in under 10 minutes
- All generated models run successfully in dbt Cloud
- Seed data produces meaningful results when queried
- Incremental model processes correctly on re-run
- Data quality scenarios (when applicable) demonstrate clearly

---

## Deliverables Checklist

### Code Artifacts
- [ ] FastAPI backend (api/main.py)
- [ ] React frontend (frontend/)
- [ ] Configuration management module
- [ ] AI interaction module with multi-provider support
- [ ] GitHub integration module
- [ ] dbt Cloud API integration module
- [ ] File generation utilities
- [ ] Requirements.txt with all dependencies
- [ ] .env.example for environment variables
- [ ] README.md with setup instructions

### Documentation
- [ ] User guide for Sales Engineers
- [ ] API configuration guide
- [ ] Troubleshooting guide
- [ ] Example scenarios and outputs

### Templates
- [ ] Base dbt project template repository
- [ ] Prompt templates for AI interactions
- [ ] Demo talking points template

---

## Environment Variables

Required environment variables (for .env):

```
# Optional: Set defaults, but allow UI override
DEFAULT_AI_PROVIDER=openai
DEFAULT_GITHUB_ORG=dbt-labs-demos
DEFAULT_DBT_ACCOUNT_ID=12345
DEFAULT_WAREHOUSE_TYPE=snowflake

# Template repo location
DBT_TEMPLATE_REPO_URL=https://github.com/dbt-labs/dbt-demo-template
```

---

## Development Phases

### Phase 1 (MVP - Initial Release)
- Core UI with all input forms
- AI scenario generation with Claude
- Manual review and confirmation flow
- GitHub repository creation with generated files
- Basic seed and model generation

### Phase 2 (Enhanced)
- dbt Cloud API integration for full automation
- Data quality scenario generation
- Semantic Layer support
- Multi-provider AI support

### Phase 3 (Advanced)
- Modification/iteration on generated demos
- Artifact downloads (talking points, guides)
- Error recovery and rollback features

---

## Success Metrics

Track these metrics to measure success:
1. Time from start to working demo (target: <10 minutes)
2. SE satisfaction score
3. Number of demos generated per week
4. Demo-to-opportunity conversion rate improvement
5. SE adoption rate of the tool

---

## Appendix A: Sample AI Prompts

### Scenario Generation Prompt Template

```
You are an expert dbt consultant creating a demo project for a sales presentation.

Company: {company_name}
Industry: {industry}
Context from discovery call: {discovery_notes}
Technical pain points: {pain_points}
Include Semantic Layer: {include_semantic_layer}

Generate a detailed demo plan that includes:

1. Business Context Summary: Restate your understanding of their use case and objectives

2. Data Architecture: Describe 3-5 source datasets needed. For each source, list column names and types. Keep it simple.

3. dbt Model Structure:
   - Staging models: Purpose and transformations
   - Intermediate models: Business logic applied
   - Marts models: Final analytics models (specify which will be incremental)

4. Semantic Layer (if applicable): Key metrics to define

5. Pain Point Demonstrations: How dbt addresses their specific technical challenges

6. Data Quality Scenarios (if relevant): Specific data issues to demonstrate testing

Keep models easy to medium complexity. Ensure foreign keys across datasets are consistent for proper joins. Use standard dbt naming conventions.

Output in clear sections with markdown formatting.
```

### Seed Data Generation Prompt Template

```
Generate CSV seed data for a dbt demo project.

Context: {business_context}

For each of these datasets: {dataset_descriptions}

Requirements:
- Generate exactly 10 rows per dataset
- Ensure foreign key IDs match across datasets for successful joins
- Use realistic but simple data appropriate for {industry}
- Include data quality issues if specified: {data_quality_issues}
- Output each dataset as a separate CSV with headers

Output format: Present each CSV with clear labels.
```

### dbt Model Generation Prompt Template

```
Generate dbt SQL models for this demo project.

Seed files available: {seed_file_names_and_columns}

Generate:
1. Staging models in models/staging/
   - One per seed file
   - Naming: stg_{source}__{table}.sql
   - Use source() macro
   - Materialized as views

2. Intermediate models in models/intermediate/
   - {intermediate_model_descriptions}
   - Use ref() macro to staging models
   - Materialized as views or ephemeral

3. Marts models in models/marts/
   - {marts_model_descriptions}
   - One model should be incremental with unique_key configuration
   - Use ref() macro to intermediate models
   - Materialized as tables (or incremental)

4. Schema.yml files for each subdirectory with:
   - Model and column descriptions
   - Tests (unique, not_null, relationships)
   - {additional_test_requirements}

Follow dbt best practices and conventions. Include comments in SQL for demo purposes.
```

---

## Appendix B: dbt Cloud API Reference Summary

### Key Endpoints Used

**Projects:**
- `GET /api/v3/accounts/{accountId}/projects/` - List projects
- `POST /api/v3/accounts/{accountId}/projects/` - Create project
- `GET /api/v3/accounts/{accountId}/projects/{projectId}/` - Get project details

**Environments:**
- `POST /api/v3/accounts/{accountId}/projects/{projectId}/environments/` - Create environment
- `PATCH /api/v3/accounts/{accountId}/environments/{environmentId}/` - Update environment

**Jobs:**
- `POST /api/v3/accounts/{accountId}/projects/{projectId}/jobs/` - Create job
- `POST /api/v2/accounts/{accountId}/jobs/{jobId}/run/` - Trigger job run
- `GET /api/v2/accounts/{accountId}/runs/{runId}/` - Get run status

**Repository:**
- `POST /api/v2/accounts/{accountId}/projects/{projectId}/repository/` - Connect repository

### Authentication
All requests require `Authorization: Token {service_token}` header.

---

## Appendix C: File Structure Output Example

```
{company_name}-dbt-demo/
├── README.md (generated with demo context)
├── dbt_project.yml (updated with project name)
├── packages.yml
├── seeds/
│   ├── customers.csv
│   ├── orders.csv
│   ├── products.csv
│   └── order_items.csv
├── models/
│   ├── staging/
│   │   ├── schema.yml
│   │   ├── stg_ecommerce__customers.sql
│   │   ├── stg_ecommerce__orders.sql
│   │   ├── stg_ecommerce__products.sql
│   │   └── stg_ecommerce__order_items.sql
│   ├── intermediate/
│   │   ├── schema.yml
│   │   └── int_orders__pivoted_to_customer.sql
│   └── marts/
│       ├── schema.yml
│       ├── fct_orders.sql (incremental)
│       └── dim_customers.sql
├── tests/
│   └── assert_positive_order_amounts.sql (if data quality demo)
└── data_quality_demo_guide.md (if applicable)
```

---

## Notes for Claude Code Implementation

1. **Start with Core Structure**: Build the app skeleton first with all pages/sections before implementing AI logic
2. **Mock AI Responses**: Create sample AI responses for testing before integrating real API calls
3. **Modular Design**: Separate concerns into distinct Python modules (ui, ai, github, dbt_cloud, file_gen)
4. **Configuration Management**: Use Pydantic models for configuration validation
5. **Logging**: Implement comprehensive logging for debugging and audit trail
6. **Error Recovery**: Build in checkpoints so partial failures don't lose all progress
7. **Testing Strategy**: Unit test file generation logic independently before integration
8. **Prompt Engineering**: Iterate on AI prompts with clear structure and constraints
9. **User Feedback**: Use proper status indicators for real-time progress updates
10. **Documentation**: Comment code thoroughly, especially prompt construction and API interactions

This requirements document provides the complete specification needed to build the dbt Cloud Demo Automation tool. All technical details, constraints, and user flows are defined for implementation.
