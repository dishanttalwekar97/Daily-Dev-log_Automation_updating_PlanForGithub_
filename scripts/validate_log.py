"""
validate_log.py - Daily Development Log Validator

Validates development journal entries in Markdown format for:
- Existence of the logs directory
- Proper file naming conventions (YYYY-MM-DD.md)
- Date syntax and calendar validity (ISO 8601: YYYY-MM-DD)
- Consistency between filename and internal Date field
- Required markdown headings and section structure
- Non-empty content and detection of untouched template placeholders
- Duplicate dates across entries
- Full UTF-8 Unicode compatibility (emojis, accents, international text)

Can be executed locally (Windows, Linux, macOS) and in GitHub Actions CI workflows.
Never modifies or deletes existing user files.
"""

from __future__ import annotations

import argparse
import datetime
import os
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional, Sequence, Tuple


# Required top-level document title
REQUIRED_TITLE = "Daily Development Log"

# Required markdown section headings (h2)
REQUIRED_SECTIONS: Sequence[str] = (
    "Learning",
    "Development",
    "Problems Solved",
    "Challenges and Solutions",
    "Next Steps",
)

# Regex patterns for validation
DATE_LINE_PATTERN = re.compile(r"^Date:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FILENAME_DATE_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$", re.IGNORECASE)
HEADING1_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)
HEADING2_PATTERN = re.compile(r"^##\s+(.+)$", re.MULTILINE)

# Template placeholder phrases that indicate unfilled logs
PLACEHOLDER_SNIPPETS = (
    "Record the actual topics studied",
    "Describe the genuine development work",
    "Record actual coding problems",
    "Describe challenges encountered",
    "Record the next planned learning",
    "YYYY-MM-DD",
)


class ValidationResult:
    """Stores validation outcome and diagnostics for a single log file."""

    def __init__(self, file_path: Path) -> None:
        self.file_path: Path = file_path
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.date_value: Optional[datetime.date] = None
        self.date_str: Optional[str] = None
        self.sections_found: List[str] = []
        self.missing_sections: List[str] = []

    def add_error(self, message: str) -> None:
        """Record a validation error and mark the result as invalid."""
        self.is_valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Record a non-fatal warning."""
        self.warnings.append(message)


class LogValidator:
    """Validates individual markdown development logs and directories of logs."""

    def __init__(self, strict_filenames: bool = True) -> None:
        self.strict_filenames: bool = strict_filenames

    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a single markdown log file."""
        result = ValidationResult(file_path)

        if not file_path.exists():
            result.add_error(f"File not found: {file_path}")
            return result

        if not file_path.is_file():
            result.add_error(f"Target is not a regular file: {file_path}")
            return result

        # Check filename naming convention
        filename_match = FILENAME_DATE_PATTERN.match(file_path.name)
        if not filename_match:
            msg = (
                f"Unexpected Markdown filename '{file_path.name}'. "
                f"Expected format is 'YYYY-MM-DD.md'."
            )
            if self.strict_filenames:
                result.add_error(msg)
            else:
                result.add_warning(msg)

        # Read content with UTF-8 decoding
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            result.add_error(f"File encoding is not valid UTF-8: {exc}")
            return result
        except OSError as exc:
            result.add_error(f"Unable to read file: {exc}")
            return result

        self._validate_content(content, result, filename_match.group(1) if filename_match else None)
        return result

    def _validate_content(
        self,
        content: str,
        result: ValidationResult,
        filename_date: Optional[str],
    ) -> None:
        """Inspect the raw text content of a log file."""
        stripped = content.strip()

        # 1. Detect empty development log files
        if not stripped:
            result.add_error("Log file is completely empty (0 characters).")
            return

        # 2. Check document title (# Daily Development Log)
        h1_matches = HEADING1_PATTERN.findall(content)
        if not h1_matches:
            result.add_error(f"Missing top-level heading. Expected: '# {REQUIRED_TITLE}'")
        elif h1_matches[0].strip().lower() != REQUIRED_TITLE.lower():
            result.add_error(
                f"Top-level heading '# {h1_matches[0].strip()}' does not match "
                f"required '# {REQUIRED_TITLE}'"
            )

        # 3. Detect and validate Date: line
        date_match = DATE_LINE_PATTERN.search(content)
        if not date_match:
            result.add_error("Missing 'Date:' metadata. Expected: 'Date: YYYY-MM-DD'")
        else:
            raw_date = date_match.group(1).strip()
            result.date_str = raw_date

            # Check for untouched placeholder
            if "YYYY-MM-DD" in raw_date:
                result.add_error("Date contains unmodified template placeholder 'YYYY-MM-DD'.")
            elif not ISO_DATE_PATTERN.match(raw_date):
                result.add_error(
                    f"Invalid date format '{raw_date}'. Expected ISO format 'YYYY-MM-DD'."
                )
            else:
                try:
                    parsed_date = datetime.datetime.strptime(raw_date, "%Y-%m-%d").date()
                    result.date_value = parsed_date
                except ValueError as exc:
                    result.add_error(f"Invalid calendar date '{raw_date}': {exc}")

            # Check consistency between filename date and content date
            if filename_date and result.date_str:
                if filename_date != result.date_str:
                    result.add_error(
                        f"Filename date '{filename_date}' does not match "
                        f"content date '{result.date_str}'."
                    )

        # 4. Check required section headings (## Section)
        h2_headings = [h.strip() for h in HEADING2_PATTERN.findall(content)]
        result.sections_found = h2_headings

        # Canonical case-insensitive lookup
        h2_lower_map = {h.lower(): h for h in h2_headings}

        for required in REQUIRED_SECTIONS:
            if required.lower() not in h2_lower_map:
                result.missing_sections.append(required)
                result.add_error(f"Missing required section heading: '## {required}'")

        # 5. Check if log is purely untouched template placeholders
        found_placeholder_count = sum(
            1 for snippet in PLACEHOLDER_SNIPPETS if snippet.lower() in content.lower()
        )
        if found_placeholder_count >= 3:
            # Check if there is genuine user writing
            # Remove headings and template markers to see remaining substance
            test_content = content
            for snippet in PLACEHOLDER_SNIPPETS:
                test_content = test_content.replace(snippet, "")
            for sec in REQUIRED_SECTIONS:
                test_content = test_content.replace(f"## {sec}", "")
            test_content = test_content.replace(f"# {REQUIRED_TITLE}", "")
            test_content = re.sub(r"Date:\s*\S+", "", test_content)
            # Remove markdown bullets and whitespace
            cleaned_text = re.sub(r"[\s\*\-\#]", "", test_content)
            if len(cleaned_text) < 20:
                result.add_error(
                    "Log contains only boilerplate template placeholders without actual "
                    "development notes."
                )

        # 6. Check for empty sections
        self._check_section_bodies(content, result)

    def _check_section_bodies(self, content: str, result: ValidationResult) -> None:
        """Verify that required sections have non-empty bodies."""
        # Split by ## headings
        sections = re.split(r"\n##\s+", content)
        for section_block in sections[1:]:
            lines = section_block.splitlines()
            if not lines:
                continue
            section_title = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
            # Clean out empty bullets like "*" or "-"
            body_clean = re.sub(r"^[\s\*\-]+$", "", body, flags=re.MULTILINE).strip()

            # If section matches one of our required sections, ensure it's not blank
            for req in REQUIRED_SECTIONS:
                if section_title.lower() == req.lower() and not body_clean:
                    result.add_error(f"Section '## {section_title}' has no recorded content.")

    def validate_directory(
        self, dir_path: Path
    ) -> Tuple[bool, List[ValidationResult], List[str]]:
        """
        Validate all Markdown log files in dir_path.

        Returns:
            Tuple of:
                - overall_valid (bool)
                - list of ValidationResults
                - list of directory-wide errors (e.g. duplicate dates, missing directory)
        """
        dir_errors: List[str] = []
        results: List[ValidationResult] = []

        # 1. Check whether logs directory exists
        if not dir_path.exists():
            dir_errors.append(f"Logs directory does not exist: {dir_path}")
            return False, results, dir_errors

        if not dir_path.is_dir():
            dir_errors.append(f"Specified logs path is not a directory: {dir_path}")
            return False, results, dir_errors

        # 2. Find Markdown development logs
        md_files = sorted(dir_path.glob("*.md"))
        if not md_files:
            # Directory exists but contains no markdown logs yet (e.g. only .gitkeep)
            return True, results, dir_errors

        # Validate each individual file
        dates_to_files: Dict[str, List[Path]] = {}

        for md_file in md_files:
            res = self.validate_file(md_file)
            results.append(res)

            if res.date_str:
                dates_to_files.setdefault(res.date_str, []).append(md_file)

        # 3. Detect duplicate dates across daily logs
        for date_str, files in dates_to_files.items():
            if len(files) > 1:
                file_names = ", ".join(f.name for f in files)
                dir_errors.append(
                    f"Duplicate date '{date_str}' declared across multiple files: {file_names}"
                )

        overall_valid = (
            len(dir_errors) == 0 and all(r.is_valid for r in results)
        )
        return overall_valid, results, dir_errors


def format_github_annotations(results: List[ValidationResult], dir_errors: List[str]) -> str:
    """Format GitHub Actions workflow command annotations (::error / ::warning)."""
    lines: List[str] = []
    for err in dir_errors:
        lines.append(f"::error::{err}")

    for res in results:
        file_str = str(res.file_path).replace("\\", "/")
        for err in res.errors:
            lines.append(f"::error file={file_str}::{err}")
        for warn in res.warnings:
            lines.append(f"::warning file={file_str}::{warn}")

    return "\n".join(lines)


def generate_markdown_summary(
    results: List[ValidationResult],
    dir_errors: List[str],
    target_description: str,
) -> str:
    """Generate a clean GitHub Step Summary in Markdown."""
    total_files = len(results)
    valid_files = sum(1 for r in results if r.is_valid)
    failed_files = total_files - valid_files
    overall_status = "PASSED" if (failed_files == 0 and not dir_errors) else "FAILED"
    status_badge = "Pass" if overall_status == "PASSED" else "Fail"

    lines: List[str] = [
        "## Daily Development Log Validation",
        "",
        f"- **Status**: `{status_badge}` ({overall_status})",
        f"- **Target**: `{target_description}`",
        f"- **Files Evaluated**: {total_files}",
        f"- **Passed**: {valid_files}",
        f"- **Failed**: {failed_files}",
        "",
    ]

    if dir_errors:
        lines.append("### Directory-Level Errors")
        for err in dir_errors:
            lines.append(f"- :x: {err}")
        lines.append("")

    if results:
        lines.append("### File Results")
        lines.append("| File | Date | Status | Details |")
        lines.append("|---|---|---|---|")
        for r in results:
            file_name = r.file_path.name
            date_display = r.date_str or "N/A"
            status_icon = ":white_check_mark: Pass" if r.is_valid else ":x: Fail"
            details = "<br>".join(r.errors) if r.errors else "All checks passed"
            if r.warnings:
                details += "<br>" + "<br>".join(f":warning: {w}" for w in r.warnings)
            lines.append(f"| `{file_name}` | `{date_display}` | {status_icon} | {details} |")
        lines.append("")

    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point for validate_log.py."""
    parser = argparse.ArgumentParser(
        description="Validate Daily Development Journal Markdown logs for formatting, date, and structure."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--file",
        "-f",
        type=Path,
        help="Path to a single Markdown log file to validate.",
    )
    group.add_argument(
        "--dir",
        "-d",
        type=Path,
        default=Path("logs"),
        help="Path to the logs directory containing Markdown files (default: logs).",
    )
    parser.add_argument(
        "--summary-file",
        type=Path,
        default=None,
        help="Write GitHub Actions step summary markdown to this file.",
    )
    parser.add_argument(
        "--no-strict-filenames",
        action="store_true",
        help="Treat unexpected filenames as warnings instead of errors.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress informational output and print only errors.",
    )

    args = parser.parse_args(argv)
    validator = LogValidator(strict_filenames=not args.no_strict_filenames)

    results: List[ValidationResult] = []
    dir_errors: List[str] = []
    overall_valid = True

    if args.file:
        target_desc = str(args.file)
        res = validator.validate_file(args.file)
        results.append(res)
        overall_valid = res.is_valid
    else:
        target_desc = str(args.dir)
        overall_valid, results, dir_errors = validator.validate_directory(args.dir)

    # Console output
    if not args.quiet:
        print("=" * 60)
        print(" DAILY DEVELOPMENT LOG VALIDATION REPORT")
        print("=" * 60)
        print(f"Target: {target_desc}")
        print(f"Files checked: {len(results)}")
        print("-" * 60)

    if dir_errors:
        print("\n[DIRECTORY ERRORS]:")
        for err in dir_errors:
            print(f"  [ERROR] {err}")

    for r in results:
        status_str = "[PASS]" if r.is_valid else "[FAIL]"
        if not args.quiet or not r.is_valid:
            print(f"{status_str} {r.file_path.name} (Date: {r.date_str or 'None'})")
        for err in r.errors:
            print(f"    - ERROR: {err}")
        for warn in r.warnings:
            print(f"    - WARNING: {warn}")

    if not args.quiet:
        print("-" * 60)
        summary_msg = "PASSED: All development logs are valid." if overall_valid else "FAILED: Validation errors detected."
        print(f"Result: {summary_msg}")
        print("=" * 60)

    # Emit GitHub Actions workflow commands if running in CI
    if os.getenv("GITHUB_ACTIONS") == "true":
        annotations = format_github_annotations(results, dir_errors)
        if annotations:
            print(annotations)

    # Write GitHub Step Summary if requested or if GITHUB_STEP_SUMMARY env var is present
    summary_path = args.summary_file or (
        Path(os.environ["GITHUB_STEP_SUMMARY"]) if "GITHUB_STEP_SUMMARY" in os.environ else None
    )
    if summary_path:
        try:
            summary_md = generate_markdown_summary(results, dir_errors, target_desc)
            with open(summary_path, "a", encoding="utf-8") as f:
                f.write(summary_md + "\n")
        except OSError as exc:
            print(f"Warning: Failed to write GitHub step summary: {exc}", file=sys.stderr)

    return 0 if overall_valid else 1


if __name__ == "__main__":
    sys.exit(main())
