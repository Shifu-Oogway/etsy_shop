# update.ps1 — apply a zip of changed files to the running AI Etsy System.
#
# Usage:
#   .\scripts\update.ps1 -Zip "C:\Downloads\nim-fallback-update.zip"
#
# What it does:
#   1. Validates the zip exists and Docker is running
#   2. Creates a timestamped rollback snapshot of files that will be overwritten
#   3. Extracts the zip into the project root (preserving directory structure)
#   4. Runs 'docker compose build' for changed services (or --no-cache if forced)
#   5. Runs 'docker compose up -d' (rolling restart — zero downtime for healthy services)
#   6. Streams migration logs so Alembic failures are never hidden
#   7. Waits for /api/v1/system/health to return 200
#   8. Prints a summary. On failure, prints rollback instructions.
#
# Rollback:
#   .\scripts\update.ps1 -Rollback "D:\ai-etsy-system\backups\20260610_153022"
#
# PowerShell 5.1 compatible: no '?.' operator, no Out-Null on fallible commands.

param(
    [string]$Zip      = "",   # path to the update zip
    [string]$Rollback = "",   # path to a backup folder to restore from
    [switch]$NoCache          # force --no-cache on docker compose build
)

$ErrorActionPreference = "Stop"
$root    = Split-Path -Parent $PSScriptRoot
$backups = Join-Path $root "backups"

# ── helpers ────────────────────────────────────────────────────────────────────

function Assert-Docker {
    $info = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker is not running. Start Docker Desktop first."
        exit 1
    }
}

function Wait-HealthEndpoint {
    Write-Host "Waiting for API health endpoint..." -ForegroundColor Cyan
    for ($i = 0; $i -lt 40; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/system/health" `
                                      -UseBasicParsing -TimeoutSec 4
            if ($resp.StatusCode -eq 200) { return $true }
        } catch { }
        Start-Sleep -Seconds 3
    }
    return $false
}

# ── ROLLBACK mode ──────────────────────────────────────────────────────────────

if ($Rollback -ne "") {
    if (-not (Test-Path $Rollback)) {
        Write-Error "Backup folder not found: $Rollback"
        exit 1
    }
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  ROLLBACK from: $Rollback" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow

    Assert-Docker

    Write-Host "[1/3] Restoring files from backup..." -ForegroundColor Cyan
    Copy-Item (Join-Path $Rollback "*") $root -Recurse -Force
    Write-Host "      Done." -ForegroundColor Green

    Write-Host "[2/3] Rebuilding images..." -ForegroundColor Cyan
    Push-Location $root
    docker compose build
    if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Error "docker compose build failed"; exit 1 }

    Write-Host "[3/3] Restarting stack..." -ForegroundColor Cyan
    docker compose up -d
    if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Error "docker compose up failed"; exit 1 }
    docker compose logs migrate
    Pop-Location

    $ok = Wait-HealthEndpoint
    if ($ok) {
        Write-Host ""
        Write-Host "Rollback complete. System is healthy." -ForegroundColor Green
    } else {
        Write-Error "API did not come up after rollback. Run: docker compose logs api"
        exit 1
    }
    exit 0
}

# ── UPDATE mode ────────────────────────────────────────────────────────────────

if ($Zip -eq "") {
    Write-Error "No zip specified. Usage: .\scripts\update.ps1 -Zip path\to\update.zip"
    exit 1
}

if (-not (Test-Path $Zip)) {
    Write-Error "Zip not found: $Zip"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI ETSY SYSTEM — UPDATE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Zip     : $Zip"
Write-Host "  Project : $root"
Write-Host ""

Assert-Docker

# ── Step 1: Inspect zip contents ───────────────────────────────────────────────
Write-Host "[1/6] Inspecting zip contents..." -ForegroundColor Cyan
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($Zip)
$entries = $archive.Entries | Where-Object { $_.Name -ne "" } | ForEach-Object { $_.FullName }
$archive.Dispose()

Write-Host "      Files in zip:"
foreach ($e in $entries) { Write-Host "        $e" -ForegroundColor Gray }

# ── Step 2: Backup files that will be overwritten ──────────────────────────────
Write-Host "[2/6] Creating rollback snapshot..." -ForegroundColor Cyan
$stamp  = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = Join-Path $backups $stamp
New-Item -ItemType Directory -Path $backup -Force | Out-Null

$backedUp = 0
foreach ($entry in $entries) {
    $target = Join-Path $root $entry
    if (Test-Path $target) {
        $dest = Join-Path $backup $entry
        $destDir = Split-Path $dest -Parent
        if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
        Copy-Item $target $dest -Force
        $backedUp++
    }
}
Write-Host "      Backed up $backedUp existing file(s) → backups\$stamp" -ForegroundColor Gray
Write-Host "      To rollback: .\scripts\update.ps1 -Rollback `"$backup`"" -ForegroundColor DarkGray

# ── Step 3: Extract zip ────────────────────────────────────────────────────────
Write-Host "[3/6] Extracting update files..." -ForegroundColor Cyan
$archive2 = [System.IO.Compression.ZipFile]::OpenRead($Zip)
foreach ($entry in $archive2.Entries) {
    if ($entry.Name -eq "") { continue }  # skip directory entries
    $destPath = Join-Path $root $entry.FullName
    $destDir  = Split-Path $destPath -Parent
    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
    [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $destPath, $true)
}
$archive2.Dispose()
Write-Host "      Done." -ForegroundColor Green

# ── Step 4: Build changed images ───────────────────────────────────────────────
Write-Host "[4/6] Rebuilding Docker images..." -ForegroundColor Cyan
Push-Location $root
if ($NoCache) {
    docker compose build --no-cache
} else {
    docker compose build
}
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Host ""
    Write-Host "Build failed. Rolling back automatically..." -ForegroundColor Red
    Copy-Item (Join-Path $backup "*") $root -Recurse -Force
    Write-Error "Build failed. Files have been restored from backup. Fix the issue and retry."
    exit 1
}
Write-Host "      Done." -ForegroundColor Green

# ── Step 5: Rolling restart ────────────────────────────────────────────────────
Write-Host "[5/6] Restarting services (rolling update)..." -ForegroundColor Cyan
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Error "docker compose up failed (exit $LASTEXITCODE). Run: docker compose logs"
    exit 1
}

# Always stream migration logs — a silent Alembic failure is the hardest bug to catch
Write-Host ""
Write-Host "--- migration logs ---" -ForegroundColor DarkGray
docker compose logs migrate
Write-Host "--- end migration logs ---" -ForegroundColor DarkGray
Write-Host ""

Pop-Location

# ── Step 6: Health check ───────────────────────────────────────────────────────
Write-Host "[6/6] Verifying API health..." -ForegroundColor Cyan
$ok = Wait-HealthEndpoint

if ($ok) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Update applied successfully." -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Dashboard  : http://localhost:3000"    -ForegroundColor Cyan
    Write-Host "  API        : http://localhost:8000"    -ForegroundColor Cyan
    Write-Host "  API docs   : http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Rollback   : .\scripts\update.ps1 -Rollback `"$backup`"" -ForegroundColor DarkGray
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "API did not become healthy after update." -ForegroundColor Red
    Write-Host "Check logs:  docker compose logs api" -ForegroundColor Yellow
    Write-Host "Rollback:    .\scripts\update.ps1 -Rollback `"$backup`"" -ForegroundColor Yellow
    exit 1
}
