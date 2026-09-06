# Vitals sources reviewed 2026-09-06

The report preserves the original July 2026 baseline from the protocol's Git history (`0bb0ae1`, before the simplified August relabel). The newer columns combine dated device readings with explicitly identified Oura calendar averages. Missing values are not carried forward. The earlier rounded 80kg/15% update is superseded in these follow-up columns by the dated Withings readings below.

## Withings observations

Read from the user's logged-in Withings web app in Opera; muscle percentages and sleep apnea were also supplied in screenshots. These are device measurements/classifications, not independent clinical diagnoses.

| Date and local time | Observation |
| :--- | :--- |
| 2026-08-26 01:03 | BP 105/71mmHg; pulse 58bpm |
| 2026-08-26 01:04 | Heart sounds normal; screenshot identifies the apex area and displays 01:03 |
| 2026-08-28 15:53 | Weight 80.3kg; BMI 24.8; fat 15.2%; muscle 80.7%; lean mass 84.8%; water 58%; bone 4.1%; visceral fat index 2.4 |
| 2026-08-28 15:53 | PWV 6.5m/s; ECG normal sinus rhythm; scale pulse 87bpm |
| 2026-08 | Nerve health score 69, confirmed; September screen explicitly labels this as last month's result |
| 2026-09-02 09:17 | Sleep apnea AHI 0/hour; app label "Normal to mild" |
| 2026-09-05 22:36 | Weight 80.4kg; BMI 24.8; fat 13.6%; lean mass 86.4%; muscle 82.3%; water 58.1%; bone 4.2%; visceral fat index 2.3 |
| 2026-09-05 22:36 | PWV 6.1m/s; ECG normal sinus rhythm; scale pulse 82bpm |
| 2026-09-05 23:15 | BP 108/76mmHg; pulse 63bpm; ECG normal sinus rhythm; heart sounds inconclusive |
| 2026-09 | Nerve health score pending |

August uses the latest available observation in that calendar month for each reported metric. September uses the latest available dated reading. The September heart-sound result comes from the journal; the dashboard still displayed the older normal August recording. An inconclusive recording is preserved without a health score or directional trend.

Bone percentages and visceral fat indices were read directly from the August 28 and September 5 measurement-detail panels in the Withings web app, rechecked September 6. Bone values are retained as displayed, rather than inferred as the remainder of separately rounded fat/muscle percentages. Withings defines visceral fat as an [index from 0 to 20, not a percentage](https://support.withings.com/hc/en-us/articles/11003948038545-Body-Scan-Learn-more-about-Visceral-Fat-Index); no percentage conversion is made. No original July bone or visceral-fat reading is available in the restored baseline.

The body-composition screenshot's 81.4% muscle/14.4% fat tooltip is explicitly a **last-week average**, not a monthly average or the August 28 snapshot. Likewise, the weight chart's -2.9kg is a last-30-days trend. These summaries are not substituted for dated measurements. Scale/cuff pulse and the Oura spot pulse are not relabeled as resting or ECG heart rate.

## Oura export

[Oura-trends.csv](Oura-trends.csv) is an unchanged copy of the export downloaded from Oura on the web with all available metrics selected. Original download name: `oura_2026-07-06_2026-09-06_trends.csv`. Its 63 unique dated rows span July 6 to September 6; September 6 has no completed sleep measurements.

For each metric below, take the arithmetic mean of nonempty daily values within the calendar window. All 31 August dates and all 5 dates on September 1-5 have values for every listed metric. Duration fields are seconds; divide by 3,600 for hours or by 60 for minutes, then round the final mean. No missing values are converted to zero. The nightly sleep stages sum to total sleep, and time in bed agrees with bedtime timestamps for all 36 included dates.

| Report metric | CSV field | August (31 nights) | September 1-5 (5 nights) |
| :--- | :--- | ---: | ---: |
| Sleep Duration | Total Sleep Duration | 7.60h | 7.51h |
| REM Sleep | REM Sleep Duration | 1.72h | 1.64h |
| Deep Sleep | Deep Sleep Duration | 1.05h | 1.14h |
| Average Sleeping HR (Oura) | Average Resting Heart Rate | 66.2bpm | 65.9bpm |
| Mean Nightly Lowest HR (Oura) | Lowest Resting Heart Rate | 58.8bpm | 59.0bpm |
| Average HRV (Sleep) | Average HRV | 25.8ms | 24.6ms |
| Respiratory Rate (Sleep) | Respiratory Rate | 12.3/min | 12.4/min |
| Sleep Efficiency | Sleep Efficiency | 84.6% | 84.8% |
| Sleep Latency | Sleep Latency | 22.7min | 15.0min |
| Sleep Score | Sleep Score | 78.7 | 81.6 |
| Time in Bed | Total Bedtime (header has a trailing space) | 9.00h | 8.86h |

Average sleeping HR is the mean of daily nighttime mean HR values. Mean nightly lowest HR is the mean of daily minima, not the lowest HR across the whole month. The older July resting/sleeping HR entries retain their original definitions and are not merged with these new rows.

## Oura screenshot observations

- **September 3:** total sleep 7h58min; REM 2h14min; deep 53min; efficiency 90%; latency 12min; lowest HR 58bpm; displayed mean HR 65bpm; average HRV 23ms; maximum HRV 51ms. The maximum is for this night only and has no corresponding maximum-HRV column in the CSV.
- **September 5:** sleep score 81; total sleep 8h17min; time in bed 9h57min; REM 1h45min; deep 1h4min; efficiency 83%; latency 6min; displayed resting HR 62bpm. That 62bpm matches the CSV's nightly **lowest** HR; the CSV nightly mean is 68.4bpm. Raw durations include seconds omitted by the screenshots.
- **Overview captured September 6:** current-month VO2max 44 (High); cardiovascular age 6.5 years younger; cumulative stress Low; typical sleep score 81 with no stated averaging window. Nighttime BP shows Typical dipping over the last 30 days, with no percentage. The BP profile study ended August 12, 2026; that is not the date of the September 5 cuff reading.
- The 63bpm "10 minutes ago" spot HR is not a resting-HR estimate or monthly mean.

Screenshots labeled "Yesterday" are assigned September 5 using the explicit September 5 cuff date, neighboring weekday/date labels and September 2026 screens. July remains the user-requested original baseline rather than being recalculated from the partial July export.

## Supplied screenshot groups

Each group contains `1-Photo-1.jpg` through `5-Photo-5.jpg` in the existing attachment directory.

- [Group A: Oura sleep and spot HR](../../.codex-remote-attachments/01a07151-90e3-7681-a1ae-3a1b8d24f5a3/f5da983d-6c08-4c8d-871a-c75b4bdee77f/1-Photo-1.jpg)
- [Group B: Oura overview, Withings BP, nerve score and weight](../../.codex-remote-attachments/01a07151-90e3-7681-a1ae-3a1b8d24f5a3/67d62d84-3ab3-49e8-a393-a197630f4b6e/1-Photo-1.jpg)
- [Group C: Withings weight, AHI, heart sounds and body composition](../../.codex-remote-attachments/01a07151-90e3-7681-a1ae-3a1b8d24f5a3/41ea3246-576d-4817-91f0-5397ad8df108/1-Photo-1.jpg)
