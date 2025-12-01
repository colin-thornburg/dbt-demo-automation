"""
dbt Cloud API Client
Handles API calls to dbt Cloud for job triggering and management
"""

import requests
from typing import Dict, Optional
import time
import re


def convert_github_url_to_git_format(url: str) -> str:
    """
    Convert GitHub HTTPS URL to git:// format with .git suffix
    
    Examples:
        https://github.com/user/repo -> git://github.com/user/repo.git
        https://github.com/user/repo.git -> git://github.com/user/repo.git
        git://github.com/user/repo.git -> git://github.com/user/repo.git (no change)
    
    Args:
        url: GitHub repository URL in any format
    
    Returns:
        URL in git:// format with .git suffix
    """
    if not url:
        return url
    
    # If already in git:// format, ensure it has .git suffix
    if url.startswith("git://"):
        if not url.endswith(".git"):
            return url + ".git"
        return url
    
    # Convert https://github.com/user/repo to git://github.com/user/repo.git
    # Handle both with and without .git suffix
    pattern = r'https?://github\.com/([^/]+/[^/]+?)(?:\.git)?/?$'
    match = re.match(pattern, url)
    if match:
        repo_path = match.group(1)
        return f"git://github.com/{repo_path}.git"
    
    # If pattern doesn't match, return as-is (might be SSH format or other)
    return url


def generate_pr_url_template(repo_url: str) -> str:
    """
    Generate PR URL template from repository URL
    
    Args:
        repo_url: Repository URL in any format
    
    Returns:
        PR URL template, e.g., "https://github.com/{owner}/{repo}/pull/{number}"
    """
    if not repo_url:
        return ""
    
    # Extract owner/repo from various URL formats
    patterns = [
        r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$',  # https://github.com/owner/repo
        r'git://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$',  # git://github.com/owner/repo.git
    ]
    
    for pattern in patterns:
        match = re.search(pattern, repo_url)
        if match:
            owner = match.group(1)
            repo = match.group(2).rstrip('.git')
            return f"https://github.com/{owner}/{repo}/pull/{{number}}"
    
    return ""


class DbtCloudApiClient:
    """Client for interacting with dbt Cloud API"""
    
    def __init__(self, account_id: str, api_token: str, host: str = "cloud.getdbt.com"):
        """
        Initialize dbt Cloud API client
        
        Args:
            account_id: dbt Cloud account ID
            api_token: API token (service token or PAT)
            host: dbt Cloud host (default: cloud.getdbt.com)
        """
        self.account_id = account_id
        self.api_token = api_token
        self.base_url = f"https://{host}/api/v2/accounts/{account_id}"
        self.base_url_v3 = f"https://{host}/api/v3/accounts/{account_id}"
        self.headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        }
        # v3 API uses Bearer token instead of Token
        self.headers_v3 = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def trigger_job(self, job_id: str, cause: str = "Initial build from demo automation") -> Dict:
        """
        Trigger a job run
        
        Args:
            job_id: ID of the job to trigger
            cause: Reason for triggering the job
        
        Returns:
            Dictionary with run information
        """
        url = f"{self.base_url}/jobs/{job_id}/run/"
        
        payload = {
            "cause": cause
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def get_run_status(self, run_id: str) -> Dict:
        """
        Get status of a job run
        
        Args:
            run_id: ID of the run
        
        Returns:
            Dictionary with run status
        """
        url = f"{self.base_url}/runs/{run_id}/"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def wait_for_run_completion(
        self, 
        run_id: str, 
        timeout: int = 600,
        poll_interval: int = 10
    ) -> Dict:
        """
        Wait for a run to complete
        
        Args:
            run_id: ID of the run to wait for
            timeout: Maximum time to wait in seconds (default: 600 = 10 min)
            poll_interval: How often to check status in seconds (default: 10)
        
        Returns:
            Final run status dictionary
        
        Raises:
            TimeoutError: If run doesn't complete within timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            run_status = self.get_run_status(run_id)
            status = run_status['data']['status']
            
            # Terminal states
            if status in [10, 20, 30]:  # Success, Error, Cancelled
                return run_status
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Run {run_id} did not complete within {timeout} seconds")
    
    def list_jobs(self, project_id: Optional[str] = None) -> Dict:
        """
        List jobs in the account
        
        Args:
            project_id: Optional project ID to filter by
        
        Returns:
            Dictionary with list of jobs
        """
        url = f"{self.base_url}/jobs/"
        
        params = {}
        if project_id:
            params['project_id'] = project_id
        
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def get_job(self, job_id: str) -> Dict:
        """
        Get details of a specific job
        
        Args:
            job_id: ID of the job
        
        Returns:
            Dictionary with job details
        """
        url = f"{self.base_url}/jobs/{job_id}/"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def get_project(self, project_id: str) -> Dict:
        """
        Get details of a specific project
        
        Args:
            project_id: ID of the project
        
        Returns:
            Dictionary with project details including repository info
        """
        url = f"{self.base_url}/projects/{project_id}/"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def update_project_repository(
        self,
        project_id: str,
        repository_id: int,
        remote_url: str,
        github_installation_id: int
    ) -> Dict:
        """
        Update a project's repository configuration
        
        This can trigger dbt Cloud to re-fetch repository metadata from GitHub.
        
        Args:
            project_id: Project ID
            repository_id: Repository ID
            remote_url: GitHub repository URL
            github_installation_id: GitHub App installation ID
        
        Returns:
            Updated repository information
        """
        url = f"{self.base_url}/projects/{project_id}/repository/"
        
        payload = {
            "id": repository_id,
            "remote_url": remote_url,
            "github_installation_id": github_installation_id,
            "git_clone_strategy": "github_app"
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def get_connection(self, project_id: str, connection_id: str) -> Dict:
        """
        Get details of a specific connection
        
        Args:
            project_id: Project ID
            connection_id: Connection ID
        
        Returns:
            Dictionary with connection details
        """
        url = f"{self.base_url}/projects/{project_id}/connections/{connection_id}/"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def list_connections(self, project_id: str) -> Dict:
        """
        List all connections for a project
        
        Args:
            project_id: Project ID
        
        Returns:
            Dictionary with list of connections
        """
        url = f"{self.base_url}/projects/{project_id}/connections/"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def get_environment(self, project_id: str, environment_id: str) -> Dict:
        """
        Get details of a specific environment
        
        Args:
            project_id: Project ID
            environment_id: Environment ID
        
        Returns:
            Dictionary with environment details including connection and credential info
        """
        url = f"{self.base_url}/projects/{project_id}/environments/{environment_id}/"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def list_environments(self, project_id: str) -> Dict:
        """
        List all environments for a project
        
        Args:
            project_id: Project ID
        
        Returns:
            Dictionary with list of environments
        """
        url = f"{self.base_url}/projects/{project_id}/environments/"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def update_repository_v3(
        self,
        project_id: str,
        repository_id: int,
        remote_url: Optional[str] = None,
        github_installation_id: Optional[int] = None,
        git_clone_strategy: Optional[str] = None,
        pull_request_url_template: Optional[str] = None
    ) -> Dict:
        """
        Update a repository using dbt Cloud API v3 (Admin API)
        
        This endpoint is more reliable for resolving timing issues with repository creation.
        Uses PATCH method and Bearer token authentication.
        
        Reference: https://docs.getdbt.com/dbt-cloud/api-v3#/operations/Update%20Repository
        
        Args:
            project_id: Project ID
            repository_id: Repository ID
            remote_url: GitHub repository URL (optional) - should be in git:// format with .git suffix
            github_installation_id: GitHub App installation ID (optional)
            git_clone_strategy: Git clone strategy, e.g., "github_app" (optional)
            pull_request_url_template: PR URL template, e.g., "https://github.com/{owner}/{repo}/pull/{number}" (optional)
        
        Returns:
            Updated repository information
        """
        url = f"{self.base_url_v3}/projects/{project_id}/repositories/{repository_id}/"
        
        # Build payload with only provided fields
        payload = {}
        if remote_url is not None:
            payload["remote_url"] = remote_url
        if github_installation_id is not None:
            payload["github_installation_id"] = github_installation_id
        if git_clone_strategy is not None:
            payload["git_clone_strategy"] = git_clone_strategy
        if pull_request_url_template is not None:
            payload["pull_request_url_template"] = pull_request_url_template
        
        # Use PATCH method for v3 API
        response = requests.patch(url, json=payload, headers=self.headers_v3)
        response.raise_for_status()
        
        return response.json()


def trigger_initial_job_run(
    account_id: str,
    api_token: str,
    job_id: str,
    wait_for_completion: bool = False,
    host: str = "cloud.getdbt.com"
) -> Dict:
    """
    Trigger an initial job run after provisioning
    
    Args:
        account_id: dbt Cloud account ID
        api_token: API token
        job_id: Job ID to trigger
        wait_for_completion: Whether to wait for the run to complete
        host: dbt Cloud host
    
    Returns:
        Dictionary with run information and status
    """
    client = DbtCloudApiClient(account_id, api_token, host)
    
    # Trigger the job
    run_response = client.trigger_job(
        job_id=job_id,
        cause="Initial build from demo automation - generating artifacts"
    )
    
    run_id = run_response['data']['id']
    run_url = run_response['data'].get('href', '')
    
    result = {
        'run_id': run_id,
        'run_url': run_url,
        'status': 'triggered',
        'trigger_response': run_response
    }
    
    # Optionally wait for completion
    if wait_for_completion:
        try:
            final_status = client.wait_for_run_completion(run_id)
            result['status'] = 'completed'
            result['final_status'] = final_status
        except TimeoutError as e:
            result['status'] = 'timeout'
            result['error'] = str(e)
    
    return result

