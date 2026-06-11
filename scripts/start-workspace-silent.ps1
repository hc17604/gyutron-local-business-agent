# GyuTron Workspace silent launcher — used by the "GyuTron Workspace" scheduled
# task (runs at user logon, hidden). Idempotent: skips whatever is already up.
# Logs: data\logs\api.log / web.log (data\ is gitignored).
$Root = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $Root "data\logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null

function PortBusy($port) {
    $null -ne (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

if (-not (PortBusy 8000)) {
    Start-Process -WindowStyle Hidden -WorkingDirectory (Join-Path $Root "apps\api") `
        -FilePath (Join-Path $Root ".venv\Scripts\python.exe") `
        -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" `
        -RedirectStandardOutput (Join-Path $LogDir "api.log") `
        -RedirectStandardError (Join-Path $LogDir "api.err.log")
}

if (-not (PortBusy 5173)) {
    Start-Process -WindowStyle Hidden -WorkingDirectory (Join-Path $Root "apps\web") `
        -FilePath "cmd.exe" `
        -ArgumentList "/c", "npm.cmd run dev -- --host 127.0.0.1 --port 5173" `
        -RedirectStandardOutput (Join-Path $LogDir "web.log") `
        -RedirectStandardError (Join-Path $LogDir "web.err.log")
}
