<#
.SYNOPSIS
Safely sync the local Baduk Insight checkout with the private GitHub main branch,
install Python dependencies, and start Streamlit.

This only pulls Git-tracked source code. SGF records, ChromaDB data, Ollama
models, and KataGo network files stay on the user's computer.
#>
param(
    [switch]$SkipDependencies
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

try {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw "Git is not available. Install Git or reopen PowerShell."
    }
    $currentBranch = (& git branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0 -or $currentBranch -ne "main") {
        throw "This launcher must run from the 'main' branch of your Baduk Insight checkout."
    }
    $origin = (& git remote get-url origin).Trim()
    if ($LASTEXITCODE -ne 0 -or $origin -notmatch "github\.com[:/]areum-hub/baduk-insight(?:\.git)?/?$") {
        throw "The origin Git remote does not match areum-hub/baduk-insight."
    }

    # Refuse to overwrite locally edited tracked files. Ignored SGFs/models
    # and untracked local learning data do not block safe source updates.
    $trackedChanges = & git status --porcelain --untracked-files=no
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to check Git working tree status."
    }
    if ($trackedChanges) {
        throw "Local tracked source changes were found. Commit/stash them before syncing. No files were overwritten."
    }

    Write-Host "[1/3] Syncing source from GitHub (main)..."
    & git pull --ff-only origin main
    if ($LASTEXITCODE -ne 0) {
        throw "Git pull failed. Check network, GitHub login, or branch divergence. Local files were not reset."
    }

    $python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
        throw "Python venv is missing: $python. Create it with: py -m venv .venv"
    }
    if (-not $SkipDependencies) {
        Write-Host "[2/3] Checking Python dependencies..."
        & $python -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
        if ($LASTEXITCODE -ne 0) {
            throw "Package installation failed. See pip output above."
        }
    }
    else {
        Write-Host "[2/3] Skipping dependency check (requested)."
    }

    Write-Host "[3/3] Starting Baduk Insight at http://localhost:8501"
    & $python -m streamlit run (Join-Path $PSScriptRoot "app.py")
    if ($LASTEXITCODE -ne 0) {
        throw "Streamlit exited with an error."
    }
}
catch {
    Write-Host ""
    Write-Host "START FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
