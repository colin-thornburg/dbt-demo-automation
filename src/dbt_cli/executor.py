"""
dbt CLI Executor

Runs dbt commands (seed, run, test, build) via the dbt Cloud CLI
and captures structured output for error analysis.
"""

import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DbtCommandResult:
    """Result of a dbt CLI command execution."""

    command: str
    success: bool
    return_code: int
    stdout: str
    stderr: str
    elapsed_seconds: float = 0.0


class DbtCliExecutor:
    """
    Execute dbt commands in a project directory using the dbt Cloud CLI.

    The Cloud CLI runs commands against dbt Cloud infrastructure, benefiting
    from secure credential storage, automatic deferral, and cross-project ref.
    """

    def __init__(
        self,
        project_dir: Path,
        dbt_cloud_project_id: Optional[str] = None,
        dbt_cloud_token: Optional[str] = None,
        dbt_cloud_host: str = "cloud.getdbt.com",
    ):
        self.project_dir = Path(project_dir)
        self.dbt_cloud_project_id = dbt_cloud_project_id
        self.dbt_cloud_token = dbt_cloud_token
        self.dbt_cloud_host = dbt_cloud_host
        self._dbt_path: Optional[str] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def dbt_path(self) -> Optional[str]:
        """Find the dbt CLI binary."""
        if self._dbt_path is None:
            self._dbt_path = shutil.which("dbt")
        return self._dbt_path

    @property
    def is_available(self) -> bool:
        """Check if dbt CLI is installed on the system."""
        return self.dbt_path is not None

    # ------------------------------------------------------------------
    # Version / type detection
    # ------------------------------------------------------------------

    def get_version_info(self) -> Dict[str, str]:
        """
        Check dbt CLI version and type (Cloud CLI vs dbt Core).

        Returns dict with 'raw', 'type', 'version' keys.
        """
        result = self._run(["--version"], timeout=15)
        raw = (result.stdout + "\n" + result.stderr).strip()
        info: Dict[str, str] = {"raw": raw, "type": "unknown", "version": ""}

        if "dbt Cloud CLI" in raw or "cloud-cli" in raw.lower():
            info["type"] = "cloud_cli"
        elif "dbt Core" in raw or "installed:" in raw.lower():
            info["type"] = "dbt_core"

        # Try to extract version number
        import re
        ver_match = re.search(r"(\d+\.\d+\.\d+)", raw)
        if ver_match:
            info["version"] = ver_match.group(1)

        return info

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup_cloud_config(self) -> None:
        """
        Write ``dbt_cloud.yml`` so the Cloud CLI connects to the right project.
        """
        if not self.dbt_cloud_project_id:
            return

        cloud_yml = self.project_dir / "dbt_cloud.yml"
        cloud_yml.write_text(f'project-id: "{self.dbt_cloud_project_id}"\n')
        logger.info("Wrote dbt_cloud.yml with project-id: %s", self.dbt_cloud_project_id)

    # ------------------------------------------------------------------
    # Command runners
    # ------------------------------------------------------------------

    def _run(self, args: List[str], timeout: int = 300) -> DbtCommandResult:
        """
        Run a dbt command and capture output.

        Args:
            args: dbt sub-command + flags (e.g. ``["build", "--fail-fast"]``)
            timeout: Maximum seconds to wait.
        """
        full_cmd = f"dbt {' '.join(args)}"

        if not self.dbt_path:
            return DbtCommandResult(
                command=full_cmd,
                success=False,
                return_code=-1,
                stdout="",
                stderr=(
                    "dbt CLI not found. Install via:\n"
                    "  brew tap dbt-labs/dbt-cli && brew install dbt\n"
                    "Or: pip install dbt --no-cache-dir"
                ),
            )

        cmd = [self.dbt_path] + args
        env = os.environ.copy()

        # Inject Cloud CLI credentials
        if self.dbt_cloud_token:
            env["DBT_CLOUD_API_KEY"] = self.dbt_cloud_token
        if self.dbt_cloud_host:
            env["DBT_CLOUD_HOST"] = self.dbt_cloud_host

        logger.info("Running: %s  (cwd=%s)", full_cmd, self.project_dir)
        start = time.time()

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            elapsed = time.time() - start
            return DbtCommandResult(
                command=full_cmd,
                success=proc.returncode == 0,
                return_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                elapsed_seconds=round(elapsed, 2),
            )
        except subprocess.TimeoutExpired:
            return DbtCommandResult(
                command=full_cmd,
                success=False,
                return_code=-2,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                elapsed_seconds=round(time.time() - start, 2),
            )
        except Exception as e:
            return DbtCommandResult(
                command=full_cmd,
                success=False,
                return_code=-3,
                stdout="",
                stderr=str(e),
                elapsed_seconds=round(time.time() - start, 2),
            )

    # -- Convenience methods --

    def deps(self, timeout: int = 120) -> DbtCommandResult:
        """Run ``dbt deps`` to install packages."""
        return self._run(["deps"], timeout=timeout)

    def seed(self, full_refresh: bool = False, timeout: int = 180) -> DbtCommandResult:
        """Run ``dbt seed``."""
        args = ["seed"]
        if full_refresh:
            args.append("--full-refresh")
        return self._run(args, timeout=timeout)

    def run(
        self,
        select: Optional[str] = None,
        full_refresh: bool = False,
        timeout: int = 300,
    ) -> DbtCommandResult:
        """Run ``dbt run``."""
        args = ["run"]
        if select:
            args.extend(["--select", select])
        if full_refresh:
            args.append("--full-refresh")
        return self._run(args, timeout=timeout)

    def test(self, select: Optional[str] = None, timeout: int = 300) -> DbtCommandResult:
        """Run ``dbt test``."""
        args = ["test"]
        if select:
            args.extend(["--select", select])
        return self._run(args, timeout=timeout)

    def build(
        self,
        select: Optional[str] = None,
        full_refresh: bool = False,
        fail_fast: bool = False,
        timeout: int = 600,
    ) -> DbtCommandResult:
        """Run ``dbt build`` (seed + run + test in DAG order)."""
        args = ["build"]
        if select:
            args.extend(["--select", select])
        if full_refresh:
            args.append("--full-refresh")
        if fail_fast:
            args.append("--fail-fast")
        return self._run(args, timeout=timeout)

    def compile(self, select: Optional[str] = None, timeout: int = 120) -> DbtCommandResult:
        """Run ``dbt compile`` to check for compilation errors without executing."""
        args = ["compile"]
        if select:
            args.extend(["--select", select])
        return self._run(args, timeout=timeout)
