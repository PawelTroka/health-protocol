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

It downloads the available Oura and Withings health collections, computes calendar-month averages of supported numeric measurements, and updates `results/vitals_monthly.json`, `results.md` and `results.html` together. It runs only when requested. The default range starts **July 1, 2026**. Imported July averages replace the corresponding July cells; original manual values remain in the generator and source history. Earlier laboratory history is retained.

## Connect each account once

Browser sessions in Opera do not grant this local program API access. Each service requires a registered OAuth application and your consent. Oura's old personal access tokens were retired in December 2025.

1. Register an application in [Oura developer applications](https://cloud.ouraring.com/oauth/applications). Register exactly this redirect URI: `http://localhost:8765/callback/oura`.
2. Run `./tools/Sync-Vitals.ps1 connect oura`. Enter that application's client ID and client secret at the local terminal prompts, then approve the Oura browser consent. The requested scopes are `daily heartrate workout session spo2 heart_health stress`. The live API required `heart_health` for cardiovascular age/VO2max and `stress` for resilience on September 6, 2026; the older authentication documentation does not list these additions.
3. Register a personal/development application in the [Withings developer dashboard](https://developer.withings.com/dashboard/). Register exactly this redirect URI: `http://localhost:8765/callback/withings`.
4. Run `./tools/Sync-Vitals.ps1 connect withings`. Enter that application's credentials locally and complete browser consent. The requested scopes are `user.metrics,user.activity`.

Do not paste credentials in chat, the protocol, shell command arguments or Git. The client secrets and rotating OAuth tokens are encrypted with Windows DPAPI for your Windows user and stored in the Git-ignored `tools/.secrets/credentials.dat`. There is no plaintext credential file. Credentials are not taken from Opera cookies. Existing authorized connections refresh automatically; if consent expires, expanded scopes need consent, or a refresh outcome is uncertain, run `authorize` again.

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
.\tools\Sync-Vitals.ps1 sync --start 2026-07-01 --end 2026-09-05
```

The default sync requests both services. Authentication, transport, invalid-response and pagination failures stop the update before publishing new reports. `--provider` explicitly allows updating one service while retaining the other's cache. Date bounds are inclusive. A complete API fetch replaces that provider's cache within the requested range, so corrected or removed readings can be reflected; outside that range, history is retained.

Optional endpoints returning HTTP 403/404 are recorded as unavailable in the source's `_sync.endpoint_status` rather than treated as measurements or zeros. Remaining accessible data can still be imported. Each complete collection replaces its own cached observations in the requested range; unavailable collections retain theirs. The monthly source file records sync coverage; check it when a device, account permission or service restriction leaves a gap. A successful endpoint with no observations is distinct from an unavailable endpoint.

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
| Oura | Sleep, readiness and activity values and contributor scores; SpO2 and breathing-disturbance index; cardiovascular age and derived PWV; VO2max; stress/recovery durations; resilience contributors; source-specific heart rate; recorded workout and session quantities |
| Withings | Body composition and segment masses; weight, height and BMI; blood pressure and pulse; SpO2, PWV, vascular/metabolic age and VO2max; numeric nerve measurements; temperature; supported urinary measurements; sleep summaries and activity quantities |

The precise numeric registry is `OURA_METRICS` in `tools/health_sync/oura.py` and `WITHINGS_METRICS` in `tools/health_sync/withings.py`. New report rows appear only when observations are returned. Provider-specific names distinguish related measurements with different definitions; adding an API field does not invent a clinical reference range or assign a health score.

Oura requests `sleep`, `daily_sleep`, `daily_readiness`, `daily_activity`, `daily_spo2`, `daily_cardiovascular_age`, `vO2_max`, `daily_stress`, `daily_resilience`, `heartrate`, `workout` and `session`. Withings requests real measurement groups, sleep summaries, activity summaries and heart/stethoscope recording metadata. OAuth scopes permit access; device support, membership, product region, recorded history and account permissions determine which observations actually exist.

- Calendar dates use **Europe/Warsaw** for Withings timestamps. Oura's recorded sleep `day` is authoritative. Current-day Oura data are deferred until the next day; Withings readings already recorded today can contribute.
- The Oura API uses the longest completed `long_sleep` record for each day; naps and rest periods are excluded. Sleep score comes from `daily_sleep.score`, never from contributor scores. Oura's API and app/CSV HR values can differ because of their sampling methods; source types remain recorded.
- Each observed day has equal weight. Multiple readings on a day are averaged first, then the daily averages are averaged across the month. Blood pressure remains paired within the same measurement group. Daily activity quantities are mean observed-day quantities, not monthly totals. Workout/session rows describe the mean recorded workout/session within a day, followed by a mean across observed days; they are not totals or estimates for days without recordings.
- Withings can split one night's sleep into multiple nonoverlapping sessions. The importer combines those sessions before calculating monthly means: durations and event counts are summed per day; HR, respiratory rate and AHI use sleep-duration weights; nightly minima/maxima retain their daily extrema; efficiency is combined sleep time divided by combined time in bed. Reported scores and latencies remain session means. HRV at Sleep Start/End remains a mean of reported session-start/session-end windows, not a reconstructed all-night HRV measure. Original session IDs, counts, intervals and aggregation rules remain traceable in the local records. Ambiguous overlapping sessions are rejected.
- Missing days are excluded, never converted to zero. Each metric records its actual observation count, number of days, first/last date, and elapsed/calendar days. Current calendar months are marked as month to date, including the last day of that month.
- Body fat, muscle and bone percentages use the same measurement group's weight and component mass; lean mass is not relabeled as muscle. Bone mass from API type 88 is converted from kilograms to percentage using that same reading's weight. Visceral fat from type 170 retains the Withings **0–20 index**, which cannot be converted to a percentage. BMI uses the recorded **180cm** height. Use `--height-cm` to change this explicit assumption if needed; derivation details remain in the local records.
- Average HRV and nightly minima are separate from maximum HRV. Oura and Withings sleep estimates, vascular-age measures and provider-specific VO2max remain separate. API nerve conductance/response scores do not replace the app's confirmed monthly nerve health score.
- Withings HRV during the first and last 90 minutes of sleep is imported separately in milliseconds, as documented in [Withings Sleep HRV](https://support.withings.com/hc/en-us/articles/35762631441681-Sleep-U-S-Nighttime-Heart-Rate-Variability-HRV).
- Supported device classifications appear in separate provider-specific rows as **observed label counts per month**. They are not averaged codes, health scores, clinical diagnoses or estimates for unrecorded days. The original dated/manual ECG, heart sounds, confirmed app nerve score, nighttime dipping and cardiovascular-age difference remain distinct. Unrecognized classification values are shown explicitly as device codes with unverified meanings, which may include unavailable-result codes; their original values also remain archived. Under-specified ECG interval and ESC fields remain raw and are not averaged. Units and labels are not guessed.

## Files and verification

- `tools/health_sync/` and `tools/sync_vitals.py`: import, authentication and averaging code.
- `tools/.secrets/credentials.dat`: Windows-user-encrypted OAuth configuration and tokens; ignored by Git.
- `.health-sync/raw/`: private, content-addressed copies of downloaded data; existing copies are never overwritten.
- `.health-sync/records.json`: private normalized daily/measurement cache and device classifications; classifications are counted separately from numeric measurements.
- `results/vitals_monthly.json`: generated per-metric averages and coverage, consumed by the report generator. Do not hand-edit it.
- `tools/generate_colored_report.py`: retains original historical/manual source values and merges generated averages into existing or new monthly columns, including July. Importing this module does not write reports.
- `results.md` and `results.html`: regenerated outputs. Imported cells receive a separate source note; manual observations keep their original provenance.

The private cache and exports are ignored by Git. The monthly summary and results are ordinary repository artifacts; review their diff before choosing to commit. Nothing is committed or pushed by the sync. The command uses an OS process lock, bounded network requests, pagination checks, safe read retries and staged report generation. File replacements roll back on a handled error; after a power loss, rerun the sync to regenerate the outputs consistently.

The PowerShell wrapper uses the bundled Codex Python runtime when available, otherwise `python` on PATH. Python 3.10+ is required; a fallback Windows Python may also need the `tzdata` package for Europe/Warsaw. API credential storage requires Windows. Tests use synthetic API responses and no real credentials:

```powershell
python -B -m unittest discover -s tools/tests -t . -v
git diff --check
```

Official references: [Oura API](https://cloud.ouraring.com/v2/docs), [Oura authentication](https://cloud.ouraring.com/docs/authentication), [Withings API schema](https://developer.withings.com/openapi.yaml), [Withings OAuth](https://developer.withings.com/developer-guide/v3/integration-guide/public-health-data-api/get-access/oauth-web-flow/), [Withings exports](https://support.withings.com/hc/en-us/articles/360001391287-Privacy-How-can-I-export-my-data).
