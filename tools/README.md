# Repository tools

Run the commands below from the repository root.

- `tools/Sync-Vitals.ps1`: import and sync monthly vitals.
- `tools/generate_colored_report.py`: regenerate both results reports.
- `tools/imaging_report.py`: curated imaging records, verified source links and shared report layout.
- `tools/generate_pillbox_guide.py`: generate the physical pillbox guide.
- `tools/tests/`: synthetic importer and sync tests.

## Dated laboratory results

`tools/generate_colored_report.py` keeps the original laboratory history in `data` and adds later specimen results through `lab_followups`. Use the specimen collection month, preserve exact dates and source-specific units/ranges in a linked source record, and add new assays to their own rows when the method or specimen differs. The [September 16, 2026 source record](../results/Labs-2026-09-16/Sources.md) covers the ALAB panel and the separate Diagnostyka stool PCR panel.

Explicitly awaited results use `pending`, which blocks an older trend; `-` means no supplied result. `lab_pending_tests` lists outstanding assays without inventing units or ranges. When later PDFs arrive, replace the corresponding pending entries and update the pending-test registry and source record. Regenerate both outputs from the repository root with `python -B tools/generate_colored_report.py`; this does not fetch new device data.

Keep report notes brief and focused on meaningful abnormalities, large changes or useful interpretation. Keep collection dates, transcription details and pending-test lists in the linked source records.

## On-demand vitals sync

Run this in the health-protocol folder after connecting your accounts:

```powershell
.\tools\Sync-Vitals.ps1
```

It downloads the available Oura, Withings and Garmin health collections from connected accounts, computes calendar-month averages of supported numeric measurements, and updates `results/vitals_monthly.json`, `results.md` and `results.html` together. It runs only when requested. The default range starts **July 1, 2026**. Imported July averages replace the corresponding July cells; original manual values remain in the generator and source history. Earlier laboratory history is retained.

### Garmin Connect

First sync the watch to Garmin Connect. Then install the optional client and connect once in a local terminal:

```powershell
.\tools\Install-Garmin.ps1
.\tools\Sync-Vitals.ps1 connect garmin
.\tools\Sync-Vitals.ps1 sync --provider garmin
```

Enter your Garmin Connect email, password and any MFA code at the hidden terminal prompts. The password is not saved. Session tokens use the existing Windows-user-encrypted vault; the tool never creates a plaintext Garmin token file or reads browser cookies. To reconnect, run `connect garmin` again. After connection, the ordinary no-argument sync includes Garmin automatically.

Garmin's [official developer program](https://developer.garmin.com/gc-developer-program/program-faq/) is for business integrations. This personal sync uses the **unofficial** [python-garminconnect client](https://github.com/cyberjunky/python-garminconnect), pinned to `0.3.15`. The installer uses an ignored project virtual environment and Python 3.12+; it does not alter the shared Python runtime. Service changes may require a client update or a fresh login.

Supported readings include steps, distance, energy, heart rate, intensity minutes, floors, stress, Body Battery, sleep stages/score, sleeping oxygen/respiration, HRV and morning training readiness/recovery time. Every row retains a Garmin source label. Metrics appear only when Garmin returns usable data; owning a particular watch does not establish availability. VO2max, workout detail and inReach messages/location are outside this initial importer.

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

The default `--provider all` requests every configured account; `--provider both` retains the original Oura+Withings selection. A configured account requiring renewed login stops the sync rather than being silently skipped. Authentication, transport, invalid-response and pagination failures stop the update before publishing new reports. `--provider` explicitly allows updating one service while retaining the others' cache and coverage metadata. Date bounds are inclusive. A complete API fetch replaces that provider's cache within the requested range, so corrected or removed readings can be reflected; outside that range, history is retained.

Optional endpoints returning HTTP 403/404 are recorded as unavailable in the source's `_sync.endpoint_status` rather than treated as measurements or zeros. Remaining accessible data can still be imported. Each complete collection replaces its own cached observations in the requested range; unavailable collections retain theirs. The monthly source file records sync coverage; check it when a device, account permission or service restriction leaves a gap. A successful endpoint with no observations is distinct from an unavailable endpoint.

For Garmin, only optional-endpoint404 responses are treated as unavailable. Authentication/403, rate limits and other failures stop publication. If any date is unavailable, that collection's existing history is retained and successfully returned dates amend it. A successful empty response is recorded separately. Requests are bounded and the Garmin fetch range is limited to 366 days per run.

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

Garmin can also reimport a saved measurement envelope from this tool with `import --garmin-json "C:\path\garmin-readings.json"`. Its supported collections (`daily_summary`, `sleep`, `hrv`, `training_readiness`) contain lists of `{"day":"YYYY-MM-DD","data":<response>}`. This is not an importer for arbitrary Garmin CSV, FIT or full-account exports. Credential-bearing files are rejected; a partial file amends only supplied observations.

## What gets averaged

| Source | Automatically imported |
| :--- | :--- |
| Oura | Sleep, readiness and activity values and contributor scores; SpO2 and breathing-disturbance index; cardiovascular age and derived PWV; VO2max; stress/recovery durations; resilience contributors; source-specific heart rate; recorded workout and session quantities |
| Withings | Body composition and segment masses; weight, height and BMI; blood pressure and pulse; SpO2, PWV, vascular/metabolic age and VO2max; numeric nerve measurements; temperature; supported urinary measurements; sleep summaries and activity quantities |
| Garmin | Daily activity, energy, heart rate, stress and Body Battery; sleep duration/stages, score, oxygen and respiration; nightly and rolling HRV; explicit morning training readiness and recovery time |

The precise numeric registries are `OURA_METRICS`, `WITHINGS_METRICS` and `GARMIN_METRICS` in their respective modules under `tools/health_sync/`. New report rows appear only when observations are returned. Provider-specific names distinguish related measurements with different definitions; adding an API field does not invent a clinical reference range or assign a health score.

Oura requests `sleep`, `daily_sleep`, `daily_readiness`, `daily_activity`, `daily_spo2`, `daily_cardiovascular_age`, `vO2_max`, `daily_stress`, `daily_resilience`, `heartrate`, `workout` and `session`. Withings requests real measurement groups, sleep summaries, activity summaries and heart/stethoscope recording metadata. OAuth scopes permit access; device support, membership, product region, recorded history and account permissions determine which observations actually exist.

- Calendar dates use **Europe/Warsaw** for Withings timestamps. Oura's recorded sleep `day` is authoritative. Current-day Oura data are deferred until the next day; Withings readings already recorded today can contribute.
- Garmin uses the response's assigned `calendarDate`, checked against the requested date. Current-day Garmin summaries are deferred until tomorrow. Missing values and negative sentinels are excluded; an all-zero daily placeholder is not a measured sedentary day. Zero activity or stress is retained when the day otherwise contains usable measurements. Garmin daily minima/maxima become means of observed daily extrema, not whole-month extrema.
- Garmin nightly HRV, highest5-minute nightly HRV and rolling7-day HRV stay distinct. Morning readiness/recovery uses only an explicit `AFTER_WAKEUP_RESET` snapshot. Body Battery charged/drained are accumulated points, separate from highest/lowest levels. HRV status is an observed label count, never a numeric average or diagnosis.
- The Oura API uses the longest completed `long_sleep` record for each day; naps and rest periods are excluded. Sleep score comes from `daily_sleep.score`, never from contributor scores. Oura's API and app/CSV HR values can differ because of their sampling methods; source types remain recorded.
- Each observed day has equal weight. Multiple readings on a day are averaged first, then the daily averages are averaged across the month. Blood pressure remains paired within the same measurement group. Daily activity quantities are mean observed-day quantities, not monthly totals. Workout/session rows describe the mean recorded workout/session within a day, followed by a mean across observed days; they are not totals or estimates for days without recordings.
- Withings can split one night's sleep into multiple nonoverlapping sessions. The importer combines those sessions before calculating monthly means: durations and event counts are summed per day; HR, respiratory rate and AHI use sleep-duration weights; nightly minima/maxima retain their daily extrema; efficiency is combined sleep time divided by combined time in bed. Reported scores and latencies remain session means. HRV at Sleep Start/End remains a mean of reported session-start/session-end windows, not a reconstructed all-night HRV measure. Original session IDs, counts, intervals and aggregation rules remain traceable in the local records. Ambiguous overlapping sessions are rejected.
- Missing days are excluded, never converted to zero. Each metric records its actual observation count, number of days, first/last date, and elapsed/calendar days. Current calendar months are marked as month to date, including the last day of that month.
- Body fat, muscle and bone percentages use the same measurement group's weight and component mass; lean mass is not relabeled as muscle. Bone mass from API type 88 is converted from kilograms to percentage using that same reading's weight. Visceral fat from type 170 retains the Withings **0–20 index**, which cannot be converted to a percentage. BMI uses the recorded **180cm** height. Use `--height-cm` to change this explicit assumption if needed; derivation details remain in the local records.
- Average HRV and nightly minima are separate from maximum HRV. Oura and Withings sleep estimates, vascular-age measures and provider-specific VO2max remain separate. API nerve conductance/response scores do not replace the app's confirmed monthly nerve health score.
- Withings HRV during the first and last 90 minutes of sleep is imported separately in milliseconds, as documented in [Withings Sleep HRV](https://support.withings.com/hc/en-us/articles/35762631441681-Sleep-U-S-Nighttime-Heart-Rate-Variability-HRV).
- Supported device classifications appear in separate provider-specific rows as **observed label counts per month**. They are not averaged codes, health scores, clinical diagnoses or estimates for unrecorded days. The original dated/manual ECG, heart sounds, confirmed app nerve score, nighttime dipping and cardiovascular-age difference remain distinct. Unrecognized classification values are shown explicitly as device codes with unverified meanings, which may include unavailable-result codes; their original values also remain archived. Under-specified ECG interval and ESC fields remain raw and are not averaged. Units and labels are not guessed.

## Report layout

The results overview groups the main vitals into smaller tables: body composition, body measurements, heart and circulation, sleep and breathing, recovery and stress, activity and fitness, and nerve health and temperature. Bone percentage and the Withings visceral fat index remain in the main body-composition table. Self-reported body sizes occupy their own table as dated snapshots, with measurement methods and source dates in the notes; they are retained during device syncs. Expand **Detailed device measurements** for additional source-specific readings, body segments, score contributors, sensor samples, model estimates and historical snapshots; expand **Sources & calculation notes** for provenance and averaging rules. Every measurement remains available. Each table shows only months containing a measurement in that table; empty reference columns are also omitted from the smaller tables. When present, Trend always follows Metric before the month columns.

`tools/health_sync/report_layout.py` controls this presentation independently of the import registry and clinical scoring. Newly imported measurements default to the detailed tables until explicitly selected for the overview. Future on-demand syncs regenerate the same layout in both Markdown and HTML.

Vitals use sourced ranges and targets from `tools/health_sync/vitals_targets.py` and its sleep, activity and recovery modules, documented in [Reference-Guide.md](../results/Reference-Guide.md). 🟢 indicates movement toward a target or a favorable recovery/device trend; 🟡 indicates the reverse. Provider scores can improve within a color band. ⚪ means an unchanged target position or a context-dependent change; single, pending and incomparable observations keep `-`. Sleep-stage percentages and combined activity volume require matching provider observation days. Source values and units remain unchanged.

Oura SpO2 aggregates equal to exactly zero are excluded as unusable readings; all positive values are retained. The source archive remains unchanged. This is a narrow data-quality rule: Oura documents missing oxygen readings but does not explicitly define a zero sentinel in the API schema. Each monthly result's coverage reflects only the retained observed days.

## Files and verification

### Imaging records

`tools/imaging_report.py` is the editable imaging catalog. Each examination has an exact date, modality, record-availability label, report-derived summary, date provenance and named source files. The facial CT examination and report dates remain separate. Studies without a written report are explicitly marked as images only; DICOM metadata supplies acquisition details, not clinical findings.

Both results reports use the same catalog: a newest-first index links to findings grouped into facial CT, abdominal-wall follow-up and dental imaging. The preoperative hernia defect and postoperative linea alba width are different measurements and are not plotted as a trend. The main protocol links directly to this index.

To add or correct an examination, update the catalog and its group membership, preserve the original medical files, then run `python -B tools/generate_colored_report.py` from the repository root. Generation validates that every catalog source is an existing file inside the repository before writing each report. View `results.html#imaging` locally for the card layout; `results.md#structural--diagnostic-imaging` provides the repository-readable version. Links to PDFs/JPEGs open the source files; ZIPs and DICOMDIR are labeled for download/import, with viewing instructions in each record. On-demand vitals syncs regenerate this same imaging section without changing its dates or findings.

### Generated and private files

- `tools/health_sync/` and `tools/sync_vitals.py`: import, authentication and averaging code.
- `tools/.secrets/credentials.dat`: Windows-user-encrypted OAuth configuration and Garmin session tokens; ignored by Git.
- `.health-sync/garmin-venv/`: optional Garmin dependencies, installed by `tools/Install-Garmin.ps1`; ignored by Git.
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
