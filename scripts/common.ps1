# SPDX-License-Identifier: MPL-2.0
$ErrorActionPreference = "Stop"

$global:RootDir = Resolve-Path (Join-Path $PSScriptRoot '..')
$global:VenvPath = if ($env:VENV_PATH) { $env:VENV_PATH } else { Join-Path $RootDir '.venv' }

function Get-VenvExecutable([string]$name) {
    $binDir = if ($IsWindows) { 'Scripts' } else { 'bin' }
    return Join-Path $VenvPath (Join-Path $binDir $name)
}

function Ensure-Venv {
    if (-not (Test-Path $VenvPath)) {
        python -m venv $VenvPath | Out-Null
    }
}

function Get-PipOptions {
    if ($env:PIP_OPTIONS) {
        return $env:PIP_OPTIONS.Split(' ')
    }
    return @()
}

function Install-DevDependencies {
    Ensure-Venv
    $opts = Get-PipOptions
    & (Get-VenvExecutable 'pip') install @opts --upgrade pip | Out-Null
    & (Get-VenvExecutable 'pip') install @opts -e .[dev]
}

function Ensure-Bootstrap {
    Install-DevDependencies
    & (Get-VenvExecutable 'pre-commit') install --install-hooks | Out-Null
    & (Get-VenvExecutable 'pre-commit') install --hook-type commit-msg | Out-Null
    git config commit.template ".github/commit_template.txt" | Out-Null
}
