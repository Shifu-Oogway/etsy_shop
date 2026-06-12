# stop-system.ps1 — stop all containers (data volumes are preserved).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
docker compose down
if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Error "docker compose down failed"; exit 1 }
Pop-Location
Write-Host "Stack stopped. Volumes preserved (use 'docker compose down -v' to wipe data)."
