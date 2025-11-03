"""
GitHub Repository Manager
Handles cloning template, creating new repos, and pushing files
"""

import os
import re
import tempfile
import shutil
from typing import Dict, Optional
from pathlib import Path
from github import Github, GithubException
from src.file_generation import GeneratedFiles
from src.ai.scenario_generator import DemoScenario


def sanitize_repo_name(name: str, fallback: str = "dbt-demo-project") -> str:
    """
    Normalize a repository name so it is GitHub-safe.

    Args:
        name: User-provided repository name
        fallback: Value to use if the sanitized name is empty

    Returns:
        Sanitized repository name
    """
    def _normalize(value: str) -> str:
        slug = re.sub(r'[^a-z0-9]+', '-', (value or '').lower())
        slug = re.sub(r'-{2,}', '-', slug).strip('-')
        return slug[:100].strip('-')

    slug = _normalize(name)
    if slug:
        return slug

    fallback_slug = _normalize(fallback)
    return fallback_slug or "dbt-demo-project"


def default_repo_name(company_name: str) -> str:
    """
    Generate a default repository name based on the company name.

    Args:
        company_name: Name of the prospect company

    Returns:
        Sanitized default repository name
    """
    base_name = f"dbt-demo-{company_name}"
    return sanitize_repo_name(base_name)


class RepositoryManager:
    """Manages GitHub repository operations"""

    def __init__(self, github_token: str, github_username: str):
        """
        Initialize repository manager

        Args:
            github_token: GitHub Personal Access Token
            github_username: GitHub username or organization
        """
        self.github = Github(github_token)
        self.username = github_username
        self.user = self.github.get_user()

    def create_repository(
        self,
        repo_name: str,
        description: str,
        private: bool = True
    ) -> str:
        """
        Create a new GitHub repository

        Args:
            repo_name: Name for the new repository
            description: Repository description
            private: Whether to make repository private

        Returns:
            Repository clone URL (HTTPS)
        """
        try:
            # Create repository
            repo = self.user.create_repo(
                name=repo_name,
                description=description,
                private=private,
                auto_init=False  # Don't initialize with README
            )

            return repo.clone_url

        except GithubException as e:
            if e.status == 422:
                raise ValueError(f"Repository '{repo_name}' already exists")
            elif e.status == 403:
                raise ValueError(
                    "GitHub token does not have permission to create repositories.\n\n"
                    "Please generate a new token with 'repo' scope:\n"
                    "1. Go to: https://github.com/settings/tokens\n"
                    "2. Click 'Generate new token (classic)'\n"
                    "3. Check the 'repo' scope\n"
                    "4. Copy the new token and update your .env file"
                )
            raise Exception(f"Failed to create repository: {e.data.get('message', str(e))}")

    def clone_template(
        self,
        template_url: str,
        target_dir: Path
    ):
        """
        Clone template repository to local directory

        Args:
            template_url: Template repository URL
            target_dir: Local directory to clone into
        """
        import subprocess

        try:
            # Clone the template repository
            subprocess.run(
                ['git', 'clone', template_url, str(target_dir)],
                check=True,
                capture_output=True,
                text=True
            )

            # Remove .git directory to start fresh
            git_dir = target_dir / '.git'
            if git_dir.exists():
                shutil.rmtree(git_dir)

        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to clone template: {e.stderr}")

    def add_generated_files(
        self,
        repo_dir: Path,
        generated_files: GeneratedFiles
    ):
        """
        Add generated files to the repository directory

        Args:
            repo_dir: Repository directory path
            generated_files: Generated files object
        """
        all_files = generated_files.all_files()

        for filepath, content in all_files.items():
            full_path = repo_dir / filepath

            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(full_path, 'w') as f:
                f.write(content)

    def push_to_repository(
        self,
        repo_dir: Path,
        repo_url: str,
        github_token: str,
        commit_message: str = "Initial commit: dbt demo project"
    ):
        """
        Initialize git and push to remote repository

        Args:
            repo_dir: Local repository directory
            repo_url: Remote repository URL
            github_token: GitHub token for authentication
            commit_message: Commit message
        """
        import subprocess

        try:
            # Convert HTTPS URL to authenticated format
            auth_url = repo_url.replace('https://', f'https://{github_token}@')

            # Git commands
            commands = [
                ['git', 'init'],
                ['git', 'add', '.'],
                ['git', 'commit', '-m', commit_message],
                ['git', 'branch', '-M', 'main'],
                ['git', 'remote', 'add', 'origin', auth_url],
                ['git', 'push', '-u', 'origin', 'main']
            ]

            # Execute commands in the repo directory
            for cmd in commands:
                subprocess.run(
                    cmd,
                    cwd=repo_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )

        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to push to repository: {e.stderr}")


def create_mesh_repositories(
    scenario: DemoScenario,
    mesh_projects: Dict[str, GeneratedFiles],
    github_token: str,
    github_username: str,
    template_repo_url: str,
    base_repo_name: Optional[str] = None
) -> Dict[str, Dict[str, str]]:
    """
    Create multiple repositories for mesh demo
    
    Args:
        scenario: Demo scenario
        mesh_projects: Dictionary of GeneratedFiles objects (producer, consumer_1, etc.)
        github_token: GitHub Personal Access Token
        github_username: GitHub username or organization
        template_repo_url: Template repository URL
        base_repo_name: Base repository name (will append -producer, -consumer-1, etc.)
        
    Returns:
        Dictionary mapping project key to repository info
    """
    manager = RepositoryManager(github_token, github_username)
    
    # Determine base repository name
    default_base = default_repo_name(scenario.company_name)
    base_name = base_repo_name or default_base
    
    results = {}
    
    # Create producer repository
    producer_name = f"{base_name}-producer"
    producer_files = mesh_projects.get('producer')
    if producer_files:
        producer_info = _create_single_repo(
            manager=manager,
            scenario=scenario,
            generated_files=producer_files,
            repo_name=producer_name,
            description=f"Producer project for {scenario.company_name} dbt Mesh demo",
            template_repo_url=template_repo_url,
            github_token=github_token
        )
        results['producer'] = producer_info
    
    # Create consumer repositories
    for key in sorted(mesh_projects.keys()):
        if key.startswith('consumer_'):
            consumer_index = key.replace('consumer_', '')
            consumer_name = f"{base_name}-consumer-{consumer_index}"
            consumer_files = mesh_projects[key]
            
            consumer_info = _create_single_repo(
                manager=manager,
                scenario=scenario,
                generated_files=consumer_files,
                repo_name=consumer_name,
                description=f"Consumer project {consumer_index} for {scenario.company_name} dbt Mesh demo",
                template_repo_url=template_repo_url,
                github_token=github_token
            )
            results[key] = consumer_info
    
    return results


def _create_single_repo(
    manager: RepositoryManager,
    scenario: DemoScenario,
    generated_files: GeneratedFiles,
    repo_name: str,
    description: str,
    template_repo_url: str,
    github_token: str
) -> Dict[str, str]:
    """
    Helper function to create a single repository
    """
    import tempfile
    from pathlib import Path
    
    final_repo_name = sanitize_repo_name(repo_name)
    
    # Create temporary directory for repository
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = Path(temp_dir) / final_repo_name
        
        # Step 1: Clone template repository
        manager.clone_template(template_repo_url, repo_dir)
        
        # Step 2: Add generated files
        manager.add_generated_files(repo_dir, generated_files)
        
        # Step 3: Create GitHub repository
        clone_url = manager.create_repository(
            repo_name=final_repo_name,
            description=description,
            private=True
        )
        
        # Step 4: Push to GitHub
        manager.push_to_repository(
            repo_dir=repo_dir,
            repo_url=clone_url,
            github_token=github_token,
            commit_message=f"Initial commit: {scenario.company_name} dbt demo"
        )
    
    # Return repository info
    repo_url = f"https://github.com/{manager.username}/{final_repo_name}"
    
    return {
        'repo_url': repo_url,
        'repo_name': final_repo_name,
        'clone_url': clone_url,
        'description': description
    }


def create_demo_repository(
    scenario: DemoScenario,
    generated_files: GeneratedFiles,
    github_token: str,
    github_username: str,
    template_repo_url: str,
    repo_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Complete workflow: clone template, add files, create repo, and push

    Args:
        scenario: Demo scenario
        generated_files: Generated dbt files
        github_token: GitHub Personal Access Token
        github_username: GitHub username
        template_repo_url: Template repository URL
        repo_name: Optional repository name override (will be sanitized)

    Returns:
        Dictionary with repository information:
        - repo_url: Repository URL
        - repo_name: Final repository name
        - clone_url: Clone URL
    """
    # Create repository manager
    manager = RepositoryManager(github_token, github_username)

    # Determine repository name
    default_name = default_repo_name(scenario.company_name)
    desired_name = repo_name or default_name
    final_repo_name = sanitize_repo_name(desired_name, fallback=default_name)

    # Create description
    description = f"dbt Cloud demo project for {scenario.company_name} ({scenario.industry})"

    # Create temporary directory for repository
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = Path(temp_dir) / final_repo_name

        # Step 1: Clone template repository
        manager.clone_template(template_repo_url, repo_dir)

        # Step 2: Add generated files
        manager.add_generated_files(repo_dir, generated_files)

        # Step 3: Create GitHub repository
        clone_url = manager.create_repository(
            repo_name=final_repo_name,
            description=description,
            private=True
        )

        # Step 4: Push to GitHub
        manager.push_to_repository(
            repo_dir=repo_dir,
            repo_url=clone_url,
            github_token=github_token,
            commit_message=f"Initial commit: {scenario.company_name} dbt demo"
        )

    # Return repository info
    repo_url = f"https://github.com/{github_username}/{final_repo_name}"

    return {
        'repo_url': repo_url,
        'repo_name': final_repo_name,
        'clone_url': clone_url,
        'description': description
    }
