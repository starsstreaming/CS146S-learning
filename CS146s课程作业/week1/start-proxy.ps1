# CS146s week 1 - Plan A: put mitmproxy between Claude Code and CC Switch.
#
#   .\start-proxy.ps1
#
# Chain: claude -> mitmweb 127.0.0.1:58888 -> CC Switch 127.0.0.1:15721 -> upstream (xAI / other)
#
# Why the second hop is 15721 and not assignment's https://api.anthropic.com:
# the global ~/.claude/settings.json is managed by CC Switch (ANTHROPIC_AUTH_TOKEN=PROXY_MANAGED,
# the real key is injected by CC Switch), so the relay must hand traffic back to CC Switch.
#
# Two preconditions - miss either one and you get ECONNREFUSED:
#   1. CC Switch is running and listening on 15721 (quit it and every claude session breaks)
#   2. This repo's .claude/settings.json points ANTHROPIC_BASE_URL at 58888
#
# The capture file is deliberately written OUTSIDE every git repo (assignment requires this).

$ErrorActionPreference = 'Stop'

$flowsDir = 'C:\Users\29468\cs146s-capture'
$flows    = Join-Path $flowsDir 'session.flows'

if (-not (Get-Command mitmweb -ErrorAction SilentlyContinue)) {
  $candidates = @("$env:USERPROFILE\.dsh-tools\mitmproxy\Scripts\mitmweb.exe")
  $found = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
  if ($found) {
    $mitmweb = $found
    Write-Host "Using mitmweb from the isolated venv: $mitmweb"
  } else {
    Write-Host '[X] mitmweb not found. Install it once (assignment step 1): https://mitmproxy.org/' -ForegroundColor Red
    exit 1
  }
} else {
  $mitmweb = 'mitmweb'
}
if (-not (Get-NetTCPConnection -LocalPort 15721 -State Listen -ErrorAction SilentlyContinue)) {
  Write-Host '[X] Nothing is listening on 15721: CC Switch is not running. Start it first, or this hop will ECONNREFUSED.' -ForegroundColor Red
  exit 1
}
if (Get-NetTCPConnection -LocalPort 58888 -State Listen -ErrorAction SilentlyContinue) {
  Write-Host '[X] Port 58888 is already in use: the relay looks like it is already running.' -ForegroundColor Red
  exit 1
}

New-Item -ItemType Directory -Force -Path $flowsDir | Out-Null

Write-Host 'Relay starting: 127.0.0.1:58888 -> 127.0.0.1:15721' -ForegroundColor Green
Write-Host 'Inspect UI:     http://localhost:8081' -ForegroundColor Green
Write-Host "Capture file:   $flows" -ForegroundColor Green
Write-Host ''

& $mitmweb `
  --listen-host 127.0.0.1 `
  --listen-port 58888 `
  --web-port 8081 `
  --web-open-browser `
  --mode reverse:http://127.0.0.1:15721 `
  -w $flows