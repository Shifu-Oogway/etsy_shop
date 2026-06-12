# register-task-scheduler.ps1 — autostart the stack at logon via Task Scheduler.
# Run from an elevated PowerShell. PowerShell 5.1 compatible.
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$startScript = Join-Path $root "scripts\start-system.ps1"

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$startScript`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Hours 1)

$existing = Get-ScheduledTask -TaskName "AI-Etsy-System" -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName "AI-Etsy-System" -Confirm:$false
    Write-Host "Replaced existing task."
}

Register-ScheduledTask -TaskName "AI-Etsy-System" -Action $action `
    -Trigger $trigger -Settings $settings -Description "Starts the AI Etsy stack at logon"

Write-Host "Task 'AI-Etsy-System' registered. The stack will start at logon." -ForegroundColor Green
