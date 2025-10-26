. "$PSScriptRoot/common.ps1"

Install-DevDependencies
& (Get-VenvExecutable 'pytest') --cov=src/lousa --cov-report=term-missing --cov-report=xml @args
