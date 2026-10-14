"""
generate_report.py - Daily Development Activity Report Generator

Extracts metrics, topics, and recent progress from verified development logs
in logs/ and compiles a deterministic Markdown report into reports/development-summary.md.

Guarantees:
- Never invents missing activities or topics.
- Strictly reflects recorded Markdown journal entries.
- Produces deterministic, reproducible output across runs.
- Avoids modifying the report file if the underlying source data has not changed.
- Does not expose private keys, credentials, or sensitive environment details.
- Fully compatible with Windows, Linux, macOS, and GitHub Actions.
"""

from __future__ import annotations

import argparse
import datetime
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional, Sequence, Tuple


REQUIRED_SECTIONS: Sequence[str] = (
    "Learning",
    "Development",
    "Problems Solved",
    "Challenges and Solutions",
    "Next Steps",
)

DATE_PATTERN = re.compile(r"^Date:\s*(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE | re.IGNORECASE)
SECTION_SPLIT_PATTERN = re.compile(r"\n##\s+")


class LogSummary:
    """Represents the parsed content and metadata of a single log file."""

    def __init__(self, file_path: Path, date_str: str, date_val: datetime.date) -> None:
        self.file_path: Path = file_path
        self.date_str: str = date_str
        self.date_val: datetime.date = date_val
        self.sections: Dict[str, List[str]] = {s: [] for s in REQUIRED_SECTIONS}
        self.missing_sections: List[str] = []

    @property
    def filename(self) -> str:
        return self.file_path.name


def extract_bullet_items(body: str) -> List[str]:
    """Extract bullet items or clean text lines from a section body."""
    items: List[str] = []
    lines = body.splitlines()
    current_item: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_item:
                items.append(" ".join(current_item))
                current_item = []
            continue

        # Bullet point marker
        if stripped.startswith(("* ", "- ", "+ ", "1. ", "2. ", "3. ", "4. ", "5. ")):
            if current_item:
                items.append(" ".join(current_item))
                current_item = []
            item_text = re.sub(r"^(\*|\-|\+|\d+\.)\s+", "", stripped)
            current_item.append(item_text)
        else:
            if current_item:
                current_item.append(stripped)
            else:
                current_item.append(stripped)

    if current_item:
        items.append(" ".join(current_item))

    # Filter out empty or placeholder items
    filtered: List[str] = []
    for it in items:
        clean = it.strip()
        if clean and not clean.startswith("Record the actual") and not clean.startswith("Describe the genuine"):
            filtered.append(clean)
    return filtered


def parse_log_file(file_path: Path) -> Optional[LogSummary]:
    """Parse a single Markdown development log file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    date_match = DATE_PATTERN.search(content)
    if not date_match:
        # Fallback to filename if date header missing
        match = re.match(r"^(\d{4}-\d{2}-\d{2})\.md$", file_path.name)
        if match:
            date_str = match.group(1)
        else:
            return None
    else:
        date_str = date_match.group(1).strip()

    try:
        date_val = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None

    summary = LogSummary(file_path=file_path, date_str=date_str, date_val=date_val)

    # Parse sections
    blocks = SECTION_SPLIT_PATTERN.split(content)
    found_sections: Dict[str, str] = {}
    for block in blocks[1:]:
        lines = block.splitlines()
        if not lines:
            continue
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        for req in REQUIRED_SECTIONS:
            if title.lower() == req.lower():
                found_sections[req] = body

    for req in REQUIRED_SECTIONS:
        if req in found_sections and found_sections[req]:
            summary.sections[req] = extract_bullet_items(found_sections[req])
        else:
            summary.missing_sections.append(req)

    return summary


def build_report_content(summaries: List[LogSummary], relative_logs_dir: str = "../logs") -> str:
    """Generate deterministic markdown content for development-summary.md."""
    # Sort logs chronologically
    sorted_summaries = sorted(summaries, key=lambda s: s.date_val)

    total_logs = len(sorted_summaries)
    if total_logs == 0:
        return (
            "# Development Activity Summary\n\n"
            "*Automated repository report generated from development logs in `logs/`.*\n\n"
            "## Summary Metrics\n\n"
            "- **Total Development Logs**: `0`\n"
            "- **Date Range**: `None recorded yet`\n"
            "- **Incomplete Entries**: `0`\n\n"
            "## Status\n\n"
            "No daily development logs recorded yet. Add your first entry in `logs/` "
            "using the template in `templates/daily-log-template.md`.\n"
        )

    earliest = sorted_summaries[0].date_str
    latest = sorted_summaries[-1].date_str
    incomplete_count = sum(1 for s in sorted_summaries if s.missing_sections)

    # Collect distinct topics and learning highlights
    all_learning: List[Tuple[str, str, str]] = []
    all_development: List[Tuple[str, str, str]] = []

    for s in sorted_summaries:
        for it in s.sections.get("Learning", []):
            all_learning.append((s.date_str, s.filename, it))
        for it in s.sections.get("Development", []):
            all_development.append((s.date_str, s.filename, it))

    # Markdown generation
    lines: List[str] = [
        "# Development Activity Summary",
        "",
        "*Automated repository report generated from validated development logs in `logs/`.*",
        "",
        "## Overview Metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| **Total Development Logs** | `{total_logs}` |",
        f"| **Earliest Recorded Entry** | `{earliest}` |",
        f"| **Latest Recorded Entry** | `{latest}` |",
        f"| **Recorded Learning Items** | `{len(all_learning)}` |",
        f"| **Recorded Development Tasks** | `{len(all_development)}` |",
        f"| **Entries with Missing Sections** | `{incomplete_count}` |",
        "",
        "## Recent Development Activities",
        "",
        "Recent entries in reverse chronological order:",
        "",
    ]

    # Show up to 10 most recent entries
    recent_entries = list(reversed(sorted_summaries))[:10]
    for s in recent_entries:
        link_target = f"{relative_logs_dir}/{s.filename}".replace("\\", "/")
        lines.append(f"### [{s.date_str}]({link_target})")
        lines.append("")

        dev_items = s.sections.get("Development", [])
        learn_items = s.sections.get("Learning", [])
        prob_items = s.sections.get("Problems Solved", [])
        next_items = s.sections.get("Next Steps", [])

        if dev_items:
            lines.append("**Development Highlights:**")
            for item in dev_items:
                lines.append(f"- {item}")
            lines.append("")

        if learn_items:
            lines.append("**Learning Highlights:**")
            for item in learn_items:
                lines.append(f"- {item}")
            lines.append("")

        if prob_items:
            lines.append("**Problems Addressed:**")
            for item in prob_items:
                lines.append(f"- {item}")
            lines.append("")

        if next_items:
            lines.append("**Next Steps:**")
            for item in next_items:
                lines.append(f"- {item}")
            lines.append("")

        if s.missing_sections:
            lines.append(
                f"> :warning: **Note**: Missing section(s): {', '.join(s.missing_sections)}"
            )
            lines.append("")

    # Complete Archive Table
    lines.append("## Complete Logs Index")
    lines.append("")
    lines.append("| Date | Log File | Learning Topics | Dev Tasks | Status |")
    lines.append("|---|---|---|---|---|")
    for s in reversed(sorted_summaries):
        link_target = f"{relative_logs_dir}/{s.filename}".replace("\\", "/")
        l_count = len(s.sections.get("Learning", []))
        d_count = len(s.sections.get("Development", []))
        status = "Complete" if not s.missing_sections else f"Missing: {', '.join(s.missing_sections)}"
        lines.append(
            f"| `{s.date_str}` | [{s.filename}]({link_target}) | {l_count} | {d_count} | {status} |"
        )
    lines.append("")

    return "\n".join(lines)


def generate_report(
    logs_dir: Path,
    output_file: Path,
    check_only: bool = False,
) -> Tuple[bool, bool, str]:
    """
    Parse logs and write the summary report if contents have changed.

    Returns:
        (success: bool, changed: bool, message: str)
    """
    if not logs_dir.exists() or not logs_dir.is_dir():
        return False, False, f"Logs directory does not exist: {logs_dir}"

    md_files = sorted(logs_dir.glob("*.md"))
    summaries: List[LogSummary] = []
    for f in md_files:
        summary = parse_log_file(f)
        if summary is not None:
            summaries.append(summary)

    new_content = build_report_content(summaries)

    existing_content: Optional[str] = None
    if output_file.exists():
        try:
            existing_content = output_file.read_text(encoding="utf-8")
        except OSError as exc:
            return False, False, f"Failed to read existing report: {exc}"

    has_changed = (existing_content != new_content)

    if check_only:
        if has_changed:
            return True, True, "Report is out of date and needs regeneration."
        return True, False, "Report is up-to-date with current logs."

    if not has_changed:
        return True, False, f"Report is already up-to-date at {output_file} (no changes)."

    # Ensure parent directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_file.write_text(new_content, encoding="utf-8")
    except OSError as exc:
        return False, False, f"Failed to write report to {output_file}: {exc}"

    return True, True, f"Successfully updated report at {output_file} ({len(summaries)} logs processed)."


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point for generate_report.py."""
    parser = argparse.ArgumentParser(
        description="Generate development summary report from genuine markdown logs in logs/."
    )
    parser.add_argument(
        "--logs-dir",
        "-l",
        type=Path,
        default=Path("logs"),
        help="Path to development logs directory (default: logs).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("reports/development-summary.md"),
        help="Path for generated summary markdown file (default: reports/development-summary.md).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check whether the report is up-to-date without writing changes (returns exit code 1 if out of date).",
    )

    args = parser.parse_args(argv)
    success, changed, msg = generate_report(
        logs_dir=args.logs_dir,
        output_file=args.output,
        check_only=args.check,
    )

    print(msg)
    if not success:
        return 1
    if args.check and changed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
