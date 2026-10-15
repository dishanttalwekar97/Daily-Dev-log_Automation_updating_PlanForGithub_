"""
test_validate_log.py - Comprehensive Unit Tests for Daily Development Automation

Covers:
- Valid development log structure
- Empty files
- Missing required sections
- Invalid date formats (calendar and syntax)
- Missing date values
- Duplicate log dates
- Missing logs directory
- Multiple valid daily logs
- Unexpected Markdown filenames
- Unicode text in development notes (emojis, accents, international scripts)
- Report generation determinism and metrics
- Duplicate and plagiarism detection
"""

from __future__ import annotations

import datetime
from pathlib import Path
import tempfile
import unittest

from scripts.validate_log import LogValidator, ValidationResult
from scripts.generate_report import build_report_content, generate_report, parse_log_file
from scripts.check_duplicates import find_duplicates


def make_valid_log_content(
    date_str: str = "2026-10-14",
    learning: str = "Studied GitHub Actions workflow syntax and concurrency controls.",
    dev: str = "Implemented Python validation script and unit tests.",
    problems: str = "Resolved path delimiter inconsistencies between Windows and Linux runners.",
    challenges: str = "Configuring step summaries in GITHUB_STEP_SUMMARY securely.",
    next_steps: str = "Implement report generation and duplicate detection algorithms.",
) -> str:
    """Helper to construct a valid log markdown string."""
    return f"""# Daily Development Log

Date: {date_str}

## Learning

* {learning}

## Development

* {dev}

## Problems Solved

* {problems}

## Challenges and Solutions

* {challenges}

## Next Steps

* {next_steps}
"""


class TestLogValidator(unittest.TestCase):
    """Unit test suite for scripts/validate_log.py."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        self.validator = LogValidator(strict_filenames=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_valid_development_log(self) -> None:
        """Verify that a properly structured daily log passes validation."""
        log_file = self.test_dir / "2026-10-14.md"
        log_file.write_text(make_valid_log_content("2026-10-14"), encoding="utf-8")

        result = self.validator.validate_file(log_file)
        self.assertTrue(result.is_valid, f"Expected valid log, got errors: {result.errors}")
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(result.date_str, "2026-10-14")
        self.assertEqual(result.date_value, datetime.date(2026, 10, 14))

    def test_empty_file(self) -> None:
        """Verify that an empty (0-byte or whitespace) file is rejected."""
        empty_file = self.test_dir / "2026-10-14.md"
        empty_file.write_text("   \n\t  \n", encoding="utf-8")

        result = self.validator.validate_file(empty_file)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("empty" in e.lower() for e in result.errors))

    def test_missing_required_sections(self) -> None:
        """Verify that omitting a mandatory section heading produces a validation failure."""
        incomplete_content = """# Daily Development Log

Date: 2026-10-14

## Learning

* Studied GitHub Actions triggers.

## Development

* Wrote new test cases.
"""
        log_file = self.test_dir / "2026-10-14.md"
        log_file.write_text(incomplete_content, encoding="utf-8")

        result = self.validator.validate_file(log_file)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Problems Solved" in e for e in result.errors))
        self.assertTrue(any("Challenges and Solutions" in e for e in result.errors))
        self.assertTrue(any("Next Steps" in e for e in result.errors))

    def test_invalid_date_formats(self) -> None:
        """Verify that invalid date formats and calendar dates are rejected."""
        bad_dates = [
            "14-10-2026",      # DD-MM-YYYY instead of ISO
            "2026/10/14",      # Slashes
            "2026-02-31",      # Invalid calendar date (Feb 31)
            "2026-13-01",      # Invalid month
            "invalid-date",    # Text string
        ]

        for bad_date in bad_dates:
            with self.subTest(bad_date=bad_date):
                # When using non-strict filename so filename match doesn't mask the content date error
                lax_validator = LogValidator(strict_filenames=False)
                log_file = self.test_dir / f"test-{bad_date.replace('/', '-')}.md"
                content = make_valid_log_content(date_str=bad_date)
                log_file.write_text(content, encoding="utf-8")

                result = lax_validator.validate_file(log_file)
                self.assertFalse(result.is_valid)
                self.assertTrue(
                    any("date" in e.lower() for e in result.errors),
                    f"Expected date error for {bad_date}, got {result.errors}",
                )

    def test_missing_date_values(self) -> None:
        """Verify that omitting the Date: line or leaving it empty fails validation."""
        no_date_content = """# Daily Development Log

## Learning

* Studied Git rebase operations.

## Development

* Fixed merge conflict in automation script.

## Problems Solved

* Solved git detached HEAD issue.

## Challenges and Solutions

* Rebasing safely: used git status and git rebase --continue.

## Next Steps

* Review pull request reviews.
"""
        log_file = self.test_dir / "2026-10-14.md"
        log_file.write_text(no_date_content, encoding="utf-8")

        result = self.validator.validate_file(log_file)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Missing 'Date:'" in e for e in result.errors))

    def test_duplicate_log_dates(self) -> None:
        """Verify that two logs claiming the same date are detected in directory validation."""
        file1 = self.test_dir / "2026-10-14.md"
        file1.write_text(make_valid_log_content("2026-10-14", dev="Entry 1"), encoding="utf-8")

        # Create another file with non-strict naming but declaring the exact same date
        lax_validator = LogValidator(strict_filenames=False)
        file2 = self.test_dir / "another_log.md"
        file2.write_text(make_valid_log_content("2026-10-14", dev="Entry 2"), encoding="utf-8")

        is_valid, results, dir_errors = lax_validator.validate_directory(self.test_dir)
        self.assertFalse(is_valid)
        self.assertTrue(any("Duplicate date" in err for err in dir_errors))

    def test_missing_logs_directory(self) -> None:
        """Verify that validating a non-existent directory reports an error."""
        non_existent = self.test_dir / "does_not_exist"
        is_valid, results, dir_errors = self.validator.validate_directory(non_existent)
        self.assertFalse(is_valid)
        self.assertTrue(any("does not exist" in err for err in dir_errors))

    def test_multiple_valid_daily_logs(self) -> None:
        """Verify that multiple distinct, valid daily logs all pass validation."""
        dates = ["2026-10-10", "2026-10-11", "2026-10-12", "2026-10-13", "2026-10-14"]
        for d in dates:
            log_file = self.test_dir / f"{d}.md"
            log_file.write_text(
                make_valid_log_content(d, dev=f"Development performed on {d}"),
                encoding="utf-8",
            )

        is_valid, results, dir_errors = self.validator.validate_directory(self.test_dir)
        self.assertTrue(is_valid, f"Expected all valid, got dir_errors: {dir_errors}")
        self.assertEqual(len(results), len(dates))
        self.assertEqual(len(dir_errors), 0)
        self.assertTrue(all(r.is_valid for r in results))

    def test_unexpected_markdown_filenames(self) -> None:
        """Verify that non-standard filenames are rejected under strict mode."""
        bad_filenames = ["notes.md", "daily-log.md", "2026_10_14.md", "log.txt"]
        for bad_name in bad_filenames:
            log_file = self.test_dir / bad_name
            log_file.write_text(make_valid_log_content("2026-10-14"), encoding="utf-8")
            result = self.validator.validate_file(log_file)
            self.assertFalse(result.is_valid)
            self.assertTrue(any("Unexpected Markdown filename" in e for e in result.errors))

    def test_unicode_text_in_development_notes(self) -> None:
        """Verify that emojis, accents, and international scripts are handled correctly."""
        unicode_content = make_valid_log_content(
            date_str="2026-10-14",
            learning="अध्ययन: GitHub Actions workflows एवं CI/CD पाइपलाइन। 🚀 Éléments clés de Docker & Kubernetes.",
            dev="Desarrollado módulo de autenticación con OAuth2 y cifrado AES-GCM. 💻",
            problems="解决跨平台路径斜杠问题 (/ vs \\)。",
            challenges="Handling Unicode character normalization (NFC vs NFD) across operating systems. 🌐",
            next_steps="Добавить автоматическое развертывание в облако. ⚡",
        )
        log_file = self.test_dir / "2026-10-14.md"
        log_file.write_text(unicode_content, encoding="utf-8")

        result = self.validator.validate_file(log_file)
        self.assertTrue(result.is_valid, f"Expected valid unicode handling, got: {result.errors}")


class TestReportGenerator(unittest.TestCase):
    """Unit test suite for scripts/generate_report.py."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        self.logs_dir = self.test_dir / "logs"
        self.logs_dir.mkdir()
        self.reports_dir = self.test_dir / "reports"
        self.reports_dir.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_empty_logs_report(self) -> None:
        """Verify report generation when no logs exist yet."""
        output_file = self.reports_dir / "development-summary.md"
        success, changed, msg = generate_report(self.logs_dir, output_file)
        self.assertTrue(success)
        self.assertTrue(changed)
        self.assertTrue(output_file.exists())
        content = output_file.read_text(encoding="utf-8")
        self.assertIn("Total Development Logs**: `0`", content)

    def test_deterministic_report_with_logs(self) -> None:
        """Verify that report generation is deterministic and does not alter unchanged reports."""
        (self.logs_dir / "2026-10-13.md").write_text(
            make_valid_log_content("2026-10-13", learning="Kafka Event Streaming", dev="Consumer group setup"),
            encoding="utf-8",
        )
        (self.logs_dir / "2026-10-14.md").write_text(
            make_valid_log_content("2026-10-14", learning="GitHub Actions Concurrency", dev="Maintenance workflow"),
            encoding="utf-8",
        )

        output_file = self.reports_dir / "development-summary.md"

        # First run: writes file
        success1, changed1, _ = generate_report(self.logs_dir, output_file)
        self.assertTrue(success1)
        self.assertTrue(changed1)
        content1 = output_file.read_text(encoding="utf-8")
        self.assertIn("Total Development Logs** | `2`", content1)
        self.assertIn("2026-10-13", content1)
        self.assertIn("2026-10-14", content1)

        # Second run: source logs didn't change, so changed must be False (deterministic)
        success2, changed2, _ = generate_report(self.logs_dir, output_file)
        self.assertTrue(success2)
        self.assertFalse(changed2)
        content2 = output_file.read_text(encoding="utf-8")
        self.assertEqual(content1, content2)


class TestDuplicateDetector(unittest.TestCase):
    """Unit test suite for scripts/check_duplicates.py."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_identical_content_warning(self) -> None:
        """Verify that duplicate content across different dates triggers a warning."""
        identical_text = make_valid_log_content(
            date_str="2026-10-10",
            learning="Identical learning notes for testing duplication.",
            dev="Identical coding tasks for testing duplication.",
        )
        (self.test_dir / "2026-10-10.md").write_text(identical_text, encoding="utf-8")

        # Same text with just the date line changed
        copy_text = identical_text.replace("Date: 2026-10-10", "Date: 2026-10-11")
        (self.test_dir / "2026-10-11.md").write_text(copy_text, encoding="utf-8")

        findings = find_duplicates(self.test_dir)
        self.assertTrue(any(f.category == "Identical Content" for f in findings))


from scripts.auto_daily_log import create_daily_log, generate_log_content, get_topic_for_date


class TestAutoDailyLog(unittest.TestCase):
    """Tests for the automated daily log generator."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_generated_content_validates_successfully(self) -> None:
        """Verify that auto-generated log content passes all validator rules."""
        test_date = datetime.date(2026, 11, 1)
        content = generate_log_content(test_date)
        file_path = self.test_dir / "2026-11-01.md"
        file_path.write_text(content, encoding="utf-8")

        validator = LogValidator(self.test_dir)
        result = validator.validate_file(file_path)
        self.assertTrue(result.is_valid, f"Validation failed: {result.errors}")

    def test_consecutive_days_have_unique_topics(self) -> None:
        """Verify that consecutive days generate distinct topics without duplicate warnings."""
        date1 = datetime.date(2026, 11, 1)
        date2 = datetime.date(2026, 11, 2)

        create_daily_log(date1, self.test_dir)
        create_daily_log(date2, self.test_dir)

        findings = find_duplicates(self.test_dir, similarity_threshold=0.88)
        self.assertEqual(len(findings), 0, f"Unexpected duplicates found: {findings}")

    def test_skip_existing_unless_forced(self) -> None:
        """Verify that existing logs are not overwritten unless force=True."""
        test_date = datetime.date(2026, 11, 3)
        created1, path, _ = create_daily_log(test_date, self.test_dir)
        self.assertTrue(created1)

        # Second call without force should not recreate
        created2, _, msg = create_daily_log(test_date, self.test_dir, force=False)
        self.assertFalse(created2)
        self.assertIn("already exists", msg)


if __name__ == "__main__":
    unittest.main()
