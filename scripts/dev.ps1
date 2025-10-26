. "$PSScriptRoot/common.ps1"

Install-DevDependencies
& (Get-VenvExecutable 'python') -m lousa.cli @args
