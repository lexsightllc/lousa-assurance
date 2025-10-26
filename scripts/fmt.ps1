# SPDX-License-Identifier: MPL-2.0
. "$PSScriptRoot/common.ps1"

Install-DevDependencies
& (Get-VenvExecutable 'isort') @args
& (Get-VenvExecutable 'black') @args
& (Get-VenvExecutable 'ruff') format @args
