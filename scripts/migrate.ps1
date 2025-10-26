# SPDX-License-Identifier: MPL-2.0
. "$PSScriptRoot/common.ps1"

Install-DevDependencies
$migrations = Join-Path $RootDir 'infra/migrations'
if (Test-Path $migrations -PathType Container) {
    Write-Host "Running migrations in infra/migrations"
    Get-ChildItem -Path $migrations -Filter '*.py' -Recurse | ForEach-Object {
        & (Get-VenvExecutable 'python') $_.FullName
    }
} else {
    Write-Host "No migrations defined."
}
