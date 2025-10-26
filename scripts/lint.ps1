. "$PSScriptRoot/common.ps1"

$fix = $false
if ($args.Length -gt 0 -and $args[0] -eq '--fix') {
    $fix = $true
    $args = $args[1..($args.Length - 1)]
}

Install-DevDependencies
if ($fix) {
    & (Get-VenvExecutable 'ruff') check --fix @args
    & (Get-VenvExecutable 'isort') @args
    & (Get-VenvExecutable 'black') @args
} else {
    & (Get-VenvExecutable 'ruff') check @args
    & (Get-VenvExecutable 'isort') --check-only @args
    & (Get-VenvExecutable 'black') --check @args
}
