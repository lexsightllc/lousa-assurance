# SPDX-License-Identifier: MPL-2.0
. "$PSScriptRoot/common.ps1"

Install-DevDependencies
& (Get-VenvExecutable 'python') -m build @args
