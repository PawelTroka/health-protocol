# Repository tools

Run the commands below from the repository root.

- `tools/Sync-Vitals.ps1`: import and sync monthly vitals.
- `tools/generate_colored_report.py`: regenerate both results reports.
- `tools/generate_pillbox_guide.py`: generate the physical pillbox guide.
- `tools/tests/`: synthetic importer and sync tests.

## On-demand vitals sync

Run this in the health-protocol folder after connecting both accounts:

```powershell
.\tools\Sync-Vitals.ps1
```

It downloads the supported Oura and Withings measurements, computes calendar-month averages, and updates `results/vitals_monthly.json`, `results.md` and `results.html` together. It runs only when requested. The default range starts August 1, 2026; the original July baseline stays intact.

## Connect each account once

Browser sessions in Opera do not grant this local program API access. Each service requires a registered OAuth application and your consent. Oura's old personal access tokens were retired in December 2025.

1. Register an application in [Oura developer applications](https://cloud.ouraring.com/oauth/applications). Register exactly this redirect URI: `http://localhost:8765/callback/oura`.
2. Run `./tools/Sync-Vitals.ps1 connect oura`. Enter that application's client ID and client secret at the local terminal prompts, then approve the Oura browser consent. The requested scope is `daily`.
3. Register a personal/development application in the [Withings developer dashboard](https://developer.withings.com/dashboard/). Register exactly this redirect URI: `http://localhost:8765/callback/withings`.
4. Run `./tools/Sync-Vitals.ps1 connect withings`. Enter that application's credentials locally and complete browser consent. The requested scope is `user.metrics`.

Do not paste credentials in chat, the protocol, shell command arguments or Git. The client secrets and rotating OAuth tokens are encrypted with Windows DPAPI for your Windows user and stored outside the repository at `%LOCALAPPDATA%/HealthProtocolSync/credentials.dat`. Credentials are not taken from Opera cookies. Existing authorized connections refresh automatically; if consent expires or a refresh outcome is uncertain, run `authorize` again.

```powershell
.\tools\Sync-Vitals.ps1 status
.\tools\Sync-Vitals.ps1 authorize oura
.\tools\Sync-Vitals.ps1 authorize withings
```

The browser connection waits up to three minutes. If interrupted or declined, the app configuration remains available for a later `authorize` command. Client IDs/secrets come from the registered apps, not from your ordinary account passwords.

## Preview, sync one service, or revisit a date range

```powershell
.\tools\Sync-Vitals.ps1 sync --dry-run
.\tools\Sync-Vitals.ps1 sync --provider oura
.\tools\Sync-Vitals.ps1 sync --provider withings
.\tools\Sync-Vitals.ps1 sync --start 2026-08-01 --end 2026-09-05
```

The default sync requires both services. A failure in either service stops the update before publishing any new report. `--provider` explicitly allows updating one service while retaining the other's cache. Date bounds are inclusive; an API fetch replaces that provider's cache within the requested range, so corrected or removed readings can be reflected. Outside that range, history is retained.

## Import an export without an API connection

Oura on the web: open Trends, select the date range, choose Download Data, select all metrics, and download the CSV.

```powershell
.\tools\Sync-Vitals.ps1 import --oura-csv "C:\Users\hyperbook\Downloads\oura_2026-07-06_2026-09-06_trends.csv"
```

The import reads the exact bytes it archives. Reimporting the same file does not duplicate observations. Partial files amend the days and metrics they contain without removing other cached observations. An incoming Oura day/metric replaces the previous daily value even if one came from CSV and the other from the API.

For Withings, the supported fallback is saved **official API measurement JSON**, with every page combined. Arbitrary app export CSVs are not guessed: Withings export columns and units can vary by export/account.

```powershell
.\tools\Sync-Vitals.ps1 import --withings-json "C:\path\withings-measurements.json"
```

Accepted Withings JSON: `{"measuregrps": [...]}` from this sync client, or `{"measure": [page1, page2, ...]}` containing complete successful API responses. A standalone successful response is also accepted when it is the final/only page. Responses with unfinished pagination, API errors, ambiguous user records or credential fields are rejected or excluded as appropriate. Real measurement IDs identify revised readings; repeat imports do not increase their weight.

## What gets averaged

| Source | Automatically imported |
| :--- | :--- |
| Oura | Sleep duration, REM, deep sleep, time in bed, efficiency, latency, sleep score, average sleeping HR, mean nightly lowest HR, average HRV and respiratory rate |
| Withings | Weight, body fat, muscle percentage, bone percentage, visceral fat index, BMI, paired blood pressure, PWV and body temperature when available |

- Calendar dates use **Europe/Warsaw** for Withings timestamps. Oura's recorded sleep `day` is authoritative. Current-day Oura data are deferred until the next day; Withings readings already recorded today can contribute.
- The Oura API uses the longest completed `long_sleep` record for each day; naps and rest periods are excluded. Sleep score comes from `daily_sleep.score`, never from contributor scores. Oura's API and app/CSV HR values can differ because of their sampling methods; source types remain recorded.
- Each observed day has equal weight. Multiple Withings readings on a day are averaged first, then the daily averages are averaged across the month. Blood pressure remains paired within the same measurement group.
- Missing days are excluded, never converted to zero. Each metric records its actual observation count, number of days, first/last date, and elapsed/calendar days. Current calendar months are marked as month to date, including the last day of that month.
- Body fat, muscle and bone percentages use the same measurement group's weight and component mass; lean mass is not relabeled as muscle. Bone mass from API type 88 is converted from kilograms to percentage using that same reading's weight. Visceral fat from type 170 retains the Withings **0–20 index**, which cannot be converted to a percentage. BMI uses the recorded **180cm** height. Use `--height-cm` to change this explicit assumption if needed; derivation details remain in the local records.
- Average HRV and nightly minima are separate from maximum HRV. Categorical or app-only results—including ECG rhythm, heart-sound classifications, confirmed nerve score, nighttime dipping and cardiovascular-age difference—retain their dated manual observations. The command does not fabricate monthly averages for them.

## Files and verification

- `tools/health_sync/` and `tools/sync_vitals.py`: import, authentication and averaging code.
- `.health-sync/raw/`: private, content-addressed copies of downloaded data; existing copies are never overwritten.
- `.health-sync/records.json`: private normalized daily/measurement cache.
- `results/vitals_monthly.json`: generated per-metric averages and coverage, consumed by the report generator. Do not hand-edit it.
- `tools/generate_colored_report.py`: retains historical/manual results and merges the generated averages. Importing this module no longer writes reports.
- `results.md` and `results.html`: regenerated outputs. Imported cells receive a separate source note; manual observations keep their original provenance.

The private cache and exports are ignored by Git. The monthly summary and results are ordinary repository artifacts; review their diff before choosing to commit. Nothing is committed or pushed by the sync. The command uses an OS process lock, bounded network requests, pagination checks, safe read retries and staged report generation. File replacements roll back on a handled error; after a power loss, rerun the sync to regenerate the outputs consistently.

The PowerShell wrapper uses the bundled Codex Python runtime when available, otherwise `python` on PATH. Python 3.10+ is required; a fallback Windows Python may also need the `tzdata` package for Europe/Warsaw. API credential storage requires Windows. Tests use synthetic API responses and no real credentials:

```powershell
python -B -m unittest discover -s tools/tests -t . -v
git diff --check
```

Official references: [Oura API](https://cloud.ouraring.com/v2/docs), [Oura authentication](https://cloud.ouraring.com/docs/authentication), [Withings API schema](https://developer.withings.com/openapi.yaml), [Withings OAuth](https://developer.withings.com/developer-guide/v3/integration-guide/public-health-data-api/get-access/oauth-web-flow/), [Withings exports](https://support.withings.com/hc/en-us/articles/360001391287-Privacy-How-can-I-export-my-data).
