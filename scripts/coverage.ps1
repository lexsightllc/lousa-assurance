. "$PSScriptRoot/common.ps1"

Install-DevDependencies
$coverageFile = Join-Path $RootDir 'coverage.xml'
if (-not (Test-Path $coverageFile)) {
    Write-Warning "Coverage data not found. Running tests first."
    & (Join-Path $PSScriptRoot 'test.ps1')
}
& (Get-VenvExecutable 'coverage') xml
& (Get-VenvExecutable 'coverage') html
& (Get-VenvExecutable 'coverage') report --fail-under=85
