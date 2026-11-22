# Repository tools

Run the commands below from the repository root.

- `tools/Sync-Vitals.ps1`: import and sync monthly vitals.
- `tools/generate_colored_report.py`: regenerate both results reports.
- `tools/imaging_report.py`: curated imaging records, verified source links and shared report layout.
- `tools/generate_pillbox_guide.py`: generate the physical pillbox guide.
- `tools/validate_pillbox_guide.py`: check pillbox source against the active protocol without generating files.
- `tools/tests/`: synthetic importer, sync and pillbox validation tests.

## Pillbox source validation

Check the manually maintained `PAGES` in `tools/generate_pillbox_guide.py` against the active **Supplements and drugs** section in `README.md` before generating the guide:

```powershell
python -B tools/validate_pillbox_guide.py
python -B -m unittest tools.tests.test_pillbox_validation -v
```

The checker reads the README and loads the generator's data without calling `build_document()`. It uses the generator's existing `python-docx` dependency. The validator itself does not generate the DOCX, write health reports, fetch data or change either input. Exit status is `0` for parity, `1` for a mismatch or unsupported notation, and `2` when inputs cannot be loaded. Diagnostics identify the slot and, for product mismatches, the README line. To check another trusted checkout, use `--root PATH`; that checkout's generator is Python code and is executed with a non-main module name. This is not a sandbox: any top-level code in that generator or its imports still executes. Use trusted source only.

Checks cover the fixed eight pages in row-major order, nine physical cells per page, all 72 compartments, explicit empty slots, and both parts of shared `.1`/`.2` cells (prescription or supplement). Ranges expand to individual slots: `M.7-8 2x` means one pill in each cell, while `B.8-9 4x` means two in each. A single-code multiplier such as `M.17 3x` is checked against `same_slot_count`. Zero-series drinks, nested powder ingredients, Notes, TODOs and Removed entries do not occupy physical cells.

The separately rendered `qty` field is checked too. An empty cell accepts only blank text or `Available compartment`. An occupied cell accepts blank text or an integer count of pills, capsules, tablets or softgels, optionally followed by `/day` or `/week`. That count must match the number in the physical compartment. An explicitly written pill form in the active README row must agree; a bare multiplier such as `3x` does not establish whether the product is a capsule, tablet or softgel, so form identity still needs review when unstated. A displayed `/day` or `/week` additionally requires a matching leading count/form/frequency instruction after the product link, such as `— 1capsule daily with Breakfast`. Counts without a period do not imply daily use. Free-text quantity instructions fail; general frequency and conditional prose remain outside this check.

For product identity and doses, the checker supports the existing leading product-link notation, compact or spaced quantities, `+` combinations, and quantity-bearing parentheses. Product names retain case, strain numbers, brands and formulation wording. It compares headline doses and their constituent labels, retaining their units; it does not convert grams to milligrams or invent name aliases. Bare `mln`/`bln` counts remain distinct from `CFU` and `heat-inactivated cells`. A parenthetical dose such as `(Butyric acid 400mg)` must appear in the guide's dose/note text. Combination doses retain ingredient order; an optional dose-field label must uniquely match an ingredient name or its final words (for example `K1` in `Vitamin K1`). Where a blend headline has no dose, the guide's displayed dose must contain a supported quantity/unit and occur as an exact phrase in that entry's indented formulation details, not as a concentration or range endpoint. Unsupported slot-bearing Markdown variants, malformed product links, and fences/comments in the active section fail instead of hiding an entry or conflicting duplicate. Unsupported notation requires a deliberate parser/test update.

**Scope:** this checks source parity, not medical correctness or the rendered DOCX. It does not validate all formulation-note quantities or their per-pill/per-serving basis, cumulative intake, evidence badges, icons, product URLs, frequency/conditional wording, callouts, or visual layout. A matching source pair can still describe an incorrect regimen. Continue the regeneration and eight-page visual review in [AGENTS.md](../AGENTS.md) after an authorized physical-pill change; the validator does not replace that review.

## Dated laboratory results

`tools/generate_colored_report.py` keeps the original laboratory history in `data` and adds later specimen results through `lab_followups`. Use the specimen collection month, preserve exact dates and source-specific units/ranges in a linked source record, and add new assays to their own rows when the method or specimen differs. The [September 16, 2026 source record](../results/Labs-2026-09-16/Sources.md) covers the ALAB panel and the separate Diagnostyka stool PCR panel.

Explicitly awaited results use `pending`, which blocks an older trend; `-` means no supplied result. `lab_pending_tests` lists outstanding assays without inventing units or ranges. When later PDFs arrive, replace the corresponding pending entries and update the pending-test registry and source record. Regenerate both outputs from the repository root with `python -B tools/generate_colored_report.py`; this does not fetch new device data.

Numeric parsing preserves signs, scientific notation and comparison operators. A decimal comma is supported when unambiguous (`1,5` or `0,125`); `1,234` is left unscored because its separator could mean decimal or thousands. Keep units in the unit column. Mixed text and multi-value strings are displayed literally without extracting unrelated digits; blood pressure requires exactly two scalar components separated by `/`.

The laboratory rows in `limit_endpoint_color_markers` retain their established upper-limit display colors. This presentation policy does not change interval scoring or let reported limits enter exact-value trends or percentage changes; other bounded results retain interval-based classification.

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

Supported readings include daily activity, heart rate, stress, Body Battery, sleep, HRV and morning readiness/recovery; Sleep Coach recommendation/shortfall, overnight heart rate/stress, wake-up Body Battery, temperature deviation and readiness contributors; dated running/cycling VO2max, fitness age, training load/status, workout training effects and HR-zone time. Every row retains a Garmin source label. Metrics appear only when Garmin returns usable data; owning a particular watch does not establish availability. inReach messages and location are outside this importer.

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

If a data request returns HTTP 401 or Withings JSON `status: 401`, the client refreshes access once and replays the same read. A repeated authentication failure stops the sync; permission errors and other API statuses do not trigger this refresh. The existing encrypted-vault token rotation remains in use.

## Preview, sync one service, or revisit a date range

```powershell
.\tools\Sync-Vitals.ps1 sync --dry-run
.\tools\Sync-Vitals.ps1 sync --provider oura
.\tools\Sync-Vitals.ps1 sync --provider withings
.\tools\Sync-Vitals.ps1 sync --start 2026-07-01 --end 2026-09-05
```

The default `--provider all` requests every configured account; `--provider both` retains the original Oura+Withings selection. A configured account requiring renewed login stops the sync rather than being silently skipped. Authentication, transport, invalid-response and pagination failures stop the update before publishing new reports. `--provider` explicitly allows updating one service while retaining the others' cache and coverage metadata. Date bounds are inclusive. A complete API fetch replaces that provider's cache within the requested range, so corrected or removed readings can be reflected; outside that range, history is retained.

Optional endpoints returning HTTP 403/404 are recorded as unavailable in the source's `_sync.endpoint_status` rather than treated as measurements or zeros. Remaining accessible data can still be imported. Each complete collection replaces its own cached observations in the requested range; unavailable collections retain theirs. The monthly source file records sync coverage; check it when a device, account permission or service restriction leaves a gap. A successful endpoint with no observations is distinct from an unavailable endpoint.

Withings sampled sleep HRV depends on both sleep samples and completed sleep summaries. Cached RMSSD/SDNN1 observations are not cleared by a successful sample fetch when summary coverage is unavailable or unknown; both collections must be complete to treat missing derived observations as removed.

For Garmin, only optional-endpoint404 responses are treated as unavailable. Authentication/403, rate limits and other failures stop publication. If any date is unavailable, that collection's existing history is retained and successfully returned dates amend it. A successful empty response is recorded separately. Requests are bounded and the Garmin fetch range is limited to 366 days per run.

## Import an export without an API connection

Oura on the web: open Trends, select the date range, choose Download Data, select all metrics, and download the CSV.

```powershell
.\tools\Sync-Vitals.ps1 import --oura-csv "C:\Users\hyperbook\Downloads\oura_2026-07-06_2026-09-06_trends.csv"
```

The import reads the exact bytes it archives. Reimporting the same file does not duplicate observations. Partial files amend the days and metrics they contain without removing other cached observations. An incoming Oura day/metric replaces the previous daily value even if one came from CSV and the other from the API.

Oura CSV imports include the optional `Light Sleep Duration` column, converting seconds to hours in the existing **Light Sleep (Oura)** row. A blank or omitted column leaves that observation absent; it is not inferred from the other sleep stages.

Each supplied provider must contribute a usable observation in the requested date range: a numeric reading, a dated device classification or a Withings ECG recording. Classification-only and ECG-only files preserve cached numeric readings. Oura/Garmin observations for the unfinished current day do not satisfy this check.

For Withings, the supported fallback is saved **official API measurement JSON**, with every page combined. Arbitrary app export CSVs are not guessed: Withings export columns and units can vary by export/account.

```powershell
.\tools\Sync-Vitals.ps1 import --withings-json "C:\path\withings-measurements.json"
```

Accepted Withings JSON: `{"measuregrps": [...]}` from this sync client, or `{"measure": [page1, page2, ...]}` containing complete successful API responses. A standalone successful response is also accepted when it is the final/only page. Responses with unfinished pagination, API errors, ambiguous user records or credential fields are rejected or excluded as appropriate. Real measurement IDs identify revised readings; repeat imports do not increase their weight.

Garmin can also reimport a saved measurement envelope from this tool with `import --garmin-json "C:\path\garmin-readings.json"`. Its supported collections (`daily_summary`, `sleep`, `hrv`, `training_readiness`, `max_metrics`, `fitness_age`, `training_status`, `activities`, `activity_hr_zones`) contain lists of `{"day":"YYYY-MM-DD","data":<response>}`. This is not an importer for arbitrary Garmin CSV, FIT or full-account exports. Credential-bearing files are rejected; a partial file amends only supplied observations.

Garmin workout HR-zone durations are already combined into daily sums. A replacement day/zone must include every previously known contributing activity; a subset or an untraceable cached total stops the import before reports, archives or cache are changed. Reimport all activities for that day or use a full API sync. Complete files may correct totals downward; omitted days and zone metrics remain unchanged.

## What gets averaged

| Source | Automatically imported |
| :--- | :--- |
| Oura | Sleep, readiness and activity values/contributors; sleep timing, midpoint variability, short-night frequency and recorded short-sleep totals; SpO2 and breathing-disturbance index; cardiovascular age/PWV and VO2max; stress/recovery and resilience; source-specific heart rate; workout/session quantities |
| Withings | Body composition; blood pressure/pulse; SpO2, PWV, age/fitness estimates; nerve/temperature/urinary measurements; sleep/activity summaries; sleep timing/variability and short-night/AHI frequencies; available sleep RMSSD/SDNN1 samples; dated ECG results and waveform graphs |
| Garmin | Daily activity, heart rate, stress and Body Battery; sleep/coaching and overnight recovery; HRV, readiness/recovery and contributors; temperature deviation; dated fitness/load estimates; recorded workout training effects and HR-zone time |

The precise numeric registries are `OURA_METRICS`, `WITHINGS_METRICS` and `GARMIN_METRICS` in their respective modules under `tools/health_sync/`. New report rows appear only when observations are returned. Provider-specific names distinguish related measurements with different definitions; adding an API field does not invent a clinical reference range or assign a health score.

Oura requests `sleep`, `daily_sleep`, `daily_readiness`, `daily_activity`, `daily_spo2`, `daily_cardiovascular_age`, `vO2_max`, `daily_stress`, `daily_resilience`, `heartrate`, `workout` and `session`. Withings requests measurement groups, sleep summaries/details, activity summaries, heart/stethoscope metadata and available ECG signals. Sleep-detail requests cover at most24h and include the preceding evening for the first requested wake date. OAuth scopes permit access; device support, membership, product region, recorded history and account permissions determine which observations actually exist.

- Calendar dates use **Europe/Warsaw** for Withings timestamps. Oura's recorded sleep `day` is authoritative. Current-day Oura data are deferred until the next day; Withings readings already recorded today can contribute.
- Garmin uses the response's assigned `calendarDate`, checked against the requested date. Current-day Garmin summaries are deferred until tomorrow. Missing values and negative sentinels are excluded; an all-zero daily placeholder is not a measured sedentary day. Zero activity or stress is retained when the day otherwise contains usable measurements. Garmin daily minima/maxima become means of observed daily extrema, not whole-month extrema.
- Garmin nightly HRV, highest5-minute nightly HRV and rolling7-day HRV stay distinct. Morning readiness/recovery uses only an explicit `AFTER_WAKEUP_RESET` snapshot. Body Battery charged/drained are accumulated points, separate from highest/lowest levels. HRV status is an observed label count, never a numeric average or diagnosis.
- The Oura API uses the longest completed `long_sleep` record for each primary-night row. Confirmed `sleep`/`late_nap` periods have separate recorded monthly counts and duration totals; they never enter primary-night sleep averages. Zero short periods require a complete sleep collection and an observed primary night. Sleep score comes from `daily_sleep.score`, never from contributor scores. Oura's API and app/CSV HR values can differ because of their sampling methods; source types remain recorded.
- Each observed day has equal weight. Multiple readings on a day are averaged first, then the daily averages are averaged across the month. Blood pressure remains paired within the same measurement group. Daily activity quantities are mean observed-day quantities, not monthly totals. Workout/session rows describe the mean recorded workout/session within a day, followed by a mean across observed days; they are not totals or estimates for days without recordings.
- Withings can split one night's sleep into multiple nonoverlapping sessions. The importer combines those sessions before calculating monthly means: durations and event counts are summed per day; HR, respiratory rate and AHI use sleep-duration weights; nightly minima/maxima retain their daily extrema; efficiency is combined sleep time divided by combined time in bed. Reported scores and latencies remain session means. HRV at Sleep Start/End remains a mean of reported session-start/session-end windows, not a reconstructed all-night HRV measure. Original session IDs, counts, intervals and aggregation rules remain traceable in the local records. Ambiguous overlapping sessions are rejected.
- Missing days are excluded, never converted to zero. Each metric records its actual observation count, number of days, first/last date, and elapsed/calendar days. Current calendar months are marked as month to date, including the last day of that month.
- Bedtime, wake-up and sleep midpoint are local clock times with circular monthly means, so23:50 and00:10 average to00:00. Midpoint variability is circular population SD in minutes and requires at least two nights. Oura timestamps retain source-local time; Withings uses Europe/Warsaw. Withings schedule rows require an unambiguous night (split sessions separated by no more than2h, overall span no more than16h). Frequency cells show the percentage and affected/observed-night count: primary sleep<7h, or valid Withings AHI≥5. These are observed-night summaries, not population prevalence or diagnoses.
- Garmin Sleep Coach shortfall is the mean positive difference between the same night's recommendation and actual sleep; it is not cumulative sleep debt. Recommendation, overnight HR/stress, wake-up Body Battery and signed skin-temperature deviation stay separate from existing daily metrics. Undated or carried-forward fitness/VO2/load snapshots are not new daily observations. HR-zone durations sum recorded workouts within each day; workout effects remain per-workout means within observed days. Training load and workout effects depend on the training plan and recovery.
- Withings sampled RMSSD and SDNN1 are daily means of available short-window samples during confirmed asleep states, followed by monthly means. SDNN1 describes one-minute windows; neither row reconstructs whole-night HRV from beat intervals. Sample timestamps/coverage remain in the private cache. A partial file cannot replace an existing daily mean with fewer known samples. Recorded ECGs show heart rate, the device's AF result and a link to the full SVG trace. Graphs retain every supplied sample without filtering, convert the API's µV to mV and use a calibrated ECG grid. The original JSON stays in the private archive.

- Body fat, muscle and bone percentages use weight from the same measurement group. Bone mass comes from API type 88. Visceral fat (type 170) uses the Withings **0–20 index**.
- Fat-free mass index (FFMI) uses whole-body fat-free mass (type 5) and the optional `height_cm` setting in the ignored `.health-sync/profile.json`. Monthly means in kg/m² use the existing result colors with [reference 18–<26 and goal 22–<26](../results/Reference-Guide.md#ffmi-reference-and-goal). Trends compare movement toward the goal; changes below 0.1kg/m², movement within the goal and comparisons involving a context-dependent value at or above 26 stay neutral. The calculator's normalized FFMI equals the imported unadjusted FFMI at 180cm; review the comparison if height changes, then run `.\tools\Sync-Vitals.ps1 rebuild-body-index`.
- Average HRV and nightly minima are separate from maximum HRV. Oura and Withings sleep estimates, vascular-age measures and provider-specific VO2max remain separate. API nerve conductance/response scores do not replace the app's confirmed monthly nerve health score.
- Withings HRV during the first and last 90 minutes of sleep is imported separately in milliseconds, as documented in [Withings Sleep HRV](https://support.withings.com/hc/en-us/articles/35762631441681-Sleep-U-S-Nighttime-Heart-Rate-Variability-HRV).
- Withings breathing disturbance intensity and breathing quality assessment are separate numeric 0–100 indices. Invalid values, including −1, are excluded; valid sessions are averaged within each day, then across observed days. Legacy categorical counts must be rebuilt from saved API records rather than converted into monthly averages.
- Supported device classifications appear in separate provider-specific rows as **observed label counts per month**. They are not averaged codes, health scores, clinical diagnoses or estimates for unrecorded days. App ECG rhythm, readable heart sounds, the confirmed nerve score and nighttime dipping remain distinct where imports lack the same information. Unrecognized classification values are shown explicitly as device codes with unverified meanings, which may include unavailable-result codes; their original values also remain archived. Under-specified ECG interval and ESC fields remain raw and are not averaged. Units and labels are not guessed.

## Report layout

Displayed numeric results and references omit an all-zero fractional part: `114.0/76.3` becomes `114/76.3`, and `22.0` becomes `22`. Nonzero fractions, stored source precision and calculations remain unchanged. The same writing rule applies throughout the protocol; product/version identifiers, dates, slot codes and links retain their exact spelling.

Recorded ECGs link to full waveform graphs in `results/ECG/`. Each graph displays its recording time, heart rate, device AF classification, duration and sampling frequency. A negative AF result is the device's classification, not a broader rhythm diagnosis. [Withings signal and classification definitions](https://developer.withings.com/openapi.yaml).

To rebuild ECG graphs from saved recordings without fetching or changing monthly averages:

```powershell
.\tools\Sync-Vitals.ps1 render-ecg
```

ECG plotting requires `tools/requirements-ecg.txt` in the Python environment used by `Sync-Vitals.ps1`; the Garmin installer includes it.

Vitals tables identify Oura, Withings and Garmin in a compact **Source** column after Reference (or Unit when Reference is empty). Displayed metric names omit provider suffixes; canonical metric identities, separate provider rows and source notes are preserved. Tables with no identified provider omit Source.

The results overview groups the main vitals into smaller tables: body composition, body measurements, heart and circulation, sleep and breathing, recovery and stress, activity and fitness, and nerve health and temperature. Bone percentage and the Withings visceral fat index remain in the main body-composition table. Self-reported body sizes occupy their own table as dated snapshots, with measurement methods and source dates in the notes; they are retained during device syncs. Expand **Detailed device measurements** for additional source-specific readings, body segments, score contributors, sensor samples and model estimates; expand **Sources & calculation notes** for provenance and averaging rules. App-only observations sit with their relevant measurements. Each table shows only months containing a measurement in that table; empty reference columns are also omitted from the smaller tables. When present, Trend always follows Metric before the month columns.

Imported series supersede the old resting/sleeping heart-rate, ECG heart-rate and cardiovascular-age-difference snapshots in the report when every snapshot month has the replacement data. Both Oura mean and minimum sleeping heart rate are required before hiding the ambiguous old heart-rate summaries. These are presentation replacements, not numerically equivalent readings; original snapshots remain in the generator and source history. A missing import or undisplayed replacement keeps the snapshot visible.

`tools/health_sync/report_layout.py` controls this presentation independently of the import registry and clinical scoring. Newly imported measurements default to the detailed tables until explicitly selected for the overview. Future on-demand syncs regenerate the same layout in both Markdown and HTML.

HTML result text and its color legend use `tools/health_sync/report_colors.py` to maintain at least 4.5:1 contrast on the explicit white page and pale alternating rows, following [WCAG 2.2 SC 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html). Light foregrounds are darkened without changing values, health scores, status emojis, trends or Markdown. If report backgrounds change, update the shared backgrounds and verify the rendered text contrast again.

Vitals use sourced ranges and targets from `tools/health_sync/vitals_targets.py` and its sleep, activity and recovery modules, documented in [Reference-Guide.md](../results/Reference-Guide.md). 🟢 indicates movement toward a target or a favorable recovery/device trend; 🟡 indicates the reverse. Supported directional metrics can improve within a normal band. Selected body-composition, BP, PWV, HR and deep-sleep metrics use documented small-change display floors; these are not clinical significance thresholds. ⚪ means a small change, unchanged target position or context-dependent change; single, pending and incomparable observations keep `-`. Sleep-stage percentages and combined activity volume require matching provider observation days. Source values and units remain unchanged.

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
- `results.md` and `results.html`: regenerated outputs. The vitals introduction points to the shared notes for monthly device measurements and classification counts. Dated snapshots keep their own source notes.

The private cache and exports are ignored by Git. The monthly summary and results are ordinary repository artifacts; review their diff before choosing to commit. Nothing is committed or pushed by the sync. The command uses an OS process lock, bounded network requests, pagination checks, safe read retries and staged report generation. File replacements roll back on a handled error; after a power loss, rerun the sync to regenerate the outputs consistently.

The PowerShell wrapper uses the bundled Codex Python runtime when available, otherwise `python` on PATH. Python 3.10+ is required; a fallback Windows Python may also need the `tzdata` package for Europe/Warsaw. API credential storage requires Windows. Tests use synthetic API responses and no real credentials:

```powershell
python -B -m unittest discover -s tools/tests -t . -v
git diff --check
```

Official references: [Oura API](https://cloud.ouraring.com/v2/docs), [Oura authentication](https://cloud.ouraring.com/docs/authentication), [Withings API schema](https://developer.withings.com/openapi.yaml), [Withings OAuth](https://developer.withings.com/developer-guide/v3/integration-guide/public-health-data-api/get-access/oauth-web-flow/), [Withings exports](https://support.withings.com/hc/en-us/articles/360001391287-Privacy-How-can-I-export-my-data).
