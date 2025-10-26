. "$PSScriptRoot/common.ps1"

$increment = 'patch'
if ($args.Length -gt 0) {
    $increment = $args[0]
    $args = $args[1..($args.Length - 1)]
}

Install-DevDependencies
& (Get-VenvExecutable 'cz') bump --yes --changelog --increment $increment
& (Join-Path $PSScriptRoot 'build.ps1') @args
Write-Host "Release bump complete. Remember to push tags."
