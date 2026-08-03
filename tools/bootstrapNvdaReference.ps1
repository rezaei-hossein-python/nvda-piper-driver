param(
    [switch]$VerifyOnly,
    [string]$ReferencePath = (Join-Path $PSScriptRoot '..\references\nvda-source')
)
$ErrorActionPreference = 'Stop'
$repo = 'https://github.com/nvaccess/nvda.git'
$lockPath = Join-Path $PSScriptRoot '..\references\nvda-source-lock.json'
$lock = Get-Content -Raw -LiteralPath $lockPath | ConvertFrom-Json
$reference = [IO.Path]::GetFullPath($ReferencePath)
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'git is required' }
if (-not (Test-Path -LiteralPath (Join-Path $reference '.git'))) {
    if ($VerifyOnly) { throw 'reference checkout is missing; run without -VerifyOnly to bootstrap it' }
    if (Test-Path -LiteralPath $reference) {
        $files = Get-ChildItem -LiteralPath $reference -Force -Recurse -File
        if ($files) { throw 'existing reference path contains files; refusing to overwrite' }
        Remove-Item -LiteralPath $reference -Recurse -Force
    }
    git clone $lock.repository $reference
}
$head = (& git -C $reference rev-parse HEAD).Trim()
if ($VerifyOnly) {
    if ($head -ne $lock.commitSha) { throw "HEAD mismatch: $head" }
} else {
    $status = (& git -C $reference status --porcelain)
    if ($status) { throw 'existing reference checkout is dirty; refusing to change it' }
    git -C $reference fetch --tags --prune origin
    git -C $reference checkout --detach $lock.commitSha
    git -C $reference submodule update --init --recursive
    $head = (& git -C $reference rev-parse HEAD).Trim()
    if ($head -ne $lock.commitSha) { throw "checkout mismatch: $head" }
}
if (-not (Test-Path -LiteralPath (Join-Path $reference 'source\synthDriverHandler.py'))) { throw 'complete source is missing source/synthDriverHandler.py' }
foreach ($path in @('source\synthDrivers', 'source\speech', 'source\globalPlugins', 'tests')) {
    if (-not (Test-Path -LiteralPath (Join-Path $reference $path))) { throw "required source directory missing: $path" }
}
$status = (& git -C $reference status --porcelain)
"reference=$reference"
"head=$head"
"tag=$((& git -C $reference tag --points-at HEAD) -join ',')"
"remote=$((& git -C $reference remote get-url origin).Trim())"
"clean=$([string]::IsNullOrWhiteSpace(($status -join '')) )"
