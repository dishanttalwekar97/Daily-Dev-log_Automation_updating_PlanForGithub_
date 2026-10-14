# Contributing to daily-dev-log

Thank you for your interest in contributing to **GitHub Daily Development Automation** (`daily-dev-log`).

This repository follows strict DevOps and software engineering principles. The primary goal is to maintain an authentic, verifiable development record, foster consistent engineering habits, and implement robust CI/CD practices.

---

## Core Principles

1. **Authenticity First**: Never fabricate coding activities, learning achievements, or project updates. All entries must describe real learning or engineering work.
2. **Deterministic Automation**: Automation generates reports and verifies integrity, but never invents fake activities.
3. **No Contribution Guarantees**: Automation does not exist to "game" the GitHub contribution graph. GitHub contribution attribution depends strictly on GitHub's official rules.
4. **Least Privilege & Security**: Workflows use minimal permissions (`contents: read` by default) and pinned action SHAs.

---

## How to Add Your Daily Development Log

### Step 1: Create Your Log File

Daily logs are stored in the `logs/` directory using ISO 8601 calendar naming:
`logs/YYYY-MM-DD.md` (e.g., `logs/2026-10-14.md`).

Copy the official template:
```powershell
# Windows PowerShell
Copy-Item templates/daily-log-template.md logs/$(Get-Date -Format 'yyyy-MM-dd').md
```
Or on Linux/macOS:
```bash
cp templates/daily-log-template.md logs/$(date +%F).md
```

### Step 2: Complete All Required Sections

Open the newly created log and replace the placeholders with your genuine daily activities. Every log requires:

* `# Daily Development Log` as the top-level heading.
* `Date: YYYY-MM-DD` matching your filename.
* `## Learning`: Specific technical topics studied, concepts reviewed, or documentation referenced.
* `## Development`: Real code authored, features designed, repositories modified, or experiments performed.
* `## Problems Solved`: Concrete programming, logic, or environment bugs resolved.
* `## Challenges and Solutions`: Obstacles faced and the specific technical solutions tried or adopted.
* `## Next Steps`: Actionable tasks planned for subsequent development sessions.

> **Tip**: Avoid submitting unmodified template boilerplate text. The validator detects unedited placeholder lines and will reject the log.

---

## Local Verification Commands

Always run local validation and tests before pushing to GitHub:

### 1. Validate Your New Log Entry
```powershell
# Validate your specific log file
python scripts/validate_log.py --file logs/2026-10-14.md

# Validate all logs in the repository
python scripts/validate_log.py --dir logs
```

### 2. Check for Duplicate Dates and Content
```powershell
python scripts/check_duplicates.py --dir logs
```

### 3. Generate or Verify Summary Report
```powershell
# Preview report generation locally
python scripts/generate_report.py --logs-dir logs --output reports/development-summary.md
```

### 4. Run the Unit Test Suite
```powershell
python -m unittest discover -s tests -v
```

---

## Pull Request Guidelines

1. **Branch Naming**: Use clear branch names, such as `log/2026-10-14` or `feature/validator-enhancement`.
2. **Commit Messages**: Use clean, descriptive commit messages, for example:
   * `docs(log): add development entry for 2026-10-14`
   * `fix(validator): resolve unicode edge case in heading detection`
3. **CI Validation**: Ensure all GitHub Actions checks pass on your PR before merging.
4. **No Destructive Operations**: Never force-push (`--force`) to the default branch.
