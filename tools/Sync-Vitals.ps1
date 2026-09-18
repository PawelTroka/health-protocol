# Run with no arguments to fetch all connected services and update the reports.
$garminEnvironment = Join-Path (Split-Path $PSScriptRoot -Parent) '.health-sync\garmin-venv'
$vitalsPython = Join-Path $garminEnvironment 'Scripts\python.exe'
if (-not ((Test-Path -LiteralPath (Join-Path $garminEnvironment '.ready')) -and (Test-Path -LiteralPath $vitalsPython))) {
    $vitalsPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (-not (Test-Path -LiteralPath $vitalsPython)) {
        $vitalsPython = (Get-Command python -ErrorAction Stop).Source
    }
}
& $vitalsPython -B -X utf8 (Join-Path $PSScriptRoot 'sync_vitals.py') @args
exit $LASTEXITCODE
