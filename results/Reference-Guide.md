# Results: references, targets and status dots

Added guidance checked on **2026-09-07**. This record covers the new annotations; the existing laboratory references and protocol targets remain in the report.

A **reference** describes the laboratory or provider's comparison population or classification. A **target** is a stated desired band. Where no separate target is established, the report says so rather than inventing one. Provider bands applied to a monthly mean describe that mean, not the number of abnormal nights or a diagnosis. September is month to date, so its coverage differs from completed months.

## Wearable and body-composition guidance

| Measurement | Reference and target used | Source and interpretation |
| :--- | :--- | :--- |
| Oura Sleep, Readiness, Activity and their contributor scores | 85–100 target/optimal; 70–<85 good; 60–<70 fair; <60 pay attention | [Oura score bands](https://support.ouraring.com/hc/en-us/articles/360025445574-Sleep-Score). Decimal monthly averages use continuous boundaries between the published integer bands. These bands are not applied to other providers, resilience contributors or score-change fields. |
| Oura sleep efficiency | ≥85% comparison / target | [Oura sleep contributors](https://support.ouraring.com/hc/en-us/articles/360057792293-Sleep-Contributors). A higher value within this band is not automatically healthier. |
| Oura sleep latency | Target 15–20min | [Oura sleep contributors](https://support.ouraring.com/hc/en-us/articles/360057792293-Sleep-Contributors). Values outside the ideal band remain neutral because this source supplies no complete severity scale; very short latency is not automatically better. |
| Oura average sleeping SpO2 | Reference / target 95–100% | [Oura blood oxygen guidance](https://support.ouraring.com/hc/en-us/articles/7328398760851-Blood-Oxygen-Sensing-SpO2). Below-range readings get a comparison flag, not a clinical severity grade. Sensor fit, movement, altitude and the observation window affect interpretation. |
| Withings sleep score | >75–100 high / target band; 50–<75 medium; <50 low | [Withings score explanation](https://www.withings.com/fr/fr/blog/sommeil/comment-withings-calcule-votre-score-de-sommeil). These provider bands are distinct from Oura's. Published versions differ/overlap at 75, so exactly 75 stays neutral. Applying the integer bands to decimal means uses 50 as the lower boundary of the middle band. |
| Withings visceral fat index | Normal / target 0–5 inclusive; >5 high; device scale 0–20 | [Body Scan visceral fat index](https://support.withings.com/hc/en-us/articles/11003948038545-Body-Scan-Learn-more-about-Visceral-Fat-Index). This is an index, not a percentage; a decrease already within normal is shown as a numerical change without extra health credit. |
| Confirmed Withings nerve health score | >50 normal; <50 low; target normal | [Body Scan NHS](https://support.withings.com/hc/en-us/articles/11888924491025-Body-Scan-Nerve-Health-Score-NHS). Exactly 50 stays neutral because the source's boundary wording is unspecified. Pending results remain neutral and block comparisons using older results. The cutoff is not applied to raw API foot-score averages. |
| Bone percentage | Male manufacturer comparison 3–5%; no clinical target | [Withings body-composition comparison ranges](https://support.withings.com/hc/en-us/articles/218500778-Body-What-are-the-normal-ranges-for-body-composition). This general Body+ guidance is shown as context for the Withings estimate; it is not a Body Scan validation or a bone-density target, so the dot stays neutral. |
| Body water percentage | Male manufacturer comparison 50–65%; no clinical target | [Withings body-composition comparison ranges](https://support.withings.com/hc/en-us/articles/218500778-Body-What-are-the-normal-ranges-for-body-composition). This comparison also stays neutral rather than treating its midpoint as an optimum. |
| HRV and context-dependent heart-rate / temperature measurements | Personal or method-specific baseline; no universal target applied | [Oura HRV guidance](https://support.ouraring.com/hc/en-us/articles/360025441974-Heart-Rate-Variability). Baselines are not estimated from the small set of displayed monthly averages. |
| Body circumferences and lengths | Individual anatomy; no universal health target applied | The existing waist observation is at the narrowest point. [NICE's central adiposity method](https://www.nice.org.uk/guidance/ng246/chapter/Identifying-and-assessing-overweight-obesity-and-central-adiposity) measures midway between the bottom ribs and top of the hips. Applying that method's risk thresholds to a different landmark would imply a comparison that has not been measured. |

Other telemetry, segment masses, calorie estimates, counts and device codes retain their definitions. A neutral dot means **not classified**, not normal or abnormal. Categorical counts remain counts and are never treated as a scalar score.

## Gut microbiota: the laboratory's scale

The [July 7 GA-map source record](Gut-Microbiota-2026-07-07/Sources.md) identifies the original report and transcription. The report supplies **reference classifications, not validated therapeutic abundance targets**.

- Dysbiosis index: reference **1–2**; the observed **3** is the lab's yellow, mild-dysbiosis band.
- Diversity: **as expected**, green; no numeric Shannon index or numeric target is reported.
- Group assessments: green for within the reference profile; orange for the lab's slightly altered classification. These group colors do not use the general report's severity score.
- Individual marker positions: the unnumbered dark-green center is encoded as **0**, the lab reference. Signed positions are ordered chart columns, not percentages, counts, fold changes or standard deviations.
- Dark green means the lab reference; light green means a small association with an increased dysbiosis index; orange means moderate and red means high association. Both greens use 🟢 in Markdown, with an explicit text label to distinguish them. HTML uses different green shades, with the source hues darkened for readability.
- Each marker's color comes from its own chart band, not the absolute size of its signed position. For example, marker 305 at −1 is light green while marker 201 at −1 is orange. Uncolored cells and unknown results remain neutral.

All 336 marker cells (48 markers × 7 positions) were checked against the PDF vector colors and rendered pixels. The observed results contain 34 dark-green, 9 light-green and 5 orange marker positions. Group assessment and individual marker band are separate findings.

For the existing stool microscopy rows, “single” or “few” against an “absent” laboratory reference receives an amber comparison flag; it does not imply a quantitative severity grade or a new target.

## Reading trends

- Existing health-score trend dots retain their established calculation.
- **↑ +value**, **↓ −value** and **→ 0** show the numerical change from the preceding available measurement in the row's unit. They do not label a change as healthier or less healthy. This also applies to the newly annotated provider scores.
- Calculations use displayed values and their precision. Percentage rows change in percentage points; score rows change in points. Missing dates are skipped, so the previous observation may be more than one month earlier.
- Only two comparable scalar observations can produce a numerical change. A single observation has no trend. Pending, inconclusive, bounded values such as `<5`, and categorical summaries cannot be turned into numeric deltas or skipped to display an older comparison.
- A table shows a Trend column only if at least one row supports one. It appears immediately after the metric. Empty month columns remain omitted.
