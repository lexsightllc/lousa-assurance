. "$PSScriptRoot/common.ps1"

Install-DevDependencies
& (Get-VenvExecutable 'mypy') src @args
