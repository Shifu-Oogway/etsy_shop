# install.ps1 — one-time setup on the Windows host (D:\ai-etsy-system)
# PowerShell 5.1 compatible: no '?.' operator, full error output, no Out-Null
# on anything that can fail.
$ErrorActionPreference = "Stop"

Write-Host "== AI Etsy System install ==" -ForegroundColor Cyan

# 1. Verify prerequisites
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    Write-Error "Docker Desktop is not installed or not on PATH. Install it first."
    exit 1
}

$ollamaPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
if (-not (Test-Path $ollamaPath)) {
    Write-Warning "Ollama not found at $ollamaPath — the pipeline needs it. Install from https://ollama.com"
} else {
    Write-Host "Ollama found: $ollamaPath"
}

# 2. Create .env from template if missing
$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $root ".env.example") $envFile
    Write-Host "Created .env from .env.example — review it before going live." -ForegroundColor Yellow
}

# 3. Pull models (errors shown in full)
if (Test-Path $ollamaPath) {
    Write-Host "Pulling Ollama models (this can take a while)..."
    & $ollamaPath pull llama3.1:8b
    if ($LASTEXITCODE -ne 0) { Write-Error "ollama pull llama3.1:8b failed (exit $LASTEXITCODE)"; exit 1 }
    & $ollamaPath pull nomic-embed-text
    if ($LASTEXITCODE -ne 0) { Write-Error "ollama pull nomic-embed-text failed (exit $LASTEXITCODE)"; exit 1 }
}

# 4. Build images — output is NOT suppressed so build failures are visible
Push-Location $root
docker compose build
if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Error "docker compose build failed (exit $LASTEXITCODE)"; exit 1 }
Pop-Location

Write-Host "Install complete. Run scripts\start-system.ps1 to launch." -ForegroundColor Green
