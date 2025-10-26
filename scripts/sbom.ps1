. "$PSScriptRoot/common.ps1"

Install-DevDependencies
$sbomDir = Join-Path $RootDir 'sbom'
New-Item -ItemType Directory -Force -Path $sbomDir | Out-Null
& (Get-VenvExecutable 'cyclonedx-bom') -o (Join-Path $sbomDir 'cyclonedx.json') -F json
