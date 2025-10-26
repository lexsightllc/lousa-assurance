# SPDX-License-Identifier: MPL-2.0
. "$PSScriptRoot/common.ps1"

Install-DevDependencies
& (Get-VenvExecutable 'pytest') --cov=src/lousa --cov-report=term-missing --cov-report=xml @args
