. "$PSScriptRoot/common.ps1"

Install-DevDependencies
& (Get-VenvExecutable 'mkdocs') build --strict
