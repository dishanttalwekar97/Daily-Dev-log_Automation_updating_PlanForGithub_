# GitHub Daily Development Automation (`daily-dev-log`)

[![Daily Validation](https://github.com/USERNAME/daily-dev-log/actions/workflows/daily-validation.yml/badge.svg)](https://github.com/USERNAME/daily-dev-log/actions/workflows/daily-validation.yml)
[![Validate on Push](https://github.com/USERNAME/daily-dev-log/actions/workflows/validate-on-push.yml/badge.svg)](https://github.com/USERNAME/daily-dev-log/actions/workflows/validate-on-push.yml)
[![Automated Maintenance](https://github.com/USERNAME/daily-dev-log/actions/workflows/maintenance.yml/badge.svg)](https://github.com/USERNAME/daily-dev-log/actions/workflows/maintenance.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An automated development journal system built with **Python 3**, **GitHub Actions**, and **Markdown**. It enables developers to maintain a genuine, verifiable daily learning and coding record, enforce structured documentation through automated CI pipelines, and aggregate activity reports in GitHub's cloud without needing their local machine to remain powered on.

---

## Table of Contents

1. [Project Introduction](#1-project-introduction)
2. [Features](#2-features)
3. [Architecture Overview](#3-architecture-overview)
4. [Repository Structure](#4-repository-structure)
5. [Technology Stack](#5-technology-stack)
6. [GitHub Repository Setup](#6-github-repository-setup)
7. [Instructions for Creating Daily Logs](#7-instructions-for-creating-daily-logs)
8. [GitHub Actions Configuration](#8-github-actions-configuration)
9. [Cron Scheduling Explanation](#9-cron-scheduling-explanation)
10. [Manual Workflow Execution](#10-manual-workflow-execution)
11. [Windows 11 PowerShell Setup](#11-windows-11-powershell-setup)
12. [Python Validation Commands](#12-python-validation-commands)
13. [Test Commands](#13-test-commands)
14. [Automatic Maintenance Configuration](#14-automatic-maintenance-configuration)
15. [GitHub Contribution Attribution & Troubleshooting](#15-github-contribution-attribution--troubleshooting)
16. [Security Practices](#16-security-practices)
17. [Common Errors and Solutions](#17-common-errors-and-solutions)
18. [How to Disable Scheduled Automation](#18-how-to-disable-scheduled-automation)
19. [How to Inspect Workflow Logs](#19-how-to-inspect-workflow-logs)
20. [How to Contribute to the Project](#20-how-to-contribute-to-the-project)

---

## 1. Project Introduction

Consistency is one of the most vital traits of a proficient software engineer. However, manually tracking daily technical learning, code changes, and bug fixes often becomes disorganized. 

**GitHub Daily Development Automation** solves this problem by providing:
- A standardized **Markdown schema** for recording daily learning, code implementations, bugs resolved, and planned next steps.
- Cloud-native **automated CI/CD verification** via GitHub Actions that validates entries against strict formatting, calendar, and structural rules.
- **Integrity scanners** that prevent duplicate dates, file collisions, and unedited copy-pasted templates.
- **Deterministic summary reports** that aggregate verified accomplishments over time without fabricating activity or faking commits.

> **Important Principle**: This project **never fabricates** coding activities or learning achievements. It exists to celebrate and track genuine, authentic development habits.

---

## 2. Features

- **Automated Schema Validation**: Validates date formats (ISO 8601), heading hierarchy, non-empty sections, and template placeholder removal.
- **Date Consistency & Collision Detection**: Ensures file names (`YYYY-MM-DD.md`) match internal `Date:` headers, detects duplicate dates, and checks case collisions.
- **Plagiarism & Similarity Detection**: Uses fuzzy content analysis (`difflib`) to flag suspicious duplicate text across logs while respecting legitimate recurring projects.
- **Deterministic Reporting**: Compiles aggregate metrics, topics studied, and chronological summaries into `reports/development-summary.md` only when real content changes.
- **Dual-Job Maintenance Architecture**: Decouples read-only validation jobs from write-enabled commit jobs. Commits are disabled by default until explicitly authorized.
- **Zero Third-Party Cloud Dependencies**: Built using standard Python 3 and native GitHub Actions; no external SaaS services or personal access tokens needed.
- **Cloud-Independent Execution**: Runs automatically on GitHub's cloud runners; your local computer does not need to stay on.
- **Full Unicode Support**: Supports international characters, technical symbols, and emojis (UTF-8).

---

## 3. Architecture Overview

```mermaid
flowchart TD
    A[Developer writes daily log in logs/YYYY-MM-DD.md] --> B[Git Commit & Push to GitHub]
    B --> C[GitHub Actions: validate-on-push.yml]
    C --> D{Unit Tests & Log Validation}
    D -- Pass --> E[Build Passes / PR Check Green]
    D -- Fail --> F[CI Fails with Detailed Error Annotation]

    G[Scheduled Trigger: 12:30 UTC / 18:00 IST] --> H[GitHub Actions: daily-validation.yml]
    H --> I[Validate All Existing Logs in logs/]
    I --> J[Publish Summary to GITHUB_STEP_SUMMARY]

    K[Scheduled / Manual Trigger] --> L[GitHub Actions: maintenance.yml]
    L --> M[Job 1: validate-and-inspect 'contents: read']
    M --> N[Generate Deterministic Report]
    N --> O{Did Report Change AND Write Authorized?}
    O -- Yes --> P[Job 2: commit-report 'contents: write']
    P --> Q[Commit & Push 'chore: update development summary [skip ci]']
    O -- No --> R[No Commit Created - Working Tree Clean]
```

---

## 4. Repository Structure

```text
daily-dev-log/
│
├── .github/
│   └── workflows/
│       ├── daily-validation.yml   # Daily scheduled health check & validation
│       ├── validate-on-push.yml   # Push and PR trigger validation & test runner
│       └── maintenance.yml        # Report generation with safe conditional commit
│
├── logs/
│   └── .gitkeep                   # Tracks the logs folder where daily logs reside
│
├── scripts/
│   ├── validate_log.py            # Log validation engine (dates, headings, content)
│   ├── generate_report.py         # Compiles development-summary.md from real logs
│   └── check_duplicates.py        # Duplicate dates, file collision, and similarity checks
│
├── reports/
│   └── .gitkeep                   # Tracks the folder where summary reports are saved
│
├── tests/
│   └── test_validate_log.py       # Comprehensive unit tests (13 test scenarios)
│
├── templates/
│   └── daily-log-template.md      # Standardized daily development journal template
│
├── .gitignore                     # Ignores caches, environments, and temporary files
├── README.md                      # Complete system documentation and guides
├── CONTRIBUTING.md                # Contribution workflow and guidelines
└── requirements-dev.txt           # Testing and development dependencies
```

---

## 5. Technology Stack

- **Version Control**: Git & GitHub
- **Automation Engine**: GitHub Actions (Ubuntu 24.04 / 22.04 LTS runners)
- **Language**: Python 3 (3.12+ compatible, standard library zero-dependency core)
- **Formatting**: Markdown (GFM - GitHub Flavored Markdown)
- **Workflow Definitions**: YAML
- **Local Platform**: Windows 11 (PowerShell 5.1 / 7+ compatible) & POSIX shells (Linux/macOS)

---

## 6. GitHub Repository Setup

Follow these exact steps to connect this local project to your GitHub account:

### Step 1: Initialize Git Locally
Open PowerShell in the project directory:
```powershell
# Navigate to the workspace
Set-Location -Path "d:\Automaton"

# Initialize local git repository
git init -b main

# Configure your Git author details (use your verified GitHub email)
git config user.name "Your Name"
git config user.email "your-github-email@example.com"
```

### Step 2: Create Remote Repository on GitHub
1. Log in to [GitHub](https://github.com).
2. Click the **+** icon in the upper-right corner and select **New repository**.
3. Set the **Repository name** to: `daily-dev-log`.
4. Choose **Public** (recommended for portfolio display) or **Private**.
5. Leave "Add a README file", ".gitignore", and "Choose a license" **UNCHECKED** (we already created them locally).
6. Click **Create repository**.

### Step 3: Add Remote and Push Local Code
```powershell
# Stage all files
git add .

# Create initial commit
git commit -m "feat: initialize daily-dev-log automation system"

# Link to your remote GitHub repository (replace USERNAME with your GitHub handle)
git remote add origin https://github.com/USERNAME/daily-dev-log.git

# Push to the main branch
git push -u origin main
```

---

## 7. Instructions for Creating Daily Logs

Daily records reside inside the `logs/` directory. Each entry file must be named strictly with the ISO 8601 calendar date: `YYYY-MM-DD.md`.

### Step-by-Step Creation

1. **Create the file from the template**:
   In PowerShell:
   ```powershell
   Copy-Item templates/daily-log-template.md logs/2026-10-14.md
   ```
2. **Open and complete the entry**:
   ```markdown
   # Daily Development Log

   Date: 2026-10-14

   ## Learning

   * Researched GitHub Actions runner architecture and least-privilege security permissions.
   * Studied Python difflib SequenceMatcher algorithm for fuzzy duplicate detection.

   ## Development

   * Implemented scripts/validate_log.py and added unit tests in tests/test_validate_log.py.
   * Configured CI workflow concurrency groups to avoid race conditions.

   ## Problems Solved

   * Resolved path delimiter mismatch between Windows backslashes and Linux forward slashes.

   ## Challenges and Solutions

   * Challenge: Determining when to write reports without creating empty git commits.
   * Solution: Evaluated content hashes and used git diff --quiet before staging.

   ## Next Steps

   * Configure optional repository variables for automatic maintenance push.
   * Write first week of daily learning notes.
   ```
3. **Validate locally before committing**:
   ```powershell
   python scripts/validate_log.py --file logs/2026-10-14.md
   ```
4. **Commit and push your entry**:
   ```powershell
   git add logs/2026-10-14.md
   git commit -m "docs(log): add development journal for 2026-10-14"
   git push origin main
   ```

---

## 8. GitHub Actions Configuration

This project includes three specialized workflows in `.github/workflows/`:

| Workflow File | Trigger | Purpose | Permissions |
|---|---|---|---|
| `daily-validation.yml` | Scheduled (12:30 UTC) & `workflow_dispatch` | Daily health check of all logs | `contents: read` |
| `validate-on-push.yml` | `push` & `pull_request` on `logs/**.md` | Validates new logs & runs unit tests | `contents: read` |
| `maintenance.yml` | Scheduled (13:00 UTC) & `workflow_dispatch` | Generates summary reports and safe conditional commit | Job 1: `read`<br>Job 2: `write` (conditional) |

### Pinned Actions
All third-party actions are pinned to immutable commit SHAs with version comments (e.g., `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2`). This prevents supply chain tampering and unexpected upstream breakages.

---

## 9. Cron Scheduling Explanation

The daily validation workflow uses the cron expression:
```yaml
schedule:
  - cron: '30 12 * * *'
```

### Breakdown:
- `30`: Minute 30
- `12`: Hour 12 (12:00 PM UTC)
- `*`: Any day of the month
- `*`: Any month
- `*`: Any day of the week

### Timezone Conversion:
GitHub Actions interprets all cron schedules strictly in **Coordinated Universal Time (UTC)**.
- **UTC**: 12:30 UTC
- **Indian Standard Time (IST, UTC+5:30)**: `12:30 + 5:30 = 18:00` (6:00 PM IST)
- **Eastern Time (EST, UTC-5)**: `12:30 - 5:00 = 07:30` (7:30 AM EST)
- **Pacific Time (PST, UTC-8)**: `12:30 - 8:00 = 04:30` (4:30 AM PST)

### Customizing the Schedule
To change the execution time, edit the `cron` line in `.github/workflows/daily-validation.yml`. For example:
- **8:00 PM IST (14:30 UTC)**: `'30 14 * * *'`
- **9:00 AM UTC**: `'0 9 * * *'`

> **GitHub Scheduling Notice**: GitHub Actions schedules are queued in shared infrastructure. During periods of high traffic (especially at the top of the hour), execution may be delayed by a few minutes. This is normal and expected platform behavior.

---

## 10. Manual Workflow Execution

You can run any workflow on demand without waiting for the scheduled time:

1. Go to your repository on GitHub.
2. Click the **Actions** tab.
3. In the left sidebar, click the workflow name (e.g., **Daily Development Log Validation**).
4. Click the **Run workflow** dropdown on the right.
5. Select the branch (e.g., `main`) and click the green **Run workflow** button.

---

## 11. Windows 11 PowerShell Setup

Follow these commands in Windows PowerShell to set up your local development environment:

```powershell
# 1. Verify Python 3 installation
python --version

# 2. Create a virtual environment (.venv)
python -m venv .venv

# 3. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# (If PowerShell blocks script execution, run: Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned)

# 4. Upgrade pip and install development dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

# 5. Verify CLI validation tool works
python scripts/validate_log.py --help
```

---

## 12. Python Validation Commands

The validation suite supports both single-file and directory-wide scanning:

```powershell
# Validate a specific daily log
python scripts/validate_log.py --file logs/2026-10-14.md

# Validate all logs inside the logs directory (default: logs)
python scripts/validate_log.py --dir logs

# Quiet mode: suppress info and only show failures
python scripts/validate_log.py --quiet

# Check for duplicate dates, case collisions, and copy-pasted logs
python scripts/check_duplicates.py --dir logs

# Strict duplicate check (fails if similarity is suspiciously high)
python scripts/check_duplicates.py --dir logs --strict

# Generate development activity report locally
python scripts/generate_report.py --logs-dir logs --output reports/development-summary.md

# Check if reports/development-summary.md is out of date without rewriting
python scripts/generate_report.py --check
```

---

## 13. Test Commands

Run the comprehensive unit test suite:

```powershell
# Run with Python standard unittest discovery
python -m unittest discover -s tests -v

# Or run with pytest (if installed from requirements-dev.txt)
pytest tests/ -v
```

All 13 test scenarios verify:
- Valid logs, empty files, missing required sections, invalid dates, missing dates, duplicate dates, non-existent directories, multiple valid entries, unexpected filenames, Unicode notes, deterministic reports, and duplicate detection.

---

## 14. Automatic Maintenance Configuration

The maintenance workflow (`.github/workflows/maintenance.yml`) aggregates verified entries into `reports/development-summary.md`.

### Default Safety Posture: Disabled
By default, automatic commits are **disabled**. The workflow will inspect logs and compute report diffs in read-only mode, but will not commit.

### How to Enable Automatic Commits

You have two safe methods to authorize automated commits:

#### Method A: One-Time Manual Run with Authorization
1. Go to **Actions** -> **Automated Maintenance & Report Generation**.
2. Click **Run workflow**.
3. Check the box: **"Explicitly authorize committing and pushing updated reports to repository"**.
4. Click **Run workflow**.

#### Method B: Enable for Scheduled Daily Runs (Repository Variable)
1. In your GitHub repository, click **Settings**.
2. In the left menu, navigate to **Secrets and variables** -> **Actions**.
3. Switch to the **Variables** tab.
4. Click **New repository variable**.
5. Set:
   - **Name**: `ENABLE_AUTO_MAINTENANCE_COMMIT`
   - **Value**: `true`
6. Click **Add variable**.

To disable automatic maintenance commits at any time, delete this variable or set its value to `false`.

---

## 15. GitHub Contribution Attribution & Troubleshooting

Understanding how GitHub attributes contributions is essential for professional software engineering.

### How GitHub Attributes Commits
GitHub attributes a Git commit to your profile **if and only if**:
1. The **author email** on the Git commit matches a **verified email address** attached to your GitHub account (check in GitHub Settings -> Emails).
2. The commit is pushed to the repository's **default branch** (usually `main`) or the `gh-pages` branch.
3. The repository is either public, or if private, your profile has **"Include private contributions on my profile"** turned ON.

### Committer vs. Author
In Git, every commit has an **Author** (who wrote the code) and a **Committer** (who created the commit).
- When you commit locally: You are both Author and Committer.
- When GitHub Actions commits a report: The author and committer are typically configured as `github-actions[bot]`.
- Bot commits **do not** generate contribution squares for personal accounts. Never misrepresent bot commits as personal human coding activity.

### Why Scheduled Workflows Do Not Generate Squares
A scheduled workflow run is a CI/CD job execution in the cloud. Running a workflow does **not** create a Git commit. GitHub contribution graphs display **commits, pull requests, and code reviews**, not CI job executions.

### How to Inspect Commit Author Details
To check the exact author and email attached to your latest local commit:
```powershell
git log -1 --pretty=fuller
```
Verify that the `Author:` field matches your verified GitHub email address.

### Contribution Graph Troubleshooting Checklist
If your commits are not showing up on your GitHub graph:
1. Run `git config user.email` locally. Does it match your verified GitHub email?
2. Did you commit to `main`? Commits to detached HEAD or non-default branches do not appear until merged into the default branch.
3. If the repository is Private: Go to your GitHub profile -> click **Contribution settings** -> ensure **"Include private contributions"** is checked.
4. Wait 5-10 minutes. GitHub's contribution cache updates asynchronously after push events.

---

## 16. Security Practices

- **Zero Hardcoded Secrets**: Workflows rely solely on the short-lived, built-in `secrets.GITHUB_TOKEN`.
- **Principle of Least Privilege**:
  - `daily-validation.yml`: strictly `permissions: contents: read`.
  - `validate-on-push.yml`: strictly `permissions: contents: read`.
  - `maintenance.yml`: Job 1 has `contents: read`; Job 2 has `contents: write` and only executes when authorized.
- **Pinned Action SHAs**: Workflows use immutable Git commit SHAs for third-party actions to prevent supply chain tampering.
- **No Force Pushes**: Maintenance workflows use safe `git pull --rebase` and regular `git push`; `--force` is strictly prohibited.
- **Preventing CI Loops**: Maintenance commits include `[skip ci]` in the commit message to prevent recursive workflow execution.

---

## 17. Common Errors and Solutions

### Error: `Invalid date format '14-10-2026'`
- **Cause**: Date was entered as `DD-MM-YYYY` instead of ISO `YYYY-MM-DD`.
- **Solution**: Use format `2026-10-14`.

### Error: `Filename date does not match content date`
- **Cause**: The file is named `2026-10-14.md` but the internal header reads `Date: 2026-10-15`.
- **Solution**: Ensure both dates are identical.

### Error: `Missing required section heading: '## Problems Solved'`
- **Cause**: One of the five required headings was deleted or misspelled.
- **Solution**: Ensure all 5 headings exist: `## Learning`, `## Development`, `## Problems Solved`, `## Challenges and Solutions`, `## Next Steps`.

### Error: `Log contains only boilerplate template placeholders`
- **Cause**: The template was committed without replacing the placeholder text with actual work.
- **Solution**: Replace all template prompt bullets with your genuine daily activities.

### Error: `Duplicate date 'YYYY-MM-DD' declared across multiple files`
- **Cause**: Two separate files in `logs/` have the same date.
- **Solution**: Consolidate daily work into a single file per calendar day.

---

## 18. How to Disable Scheduled Automation

If you ever wish to pause or disable the daily scheduled workflows:
1. In your GitHub repository, click the **Actions** tab.
2. Select the workflow in the left sidebar (e.g., **Daily Development Log Validation**).
3. Click the **...** (three dots) menu near the top right of the workflow list.
4. Click **Disable workflow**.
5. Repeat for **Automated Maintenance & Report Generation** if desired.

To re-enable, return to the same menu and click **Enable workflow**.

---

## 19. How to Inspect Workflow Logs

To inspect execution results and debug errors:
1. Go to the **Actions** tab in your repository.
2. Click on the latest workflow run.
3. Review the **Step Summary** for high-level validation results and diagnostic tables.
4. Click on the specific job (e.g., `Validate Daily Development Logs`) to expand detailed terminal step output.

---

## 20. How to Contribute to the Project

See [CONTRIBUTING.md](CONTRIBUTING.md) for full instructions on opening issues, writing daily logs, running tests, and submitting pull requests.

---

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
