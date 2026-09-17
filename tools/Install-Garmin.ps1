# Install the optional client in a private project environment, without changing
# the bundled Python runtime or storing any account credentials.
$ErrorActionPreference = 'Stop'
$garminBasePython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $garminBasePython)) {
    $garminBasePython = (Get-Command python -ErrorAction Stop).Source
}
& $garminBasePython -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'
if ($LASTEXITCODE -ne 0) { throw 'Garmin requires Python 3.12 or newer.' }
$garminEnvironment = Join-Path (Split-Path $PSScriptRoot -Parent) '.health-sync\garmin-venv'
& $garminBasePython -m venv $garminEnvironment
if ($LASTEXITCODE -ne 0) { throw 'Could not create the Garmin Python environment.' }
$garminPython = Join-Path $garminEnvironment 'Scripts\python.exe'
& $garminPython -m pip install --disable-pip-version-check -r (Join-Path $PSScriptRoot 'requirements-garmin.txt')
if ($LASTEXITCODE -ne 0) { throw 'Garmin dependencies could not be installed.' }
& $garminPython -B -c 'from garminconnect import Garmin; from zoneinfo import ZoneInfo; ZoneInfo("Europe/Warsaw")'
if ($LASTEXITCODE -ne 0) { throw 'Garmin installation verification failed.' }
Set-Content -LiteralPath (Join-Path $garminEnvironment '.ready') -Value 'garminconnect 0.3.15' -Encoding ascii
Write-Host 'Garmin client installed. Connect once: .\tools\Sync-Vitals.ps1 connect garmin'
