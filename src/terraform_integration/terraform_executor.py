"""
Terraform Executor
Handles execution of Terraform commands
"""

import subprocess
import json
from typing import Optional, Dict, List
from pathlib import Path
from pydantic import BaseModel


class TerraformResult(BaseModel):
    """Result of a Terraform operation"""
    success: bool
    command: str
    stdout: str
    stderr: str
    return_code: int
    outputs: Optional[Dict] = None


class TerraformExecutor:
    """Executes Terraform commands in a given directory"""
    
    def __init__(self, working_dir: Path):
        """
        Initialize Terraform executor
        
        Args:
            working_dir: Directory containing Terraform configuration
        """
        self.working_dir = Path(working_dir)
        
        if not self.working_dir.exists():
            raise ValueError(f"Working directory does not exist: {working_dir}")
    
    def _run_command(
        self,
        args: List[str],
        capture_output: bool = True
    ) -> TerraformResult:
        """
        Run a Terraform command
        
        Args:
            args: Command arguments (e.g., ['init'], ['plan'])
            capture_output: Whether to capture stdout/stderr
        
        Returns:
            TerraformResult object
        """
        
        cmd = ['terraform'] + args
        cmd_str = ' '.join(cmd)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=capture_output,
                text=True,
                check=False
            )
            
            return TerraformResult(
                success=result.returncode == 0,
                command=cmd_str,
                stdout=result.stdout if capture_output else "",
                stderr=result.stderr if capture_output else "",
                return_code=result.returncode
            )
            
        except Exception as e:
            return TerraformResult(
                success=False,
                command=cmd_str,
                stdout="",
                stderr=str(e),
                return_code=-1
            )
    
    def init(self) -> TerraformResult:
        """
        Run terraform init
        
        Returns:
            TerraformResult object
        """
        return self._run_command(['init'])
    
    def plan(self) -> TerraformResult:
        """
        Run terraform plan
        
        Returns:
            TerraformResult object
        """
        return self._run_command(['plan'])
    
    def apply(self, auto_approve: bool = False) -> TerraformResult:
        """
        Run terraform apply
        
        Args:
            auto_approve: Whether to auto-approve the apply
        
        Returns:
            TerraformResult object
        """
        args = ['apply']
        if auto_approve:
            args.append('-auto-approve')
        
        return self._run_command(args)
    
    def output(self) -> TerraformResult:
        """
        Run terraform output to get output values
        
        Returns:
            TerraformResult object with outputs parsed
        """
        result = self._run_command(['output', '-json'])
        
        if result.success and result.stdout:
            try:
                outputs = json.loads(result.stdout)
                # Extract just the values
                result.outputs = {
                    key: val.get('value')
                    for key, val in outputs.items()
                }
            except json.JSONDecodeError:
                pass
        
        return result
    
    def destroy(self, auto_approve: bool = False) -> TerraformResult:
        """
        Run terraform destroy
        
        Args:
            auto_approve: Whether to auto-approve the destroy
        
        Returns:
            TerraformResult object
        """
        args = ['destroy']
        if auto_approve:
            args.append('-auto-approve')
        
        return self._run_command(args)
    
    def validate(self) -> TerraformResult:
        """
        Run terraform validate
        
        Returns:
            TerraformResult object
        """
        return self._run_command(['validate'])


def apply_terraform_config(
    terraform_dir: Path,
    auto_approve: bool = False
) -> Dict[str, TerraformResult]:
    """
    Complete Terraform workflow: init, plan, apply, and get outputs
    
    Args:
        terraform_dir: Directory containing Terraform configuration
        auto_approve: Whether to auto-approve the apply
    
    Returns:
        Dictionary with results for each step
    """
    
    executor = TerraformExecutor(terraform_dir)
    results = {}
    
    # Step 1: Init
    results['init'] = executor.init()
    if not results['init'].success:
        return results
    
    # Step 2: Validate
    results['validate'] = executor.validate()
    if not results['validate'].success:
        return results
    
    # Step 3: Plan
    results['plan'] = executor.plan()
    if not results['plan'].success:
        return results
    
    # Step 4: Apply
    results['apply'] = executor.apply(auto_approve=auto_approve)
    if not results['apply'].success:
        return results
    
    # Step 5: Get outputs
    results['output'] = executor.output()
    
    return results


