$ErrorActionPreference = 'Stop'

$pythonCommand = Get-Command py -ErrorAction SilentlyContinue
if ($null -ne $pythonCommand) {
    & py -3 (Join-Path $PSScriptRoot 'runner.py') --serve --port 8765
} else {
    & python (Join-Path $PSScriptRoot 'runner.py') --serve --port 8765
}
