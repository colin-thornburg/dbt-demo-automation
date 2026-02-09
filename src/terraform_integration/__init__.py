"""
Terraform Integration Module
Handles generation of Terraform configurations and execution
"""

from .terraform_generator import (
    TerraformConfig,
    generate_terraform_config,
    write_terraform_files,
    generate_tfvars_content,
)
from .terraform_executor import (
    TerraformExecutor,
    TerraformResult,
    apply_terraform_config,
)

__all__ = [
    'TerraformConfig',
    'generate_terraform_config',
    'generate_tfvars_content',
    'write_terraform_files',
    'TerraformExecutor',
    'TerraformResult',
    'apply_terraform_config',
]
