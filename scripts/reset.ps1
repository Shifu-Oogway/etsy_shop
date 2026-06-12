# reset.ps1 - full wipe and rebuild of the AI Etsy System.
# Stops all containers, removes volumes (ALL DATA LOST), removes built images,
# recreates .env from template, then rebuilds and starts fresh.
# PowerShell 5.1 compatible: no '?.' operator, no Out-Null on fallible commands,
# ASCII-only (no Unicode arrows or special chars).

param([switch]$Force)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host "  AI ETSY SYSTEM - COMPLETE RESET" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  - Stop all running containers" -ForegroundColor Yellow
Write-Host "  - DELETE all volumes (database, redis data)" -ForegroundColor Yellow
Write-Host "  - Remove all built Docker images for this project" -ForegroundColor Yellow
Write-Host "  - Recreate .env from .env.example" -ForegroundColor Yellow
Write-Host "  - Rebuild all images from scratch" -ForegroundColor Yellow
Write-Host "  - Start the stack" -ForegroundColor Yellow
Write-Host ""

if (-not $Force) {
    $confirm = Read-Host "Type YES to continue"
    if ($confirm -ne "YES") {
        Write-Host "Aborted." -ForegroundColor Cyan
        exit 0
    }
}

Write-Host ""

# -- Step 1: Stop containers and wipe volumes ---------------------------------
Write-Host "[1/5] Stopping containers and removing volumes..." -ForegroundColor Cyan
Push-Location $root
docker compose down -v --remove-orphans
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Error "docker compose down failed (exit $LASTEXITCODE)"
    exit 1
}
Pop-Location
Write-Host "      Done." -ForegroundColor Green

# -- Step 2: Remove project images --------------------------------------------
Write-Host "[2/5] Removing built project images..." -ForegroundColor Cyan

$images = @(
    "ai-etsy-system-api",
    "ai-etsy-system-worker",
    "ai-etsy-system-beat",
    "ai-etsy-system-migrate",
    "ai-etsy-system-frontend"
)

foreach ($img in $images) {
    $exists = docker images -q $img 2>&1
    if ($exists) {
        docker rmi $img --force
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Could not remove image $img (exit $LASTEXITCODE) - continuing."
        } else {
            Write-Host "      Removed: $img" -ForegroundColor Gray
        }
    }
}
Write-Host "      Done." -ForegroundColor Green

# -- Step 3: Recreate .env ----------------------------------------------------
Write-Host "[3/5] Recreating .env from .env.example..." -ForegroundColor Cyan
$envFile    = Join-Path $root ".env"
$envExample = Join-Path $root ".env.example"

if (-not (Test-Path $envExample)) {
    Write-Error ".env.example not found at $envExample - cannot continue."
    exit 1
}

if (Test-Path $envFile) {
    $backup = Join-Path $root ".env.bak"
    Copy-Item $envFile $backup -Force
    Write-Host "      Backed up existing .env to .env.bak" -ForegroundColor Gray
}

Copy-Item $envExample $envFile -Force
Write-Host "      Done. Edit .env before going live (Etsy keys, ETSY_DRY_RUN)." -ForegroundColor Yellow

# -- Step 4: Rebuild images ---------------------------------------------------
Write-Host "[4/5] Rebuilding all Docker images (no cache)..." -ForegroundColor Cyan
Push-Location $root
docker compose build --no-cache
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Error "docker compose build failed (exit $LASTEXITCODE)"
    exit 1
}
Pop-Location
Write-Host "      Done." -ForegroundColor Green

# -- Step 5: Start stack ------------------------------------------------------
Write-Host "[5/5] Starting stack..." -ForegroundColor Cyan
Push-Location $root
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Error "docker compose up failed (exit $LASTEXITCODE)"
    exit 1
}
Pop-Location

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Reset complete - stack is running." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Dashboard : http://localhost:3000" -ForegroundColor Cyan
Write-Host "  API       : http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API docs  : http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "NOTE: .env was reset to defaults." -ForegroundColor Yellow
Write-Host "      If you had credentials in the old .env, they are in .env.bak" -ForegroundColor Yellow
Write-Host ""
