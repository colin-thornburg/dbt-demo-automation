"""
dbt Cloud API Client
Handles API calls to dbt Cloud for job triggering and management
"""

import requests
from typing import Dict, Optional
import time


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
        self.headers = {
            "Authorization": f"Token {api_token}",
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

