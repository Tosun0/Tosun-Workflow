$ErrorActionPreference = 'Stop'

$root = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$python = 'C:\Users\mjo24\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$packageRoot = Join-Path $root 'packaged'
$bundleRoot = Join-Path $packageRoot 'TosunStudio'
$buildRoot = Join-Path $root 'build'

if (-not (Test-Path -LiteralPath $python)) {
    throw "Bundled Python was not found: $python"
}

New-Item -ItemType Directory -Path $packageRoot -Force | Out-Null
if (Test-Path -LiteralPath $bundleRoot) {
    Remove-Item -LiteralPath $bundleRoot -Recurse -Force
}
if (Test-Path -LiteralPath $buildRoot) {
    Remove-Item -LiteralPath $buildRoot -Recurse -Force
}

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --windowed `
    --name TosunStudio `
    --distpath $packageRoot `
    --workpath $buildRoot `
    --specpath $buildRoot `
    (Join-Path $root 'runner.py')

foreach ($folder in @('web', 'config', 'instructions', 'workspace')) {
    Copy-Item -LiteralPath (Join-Path $root $folder) -Destination (Join-Path $bundleRoot $folder) -Recurse -Force
}
Copy-Item -LiteralPath (Join-Path $root 'README.md') -Destination (Join-Path $bundleRoot 'README.md') -Force
Copy-Item -LiteralPath (Join-Path $root 'AGENTS.md') -Destination (Join-Path $bundleRoot 'AGENTS.md') -Force

$launch = @"
@echo off
start "" "%~dp0TosunStudio.exe"
"@
[System.IO.File]::WriteAllText((Join-Path $bundleRoot 'TosunStudio.cmd'), $launch, [System.Text.Encoding]::ASCII)

$readme = @"
# Tosun Studio packaged build

실행 파일: TosunStudio.exe

실행하면 로컬 GUI가 브라우저에서 자동으로 열립니다.
작업 파일은 이 폴더의 workspace에 저장됩니다.
"@
[System.IO.File]::WriteAllText((Join-Path $bundleRoot 'RUNME.md'), $readme, [System.Text.Encoding]::UTF8)

Write-Output "Package created: $bundleRoot"
