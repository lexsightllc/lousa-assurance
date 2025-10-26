. "$PSScriptRoot/common.ps1"

Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $VenvPath, 'build', 'dist', 'htmlcov', '.pytest_cache', '.mypy_cache', 'coverage.xml'
Get-ChildItem -Path $RootDir -Directory -Recurse -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
