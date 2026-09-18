"""Sourced sleep comparisons in the exact provider registry names.

Rules describe comparisons, not diagnoses or proven longevity effects.  Ratio
rules keep stage hours in the report, but compare their percentage of a matched
same-provider sleep duration.  ``valid`` bounds apply to the raw measurement;
the evaluator must also reject ratios outside 0–100% or unmatched observations.
"""


TARGETS = {}


def _add(markers, **rule):
    for marker in markers:
        TARGETS[marker] = dict(rule)


# AASM/SRS: >=7 h for adults, with no universal harmful upper boundary.
# Oura/NSF use 7–9 h as a practical full-night range.  More than 9 h remains
# within the broad recommendation; distance to the typical range is not risk.
# https://www.aasm.org/resources/pdf/adultsleepdurationconsensus.pdf
# https://support.ouraring.com/hc/en-us/articles/360057792293-Sleep-Contributors
_add(
    ("Sleep Duration", "Sleep Duration (Withings)",
     "External Sleep Duration (Withings)", "Sleep Duration (Garmin)"),
    reference="≥7; target 7–9", target=(7, 9), normal=(7, None), valid=(0, 24),
)

# NSF consensus: efficiency >=85%; WASO <=20 min for adult sleep quality.
# https://www.thensf.org/what-is-sleep-quality/
# https://escholarship.org/uc/item/9xc5x5h2
_add(
    ("Sleep Efficiency", "Sleep Efficiency (Withings)"),
    reference="≥85", target=(85, 100), valid=(0, 100),
)
_add(
    ("Wake After Sleep Onset (Withings)",),
    reference="≤20", target=(0, 20), valid=(0, 1440),
)

# NSF accepts <=30 min; Oura's narrower 15–20 min is explicitly a practical
# target.  <5 min can reflect sleep debt, so latency is not lower-is-better.
# The Withings physiological latency uses the same practical comparison, not
# a claim that its proprietary algorithm has validated the Oura target.
_add(
    ("Sleep Latency", "Sleep Latency (Withings)"),
    reference="≤30; practical target 15–20", target=(15, 20),
    normal=(5, 30), valid=(0, 1440),
)

# Score direction is continuous even when both observations share a band.
# These are provider quality scores, not laboratory or clinical risk scales.
# https://www.withings.com/fr/fr/blog/sommeil/comment-withings-calcule-votre-score-de-sommeil
_add(
    ("Sleep Score (Withings)",),
    reference=">75; higher is better", valid=(0, 100), direction="up",
    bands=((75, "🟢", "Withings: high sleep score"),
           (50, "🟡", "Withings: medium sleep score"),
           (0, "🟠", "Withings: low sleep score")),
    neutral_at=(75,),  # Published provider descriptions overlap at exactly 75.
)
# https://support.garmin.com/en-IN/?faq=mBRMf4ks7XAQ03qtsbI8J6
_add(
    ("Sleep Score (Garmin)",),
    reference="≥80 good; target ≥90", valid=(0, 100), direction="up",
    bands=((90, "🔵", "Garmin: excellent sleep score"),
           (80, "🟢", "Garmin: good sleep score"),
           (60, "🟡", "Garmin: fair sleep score"),
           (0, "🟠", "Garmin: poor sleep score")),
)

# Oura's stated usual mean respiratory range is 12–20/min.  No reviewed source
# establishes 12–16 as universally better.  Nightly extrema need other context.
# https://support.ouraring.com/hc/en-us/articles/360025443174-Respiratory-Rate
_add(
    ("Respiratory Rate (Sleep)", "Respiratory Rate During Sleep (Withings)",
     "Wellness Respiratory Rate (Withings)", "Respiratory Rate (Sleep) (Garmin)"),
    reference="12–20", target=(12, 20), valid=(0.01, None),
)
# https://support.ouraring.com/hc/en-us/articles/7328398760851-Blood-Oxygen-Sensing-SpO2
_add(
    ("Average Sleeping SpO2 (Oura)", "Average Sleeping SpO2 (Garmin)",
     "SpO2 (Withings)"),
    reference="95–100", target=(95, 100), valid=(0.01, 100),
)

# Conventional AHI severity boundaries; lower event burden is favorable.
# https://pmc.ncbi.nlm.nih.gov/articles/PMC8314651/
_add(
    ("Sleep Apnea AHI",),
    reference="<5", valid=(0, None), direction="down",
    bands=((30, "🔴", "AHI: severe range"),
           (15, "🟠", "AHI: moderate range"),
           (5, "🟡", "AHI: mild range"),
           (0, "🔵", "AHI: below 5 events/h")),
)
# The separate FDA-cleared Sleep Rx index merges no/mild below15; its green
# comparison must not be presented as absence of apnea or relabeled as AHI.
# https://media.withings.com/kits/guides/2026/sleep-rx/AW_IFU_WSM02_Rx_US_B.pdf
_add(
    ("Sleep Rx Breathing Events Index (Withings)",),
    reference="<15 no/mild; lower is better", valid=(0, None), direction="down",
    bands=((30, "🔴", "Withings Sleep Rx: severe range"),
           (15, "🟡", "Withings Sleep Rx: moderate range"),
           (0, "🟢", "Withings Sleep Rx: no/mild range")),
)

# Typical architecture is a percentage of the same night's total sleep, never
# another provider's total.  Oura: REM20–25%, deep13–23%, light45–55%.
# NSF supports adult REM21–30% and N3 16–20% as good-quality comparisons, but
# does not establish every value outside these intervals as pathological.
# These broader Oura comparisons are labeled typical, not clinical limits.
# https://support.ouraring.com/hc/en-us/articles/4403155260307-Sleep-Graphs
for _provider, _sleep_marker in (
    ("Oura", "Sleep Duration"),
    ("Withings", "Sleep Duration (Withings)"),
    ("Garmin", "Sleep Duration (Garmin)"),
):
    for _stage, _low, _high in (("REM Sleep", 20, 25),
                                ("Deep Sleep", 13, 23),
                                ("Light Sleep", 45, 55)):
        _marker = (_stage if _provider == "Oura" and _stage != "Light Sleep"
                   else f"{_stage} ({_provider})")
        _add(
            (_marker,), reference=f"Typical {_low}–{_high}% of sleep",
            target=(_low, _high), valid=(0, 24),
            transform=("ratio", _sleep_marker, 100),
        )
        if _stage == "Deep Sleep":
            # Favor a rise in both actual deep time and its sleep share, even
            # within the typical band. Saturate at23%; that typical upper end
            # is not a harmful threshold or an unlimited more-is-better goal.
            # 5min /1 percentage point are display sensitivity settings only.
            TARGETS[_marker].update(
                trend_target=(23, None), trend_min_change=5 / 60,
                trend_min_evaluated_change=1, trend_agreement=True,
            )

# Less excessive awake time/movement reflects better continuity.  These source
# fields do not all mean WASO, so they receive a direction without a fabricated
# 20-minute cutoff.  Likewise, Withings wakeupcount lacks the >5-minute episode
# restriction used by NSF's <=1 awakening benchmark and excludes leaving bed.
# https://support.ouraring.com/hc/en-us/articles/360057792293-Sleep-Contributors
# https://ouraring.com/blog/nighttime-movement/
# https://developer.withings.com/api-reference/#operation/sleepv2-getsummary
_add(
    ("Awake Time During Sleep (Oura)", "Awake Time During Sleep (Garmin)"),
    reference="Less awake time; interpret with sleep duration",
    direction="down", valid=(0, 24),
)
_add(
    ("Awake Duration (Withings)", "Sleeping Movement Duration (Withings)"),
    reference="Less disruption; interpret with sleep duration",
    direction="down", valid=(0, 1440),
)
_add(
    ("Restless Periods During Sleep (Oura)", "Wakeup Count (Withings)",
     "Out of Bed Count (Withings)"),
    reference="Fewer disruptions", direction="down", valid=(0, None),
)
_add(
    ("Sleeping Movement Score (Withings)",),
    reference="Less movement; device scale 0–255",
    direction="down", valid=(0, 255),
)

# AASM recognizes reduced primary snoring as a useful symptom outcome.  No
# validated minutes/episode cutoff grades cardiovascular risk or excludes OSA.
# https://pmc.ncbi.nlm.nih.gov/articles/PMC4481062/
_add(
    ("Snoring Duration (Withings)",),
    reference="Lower snoring burden", direction="down", valid=(0, 1440),
)
_add(
    ("Snoring Episode Count (Withings)",),
    reference="Fewer snoring episodes", direction="down", valid=(0, None),
)

# Explicitly retain context-dependent quantities instead of mistaking missing
# thresholds for normality or importing thresholds from different quantities.
_add(
    ("Time in Bed", "Time in Bed (Withings)"),
    reference="Allow enough time for 7–9h of sleep", direction="none", valid=(0, 24),
)
_add(
    ("Minimum Sleeping Respiratory Rate (Withings)",
     "Maximum Sleeping Respiratory Rate (Withings)",
     "Minimum Wellness Respiratory Rate (Withings)",
     "Maximum Wellness Respiratory Rate (Withings)"),
    reference="Nightly extrema; compare with personal baseline",
    direction="none", valid=(0.01, None),
)
_add(
    ("REM Episode Count (Withings)",),
    reference="Interpret with sleep duration and continuity",
    direction="none", valid=(0, None),
)
_add(
    ("Nap Duration (Garmin)",),
    reference="Interpret with nighttime sleep and nap timing",
    direction="none", valid=(0, 24),
)
_add(
    ("Wakeup Latency (Withings)",),
    reference="Time in bed after waking; contextual",
    direction="none", valid=(0, 1440),
)
_add(
    ("Primary Sleep Score Change (Oura)",
     "Primary Sleep Readiness Score Change (Oura)"),
    reference="Algorithm contribution; not a quality score",
    direction="none", valid=(None, None),
)
# The API defines a 0–100 index derived from detected SpO2 drops. Fewer drops
# support the direction, but do not establish clinical severity thresholds.
# https://api.ouraring.com/v2/static/json/openapi-1.37.json
# https://ouraring.com/blog/blood-oxygen-sensing-spo2/
_add(
    ("Breathing Disturbance Index (Oura)",),
    reference="Lower disturbance burden; device index 0–100",
    direction="down", valid=(0, 100), trend_min_change=0.1,
)
# These two API fields are numeric intensities, not category codes. Preserve
# their identities; the provider's wellness bands are separate from AHI.
# Sleep Analyzer manual v6, p29:
# https://support.withings.com/hc/article_attachments/13710141655825
_add(
    ("Breathing Disturbance Intensity (Withings)", "Breathing Quality Assessment (Withings)"),
    reference="<30 few; 30–<60 moderate; ≥60 high",
    direction="down", valid=(0, 100), trend_min_change=0.1,
    bands=((60, "🟠", "Withings: high breathing disturbances"),
           (30, "🟡", "Withings: moderate breathing disturbances"),
           (0, "🟢", "Withings: few breathing disturbances")),
)
_add(
    ("Breathing Sounds Duration (Withings)",),
    reference="Recorded breathing sounds; contextual",
    direction="none", valid=(0, 1440),
)
_add(
    ("Breathing Sounds Episode Count (Withings)",),
    reference="Recorded breathing sounds; contextual",
    direction="none", valid=(0, None),
)
_add(
    ("Chest Movement Rate (Withings)", "Minimum Chest Movement Rate (Withings)",
     "Maximum Chest Movement Rate (Withings)"),
    reference="Device chest-movement rate; contextual",
    direction="none", valid=(0, None),
)
