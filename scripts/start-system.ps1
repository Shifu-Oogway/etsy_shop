# start-system.ps1 — start the full stack and verify health.
# PowerShell 5.1 compatible. Errors and migration output are always shown.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

# 1. Make sure Ollama is serving
$ollamaPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
$ollamaUp = $false
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 3
    if ($resp.StatusCode -eq 200) { $ollamaUp = $true }
} catch { $ollamaUp = $false }

if (-not $ollamaUp) {
    if (Test-Path $ollamaPath) {
        Write-Host "Starting Ollama..."
        Start-Process -FilePath $ollamaPath -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 5
    } else {
        Write-Warning "Ollama is not running and was not found at $ollamaPath."
    }
}

# 2. Start the stack. Migration logs stream to the console — do NOT pipe this
#    to Out-Null; a failed migration must be visible.
Push-Location $root
docker compose up -d
if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Error "docker compose up failed (exit $LASTEXITCODE)"; exit 1 }
docker compose logs migrate
Pop-Location

# 3. Wait for the API health endpoint
Write-Host "Waiting for API..."
$healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/system/health" -UseBasicParsing -TimeoutSec 3
        if ($resp.StatusCode -eq 200) { $healthy = $true; break }
    } catch { Start-Sleep -Seconds 2 }
}

if ($healthy) {
    Write-Host "System is up." -ForegroundColor Green
    Write-Host "  API:       http://localhost:8000/docs"
    Write-Host "  Dashboard: http://localhost:3000"
} else {
    Write-Error "API did not become healthy. Inspect with: docker compose logs api"
    exit 1
}
