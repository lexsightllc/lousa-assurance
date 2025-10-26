# SPDX-License-Identifier: MPL-2.0
. "$PSScriptRoot/common.ps1"

Install-DevDependencies
$e2ePath = Join-Path $RootDir 'tests/e2e'
if (Test-Path $e2ePath -PathType Container -and (Get-ChildItem -Path $e2ePath -Filter '*.py').Count -gt 0) {
    & (Get-VenvExecutable 'pytest') $e2ePath @args
} else {
    Write-Warning "No end-to-end tests defined. Skipping."
}
