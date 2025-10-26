# SPDX-License-Identifier: MPL-2.0
. "$PSScriptRoot/common.ps1"

$group = if ($args.Length -gt 0) { $args[0] } else { 'all' }

Install-DevDependencies
 $targets = @()
switch ($group) {
    'runtime' {
        & (Get-VenvExecutable 'pip-compile') pyproject.toml --output-file requirements.txt
        $targets += 'requirements.txt'
    }
    'dev' {
        & (Get-VenvExecutable 'pip-compile') pyproject.toml --extra dev --output-file requirements-dev.txt
        $targets += 'requirements-dev.txt'
    }
    'all' {
        & (Get-VenvExecutable 'pip-compile') pyproject.toml --output-file requirements.txt
        & (Get-VenvExecutable 'pip-compile') pyproject.toml --extra dev --output-file requirements-dev.txt
        $targets += 'requirements-dev.txt','requirements.txt'
    }
    Default {
        Write-Error "Unknown dependency group: $group"
    }
}
& (Get-VenvExecutable 'pip-sync') $targets
& (Get-VenvExecutable 'pip') list --outdated
