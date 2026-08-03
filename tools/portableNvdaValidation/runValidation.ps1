param(
    [ValidateSet('Control','Cache','All','Functional','Performance')]
    [string]$Mode = 'All',
    [string]$PackagePath = (Join-Path $PSScriptRoot '..\..\nvdaPiperDriver-0.1.0.nvda-addon'),
    [switch]$ApproveLaunch
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = Join-Path $repo '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'repository .venv Python is missing' }
$arguments = @((Join-Path $PSScriptRoot 'runValidation.py'), '--mode', $Mode, '--package', (Resolve-Path $PackagePath).Path)
if ($ApproveLaunch) { $arguments += '--approve-launch' }
& $python @arguments
exit $LASTEXITCODE
