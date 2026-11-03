$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
Write-Host 'Open http://127.0.0.1:8765/outputs/03_savivaldybiu_zemelapis.html in your browser.'
Write-Host 'Keep this terminal open. Press Ctrl+C to stop the map server.'
& "$PSScriptRoot\.venv\Scripts\python.exe" -m http.server 8765 --bind 127.0.0.1
