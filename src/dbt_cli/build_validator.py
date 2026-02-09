"""
Build Validator

Orchestrates the  build → parse errors → AI fix → rebuild  loop.

Key features:
- False-positive detection: checks stdout for ERROR/FAIL even when exit=0
- Full log capture per attempt (stdout + stderr visible in UI)
- Robust git push with branch detection and full environment
- CLI version detection (Cloud CLI vs dbt Core)
- Final push after successful build to ensure repo is up-to-date
"""

import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from src.file_generation.orchestrator import GeneratedFiles

from .auto_fixer import DbtAutoFixer, FilePatch, FixResult
from .error_parser import DbtError, DbtErrorParser
from .executor import DbtCliExecutor, DbtCommandResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class BuildAttempt:
    """Record of a single build attempt with full log capture."""

    attempt_number: int
    command_result: Optional[DbtCommandResult] = None
    errors: List[DbtError] = field(default_factory=list)
    fixes_applied: List[FilePatch] = field(default_factory=list)
    status: str = "pending"  # pending | building | fixing | success | failed
    # Full captured output for the UI
    logs: str = ""


@dataclass
class BuildResult:
    """Final result of the full build-validation process."""

    success: bool
    total_attempts: int
    attempts: List[BuildAttempt] = field(default_factory=list)
    final_errors: List[DbtError] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    message: str = ""
    elapsed_seconds: float = 0.0
    # Metadata for transparency
    project_dir: str = ""
    cli_info: Dict[str, str] = field(default_factory=dict)
    pushed_to_github: bool = False


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class BuildValidator:
    """
    Orchestrates the dbt build → fix → rebuild loop.

    Typical flow after provisioning:
    1. Clone the repo to a working directory.
    2. Configure dbt Cloud CLI (``dbt_cloud.yml``).
    3. Run ``dbt build``.
    4. On failure: parse errors → AI fix → apply patches → git push → rebuild.
    5. Repeat up to ``max_attempts``.
    6. After final success: ensure all fixes are pushed to GitHub.
    """

    def __init__(
        self,
        ai_provider,
        project_dir: Path,
        dbt_cloud_project_id: Optional[str] = None,
        dbt_cloud_token: Optional[str] = None,
        dbt_cloud_host: str = "cloud.getdbt.com",
        max_attempts: int = 3,
        on_progress: Optional[Callable[[str, str], None]] = None,
    ):
        self.ai_provider = ai_provider
        self.project_dir = Path(project_dir)
        self.max_attempts = max_attempts
        self._progress = on_progress or (lambda *_a: None)

        self.executor = DbtCliExecutor(
            project_dir=project_dir,
            dbt_cloud_project_id=dbt_cloud_project_id,
            dbt_cloud_token=dbt_cloud_token,
            dbt_cloud_host=dbt_cloud_host,
        )
        self.parser = DbtErrorParser()
        self.fixer = DbtAutoFixer(ai_provider=ai_provider, project_dir=project_dir)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def cli_available(self) -> bool:
        return self.executor.is_available

    def get_cli_info(self) -> Dict[str, str]:
        """Return CLI version / type info for UI display."""
        if not self.cli_available:
            return {"type": "not_found", "raw": "", "version": ""}
        return self.executor.get_version_info()

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def validate(
        self,
        generated_files: Optional[GeneratedFiles] = None,
        github_token: Optional[str] = None,
        github_repo_url: Optional[str] = None,
    ) -> BuildResult:
        """
        Run the full build-validation loop.

        Args:
            generated_files: If provided, writes these files to project_dir first.
            github_token: If provided, pushes fixes to GitHub after each fix pass.
            github_repo_url: Remote URL for pushing fixes.
        """
        start = time.time()
        attempts: List[BuildAttempt] = []
        all_modified: List[str] = []
        pushed = False

        can_push = bool(github_token and github_repo_url)
        logger.info(
            "Build validation: can_push=%s, github_token=%s, repo_url=%s",
            can_push,
            "set" if github_token else "MISSING",
            github_repo_url or "MISSING",
        )

        # -- Pre-flight ---------------------------------------------------

        cli_info = self.get_cli_info() if self.cli_available else {"type": "not_found"}

        if not self.cli_available:
            return BuildResult(
                success=False,
                total_attempts=0,
                message=(
                    "dbt Cloud CLI not found. Install it via:\n"
                    "  brew tap dbt-labs/dbt-cli && brew install dbt\n"
                    "Or: pip install dbt --no-cache-dir\n\n"
                    "See: https://docs.getdbt.com/docs/cloud/cloud-cli-installation"
                ),
                elapsed_seconds=round(time.time() - start, 2),
                project_dir=str(self.project_dir),
                cli_info=cli_info,
            )

        # Ensure .gitignore exists so dbt artefacts don't pollute commits
        self._ensure_gitignore()

        # Write files if provided
        if generated_files:
            self._progress("Writing project files", "in_progress")
            self._write_files(generated_files)
            self._progress("Writing project files", "completed")

        # Configure Cloud CLI
        self._progress("Configuring dbt Cloud CLI", "in_progress")
        self.executor.setup_cloud_config()
        self._progress("Configuring dbt Cloud CLI", "completed")

        # Detect branch name
        branch = self._detect_branch()
        logger.info("Detected git branch: %s", branch)

        # Install deps
        self._progress("Installing dbt packages (dbt deps)", "in_progress")
        deps_result = self.executor.deps()
        self._progress(
            f"dbt deps {'succeeded' if deps_result.success else 'had warnings'}",
            "completed",
        )

        # -- Seed pre-check (first attempt only) ---------------------------
        # Run dbt seed separately first to catch CSV / schema issues early
        self._progress("Loading seed data (dbt seed --full-refresh)", "in_progress")
        seed_result = self.executor.seed(full_refresh=True)
        if not seed_result.success or self.parser.has_error_indicators(seed_result.stdout, seed_result.stderr):
            seed_errors = self.parser.parse(seed_result.stdout, seed_result.stderr)
            if seed_errors:
                logger.warning("Seed pre-check failed with %d error(s)", len(seed_errors))
                self._progress(
                    f"Seed loading failed with {len(seed_errors)} error(s) — will attempt fixes",
                    "error",
                )
            else:
                self._progress("Seed loading completed with warnings", "completed")
        else:
            self._progress("Seed data loaded successfully", "completed")

        # -- Build loop ---------------------------------------------------

        for num in range(1, self.max_attempts + 1):
            attempt = BuildAttempt(attempt_number=num)

            self._progress(f"Running dbt build --full-refresh (attempt {num}/{self.max_attempts})", "in_progress")
            attempt.status = "building"

            result = self.executor.build(full_refresh=True)
            attempt.command_result = result

            # Capture full logs for the UI
            log_parts = [f"$ {result.command}", f"Exit code: {result.return_code}", ""]
            if result.stdout:
                log_parts.append("--- stdout ---")
                log_parts.append(result.stdout)
            if result.stderr:
                log_parts.append("--- stderr ---")
                log_parts.append(result.stderr)
            log_parts.append(f"\nElapsed: {result.elapsed_seconds}s")
            attempt.logs = "\n".join(log_parts)

            # ── False-positive detection ──
            apparent_success = result.success
            if apparent_success and self.parser.has_error_indicators(result.stdout, result.stderr):
                logger.warning(
                    "Exit code 0 but ERROR/FAIL indicators found in output — treating as failure"
                )
                apparent_success = False

            if apparent_success:
                attempt.status = "success"
                attempts.append(attempt)

                # Final push: ensure all accumulated fixes are in the repo
                if can_push and all_modified:
                    self._progress("Pushing final fixes to GitHub…", "in_progress")
                    push_ok = self._push_fixes(github_token, github_repo_url, "final", branch)
                    pushed = push_ok
                    self._progress(
                        "All fixes pushed to GitHub" if push_ok else "Warning: final push failed",
                        "completed" if push_ok else "error",
                    )

                self._progress(f"dbt build succeeded (attempt {num})", "completed")
                return BuildResult(
                    success=True,
                    total_attempts=num,
                    attempts=attempts,
                    files_modified=all_modified,
                    message=f"Build passed on attempt {num}."
                    + (" Fixes pushed to GitHub." if pushed else ""),
                    elapsed_seconds=round(time.time() - start, 2),
                    project_dir=str(self.project_dir),
                    cli_info=cli_info,
                    pushed_to_github=pushed,
                )

            # Parse errors
            errors = self.parser.parse(result.stdout, result.stderr)
            attempt.errors = errors

            if not errors:
                errors = [
                    DbtError(
                        category="unknown",
                        message=self.parser._extract_context(result.stdout + "\n" + result.stderr),
                        raw_output=(result.stdout + "\n" + result.stderr)[-3000:],
                    )
                ]
                attempt.errors = errors

            err_summary = self.parser.get_error_summary(errors)
            logger.info("Attempt %d: %d error(s) — %s", num, len(errors), err_summary)
            self._progress(
                f"Build failed with {len(errors)} error(s): {err_summary}",
                "error",
            )

            # Don't fix on the last attempt
            if num >= self.max_attempts:
                attempt.status = "failed"
                attempts.append(attempt)
                self._progress(f"Max attempts reached ({len(errors)} errors remain)", "error")
                break

            # AI fix
            self._progress(
                f"AI analysing {len(errors)} error(s) and generating fixes…",
                "in_progress",
            )
            attempt.status = "fixing"

            fix_result = self.fixer.diagnose_and_fix(errors)

            if not fix_result.success or not fix_result.patches:
                logger.warning(
                    "AI fix failed — success=%s, patches=%d, explanation=%s",
                    fix_result.success,
                    len(fix_result.patches),
                    fix_result.explanation,
                )
                attempt.status = "failed"
                attempt.logs += f"\n\n--- AI Fix Result ---\n{fix_result.explanation}"
                attempts.append(attempt)
                self._progress(
                    f"AI could not generate fixes: {fix_result.explanation}",
                    "error",
                )
                break

            # Apply patches locally
            modified = self.fixer.apply_patches(fix_result.patches)
            attempt.fixes_applied = fix_result.patches
            all_modified.extend(modified)

            # Push fixes to GitHub so the Cloud project picks them up
            if can_push:
                self._progress("Pushing auto-fixes to GitHub…", "in_progress")
                push_ok = self._push_fixes(github_token, github_repo_url, str(num), branch)
                pushed = pushed or push_ok
                self._progress(
                    "Pushed fixes to GitHub" if push_ok else "Warning: push failed",
                    "completed" if push_ok else "error",
                )
            else:
                logger.warning(
                    "Skipping push — github_token=%s, repo_url=%s",
                    "set" if github_token else "MISSING",
                    github_repo_url or "MISSING",
                )

            self._progress(
                f"Applied {len(fix_result.patches)} fix(es), rebuilding…",
                "completed",
            )
            attempt.status = "fixed"
            attempts.append(attempt)

        # -- Post-loop ----------------------------------------------------

        final_errors = attempts[-1].errors if attempts else []
        return BuildResult(
            success=False,
            total_attempts=len(attempts),
            attempts=attempts,
            final_errors=final_errors,
            files_modified=all_modified,
            message=f"Build failed after {len(attempts)} attempt(s) with {len(final_errors)} error(s).",
            elapsed_seconds=round(time.time() - start, 2),
            project_dir=str(self.project_dir),
            cli_info=cli_info,
            pushed_to_github=pushed,
        )

    # ------------------------------------------------------------------
    # Git helpers
    # ------------------------------------------------------------------

    def _detect_branch(self) -> str:
        """Detect the current branch name of the cloned repo."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
            )
            branch = result.stdout.strip()
            return branch if branch else "main"
        except Exception:
            return "main"

    def _ensure_gitignore(self) -> None:
        """Append dbt artefact paths to .gitignore if missing."""
        gitignore = self.project_dir / ".gitignore"
        needed = ["target/", "dbt_packages/", "logs/", "dbt_cloud.yml"]

        existing = ""
        if gitignore.exists():
            existing = gitignore.read_text()

        additions = [p for p in needed if p not in existing]
        if additions:
            with open(gitignore, "a") as f:
                f.write("\n# Added by build validator\n")
                for p in additions:
                    f.write(f"{p}\n")
            logger.info("Updated .gitignore with: %s", additions)

    def _push_fixes(self, token: str, repo_url: str, attempt_label: str, branch: str = "main") -> bool:
        """Commit and push auto-fixes to the GitHub repo. Returns True on success."""
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"

        # Ensure the remote uses the authenticated URL
        auth_url = repo_url
        if token and "github.com" in repo_url:
            auth_url = repo_url.replace("https://", f"https://{token}@")

        def _git(*args, check=True):
            """Run a git command in the project dir."""
            cmd = ["git"] + list(args)
            logger.info("git: %s", " ".join(args))
            return subprocess.run(
                cmd,
                cwd=str(self.project_dir),
                check=check,
                capture_output=True,
                text=True,
                env=env,
            )

        try:
            # Set the remote to the authenticated URL
            _git("remote", "set-url", "origin", auth_url)

            # Stage all changes
            _git("add", "-A")

            # Check if there are actually changes to commit
            status = _git("status", "--porcelain", check=False)
            if not status.stdout.strip():
                logger.info("No changes to commit (attempt %s)", attempt_label)
                return True

            logger.info("Changes to commit:\n%s", status.stdout.strip())

            # Commit
            _git(
                "-c", "user.name=Demo Automation",
                "-c", "user.email=demo-automation@dbt.com",
                "commit", "-m",
                f"Auto-fix: build validation attempt {attempt_label}\n\n"
                f"Automated fixes applied by the dbt demo automation tool.",
            )

            # Push
            result = _git("push", "origin", branch)
            logger.info("Push stdout: %s", result.stdout.strip())
            logger.info("Push stderr: %s", result.stderr.strip())
            logger.info("Successfully pushed fixes to GitHub (attempt %s, branch %s)", attempt_label, branch)
            return True

        except subprocess.CalledProcessError as e:
            logger.error(
                "Failed to push fixes (attempt %s): cmd=%s, returncode=%d, stderr=%s, stdout=%s",
                attempt_label,
                e.cmd,
                e.returncode,
                e.stderr,
                e.stdout,
            )
            return False

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------

    def _write_files(self, generated_files: GeneratedFiles) -> None:
        for filepath, content in generated_files.all_files().items():
            fp = self.project_dir / filepath
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content)

    def get_all_files(self) -> Dict[str, str]:
        """Read back all project files from disk."""
        files: Dict[str, str] = {}
        for ext in ("*.sql", "*.yml", "*.yaml", "*.csv", "*.md"):
            for f in self.project_dir.rglob(ext):
                rel = f.relative_to(self.project_dir)
                if any(p.startswith(".") for p in rel.parts):
                    continue
                if any(p in ("target", "logs", "dbt_packages") for p in rel.parts):
                    continue
                files[str(rel)] = f.read_text()
        return files
