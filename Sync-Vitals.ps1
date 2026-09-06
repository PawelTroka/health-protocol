# Run with no arguments to fetch both connected services and update the reports.
$vitalsPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $vitalsPython)) {
    $vitalsPython = (Get-Command python -ErrorAction Stop).Source
}
& $vitalsPython -B (Join-Path $PSScriptRoot 'sync_vitals.py') @args
exit $LASTEXITCODE
