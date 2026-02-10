"""
FastAPI Backend for dbt Cloud Demo Automation
Provides REST API endpoints for the React frontend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.config.settings import load_config, AppConfig
from src.ai import get_ai_provider, generate_demo_scenario
from src.ai.scenario_generator import DemoScenario, regenerate_scenario, build_generation_prompts
from src.file_generation import generate_all_files, generate_mesh_projects
from src.github_integration import create_demo_repository, create_mesh_repositories, default_repo_name
from src.terraform_integration import generate_terraform_config, write_terraform_files
from src.terraform_integration.terraform_executor import TerraformExecutor
from src.dbt_cli import DbtCliExecutor, DbtErrorParser, BuildValidator

app = FastAPI(title="dbt Cloud Demo Automation API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (in production, use Redis or similar)
sessions: Dict[str, Dict[str, Any]] = {}


# Request/Response Models
class DemoInputsRequest(BaseModel):
    company_name: str
    industry: str
    discovery_notes: str = ""
    pain_points: str = ""
    include_semantic_layer: bool = False
    mesh_demo: bool = False
    num_downstream_projects: int = 1


class AIConfigRequest(BaseModel):
    provider: str  # 'claude' or 'openai'
    api_key: str
    model: str


class GitHubConfigRequest(BaseModel):
    username: str
    token: str
    template_repo_url: Optional[str] = None


class DbtCloudConfigRequest(BaseModel):
    account_id: str
    service_token: str
    warehouse_type: str = "snowflake"
    project_id: Optional[str] = None
    host: Optional[str] = None
    pat_name: Optional[str] = None
    pat_value: Optional[str] = None
    defer_env_id: Optional[str] = None
    snowflake_user: Optional[str] = None
    snowflake_password: Optional[str] = None


class RegenerateRequest(BaseModel):
    feedback: str


class PromptPreviewRequest(BaseModel):
    company_name: str
    industry: str
    discovery_notes: str = ""
    pain_points: str = ""
    include_semantic_layer: bool = False


class SessionResponse(BaseModel):
    session_id: str


@app.get("/")
async def root():
    return {"message": "dbt Cloud Demo Automation API", "version": "1.0.0"}


@app.post("/api/sessions", response_model=SessionResponse)
async def create_session():
    """Create a new session"""
    import uuid
    session_id = str(uuid.uuid4())
    config = load_config()
    
    sessions[session_id] = {
        "demo_inputs": None,
        "ai_config": None,
        "github_config": None,
        "dbt_config": None,
        "scenario": None,
        "generated_files": None,
        "mesh_projects": None,
        "is_mesh_demo": False,
        "repository_info": None,
        "provisioning_result": None,
        "provisioning_progress": {
            "current_step": None,
            "status": "idle",  # idle, in_progress, completed, error
            "steps": []
        },
        "config": {
            "default_ai_provider": config.default_ai_provider,
            "default_claude_model": config.default_claude_model,
            "default_openai_model": config.default_openai_model,
            "default_github_org": config.default_github_org,
            "dbt_template_repo_url": config.dbt_template_repo_url,
            "default_dbt_account_id": config.default_dbt_account_id,
            "default_warehouse_type": config.default_warehouse_type,
            "default_dbt_cloud_project_id": config.default_dbt_cloud_project_id,
            "default_dbt_cloud_host": config.default_dbt_cloud_host,
            "dbt_cloud_pat_name": config.dbt_cloud_pat_name,
            "dbt_cloud_pat_value": config.dbt_cloud_pat_value,
            "dbt_cloud_defer_env_id": config.dbt_cloud_defer_env_id,
            "snowflake_user": config.snowflake_user,
        }
    }
    
    return SessionResponse(session_id=session_id)


@app.get("/api/sessions/{session_id}/config")
async def get_config(session_id: str):
    """Get configuration defaults from .env"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return sessions[session_id]["config"]


@app.post("/api/sessions/{session_id}/demo-inputs")
async def set_demo_inputs(session_id: str, inputs: DemoInputsRequest):
    """Set demo inputs"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sessions[session_id]["demo_inputs"] = inputs.dict()
    return {"status": "ok"}


@app.post("/api/sessions/{session_id}/ai-config")
async def set_ai_config(session_id: str, config: AIConfigRequest):
    """Set AI configuration"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sessions[session_id]["ai_config"] = config.dict()
    return {"status": "ok"}


@app.post("/api/sessions/{session_id}/github-config")
async def set_github_config(session_id: str, config: GitHubConfigRequest):
    """Set GitHub configuration"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sessions[session_id]["github_config"] = config.dict()
    return {"status": "ok"}


@app.post("/api/sessions/{session_id}/dbt-config")
async def set_dbt_config(session_id: str, config: DbtCloudConfigRequest):
    """Set dbt Cloud configuration"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sessions[session_id]["dbt_config"] = config.dict()
    return {"status": "ok"}


@app.get("/api/sessions/{session_id}/status")
async def get_status(session_id: str):
    """Get configuration status"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    config = load_config()
    
    # Check demo inputs
    demo_inputs = session.get("demo_inputs")
    has_demo_inputs = bool(
        demo_inputs and 
        demo_inputs.get("company_name") and 
        demo_inputs.get("industry")
    )
    
    # Check AI config
    ai_config = session.get("ai_config")
    has_ai_config = bool(ai_config and ai_config.get("api_key"))
    if not has_ai_config:
        # Check .env defaults
        provider = ai_config.get("provider") if ai_config else config.default_ai_provider
        if provider == "claude" and config.anthropic_api_key:
            has_ai_config = True
        elif provider == "openai" and config.openai_api_key:
            has_ai_config = True
    
    # Check GitHub config
    github_config = session.get("github_config")
    has_github_config = bool(
        github_config and 
        github_config.get("username") and 
        github_config.get("token")
    )
    if not has_github_config:
        has_github_config = bool(config.github_token and config.default_github_org)
    
    # Check dbt config
    dbt_config = session.get("dbt_config")
    has_dbt_config = bool(
        dbt_config and 
        dbt_config.get("account_id") and 
        dbt_config.get("service_token")
    )
    if not has_dbt_config:
        has_dbt_config = bool(config.dbt_cloud_service_token and config.default_dbt_account_id)
    
    return {
        "demo_inputs": has_demo_inputs,
        "ai_config": has_ai_config,
        "github_config": has_github_config,
        "dbt_config": has_dbt_config,
        "all_ready": has_demo_inputs and has_ai_config and has_github_config and has_dbt_config
    }


@app.get("/api/sessions/{session_id}/missing-fields")
async def get_missing_fields(session_id: str):
    """Get detailed list of missing required fields (considering .env defaults)"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    config = load_config()
    missing = []
    
    # Check demo inputs
    demo_inputs = session.get("demo_inputs")
    if not demo_inputs or not demo_inputs.get("company_name", "").strip():
        missing.append("Company Name")
    if not demo_inputs or not demo_inputs.get("industry", "").strip():
        missing.append("Industry / Vertical")
    
    # Check AI config
    ai_config = session.get("ai_config")
    provider = ai_config.get("provider") if ai_config else config.default_ai_provider
    api_key = ai_config.get("api_key") if ai_config else None
    
    # Check if API key is missing AND not in .env
    if not api_key or not api_key.strip():
        if provider == "claude":
            if not config.anthropic_api_key:
                missing.append("Claude API Key")
        elif provider == "openai":
            if not config.openai_api_key:
                missing.append("OpenAI API Key")
    
    # Check GitHub config
    github_config = session.get("github_config")
    github_username = github_config.get("username") if github_config else None
    github_token = github_config.get("token") if github_config else None
    
    if (not github_username or not github_username.strip()) and not config.default_github_org:
        missing.append("GitHub Owner (Username or Organization)")
    
    if (not github_token or not github_token.strip()) and not config.github_token:
        missing.append("GitHub Personal Access Token")
    
    # Check dbt Cloud config
    dbt_config = session.get("dbt_config")
    dbt_account_id = dbt_config.get("account_id") if dbt_config else None
    dbt_service_token = dbt_config.get("service_token") if dbt_config else None
    
    if (not dbt_account_id or not dbt_account_id.strip()) and not config.default_dbt_account_id:
        missing.append("dbt Cloud Account ID")
    
    if (not dbt_service_token or not dbt_service_token.strip()) and not config.dbt_cloud_service_token:
        missing.append("dbt Cloud Service Token")
    
    return {
        "missing_fields": missing,
        "all_ready": len(missing) == 0
    }


@app.post("/api/sessions/{session_id}/generate-scenario")
async def generate_scenario(session_id: str):
    """Generate demo scenario using AI"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    demo_inputs = session.get("demo_inputs")
    ai_config = session.get("ai_config")
    config = load_config()
    
    if not demo_inputs:
        raise HTTPException(status_code=400, detail="Demo inputs not set")
    
    # Get AI provider
    provider = ai_config.get("provider") if ai_config else config.default_ai_provider
    api_key = ai_config.get("api_key") if ai_config else None
    
    if not api_key:
        if provider == "claude":
            api_key = config.anthropic_api_key
        elif provider == "openai":
            api_key = config.openai_api_key
    
    if not api_key:
        raise HTTPException(status_code=400, detail="AI API key not configured")
    
    model = ai_config.get("model") if ai_config else (
        config.default_claude_model if provider == "claude" else config.default_openai_model
    )
    
    try:
        ai_provider = get_ai_provider(
            provider_type=provider,
            api_key=api_key,
            model=model
        )
        
        scenario = generate_demo_scenario(
            company_name=demo_inputs["company_name"],
            industry=demo_inputs["industry"],
            ai_provider=ai_provider,
            discovery_notes=demo_inputs.get("discovery_notes", ""),
            pain_points=demo_inputs.get("pain_points", ""),
            include_semantic_layer=demo_inputs.get("include_semantic_layer", False)
        )
        
        # Store scenario
        sessions[session_id]["scenario"] = scenario.model_dump()
        sessions[session_id]["repo_name"] = default_repo_name(scenario.company_name)
        
        return scenario.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/scenario")
async def get_scenario(session_id: str):
    """Get generated scenario"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    scenario = sessions[session_id].get("scenario")
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not generated")
    
    return scenario


@app.post("/api/sessions/{session_id}/regenerate-scenario")
async def regenerate_scenario_endpoint(session_id: str, request: RegenerateRequest):
    """Regenerate scenario with feedback"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    original_scenario_data = session.get("scenario")
    demo_inputs = session.get("demo_inputs")
    ai_config = session.get("ai_config")
    config = load_config()
    
    if not original_scenario_data:
        raise HTTPException(status_code=400, detail="No scenario to regenerate")
    
    # Get AI provider
    provider = ai_config.get("provider") if ai_config else config.default_ai_provider
    api_key = ai_config.get("api_key") if ai_config else None
    
    if not api_key:
        if provider == "claude":
            api_key = config.anthropic_api_key
        elif provider == "openai":
            api_key = config.openai_api_key
    
    if not api_key:
        raise HTTPException(status_code=400, detail="AI API key not configured")
    
    model = ai_config.get("model") if ai_config else (
        config.default_claude_model if provider == "claude" else config.default_openai_model
    )
    
    try:
        ai_provider = get_ai_provider(
            provider_type=provider,
            api_key=api_key,
            model=model
        )
        
        original_scenario = DemoScenario(**original_scenario_data)
        
        new_scenario = regenerate_scenario(
            original_scenario=original_scenario,
            feedback=request.feedback,
            ai_provider=ai_provider,
            discovery_notes=demo_inputs.get("discovery_notes", ""),
            pain_points=demo_inputs.get("pain_points", ""),
            include_semantic_layer=demo_inputs.get("include_semantic_layer", False)
        )
        
        sessions[session_id]["scenario"] = new_scenario.model_dump()
        
        return new_scenario.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/prompt-preview")
async def get_prompt_preview(session_id: str, request: PromptPreviewRequest):
    """Return the exact prompts that will be sent to AI generation."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    prompts = build_generation_prompts(
        company_name=request.company_name,
        industry=request.industry,
        discovery_notes=request.discovery_notes,
        pain_points=request.pain_points,
        include_semantic_layer=request.include_semantic_layer,
    )
    return prompts


@app.post("/api/sessions/{session_id}/generate-files")
async def generate_files_endpoint(session_id: str):
    """Generate dbt project files"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    scenario_data = session.get("scenario")
    demo_inputs = session.get("demo_inputs")
    dbt_config = session.get("dbt_config")
    config = load_config()
    
    if not scenario_data:
        raise HTTPException(status_code=400, detail="Scenario not generated")
    
    try:
        scenario = DemoScenario(**scenario_data)
        mesh_demo = demo_inputs.get("mesh_demo", False) if demo_inputs else False
        num_downstream = demo_inputs.get("num_downstream_projects", 1) if demo_inputs else 1
        
        project_id = None
        if dbt_config:
            project_id = dbt_config.get("project_id")
        if not project_id:
            project_id = config.default_dbt_cloud_project_id
        
        include_semantic_layer = demo_inputs.get("include_semantic_layer", False) if demo_inputs else False
        
        if mesh_demo:
            mesh_projects = generate_mesh_projects(
                scenario,
                num_downstream_projects=num_downstream,
                num_seed_rows=20,
                dbt_cloud_project_id=project_id,
                include_semantic_layer=include_semantic_layer
            )
            sessions[session_id]["mesh_projects"] = {
                k: {
                    "seeds": v.seeds,
                    "models": v.models,
                    "schemas": v.schemas,
                    "semantic_models": v.semantic_models,
                    "metrics_yml": v.metrics_yml,
                    "project_yml": v.project_yml,
                    "readme": v.readme,
                } for k, v in mesh_projects.items()
            }
            sessions[session_id]["is_mesh_demo"] = True
            sessions[session_id]["generated_files"] = {
                "seeds": mesh_projects["producer"].seeds,
                "models": mesh_projects["producer"].models,
                "schemas": mesh_projects["producer"].schemas,
                "semantic_models": mesh_projects["producer"].semantic_models,
                "metrics_yml": mesh_projects["producer"].metrics_yml,
                "project_yml": mesh_projects["producer"].project_yml,
                "readme": mesh_projects["producer"].readme,
            }
        else:
            generated_files = generate_all_files(
                scenario,
                num_seed_rows=20,
                dbt_cloud_project_id=project_id,
                include_semantic_layer=include_semantic_layer
            )
            sessions[session_id]["generated_files"] = {
                "seeds": generated_files.seeds,
                "models": generated_files.models,
                "schemas": generated_files.schemas,
                "semantic_models": generated_files.semantic_models,
                "metrics_yml": generated_files.metrics_yml,
                "project_yml": generated_files.project_yml,
                "readme": generated_files.readme,
            }
            sessions[session_id]["is_mesh_demo"] = False
        
        return {"status": "ok", "is_mesh_demo": mesh_demo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/files")
async def get_files(session_id: str):
    """Get generated files"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    files = sessions[session_id].get("generated_files")
    if not files:
        raise HTTPException(status_code=404, detail="Files not generated")
    
    return files


@app.post("/api/sessions/{session_id}/create-repository")
async def create_repository_endpoint(session_id: str, repo_name: Optional[str] = None):
    """Create GitHub repository"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    generated_files_data = session.get("generated_files")
    scenario_data = session.get("scenario")
    github_config = session.get("github_config")
    config = load_config()
    
    if not generated_files_data:
        raise HTTPException(status_code=400, detail="Files not generated")
    
    if not scenario_data:
        raise HTTPException(status_code=400, detail="Scenario not found")
    
    # Get GitHub config
    username = github_config.get("username") if github_config else None
    token = github_config.get("token") if github_config else None
    
    if not username:
        username = config.default_github_org
    if not token:
        token = config.github_token
    
    if not username or not token:
        raise HTTPException(status_code=400, detail="GitHub configuration not set")
    
    template_repo = github_config.get("template_repo_url") if github_config else config.dbt_template_repo_url
    
    if not repo_name:
        repo_name = session.get("repo_name") or default_repo_name(scenario_data.get("company_name", "demo"))
    
    try:
        scenario = DemoScenario(**scenario_data)
        mesh_demo = session.get("is_mesh_demo", False)
        demo_inputs = session.get("demo_inputs")
        
        # Regenerate files to ensure we have the actual objects (not just dicts)
        # This is necessary because we need GeneratedFiles objects for repository creation
        dbt_config = session.get("dbt_config")
        project_id = None
        if dbt_config:
            project_id = dbt_config.get("project_id")
        if not project_id:
            project_id = config.default_dbt_cloud_project_id
        
        include_semantic_layer = demo_inputs.get("include_semantic_layer", False) if demo_inputs else False
        
        if mesh_demo:
            num_downstream = demo_inputs.get("num_downstream_projects", 1) if demo_inputs else 1
            mesh_projects = generate_mesh_projects(
                scenario,
                num_downstream_projects=num_downstream,
                num_seed_rows=20,
                dbt_cloud_project_id=project_id,
                include_semantic_layer=include_semantic_layer
            )
            # Create repos for all projects
            repo_info = create_mesh_repositories(
                scenario=scenario,
                mesh_projects=mesh_projects,
                github_token=token,
                github_username=username,
                template_repo_url=template_repo,
                base_repo_name=repo_name
            )
            # Format response
            repo_info = {
                "url": repo_info.get("producer", {}).get("repo_url", ""),
                "repositories": repo_info
            }
        else:
            generated_files = generate_all_files(
                scenario,
                num_seed_rows=20,
                dbt_cloud_project_id=project_id,
                include_semantic_layer=include_semantic_layer
            )
            repo_info = create_demo_repository(
                scenario=scenario,
                generated_files=generated_files,
                github_token=token,
                github_username=username,
                template_repo_url=template_repo,
                repo_name=repo_name
            )
            # Format response
            repo_info = {
                "url": repo_info.get("repo_url", ""),
                "repositories": None
            }
        
        sessions[session_id]["repository_info"] = repo_info
        
        return repo_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/repository")
async def get_repository(session_id: str):
    """Get repository info"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    repo_info = sessions[session_id].get("repository_info")
    if not repo_info:
        raise HTTPException(status_code=404, detail="Repository not created")
    
    return repo_info


@app.post("/api/sessions/{session_id}/provision-dbt-cloud")
async def provision_dbt_cloud(session_id: str):
    """Provision dbt Cloud using Terraform"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    repository_info = session.get("repository_info")
    dbt_config = session.get("dbt_config")
    config = load_config()
    
    if not repository_info:
        raise HTTPException(status_code=400, detail="Repository not created")
    
    if not dbt_config:
        raise HTTPException(status_code=400, detail="dbt Cloud configuration not set")
    
    try:
        scenario_data = session.get("scenario")
        if not scenario_data:
            raise HTTPException(status_code=400, detail="Scenario not found")
        
        from src.terraform_integration.terraform_generator import TerraformConfig, generate_tfvars_content
        
        # Get Snowflake credentials - prefer session config, fall back to .env
        snowflake_user = (dbt_config or {}).get("snowflake_user") or config.snowflake_user
        snowflake_password = (dbt_config or {}).get("snowflake_password") or config.snowflake_password
        if hasattr(snowflake_password, "get_secret_value"):
            snowflake_password = snowflake_password.get_secret_value()
        
        # Check for required Terraform configuration
        missing_vars = []
        if not config.github_app_installation_id:
            missing_vars.append("GITHUB_APP_INSTALLATION_ID")
        if not config.snowflake_account:
            missing_vars.append("SNOWFLAKE_ACCOUNT")
        if not config.snowflake_database:
            missing_vars.append("SNOWFLAKE_DATABASE")
        if not config.snowflake_warehouse:
            missing_vars.append("SNOWFLAKE_WAREHOUSE")
        if not config.snowflake_role:
            missing_vars.append("SNOWFLAKE_ROLE")
        if not snowflake_user:
            missing_vars.append("SNOWFLAKE_USER")
        if not snowflake_password:
            missing_vars.append("SNOWFLAKE_PASSWORD")
        
        if missing_vars:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required environment variables for Terraform provisioning: {', '.join(missing_vars)}. Please add these to your .env file."
            )
        
        # Extract project name from scenario
        project_name = f"{scenario_data.get('company_name', 'Demo')} Demo"
        project_description = f"dbt Cloud demo project for {scenario_data.get('company_name', 'Demo')}"
        
        # Get dbt Cloud token - use session config or fall back to .env
        dbt_token = dbt_config.get("service_token") or ""
        if not dbt_token or not dbt_token.strip():
            # Fall back to .env config
            dbt_token = config.dbt_cloud_service_token
            if hasattr(dbt_token, 'get_secret_value'):
                dbt_token = dbt_token.get_secret_value()
        
        # Get dbt Cloud account ID - use session config or fall back to .env
        dbt_account_id = dbt_config.get("account_id") or ""
        if not dbt_account_id or not dbt_account_id.strip():
            dbt_account_id = config.default_dbt_account_id or ""
        
        # Get dbt Cloud host - use session config or fall back to .env
        dbt_host = dbt_config.get("host", "cloud.getdbt.com")
        if not dbt_host or dbt_host.strip() == "":
            dbt_host = config.default_dbt_cloud_host or "cloud.getdbt.com"
        
        if not dbt_token:
            raise HTTPException(
                status_code=400,
                detail="dbt Cloud service token is required. Please provide it in the Setup form or set DBT_CLOUD_SERVICE_TOKEN in your .env file."
            )
        
        if not dbt_account_id:
            raise HTTPException(
                status_code=400,
                detail="dbt Cloud account ID is required. Please provide it in the Setup form or set DEFAULT_DBT_ACCOUNT_ID in your .env file."
            )
        
        # Construct proper host URL for Terraform provider
        dbt_host_url = dbt_host
        if not dbt_host_url.startswith('http'):
            dbt_host_url = f"https://{dbt_host_url}"
        if not dbt_host_url.endswith('/api'):
            dbt_host_url = f"{dbt_host_url}/api"
        
        # Convert repository URL to git:// format with .git suffix (required for proper IDE integration)
        from src.dbt_cloud.api_client import convert_github_url_to_git_format
        repo_url_https = repository_info.get("url", "")
        repo_url_git = convert_github_url_to_git_format(repo_url_https)
        
        # Create Terraform configuration
        terraform_config = TerraformConfig(
            dbt_cloud_account_id=dbt_account_id,
            dbt_cloud_token=dbt_token,
            dbt_cloud_host_url=dbt_host_url,
            project_name=project_name,
            project_description=project_description,
            github_repo_url=repo_url_git,  # Use git:// format from the start
            github_installation_id=config.github_app_installation_id,
            snowflake_account=config.snowflake_account,
            snowflake_database=config.snowflake_database,
            snowflake_warehouse=config.snowflake_warehouse,
            snowflake_role=config.snowflake_role,
            snowflake_user=snowflake_user,
            snowflake_password=snowflake_password,
            snowflake_schema=config.snowflake_schema or "analytics",
            enable_semantic_layer=scenario_data.get("include_semantic_layer", False)
        )
        
        # Generate terraform.tfvars content
        terraform_vars = generate_tfvars_content(terraform_config)
        
        # Initialize progress tracking
        sessions[session_id]["provisioning_progress"] = {
            "current_step": "Preparing Terraform configuration",
            "status": "in_progress",
            "steps": []
        }
        
        def update_progress(step_name: str, status: str = "completed"):
            """Helper to update progress"""
            progress = sessions[session_id].get("provisioning_progress", {})
            progress["current_step"] = step_name
            progress["status"] = "in_progress" if status == "in_progress" else progress["status"]
            if status == "completed":
                progress["steps"].append({"name": step_name, "status": "completed"})
            elif status == "error":
                progress["steps"].append({"name": step_name, "status": "error"})
            sessions[session_id]["provisioning_progress"] = progress
        
        # Write Terraform files to session-specific directory
        update_progress("Preparing Terraform configuration", "in_progress")
        terraform_dir = Path(__file__).parent.parent / "terraform" / f"session_{session_id}"
        terraform_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean up any existing Terraform state/lock files from previous runs
        import shutil
        terraform_lock = terraform_dir / ".terraform.lock.hcl"
        terraform_dir_state = terraform_dir / ".terraform"
        if terraform_lock.exists():
            terraform_lock.unlink()
        if terraform_dir_state.exists():
            shutil.rmtree(terraform_dir_state)
        
        # Write terraform.tfvars
        tfvars_path = terraform_dir / "terraform.tfvars"
        with open(tfvars_path, 'w') as f:
            f.write(terraform_vars)
        
        # Copy main terraform files from template directory
        template_dir = Path(__file__).parent.parent / "terraform"
        for file in ["main.tf", "variables.tf", "outputs.tf", "providers.tf"]:
            src = template_dir / file
            dst = terraform_dir / file
            if src.exists():
                shutil.copy2(src, dst)
        
        update_progress("Preparing Terraform configuration", "completed")
        
        # Execute Terraform
        update_progress("Initializing Terraform", "in_progress")
        executor = TerraformExecutor(terraform_dir)
        # Use -upgrade to allow provider version changes
        init_result = executor.init(upgrade=True)
        if not init_result.success:
            update_progress("Initializing Terraform", "error")
            raise HTTPException(
                status_code=500,
                detail=f"Terraform init failed: {init_result.stderr}"
            )
        update_progress("Initializing Terraform", "completed")
        
        update_progress("Applying Terraform configuration", "in_progress")
        # Always auto-approve when running from API (non-interactive)
        # User has already clicked "Provision" button, so approval is implicit
        apply_result = executor.apply(auto_approve=True)
        if not apply_result.success:
            update_progress("Applying Terraform configuration", "error")
            raise HTTPException(
                status_code=500,
                detail=f"Terraform apply failed: {apply_result.stderr}"
            )
        update_progress("Applying Terraform configuration", "completed")
        
        update_progress("Retrieving Terraform outputs", "in_progress")
        output_result = executor.output()
        if not output_result.success or not output_result.outputs:
            update_progress("Retrieving Terraform outputs", "error")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get Terraform outputs: {output_result.stderr or 'No outputs available'}"
            )
        update_progress("Retrieving Terraform outputs", "completed")
        
        # Format outputs for frontend
        # outputs.outputs is a dict where values are already extracted
        outputs_dict = output_result.outputs
        project_id = str(outputs_dict.get("project_id", ""))
        repository_id = outputs_dict.get("repository_id")
        connection_id = outputs_dict.get("connection_id")
        
        # Verify and refresh connections after Terraform completes
        if project_id:
            try:
                import time
                from src.dbt_cloud.api_client import DbtCloudApiClient
                
                update_progress("Waiting for GitHub App propagation", "in_progress")
                # Wait 30 seconds for GitHub App propagation and connection setup
                time.sleep(30)
                update_progress("Waiting for GitHub App propagation", "completed")
                
                update_progress("Connecting to dbt Cloud API", "in_progress")
                # Create API client
                client = DbtCloudApiClient(
                    account_id=dbt_account_id,
                    api_token=dbt_token,
                    host=dbt_host
                )
                update_progress("Connecting to dbt Cloud API", "completed")
                
                update_progress("Verifying project configuration", "in_progress")
                # Get current project state to verify connections
                project_data = client.get_project(project_id)
                project_info = project_data.get('data', {})
                update_progress("Verifying project configuration", "completed")
                
                # Verify and refresh repository connection using v3 API
                # v3 API is more reliable for resolving timing issues with repository creation
                if repository_id and repository_info.get("url"):
                    update_progress("Updating repository connection (v3 API)", "in_progress")
                    repository = project_info.get('repository', {})
                    
                    if repository and repository.get('id'):
                        import logging
                        from src.dbt_cloud.api_client import convert_github_url_to_git_format, generate_pr_url_template
                        
                        logging.info("Updating repository using dbt Cloud API v3 to resolve timing issues...")
                        
                        # Convert URL to git:// format with .git suffix (required for proper IDE integration)
                        repo_url_https = repository_info.get("url", "")
                        repo_url_git = convert_github_url_to_git_format(repo_url_https)
                        pr_url_template = generate_pr_url_template(repo_url_https)
                        
                        logging.info(f"Converting repository URL: {repo_url_https} -> {repo_url_git}")
                        if pr_url_template:
                            logging.info(f"PR URL template: {pr_url_template}")
                        
                        # Use v3 API to update repository - more reliable for timing issues
                        try:
                            client.update_repository_v3(
                                project_id=project_id,
                                repository_id=int(repository['id']),
                                remote_url=repo_url_git,
                                github_installation_id=int(config.github_app_installation_id),
                                git_clone_strategy="github_app",
                                pull_request_url_template=pr_url_template if pr_url_template else None
                            )
                            logging.info("Repository updated successfully via v3 API with git:// format and PR URL template")
                            update_progress("Updating repository connection (v3 API)", "completed")
                        except Exception as v3_error:
                            # Fallback to v2 API if v3 fails
                            logging.warning(f"v3 API update failed, falling back to v2: {v3_error}")
                            try:
                                client.update_project_repository(
                                    project_id=project_id,
                                    repository_id=int(repository['id']),
                                    remote_url=repo_url_git,  # Use git:// format for v2 as well
                                    github_installation_id=int(config.github_app_installation_id)
                                )
                                logging.info("Repository updated successfully via v2 API (fallback)")
                                update_progress("Updating repository connection (v2 API fallback)", "completed")
                            except Exception as v2_error:
                                logging.warning(f"Both v3 and v2 API updates failed: {v2_error}")
                                update_progress("Updating repository connection", "error")
                
                # Verify Snowflake connection exists and is properly configured
                update_progress("Verifying Snowflake connection", "in_progress")
                import logging
                if connection_id:
                    try:
                        # Try to get the connection details to verify it exists
                        connection_data = client.get_connection(project_id, str(connection_id))
                        logging.info(f"Snowflake connection verified: {connection_data.get('data', {}).get('name', 'Unknown')}")
                        
                        # Also list all connections to ensure it's in the project
                        connections_list = client.list_connections(project_id)
                        connections = connections_list.get('data', [])
                        connection_found = any(
                            str(conn.get('id')) == str(connection_id) 
                            for conn in connections
                        )
                        
                        if not connection_found:
                            logging.warning(f"Connection {connection_id} not found in project connections list - may need manual linking")
                        update_progress("Verifying Snowflake connection", "completed")
                    except Exception as conn_error:
                        # Connection might not be immediately available via API
                        # Check if we can list connections to see what's there
                        try:
                            connections_list = client.list_connections(project_id)
                            connections = connections_list.get('data', [])
                            logging.info(f"Found {len(connections)} connection(s) in project")
                            if connections:
                                logging.info(f"Connection IDs: {[c.get('id') for c in connections]}")
                        except:
                            pass
                        logging.warning(f"Could not verify connection {connection_id} via API: {conn_error}")
                        update_progress("Verifying Snowflake connection", "completed")  # Still mark as completed
                else:
                    # No connection_id in outputs - Terraform might not have created it
                    logging.warning("No connection_id found in Terraform outputs - connection may not have been created")
                    # Try to list connections to see what exists
                    try:
                        connections_list = client.list_connections(project_id)
                        connections = connections_list.get('data', [])
                        if connections:
                            logging.info(f"Found existing connections: {[c.get('name') for c in connections]}")
                        else:
                            logging.warning("No connections found in project - connection creation may have failed")
                    except Exception as list_error:
                        logging.warning(f"Could not list connections: {list_error}")
                    update_progress("Verifying Snowflake connection", "completed")
                
                # Verify environments were created with proper credentials
                update_progress("Verifying environments", "in_progress")
                dev_env_id = outputs_dict.get("dev_environment_id")
                prod_env_id = outputs_dict.get("prod_environment_id")
                
                if dev_env_id:
                    try:
                        dev_env = client.get_environment(project_id, str(dev_env_id))
                        env_data = dev_env.get('data', {})
                        logging.info(f"Development environment verified: {env_data.get('name')} - Connection: {env_data.get('connection_id')}, Credential: {env_data.get('credential_id')}")
                    except Exception as env_error:
                        logging.warning(f"Could not verify development environment: {env_error}")
                
                if prod_env_id:
                    try:
                        prod_env = client.get_environment(project_id, str(prod_env_id))
                        env_data = prod_env.get('data', {})
                        logging.info(f"Production environment verified: {env_data.get('name')} - Connection: {env_data.get('connection_id')}, Credential: {env_data.get('credential_id')}")
                    except Exception as env_error:
                        logging.warning(f"Could not verify production environment: {env_error}")
                
                # List all environments to ensure both are present
                try:
                    environments_list = client.list_environments(project_id)
                    environments = environments_list.get('data', [])
                    logging.info(f"Found {len(environments)} environment(s) in project: {[e.get('name') for e in environments]}")
                except Exception as list_error:
                    logging.warning(f"Could not list environments: {list_error}")
                
                update_progress("Verifying environments", "completed")
                
                update_progress("Finalizing setup", "in_progress")
                # Wait another 10 seconds for refreshes to complete
                time.sleep(10)
                update_progress("Finalizing setup", "completed")
            except Exception as e:
                # Don't fail provisioning if verification/refresh fails
                # Log the error but continue
                import logging
                logging.warning(f"Connection verification/refresh failed (non-critical): {e}")
        
        # Trigger production job if it was created
        production_job_id = outputs_dict.get("production_job_id")
        job_run_id = None
        job_run_url = None
        
        if production_job_id:
            update_progress("Triggering initial production job run", "in_progress")
            try:
                from src.dbt_cloud.api_client import trigger_initial_job_run
                import logging
                
                logging.info(f"Triggering production job {production_job_id} for initial build...")
                
                job_result = trigger_initial_job_run(
                    account_id=dbt_account_id,
                    api_token=dbt_token,
                    job_id=str(production_job_id),
                    wait_for_completion=False,
                    host=dbt_host
                )
                
                job_run_id = job_result.get('run_id')
                job_run_url = job_result.get('run_url')
                
                logging.info(f"Production job triggered successfully. Run ID: {job_run_id}")
                update_progress("Triggering initial production job run", "completed")
            except Exception as job_error:
                import logging
                logging.warning(f"Failed to trigger production job (non-critical): {job_error}")
                update_progress("Triggering initial production job run", "error")
        
        # Mark provisioning as completed
        sessions[session_id]["provisioning_progress"]["status"] = "completed"
        sessions[session_id]["provisioning_progress"]["current_step"] = "Provisioning complete"
        
        result = {
            "project_id": project_id,
            "project_name": outputs_dict.get("project_name"),
            "project_url": outputs_dict.get("project_url"),
            "dev_environment_id": outputs_dict.get("dev_environment_id"),
            "prod_environment_id": outputs_dict.get("prod_environment_id"),
            "production_job_id": production_job_id,
            "job_run_id": job_run_id,
            "job_run_url": job_run_url,
            "repository_id": repository_id,
            "connection_id": outputs_dict.get("connection_id"),
            "message": "Provisioning complete! Your dbt Cloud project has been created with development and production environments.",
            "instructions": f"Both environments are configured with Snowflake connections and credentials. {f'The production job has been triggered (Run ID: {job_run_id}).' if job_run_id else 'You can now run dbt commands in the Development environment or trigger the Production job.'}"
        }
        
        sessions[session_id]["provisioning_result"] = result
        
        return result
    except Exception as e:
        import traceback
        # Mark provisioning as failed
        if session_id in sessions:
            sessions[session_id]["provisioning_progress"]["status"] = "error"
            sessions[session_id]["provisioning_progress"]["current_step"] = f"Error: {str(e)}"
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/api/sessions/{session_id}/provisioning")
async def get_provisioning_result(session_id: str):
    """Get provisioning result"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    result = sessions[session_id].get("provisioning_result")
    if not result:
        raise HTTPException(status_code=404, detail="Provisioning not completed")
    
    return result


@app.get("/api/sessions/{session_id}/provisioning-progress")
async def get_provisioning_progress(session_id: str):
    """Get current provisioning progress"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    progress = sessions[session_id].get("provisioning_progress", {
        "current_step": None,
        "status": "idle",
        "steps": []
    })
    
    return progress


@app.post("/api/sessions/{session_id}/refresh-repository")
async def refresh_repository_connection(session_id: str):
    """Refresh repository connection for an existing dbt Cloud project"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    repository_info = session.get("repository_info")
    dbt_config = session.get("dbt_config")
    provisioning_result = session.get("provisioning_result")
    config = load_config()
    
    if not repository_info:
        raise HTTPException(status_code=400, detail="Repository information not found")
    
    if not provisioning_result or not provisioning_result.get("project_id"):
        raise HTTPException(status_code=400, detail="Project not provisioned yet")
    
    # Get dbt Cloud token - use session config or fall back to .env
    dbt_token = dbt_config.get("service_token") if dbt_config else ""
    if not dbt_token or not dbt_token.strip():
        dbt_token = config.dbt_cloud_service_token
        if hasattr(dbt_token, 'get_secret_value'):
            dbt_token = dbt_token.get_secret_value()
    
    # Get dbt Cloud account ID
    dbt_account_id = dbt_config.get("account_id") if dbt_config else ""
    if not dbt_account_id or not dbt_account_id.strip():
        dbt_account_id = config.default_dbt_account_id or ""
    
    # Get dbt Cloud host
    dbt_host = dbt_config.get("host", "cloud.getdbt.com") if dbt_config else "cloud.getdbt.com"
    if not dbt_host or dbt_host.strip() == "":
        dbt_host = config.default_dbt_cloud_host or "cloud.getdbt.com"
    
    if not dbt_token or not dbt_account_id:
        raise HTTPException(
            status_code=400,
            detail="dbt Cloud credentials required. Please configure in Setup or .env file."
        )
    
    try:
        from src.dbt_cloud.api_client import DbtCloudApiClient
        
        project_id = str(provisioning_result["project_id"])
        repo_url = repository_info.get("url", "")
        
        # Create API client
        client = DbtCloudApiClient(
            account_id=dbt_account_id,
            api_token=dbt_token,
            host=dbt_host
        )
        
        # Get current project state
        project_data = client.get_project(project_id)
        repository = project_data.get('data', {}).get('repository', {})
        
        if not repository or not repository.get('id'):
            raise HTTPException(
                status_code=404,
                detail="Repository not found in project. Please check the project configuration."
            )
        
        # Convert URL to git:// format with .git suffix (required for proper IDE integration)
        from src.dbt_cloud.api_client import convert_github_url_to_git_format, generate_pr_url_template
        
        repo_url_git = convert_github_url_to_git_format(repo_url)
        pr_url_template = generate_pr_url_template(repo_url)
        
        import logging
        logging.info(f"Converting repository URL: {repo_url} -> {repo_url_git}")
        if pr_url_template:
            logging.info(f"PR URL template: {pr_url_template}")
        
        # Update repository connection using v3 API (more reliable for timing issues)
        try:
            client.update_repository_v3(
                project_id=project_id,
                repository_id=int(repository['id']),
                remote_url=repo_url_git,
                github_installation_id=int(config.github_app_installation_id),
                git_clone_strategy="github_app",
                pull_request_url_template=pr_url_template if pr_url_template else None
            )
        except Exception as v3_error:
            # Fallback to v2 API if v3 fails
            logging.warning(f"v3 API update failed, falling back to v2: {v3_error}")
            client.update_project_repository(
                project_id=project_id,
                repository_id=int(repository['id']),
                remote_url=repo_url_git,  # Use git:// format for v2 as well
                github_installation_id=int(config.github_app_installation_id)
            )
        
        return {
            "status": "success",
            "message": "Repository connection refreshed successfully",
            "project_id": project_id,
            "repository_id": repository['id']
        }
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


# ======================================================================
# Build Validation (dbt Cloud CLI + AI Auto-Fix)
# ======================================================================


@app.get("/api/sessions/{session_id}/build-cli-status")
async def get_build_cli_status(session_id: str):
    """Check whether the dbt Cloud CLI is available locally."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    executor = DbtCliExecutor(project_dir=Path("/tmp"))
    info = {
        "cli_available": executor.is_available,
        "cli_path": executor.dbt_path,
    }
    if executor.is_available:
        info["cli_info"] = executor.get_version_info()
    return info


@app.post("/api/sessions/{session_id}/validate-build")
async def start_build_validation(session_id: str):
    """
    Start the dbt build-validate-fix loop.

    Runs dbt build via the Cloud CLI, parses errors, uses AI + dbt
    agent skills to auto-fix, and retries up to 3 times.

    Requires:
    - dbt Cloud CLI installed locally
    - Repository already created and pushed
    - dbt Cloud project already provisioned
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    provisioning_result = session.get("provisioning_result")
    repository_info = session.get("repository_info")
    scenario_data = session.get("scenario")
    ai_config = session.get("ai_config")
    dbt_config = session.get("dbt_config")
    config = load_config()

    if not provisioning_result:
        raise HTTPException(status_code=400, detail="Project not provisioned yet")
    if not repository_info:
        raise HTTPException(status_code=400, detail="Repository not created yet")
    if not scenario_data:
        raise HTTPException(status_code=400, detail="Scenario not found")

    # Get AI provider for auto-fixing
    provider = ai_config.get("provider") if ai_config else config.default_ai_provider
    api_key = ai_config.get("api_key") if ai_config else None
    if not api_key:
        api_key = (
            config.anthropic_api_key if provider == "claude" else config.openai_api_key
        )
    if not api_key:
        raise HTTPException(status_code=400, detail="AI API key required for auto-fix")

    model = ai_config.get("model") if ai_config else (
        config.default_claude_model if provider == "claude" else config.default_openai_model
    )
    ai_provider = get_ai_provider(provider_type=provider, api_key=api_key, model=model)

    # Get dbt Cloud CLI config
    project_id = str(provisioning_result.get("project_id", ""))
    dbt_token = dbt_config.get("service_token") if dbt_config else ""
    if not dbt_token or not dbt_token.strip():
        dbt_token = config.dbt_cloud_service_token
        if hasattr(dbt_token, "get_secret_value"):
            dbt_token = dbt_token.get_secret_value()
    dbt_host = dbt_config.get("host", "cloud.getdbt.com") if dbt_config else "cloud.getdbt.com"
    if not dbt_host or dbt_host.strip() == "":
        dbt_host = config.default_dbt_cloud_host or "cloud.getdbt.com"

    # GitHub credentials for pushing fixes — fall back to .env if session is empty
    github_config = session.get("github_config")
    github_token = github_config.get("token") if github_config else None
    if not github_token or not github_token.strip():
        github_token = config.github_token
    repo_url = repository_info.get("url", "")

    import logging as _log
    _log.info(
        "Build validation: github_token=%s, repo_url=%s",
        "set" if github_token else "MISSING",
        repo_url or "MISSING",
    )

    # Clone the repo to a temp directory
    import tempfile
    import subprocess

    work_dir = Path(tempfile.mkdtemp(prefix="dbt_validate_"))
    repo_clone_url = repo_url
    if github_token and "github.com" in repo_url:
        repo_clone_url = repo_url.replace("https://", f"https://{github_token}@")

    # Initialise build progress tracking
    sessions[session_id]["build_validation"] = {
        "status": "in_progress",
        "current_step": "Cloning repository",
        "steps": [],
        "result": None,
    }

    def update_progress(step: str, status: str):
        bv = sessions[session_id].get("build_validation", {})
        bv["current_step"] = step
        if status == "completed":
            bv["steps"].append({"name": step, "status": "completed"})
        elif status == "error":
            bv["steps"].append({"name": step, "status": "error"})
        sessions[session_id]["build_validation"] = bv

    try:
        # Clone
        update_progress("Cloning repository", "in_progress")
        subprocess.run(
            ["git", "clone", repo_clone_url, str(work_dir / "project")],
            check=True, capture_output=True, text=True,
        )
        project_dir = work_dir / "project"

        # Remove dbt example models if present
        example_dir = project_dir / "models" / "example"
        if example_dir.exists():
            import shutil
            shutil.rmtree(example_dir)

        update_progress("Cloning repository", "completed")

        # Create validator
        validator = BuildValidator(
            ai_provider=ai_provider,
            project_dir=project_dir,
            dbt_cloud_project_id=project_id,
            dbt_cloud_token=dbt_token,
            dbt_cloud_host=dbt_host,
            max_attempts=3,
            on_progress=update_progress,
        )

        if not validator.cli_available:
            sessions[session_id]["build_validation"]["status"] = "cli_not_found"
            sessions[session_id]["build_validation"]["current_step"] = "dbt CLI not found"
            return {
                "status": "cli_not_found",
                "message": (
                    "dbt Cloud CLI not found on this machine. "
                    "Install via: brew tap dbt-labs/dbt-cli && brew install dbt"
                ),
                "install_url": "https://docs.getdbt.com/docs/cloud/cloud-cli-installation",
            }

        # Run the build-fix loop
        build_result = validator.validate(
            github_token=github_token,
            github_repo_url=repo_url,
        )

        # Store result with full transparency: logs, project path, CLI info
        result_data = {
            "success": build_result.success,
            "total_attempts": build_result.total_attempts,
            "message": build_result.message,
            "elapsed_seconds": build_result.elapsed_seconds,
            "files_modified": build_result.files_modified,
            "project_dir": build_result.project_dir,
            "cli_info": build_result.cli_info,
            "pushed_to_github": build_result.pushed_to_github,
            "final_errors": [
                {
                    "category": e.category.value if hasattr(e.category, 'value') else str(e.category),
                    "model_name": e.model_name,
                    "file_path": e.file_path,
                    "message": e.message[:500],
                }
                for e in build_result.final_errors
            ],
            "attempts": [
                {
                    "attempt_number": a.attempt_number,
                    "status": a.status,
                    "error_count": len(a.errors),
                    "fixes_count": len(a.fixes_applied),
                    "logs": a.logs,
                    "errors": [
                        {
                            "category": e.category.value if hasattr(e.category, 'value') else str(e.category),
                            "model_name": e.model_name,
                            "message": e.message[:300],
                        }
                        for e in a.errors
                    ],
                    "fixes": [
                        {"file": f.file_path, "explanation": f.explanation}
                        for f in a.fixes_applied
                    ],
                }
                for a in build_result.attempts
            ],
        }

        sessions[session_id]["build_validation"]["status"] = (
            "completed" if build_result.success else "failed"
        )
        sessions[session_id]["build_validation"]["result"] = result_data
        sessions[session_id]["build_validation"]["current_step"] = (
            "Build validation complete" if build_result.success else build_result.message
        )

        return result_data

    except Exception as e:
        import traceback
        sessions[session_id]["build_validation"]["status"] = "error"
        sessions[session_id]["build_validation"]["current_step"] = f"Error: {str(e)}"
        raise HTTPException(status_code=500, detail=f"{e}\n\n{traceback.format_exc()}")


@app.get("/api/sessions/{session_id}/build-validation")
async def get_build_validation(session_id: str):
    """Get current build validation progress / result."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    bv = sessions[session_id].get("build_validation")
    if not bv:
        return {"status": "idle", "current_step": None, "steps": [], "result": None}
    return bv

