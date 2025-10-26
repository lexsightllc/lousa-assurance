# SPDX-License-Identifier: MPL-2.0
. "$PSScriptRoot/common.ps1"

Install-DevDependencies
& (Get-VenvExecutable 'pip-audit') @args
& (Get-VenvExecutable 'bandit') -r src/lousa -ll
$tmp = Join-Path ([System.IO.Path]::GetTempPath()) 'detect-secrets.json'
& (Get-VenvExecutable 'detect-secrets') scan --baseline .secrets.baseline --all-files --fail-on-unaudited --output $tmp
