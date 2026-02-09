"""
dbt Error Parser

Parses dbt CLI output (stdout / stderr) into structured error objects
that can be analysed and fixed by the AI auto-fixer.

Also provides false-positive detection: even when exit code is 0,
some dbt output patterns indicate real failures (e.g. ERROR in seed loading).
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class ErrorCategory(str, Enum):
    """Categories of dbt errors."""

    COMPILATION = "compilation"
    DATABASE = "database"
    TEST_FAILURE = "test_failure"
    SEED_ERROR = "seed_error"
    DEPENDENCY = "dependency"
    YAML_PARSE = "yaml_parse"
    CONNECTION = "connection"
    UNKNOWN = "unknown"


@dataclass
class DbtError:
    """Structured representation of a single dbt error."""

    category: ErrorCategory
    model_name: str = ""
    file_path: str = ""
    message: str = ""
    sql_error_code: str = ""
    raw_output: str = ""
    test_name: str = ""
    column_name: str = ""
    is_warning: bool = False

    def summary(self) -> str:
        parts = [self.category.value]
        if self.model_name:
            parts.append(f"in {self.model_name}")
        if self.file_path:
            parts.append(f"({self.file_path})")
        parts.append(f": {self.message[:200]}")
        return " ".join(parts)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

# Patterns that indicate real errors regardless of exit code.
_ERROR_INDICATORS = [
    "ERROR loading seed",
    "Database Error in",
    "Compilation Error in",
    "Runtime Error in",
    "Failure in test",
    "Failure in seed",
    "Parsing Error",
    "Validation Error",
]

# Summary-line pattern:  "3 of 33 ERROR loading seed ..."
_SUMMARY_ERROR_RE = re.compile(
    r"\d+ of \d+ (ERROR|FAIL)\s+(?:loading\s+)?(?:seed\s+file\s+|model\s+|test\s+)?(\S+)"
)


class DbtErrorParser:
    """Parse dbt CLI output into structured ``DbtError`` objects."""

    # ---- regex patterns ----

    _COMPILATION_RE = re.compile(
        r"Compilation Error in model (\S+) \(([^)]+)\)\s*\n(.*?)(?=\n\n|\Z)",
        re.DOTALL,
    )
    _DATABASE_RE = re.compile(
        r"Database Error in (?:model|test|seed) (\S+) \(([^)]+)\)\s*\n\s*(.*?)(?=\n\n|\Z)",
        re.DOTALL,
    )
    _TEST_FAIL_RE = re.compile(
        r"Failure in test (\S+) \(([^)]+)\)\s*\n(.*?)(?=\n\n|\Z)",
        re.DOTALL,
    )
    _YAML_RE = re.compile(
        r"(?:Parsing|Validation) Error.*?in\s+(\S+\.yml)\s*\n(.*?)(?=\n\n|\Z)",
        re.DOTALL,
    )
    _SEED_RE = re.compile(
        r"(?:Database Error|Runtime Error) in seed (\S+) \(([^)]+)\)\s*\n(.*?)(?=\n\n|\Z)",
        re.DOTALL,
    )
    _SEED_FAILURE_RE = re.compile(
        r"Failure in seed (\S+) \(([^)]+)\)\s*\n(.*?)(?=\n\n|\Z)",
        re.DOTALL,
    )
    _RESULT_LINE_RE = re.compile(r"\d+ of \d+ (PASS|FAIL|ERROR|WARN|SKIP)\s+(\S+)")

    # ---- public API ----

    def parse(self, stdout: str, stderr: str = "") -> List[DbtError]:
        """Return a list of ``DbtError`` objects extracted from dbt output."""
        errors: List[DbtError] = []
        combined = f"{stdout}\n{stderr}"

        # Structured patterns
        for m in self._COMPILATION_RE.finditer(combined):
            errors.append(
                DbtError(
                    category=ErrorCategory.COMPILATION,
                    model_name=m.group(1),
                    file_path=m.group(2),
                    message=m.group(3).strip(),
                    raw_output=m.group(0),
                )
            )

        for m in self._DATABASE_RE.finditer(combined):
            msg = m.group(3).strip()
            sql_code = ""
            code_match = re.match(r"(\d{6})\s+\(\w+\):", msg)
            if code_match:
                sql_code = code_match.group(1)
            errors.append(
                DbtError(
                    category=ErrorCategory.DATABASE,
                    model_name=m.group(1),
                    file_path=m.group(2),
                    message=msg,
                    sql_error_code=sql_code,
                    raw_output=m.group(0),
                )
            )

        for m in self._TEST_FAIL_RE.finditer(combined):
            errors.append(
                DbtError(
                    category=ErrorCategory.TEST_FAILURE,
                    model_name=m.group(1),
                    file_path=m.group(2),
                    message=m.group(3).strip(),
                    test_name=m.group(1),
                    raw_output=m.group(0),
                )
            )

        for m in self._SEED_RE.finditer(combined):
            errors.append(
                DbtError(
                    category=ErrorCategory.SEED_ERROR,
                    model_name=m.group(1),
                    file_path=m.group(2),
                    message=m.group(3).strip(),
                    raw_output=m.group(0),
                )
            )

        for m in self._SEED_FAILURE_RE.finditer(combined):
            name = m.group(1)
            if not any(e.model_name == name for e in errors):
                errors.append(
                    DbtError(
                        category=ErrorCategory.SEED_ERROR,
                        model_name=name,
                        file_path=m.group(2),
                        message=m.group(3).strip(),
                        raw_output=m.group(0),
                    )
                )

        for m in self._YAML_RE.finditer(combined):
            errors.append(
                DbtError(
                    category=ErrorCategory.YAML_PARSE,
                    file_path=m.group(1),
                    message=m.group(2).strip(),
                    raw_output=m.group(0),
                )
            )

        # Capture FAIL / ERROR lines from summary (e.g. "3 of 33 ERROR loading seed ...")
        for m in self._RESULT_LINE_RE.finditer(combined):
            status, name = m.group(1), m.group(2)
            if status in ("FAIL", "ERROR"):
                if not any(e.model_name == name or e.test_name == name for e in errors):
                    errors.append(
                        DbtError(
                            category=(
                                ErrorCategory.TEST_FAILURE
                                if status == "FAIL"
                                else ErrorCategory.UNKNOWN
                            ),
                            model_name=name,
                            message=f"{status}: {name}",
                            raw_output=m.group(0),
                        )
                    )

        # Fallback: generic failure indicators
        if not errors and ("ERROR" in combined or "FAIL" in combined):
            if any(
                kw in combined.lower()
                for kw in ("connection", "timeout", "refused", "authentication")
            ):
                errors.append(
                    DbtError(
                        category=ErrorCategory.CONNECTION,
                        message=self._extract_context(combined),
                        raw_output=combined[-2000:],
                    )
                )
            elif "Error" in combined:
                errors.append(
                    DbtError(
                        category=ErrorCategory.UNKNOWN,
                        message=self._extract_context(combined),
                        raw_output=combined[-2000:],
                    )
                )

        logger.info("Parsed %d error(s) from dbt output", len(errors))
        return errors

    # ---- false-positive detection ----

    @staticmethod
    def has_error_indicators(stdout: str, stderr: str = "") -> bool:
        """
        Check whether dbt output contains error indicators *even if the
        exit code was 0*.  Some dbt versions / configurations can return 0
        while individual nodes still errored.
        """
        combined = f"{stdout}\n{stderr}"
        for indicator in _ERROR_INDICATORS:
            if indicator in combined:
                return True
        # Also check for ERROR summary lines
        if _SUMMARY_ERROR_RE.search(combined):
            return True
        return False

    # ---- helpers ----

    @staticmethod
    def _extract_context(text: str, max_len: int = 500) -> str:
        lines = text.split("\n")
        error_lines = [l.strip() for l in lines if "Error" in l or "FAIL" in l]
        if error_lines:
            return "\n".join(error_lines[:5])
        return text[-max_len:]

    @staticmethod
    def get_error_summary(errors: List[DbtError]) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for e in errors:
            key = e.category.value
            summary[key] = summary.get(key, 0) + 1
        return summary
