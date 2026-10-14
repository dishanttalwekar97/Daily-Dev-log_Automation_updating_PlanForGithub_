"""
check_duplicates.py - Duplicate & Suspicious Content Detector for Development Logs

Analyzes Markdown development journals in logs/ to detect:
1. Duplicate date declarations across files.
2. Case-insensitive filename collisions (e.g. 2026-10-14.md vs 2026-10-14.MD).
3. Identical content across different dates (exact hash match).
4. Suspiciously high text similarity between separate logs (copy-paste detection).

Guarantees:
- Produces clear warnings and diagnostic advice.
- Never deletes, rewrites, or merges user files automatically.
- Distinguishes between recurring project topics and suspicious copy-pasted logs.
- Compatible with Windows, Linux, macOS, and GitHub Actions CI.
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import hashlib
from pathlib import Path
import re
import sys
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple


DATE_PATTERN = re.compile(r"^Date:\s*(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE | re.IGNORECASE)
SECTION_SPLIT_PATTERN = re.compile(r"\n##\s+")


class DuplicateFinding(NamedTuple):
    severity: str  # "ERROR" or "WARNING"
    category: str
    message: str
    files: List[Path]


class ParsedLog:
    """Stores normalized content and date information for duplication analysis."""

    def __init__(self, file_path: Path, raw_content: str, date_str: Optional[str]) -> None:
        self.file_path: Path = file_path
        self.raw_content: str = raw_content
        self.date_str: Optional[str] = date_str

        # Cleaned body content for similarity comparison (ignoring date header and markdown formatting)
        cleaned = re.sub(r"^Date:\s*.*$", "", raw_content, flags=re.MULTILINE)
        cleaned = re.sub(r"^#.*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"[\r\n\t ]+", " ", cleaned).strip().lower()
        self.normalized_body: str = cleaned
        self.content_hash: str = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


def parse_log(file_path: Path) -> Optional[ParsedLog]:
    """Read and extract metadata from a log file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    date_match = DATE_PATTERN.search(content)
    date_str = date_match.group(1).strip() if date_match else None
    return ParsedLog(file_path, content, date_str)


def find_duplicates(
    logs_dir: Path,
    similarity_threshold: float = 0.88,
) -> List[DuplicateFinding]:
    """
    Scan logs_dir for duplicate dates, case collisions, and suspicious duplicate content.
    """
    findings: List[DuplicateFinding] = []

    if not logs_dir.exists() or not logs_dir.is_dir():
        findings.append(
            DuplicateFinding(
                severity="ERROR",
                category="Directory Missing",
                message=f"Logs directory does not exist: {logs_dir}",
                files=[],
            )
        )
        return findings

    md_files = sorted(logs_dir.glob("*.md"))
    if len(md_files) < 2:
        # Not enough files to have duplicates
        return findings

    parsed_logs: List[ParsedLog] = []
    # 1. Check case-insensitive filename collisions
    filename_case_map: Dict[str, List[Path]] = {}

    for f in md_files:
        lower_name = f.name.lower()
        filename_case_map.setdefault(lower_name, []).append(f)
        parsed = parse_log(f)
        if parsed:
            parsed_logs.append(parsed)

    for lower_name, file_list in filename_case_map.items():
        if len(file_list) > 1:
            names = ", ".join(f.name for f in file_list)
            findings.append(
                DuplicateFinding(
                    severity="ERROR",
                    category="Filename Collision",
                    message=(
                        f"Case-insensitive filename collision detected: {names}. "
                        "This causes conflicts between Windows and Linux/Git."
                    ),
                    files=file_list,
                )
            )

    # 2. Check duplicate dates
    date_map: Dict[str, List[Path]] = {}
    for p in parsed_logs:
        if p.date_str:
            date_map.setdefault(p.date_str, []).append(p.file_path)

    for date_str, file_list in date_map.items():
        if len(file_list) > 1:
            names = ", ".join(f.name for f in file_list)
            findings.append(
                DuplicateFinding(
                    severity="ERROR",
                    category="Duplicate Date",
                    message=f"Date '{date_str}' is declared in multiple log files: {names}",
                    files=file_list,
                )
            )

    # 3. Check exact content matches (excluding Date header)
    hash_map: Dict[str, List[ParsedLog]] = {}
    for p in parsed_logs:
        if len(p.normalized_body) > 30:  # Ignore tiny or empty logs
            hash_map.setdefault(p.content_hash, []).append(p)

    checked_pairs = set()

    for content_hash, log_list in hash_map.items():
        if len(log_list) > 1:
            file_names = ", ".join(p.file_path.name for p in log_list)
            findings.append(
                DuplicateFinding(
                    severity="WARNING",
                    category="Identical Content",
                    message=(
                        f"Identical development log content detected across files: {file_names}. "
                        "Ensure each daily entry reflects genuine, distinct daily work."
                    ),
                    files=[p.file_path for p in log_list],
                )
            )
            for i in range(len(log_list)):
                for j in range(i + 1, len(log_list)):
                    checked_pairs.add((log_list[i].file_path, log_list[j].file_path))
                    checked_pairs.add((log_list[j].file_path, log_list[i].file_path))

    # 4. Check high similarity (fuzzy copy-paste detection)
    n = len(parsed_logs)
    for i in range(n):
        for j in range(i + 1, n):
            log_a = parsed_logs[i]
            log_b = parsed_logs[j]
            pair = (log_a.file_path, log_b.file_path)

            if pair in checked_pairs:
                continue

            if len(log_a.normalized_body) < 50 or len(log_b.normalized_body) < 50:
                continue

            # Quick length heuristic before running sequence matcher
            len_ratio = len(log_a.normalized_body) / len(log_b.normalized_body)
            if len_ratio < 0.6 or len_ratio > 1.6:
                continue

            matcher = difflib.SequenceMatcher(
                None,
                log_a.normalized_body,
                log_b.normalized_body,
                autojunk=False,
            )
            ratio = matcher.ratio()

            if ratio >= similarity_threshold:
                pct = int(ratio * 100)
                findings.append(
                    DuplicateFinding(
                        severity="WARNING",
                        category="High Content Similarity",
                        message=(
                            f"Suspiciously high content similarity ({pct}%) between "
                            f"'{log_a.file_path.name}' and '{log_b.file_path.name}'. "
                            "Review both files to confirm they record genuine separate achievements."
                        ),
                        files=[log_a.file_path, log_b.file_path],
                    )
                )

    return findings


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point for check_duplicates.py."""
    parser = argparse.ArgumentParser(
        description="Check development logs for duplicate dates, file collisions, and duplicate content."
    )
    parser.add_argument(
        "--dir",
        "-d",
        type=Path,
        default=Path("logs"),
        help="Path to development logs directory (default: logs).",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.88,
        help="Similarity ratio threshold (0.0 to 1.0) for copy-paste warnings (default: 0.88).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail with exit code 1 if any warnings or errors are found.",
    )

    args = parser.parse_args(argv)
    findings = find_duplicates(args.dir, similarity_threshold=args.similarity_threshold)

    print("=" * 60)
    print(" DEVELOPMENT LOG DUPLICATE & INTEGRITY CHECK")
    print("=" * 60)
    print(f"Target Directory: {args.dir}")
    print(f"Total Findings: {len(findings)}")
    print("-" * 60)

    has_errors = any(f.severity == "ERROR" for f in findings)
    has_warnings = any(f.severity == "WARNING" for f in findings)

    if not findings:
        print("[OK] No duplicate dates, collisions, or suspicious content detected.")
        print("=" * 60)
        return 0

    for f in findings:
        file_list_str = " | Files: " + ", ".join(p.name for p in f.files) if f.files else ""
        print(f"[{f.severity}] [{f.category}]{file_list_str}")
        print(f"  {f.message}")

    print("-" * 60)
    if has_errors:
        print("RESULT: FAILED - Errors detected (duplicate dates or filename collisions).")
        print("=" * 60)
        return 1

    if args.strict and has_warnings:
        print("RESULT: FAILED - Warnings treated as errors under --strict mode.")
        print("=" * 60)
        return 1

    print("RESULT: PASSED with warnings. No blocking errors found.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
