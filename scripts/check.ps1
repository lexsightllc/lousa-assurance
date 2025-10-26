$root = Resolve-Path (Join-Path $PSScriptRoot '..')
& (Join-Path $root 'scripts/lint.ps1') @args
& (Join-Path $root 'scripts/typecheck.ps1') @args
& (Join-Path $root 'scripts/test.ps1') @args
& (Join-Path $root 'scripts/coverage.ps1') @args
& (Join-Path $root 'scripts/security-scan.ps1') @args
