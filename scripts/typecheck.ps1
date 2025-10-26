# SPDX-License-Identifier: MPL-2.0
. "$PSScriptRoot/common.ps1"

Install-DevDependencies
& (Get-VenvExecutable 'mypy') src @args
