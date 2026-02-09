"""
dbt CLI integration for local build validation and auto-fixing.

Uses the dbt Cloud CLI to run builds locally against dbt Cloud
infrastructure, and leverages AI with embedded dbt agent skills
to automatically diagnose and fix errors.
"""

from .executor import DbtCliExecutor, DbtCommandResult
from .error_parser import DbtErrorParser, DbtError, ErrorCategory
from .auto_fixer import DbtAutoFixer, FilePatch, FixResult
from .build_validator import BuildValidator, BuildResult, BuildAttempt

__all__ = [
    "DbtCliExecutor",
    "DbtCommandResult",
    "DbtErrorParser",
    "DbtError",
    "ErrorCategory",
    "DbtAutoFixer",
    "FilePatch",
    "FixResult",
    "BuildValidator",
    "BuildResult",
    "BuildAttempt",
]
