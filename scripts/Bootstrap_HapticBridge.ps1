param(
  [Parameter(Mandatory = $false)]
  [string]$Backend = "openhaptics-touch",

  [Parameter(Mandatory = $false)]
  [string]$BuildType = "Release",

  [Parameter(Mandatory = $false)]
  [string]$SdkRoot = "",

  [switch]$Build
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-ExistingPath {
  param([string]$PathValue)
  if ([string]::IsNullOrWhiteSpace($PathValue)) {
    return $null
  }
  if (Test-Path $PathValue) {
    return (Resolve-Path $PathValue).Path
  }
  return $null
}

function Convert-ToCMakePath {
  param([string]$PathValue)
  if ([string]::IsNullOrWhiteSpace($PathValue)) {
    return $PathValue
  }
  return ($PathValue -replace "\\", "/")
}

function Resolve-ToolPath {
  param(
    [string]$CommandName,
    [string]$OverrideEnvVar,
    [string[]]$Candidates
  )

  $override = Resolve-ExistingPath ([Environment]::GetEnvironmentVariable($OverrideEnvVar))
  if ($override) {
    return $override
  }

  $command = Get-Command $CommandName -ErrorAction SilentlyContinue
  if ($command) {
    return $command.Source
  }

  foreach ($candidate in $Candidates) {
    $resolved = Resolve-ExistingPath $candidate
    if ($resolved) {
      return $resolved
    }
  }

  return $null
}

function Invoke-CheckedExternal {
  param(
    [string]$Executable,
    [string[]]$Arguments
  )

  & $Executable @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "Command failed with exit code ${LASTEXITCODE}: $Executable $($Arguments -join ' ')"
  }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$nativeRoot = Join-Path $repoRoot "native"
$buildRoot = Join-Path $nativeRoot "build"
$buildDir = Join-Path $buildRoot $Backend

$vsRoot = "C:\Program Files\Microsoft Visual Studio\2022\Community"
$cmakeExe = Resolve-ToolPath -CommandName "cmake" -OverrideEnvVar "FEELIT_CMAKE_EXE" -Candidates @(
  "C:\Program Files\CMake\bin\cmake.exe",
  (Join-Path $vsRoot "Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe")
)
$ninjaExe = Resolve-ToolPath -CommandName "ninja" -OverrideEnvVar "FEELIT_NINJA_EXE" -Candidates @(
  (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\ninja.exe"),
  (Join-Path $vsRoot "Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe")
)
$clangExe = Resolve-ToolPath -CommandName "clang++" -OverrideEnvVar "FEELIT_CLANGXX_EXE" -Candidates @(
  "C:\Program Files\LLVM\bin\clang++.exe"
)
$resourceCompilerExe = Resolve-ToolPath -CommandName "llvm-rc" -OverrideEnvVar "FEELIT_RC_EXE" -Candidates @(
  "C:\Program Files\LLVM\bin\llvm-rc.exe",
  "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\rc.exe"
)
$msbuildExe = Resolve-ToolPath -CommandName "msbuild" -OverrideEnvVar "FEELIT_MSBUILD_EXE" -Candidates @(
  (Join-Path $vsRoot "MSBuild\Current\Bin\MSBuild.exe")
)

if (-not $cmakeExe) {
  throw "CMake was not detected. Install Kitware.CMake or set FEELIT_CMAKE_EXE."
}

if (-not $resourceCompilerExe) {
  throw "A Windows resource compiler was not detected. Install LLVM or the Windows SDK and set FEELIT_RC_EXE if needed."
}

$generator = "Ninja"
$cmakeArgs = @(
  "-S", $nativeRoot,
  "-B", $buildDir,
  "-G", $generator,
  "-DCMAKE_BUILD_TYPE=$BuildType",
  "-DFEELIT_BRIDGE_DEFAULT_BACKEND=$Backend"
)

if ($ninjaExe -and $clangExe) {
  $cmakeArgs += "-DCMAKE_MAKE_PROGRAM=$(Convert-ToCMakePath $ninjaExe)"
  $cmakeArgs += "-DCMAKE_CXX_COMPILER=$(Convert-ToCMakePath $clangExe)"
  $cmakeArgs += "-DCMAKE_RC_COMPILER=$(Convert-ToCMakePath $resourceCompilerExe)"
}
elseif ($msbuildExe) {
  $generator = "Visual Studio 17 2022"
  $cmakeArgs = @(
    "-S", $nativeRoot,
    "-B", $buildDir,
    "-G", $generator,
    "-A", "x64",
    "-DFEELIT_BRIDGE_DEFAULT_BACKEND=$Backend",
    "-DCMAKE_RC_COMPILER=$(Convert-ToCMakePath $resourceCompilerExe)"
  )
}
else {
  throw "No compatible native toolchain was detected. Install Ninja plus LLVM or Visual Studio Build Tools."
}

if ($SdkRoot) {
  $resolvedSdkRoot = Resolve-ExistingPath $SdkRoot
  if (-not $resolvedSdkRoot) {
    throw "The provided -SdkRoot path does not exist: $SdkRoot"
  }
  $cmakeArgs += "-DFEELIT_VENDOR_SDK_ROOT=$resolvedSdkRoot"
}

New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

Write-Host "Configuring FeelIT bridge scaffold"
Write-Host "  Backend : $Backend"
Write-Host "  Build   : $BuildType"
Write-Host "  Native  : $nativeRoot"
Write-Host "  BuildDir: $buildDir"
Invoke-CheckedExternal -Executable $cmakeExe -Arguments $cmakeArgs

if ($Build) {
  Write-Host "Building FeelIT bridge scaffold"
  Invoke-CheckedExternal -Executable $cmakeExe -Arguments @("--build", $buildDir, "--config", $BuildType)
}

$probeExe = Join-Path $buildDir "out\feelit_bridge_probe.exe"
if (Test-Path $probeExe) {
  Write-Host "Probe executable ready at $probeExe"
} else {
  Write-Host "Configured build tree at $buildDir"
}
