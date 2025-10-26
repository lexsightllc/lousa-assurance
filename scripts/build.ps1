. "$PSScriptRoot/common.ps1"

Install-DevDependencies
& (Get-VenvExecutable 'python') -m build @args
