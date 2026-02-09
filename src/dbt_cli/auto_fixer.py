"""
dbt Auto-Fixer

Uses AI providers (Claude / OpenAI) augmented with embedded dbt agent
skills knowledge to diagnose and fix errors in generated dbt projects.

Flow:
1. Receive structured errors from the error parser
2. Gather relevant file context (failing model, schema, seed data, upstream refs)
3. Send everything to the AI with dbt best-practices as system context
4. Return file patches that can be applied to fix the errors
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .error_parser import DbtError, ErrorCategory

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Embedded dbt Agent Skills context
# ---------------------------------------------------------------------------
# Distilled from https://github.com/dbt-labs/dbt-agent-skills — the key
# knowledge the AI needs to diagnose and fix common dbt build errors.

DBT_SKILLS_CONTEXT = """
## dbt Best Practices — Agent Skills Reference

### Key Principles
1. **Always inspect the data first.** Before fixing a model, understand the upstream data shape.
2. **Check the DAG.** Understand upstream dependencies before modifying a model.
3. **Work iteratively.** Fix one error at a time, validate, then proceed.
4. **Use ref() for seeds, source() only for warehouse-external sources.**
5. **Avoid SELECT * in joins** — it causes duplicate column errors. Explicitly list columns.
6. **Schema resolution:** When seeds use `+schema: seeds` in dbt_project.yml the actual
   schema is `<target_schema>_seeds`, NOT a literal `seeds` schema.  Never define seeds
   as sources — use the `seeds:` key in schema.yml.
7. **Test what exists.** Only add accepted_values tests after confirming actual column values.

### Common Error Patterns & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| Duplicate column name | `SELECT *` on a JOIN where both tables share a column | Use `base.*` + explicit non-overlapping columns from joined tables |
| Schema does not exist | Seeds defined as `sources:` instead of `seeds:` in schema.yml | Use `seeds:` key; models should `ref()` seeds |
| Model not found | `ref('name')` has a typo or model file is missing | Verify filenames match ref() arguments exactly |
| Test failure (unique/not_null) | Seed data has duplicates or NULLs in tested columns | Fix seed CSV data, or loosen the test |
| Invalid identifier | Column referenced doesn't exist upstream | Check actual columns in the source/upstream model |
| Ambiguous column | Column exists in multiple joined tables without qualifier | Prefix with table alias in JOINs |

### dbt Layer Conventions
- **Staging:** Simple rename/cast, materialized as view, one per source.
- **Intermediate:** Business logic + joins.  Always alias joined columns.
- **Marts:** Final aggregations, materialized as table.
- **Seeds:** Small reference/demo data.  Every table must have a unique `id` column first.

### SQL Style
- Use CTEs (WITH clauses), not subqueries.
- One model per file; lowercase SQL keywords.
- End SELECT with an explicit column list when joining.
"""


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class FilePatch:
    """A proposed file modification to fix a dbt error."""

    file_path: str
    original_content: str
    fixed_content: str
    explanation: str
    error_ref: str = ""


@dataclass
class FixResult:
    """Result of an auto-fix attempt."""

    success: bool
    patches: List[FilePatch] = field(default_factory=list)
    explanation: str = ""
    errors_addressed: int = 0
    errors_remaining: int = 0


# ---------------------------------------------------------------------------
# Auto-fixer
# ---------------------------------------------------------------------------


class DbtAutoFixer:
    """
    AI-powered auto-fixer for dbt build errors.

    Uses the same AI provider as scenario generation, augmented with
    embedded dbt agent skills knowledge.
    """

    def __init__(self, ai_provider, project_dir: Path):
        """
        Args:
            ai_provider: An initialised ClaudeProvider or OpenAIProvider.
            project_dir: Root of the dbt project on disk.
        """
        self.ai_provider = ai_provider
        self.project_dir = Path(project_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def diagnose_and_fix(
        self,
        errors: List[DbtError],
        max_errors: int = 5,
    ) -> FixResult:
        """
        Analyse errors and generate file patches.

        Args:
            errors: Structured errors from the error parser.
            max_errors: Cap on how many errors to address per pass.
        """
        if not errors:
            return FixResult(success=True, explanation="No errors to fix.")

        # Priority: YAML parse > compilation > DB > seed > test > other
        priority = [
            ErrorCategory.YAML_PARSE,
            ErrorCategory.COMPILATION,
            ErrorCategory.DATABASE,
            ErrorCategory.SEED_ERROR,
            ErrorCategory.TEST_FAILURE,
            ErrorCategory.DEPENDENCY,
        ]
        sorted_errors = sorted(
            errors,
            key=lambda e: priority.index(e.category) if e.category in priority else 99,
        )[:max_errors]

        # Gather file context per error
        contexts = [self._gather_context(e) for e in sorted_errors]

        prompt = self._build_prompt(sorted_errors, contexts)

        try:
            response = self.ai_provider.generate(
                prompt=prompt,
                system_prompt=self._system_prompt(),
                temperature=0.2,
                max_tokens=8192,
            )
            patches = self._parse_response(response)
            return FixResult(
                success=len(patches) > 0,
                patches=patches,
                explanation=f"Generated {len(patches)} fix(es) for {len(sorted_errors)} error(s).",
                errors_addressed=len(sorted_errors),
                errors_remaining=len(errors) - len(sorted_errors),
            )
        except Exception as e:
            logger.error("AI fix generation failed: %s", e)
            return FixResult(success=False, explanation=f"Failed to generate fixes: {e}")

    def apply_patches(self, patches: List[FilePatch]) -> List[str]:
        """Write patches to disk. Returns list of modified file paths."""
        modified: List[str] = []
        for p in patches:
            fp = self.project_dir / p.file_path
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(p.fixed_content)
            modified.append(p.file_path)
            logger.info("Applied fix to %s: %s", p.file_path, p.explanation)
        return modified

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are a senior dbt analytics engineer tasked with fixing errors "
            "in a dbt project.  You have deep expertise in dbt best practices, "
            "SQL, and data modelling.\n\n"
            f"{DBT_SKILLS_CONTEXT}\n\n"
            "## Your Task\n"
            "You will receive:\n"
            "1. One or more dbt errors with their full error messages\n"
            "2. The relevant file contents (models, schemas, seed data)\n"
            "3. The dbt_project.yml configuration\n\n"
            "For each error, provide:\n"
            "1. A brief diagnosis (what went wrong and why)\n"
            "2. The exact file fix needed\n\n"
            "## Response Format\n"
            "For each fix, respond with this EXACT format:\n\n"
            "### FIX: <brief description>\n"
            "**File:** <relative file path>\n"
            "**Diagnosis:** <one sentence explanation>\n"
            "```sql\n<complete fixed file content>\n```\n\n"
            "IMPORTANT:\n"
            "- Provide the COMPLETE file content, not just changed lines.\n"
            "- For YAML files use ```yaml, for CSV use ```csv.\n"
            "- Fix the root cause, not the symptom.\n"
            "- If an error is caused by an upstream issue, fix upstream first.\n"
            "- Never add columns that don't exist in the source data.\n"
            "- When fixing duplicate columns, use explicit column lists.\n"
        )

    def _build_prompt(
        self,
        errors: List[DbtError],
        contexts: List[Dict[str, str]],
    ) -> str:
        sections: List[str] = ["# dbt Build Errors to Fix\n"]

        for i, (error, ctx) in enumerate(zip(errors, contexts), 1):
            sections.append(f"## Error {i}: {error.category.value}")
            sections.append(f"**Model/Test:** {error.model_name}")
            if error.file_path:
                sections.append(f"**File:** {error.file_path}")
            sections.append(f"**Message:**\n```\n{error.message}\n```")
            if error.raw_output and error.raw_output != error.message:
                sections.append(f"**Full Output:**\n```\n{error.raw_output[:1500]}\n```")

            sections.append("\n**Relevant Files:**")
            for fpath, content in ctx.items():
                ext = fpath.rsplit(".", 1)[-1] if "." in fpath else "text"
                lang = {"sql": "sql", "yml": "yaml", "yaml": "yaml", "csv": "csv"}.get(ext, "text")
                sections.append(f"\n### {fpath}\n```{lang}\n{content}\n```")
            sections.append("---\n")

        sections.append(
            "Please diagnose each error and provide the exact file fixes needed. "
            "Remember to provide COMPLETE file contents for each fix."
        )
        return "\n".join(sections)

    # ------------------------------------------------------------------
    # Context gathering
    # ------------------------------------------------------------------

    def _gather_context(self, error: DbtError) -> Dict[str, str]:
        """Collect file contents relevant to an error."""
        ctx: Dict[str, str] = {}

        # The failing file itself
        if error.file_path:
            self._read_into(ctx, error.file_path)

        # dbt_project.yml
        self._read_into(ctx, "dbt_project.yml")

        # Layer-level schema.yml
        if error.file_path and error.file_path.startswith("models/"):
            parts = error.file_path.split("/")
            if len(parts) >= 2:
                self._read_into(ctx, f"models/{parts[1]}/schema.yml")

        # Seeds schema
        if error.category in (ErrorCategory.SEED_ERROR, ErrorCategory.TEST_FAILURE):
            self._read_into(ctx, "seeds/schema.yml")

        # Upstream ref() targets
        if error.file_path:
            content = ctx.get(error.file_path, "")
            for ref_name in re.findall(r"ref\(['\"](\w+)['\"]\)", content):
                for prefix in ("models/staging", "models/intermediate", "seeds"):
                    for ext in (".sql", ".csv"):
                        candidate = f"{prefix}/{ref_name}{ext}"
                        if (self.project_dir / candidate).exists():
                            c = (self.project_dir / candidate).read_text()
                            if ext == ".csv":
                                c = "\n".join(c.split("\n")[:15])
                            ctx[candidate] = c

        # For test failures, find matching seed CSV
        if error.category == ErrorCategory.TEST_FAILURE:
            seeds_dir = self.project_dir / "seeds"
            if seeds_dir.is_dir():
                for csv in seeds_dir.glob("*.csv"):
                    if csv.stem in error.model_name or error.model_name in csv.stem:
                        lines = csv.read_text().split("\n")[:20]
                        ctx[f"seeds/{csv.name}"] = "\n".join(lines)

        return ctx

    def _read_into(self, ctx: Dict[str, str], rel_path: str) -> None:
        fp = self.project_dir / rel_path
        if fp.exists() and rel_path not in ctx:
            ctx[rel_path] = fp.read_text()

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(self, response: str) -> List[FilePatch]:
        """Extract ``FilePatch`` objects from the AI response."""
        patches: List[FilePatch] = []

        fix_re = re.compile(
            r"### FIX:\s*(.+?)\n"
            r"\*\*File:\*\*\s*(.+?)\n"
            r"\*\*Diagnosis:\*\*\s*(.+?)\n"
            r"```(?:sql|yaml|csv|text)?\n(.*?)```",
            re.DOTALL,
        )

        for m in fix_re.finditer(response):
            desc = m.group(1).strip()
            fpath = m.group(2).strip().strip("`")
            diag = m.group(3).strip()
            content = m.group(4).strip()

            original = ""
            orig_path = self.project_dir / fpath
            if orig_path.exists():
                original = orig_path.read_text()

            if content and content != original.strip():
                patches.append(
                    FilePatch(
                        file_path=fpath,
                        original_content=original,
                        fixed_content=content + "\n",
                        explanation=f"{desc}: {diag}",
                    )
                )

        # Fallback: more lenient parsing
        if not patches and "```" in response:
            alt_re = re.compile(
                r"(?:file|path)[:\s]*`?([^`\n]+\.\w{2,4})`?\s*\n"
                r"```(?:sql|yaml|csv|text)?\n(.*?)```",
                re.DOTALL | re.IGNORECASE,
            )
            for m in alt_re.finditer(response):
                fpath = m.group(1).strip()
                content = m.group(2).strip()
                orig_path = self.project_dir / fpath
                original = orig_path.read_text() if orig_path.exists() else ""
                if content and content != original.strip():
                    patches.append(
                        FilePatch(
                            file_path=fpath,
                            original_content=original,
                            fixed_content=content + "\n",
                            explanation="AI-generated fix",
                        )
                    )

        logger.info("Parsed %d patch(es) from AI response", len(patches))
        return patches
