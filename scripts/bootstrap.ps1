# SPDX-License-Identifier: MPL-2.0
. "$PSScriptRoot/common.ps1"

Install-DevDependencies
& (Get-VenvExecutable 'detect-secrets') scan --update .secrets.baseline --all-files | Out-Null
Ensure-Bootstrap
Write-Host "Bootstrap complete. Virtual environment located at $VenvPath."
