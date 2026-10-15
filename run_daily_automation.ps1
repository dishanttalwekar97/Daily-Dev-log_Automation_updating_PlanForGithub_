<#
.SYNOPSIS
    Daily Development Automation Runner
    Automatically generates today's log, validates all entries, updates reports, and pushes to GitHub.

.DESCRIPTION
    Runs the automated daily logging cycle with zero manual edits required.
    Usage:
        .\run_daily_automation.ps1
        .\run_daily_automation.ps1 -Push
        .\run_daily_automation.ps1 -Force
#>

[CmdletBinding()]
param (
    [switch]$Push,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DAILY DEVELOPMENT LOG AUTOMATION RUNNER" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Ensure Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[INFO] Detected Python: $pythonVersion" -ForegroundColor Gray
} catch {
    Write-Error "Python 3 is not found in PATH. Please install Python 3.12+."
    exit 1
}

# 2. Run auto_daily_log.py
$forceArg = if ($Force) { "--force" } else { "" }
Write-Host "`n[STEP 1/3] Generating today's development log..." -ForegroundColor Yellow
python scripts/auto_daily_log.py --date today $forceArg
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to generate or validate daily log."
    exit $LASTEXITCODE
}

# 3. Run unit tests
Write-Host "`n[STEP 2/3] Running unit test suite..." -ForegroundColor Yellow
python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) {
    Write-Error "Unit tests failed."
    exit $LASTEXITCODE
}
Write-Host "  [OK] All unit tests passed successfully." -ForegroundColor Green

# 4. Check git status
Write-Host "`n[STEP 3/3] Checking Git status..." -ForegroundColor Yellow
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "  [INFO] Working tree clean. Today's log and report are already up to date." -ForegroundColor Cyan
} else {
    Write-Host "  [INFO] Detected pending changes in logs/ or reports/:" -ForegroundColor Gray
    git status -s

    if ($Push) {
        Write-Host "`n[GIT] Committing and pushing to GitHub..." -ForegroundColor Yellow
        git add logs/ reports/
        $todayStr = (Get-Date).ToString("yyyy-MM-dd")
        git commit -m "docs(log): add automated daily dev log for $todayStr"
        git pull --rebase origin main
        git push origin main
        Write-Host "  [OK] Successfully pushed daily update to GitHub!" -ForegroundColor Green
    } else {
        Write-Host "`n[TIP] Changes are ready locally. To commit and push automatically, run:" -ForegroundColor Magenta
        Write-Host "      .\run_daily_automation.ps1 -Push" -ForegroundColor White
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host " ALL AUTOMATION CHECKS COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
