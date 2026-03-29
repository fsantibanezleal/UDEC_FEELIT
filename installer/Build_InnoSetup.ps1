<#
.SYNOPSIS
    Compile the FeelIT Windows installer using Inno Setup.
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$InstallerRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$InnoScript = Join-Path $InstallerRoot "FeelIT_installer.iss"
$ISCC = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $ISCC)) {
    throw "Inno Setup compiler not found at $ISCC"
}

Set-Location $ProjectRoot
if (-not (Test-Path $VenvPython)) {
    python -m venv .venv
}

$Version = (& $VenvPython scripts\sync_version.py).Trim()
Write-Host "Compiling FeelIT installer for version $Version" -ForegroundColor Cyan
& $ISCC $InnoScript
