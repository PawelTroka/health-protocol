"""Recovery comparisons for exact provider metrics, checked 2026-09-17.

This module contains display policy only. Provider score bands are not clinical
diagnoses, and a directional recovery signal is not a measured longevity effect.
Personal-baseline fields deliberately do not invent population cutoffs.
"""


# Official provider sources:
# Garmin stress:
# https://support.garmin.com/en-IE/?faq=WT9BmhjacO4ZpxbCc0EKn9
# Garmin Body Battery:
# https://support.garmin.com/en-SG/?faq=2qczgfbN00AIMJbX33dRq9
# Garmin training readiness:
# https://www8.garmin.com/manuals/webhelp/GUID-0221611A-992D-495E-8DED-1DD448F7A066/EN-AU/GUID-C21BE0C8-A08E-4DA1-B6C6-2E0E2DDDB372.html
# Decimal monthly means extend the published integer bands continuously from
# each published lower limit. These describe the mean, not abnormal-day counts.
_GARMIN_STRESS_BANDS = (
    (76, "🟠", "Garmin: high physiological stress"),
    (51, "🟡", "Garmin: medium physiological stress"),
    (26, "🟢", "Garmin: low physiological stress"),
    (0, "🔵", "Garmin: resting stress band"),
)
_GARMIN_BATTERY_BANDS = (
    (76, "🔵", "Garmin: very high energy reserve"),
    (51, "🟢", "Garmin: high energy reserve"),
    (26, "🟡", "Garmin: medium energy reserve"),
    (0, "🟠", "Garmin: low energy reserve"),
)
_GARMIN_READINESS_BANDS = (
    (95, "🔵", "Garmin: prime training readiness"),
    (75, "🔵", "Garmin: high training readiness"),
    (50, "🟢", "Garmin: moderate training readiness"),
    (25, "🟠", "Garmin: low training readiness"),
    (1, "🔴", "Garmin: poor training readiness"),
)


TARGETS = {
    "Average Stress (Garmin)": {
        "reference": "0–25 resting; 26–50 low",
        "target": (0, 25),
        "normal": (0, 50),
        "valid": (0, 100),
        "direction": "down",
        "bands": _GARMIN_STRESS_BANDS,
    },
    "Maximum Stress (Garmin)": {
        "reference": "0–25 resting; 76–100 high peak",
        "valid": (0, 100),
        # A brief stress maximum is not sustained stress burden.
        "direction": "none",
        "bands": _GARMIN_STRESS_BANDS,
    },
    "Body Battery Highest (Garmin)": {
        "reference": "51–100 high reserve; target 76–100",
        "target": (76, 100),
        "normal": (51, 100),
        "valid": (0, 100),
        "direction": "up",
        "bands": _GARMIN_BATTERY_BANDS,
    },
    "Body Battery Lowest (Garmin)": {
        "reference": "0–25 low; 51–100 high reserve",
        "valid": (0, 100),
        # Higher means more remaining reserve, not less exercise is healthier.
        "direction": "up",
        "bands": _GARMIN_BATTERY_BANDS,
    },
    "Body Battery Charged (Garmin)": {
        "reference": "Recovery and prior depletion",
        "direction": "none",
    },
    "Body Battery Drained (Garmin)": {
        "reference": "Activity and stress dependent",
        "direction": "none",
    },
    "Morning Training Readiness (Garmin)": {
        "reference": "50–100 ready; target 75–100",
        "target": (75, 100),
        "normal": (50, 100),
        "valid": (1, 100),
        "direction": "up",
        "bands": _GARMIN_READINESS_BANDS,
    },
    "Morning Recovery Time (Garmin)": {
        # Garmin defines 0–96h until readiness for a comparable hard workout.
        # A lower countdown indicates readiness, not a need to avoid exercise.
        # https://support.garmin.com/en-IE/?faq=8ImmxVkZMh4EYYq5Zp2bR8
        "reference": "0 before the next hard workout",
        "valid": (0, 96),
        "direction": "down",
    },
    "High Stress Time (Oura)": {
        # Sustained high physiological stress is a recovery burden; zero daily
        # stress is not a clinical goal, and wear duration affects this total.
        # https://support.ouraring.com/hc/en-us/articles/21205822135315-Daytime-Stress
        "reference": "Balance sustained stress with recovery",
        "valid": (0, 24),
        "direction": "down",
    },
    "High Recovery Time (Oura)": {
        # No published universal minute/hour cutoff. More regular daytime
        # restoration is favorable when monitoring coverage is comparable.
        # https://support.ouraring.com/hc/en-us/articles/4410641295763-Restorative-Time
        "reference": "Regular daytime recovery",
        "valid": (0, 24),
        "direction": "up",
    },
    "Resilience Stress Contributor Score (Oura)": {
        # Oura defines low/moderate/high stress-load categories separately
        # from recovery scores; its numeric thresholds/polarity are not given.
        # https://support.ouraring.com/hc/en-us/articles/25358829055251-Resilience
        "reference": "Balance stress load with recovery",
        "valid": (0, 100),
        "direction": "none",
    },
    "Nerve Health Score": {
        "reference": ">50",
        "target": (50, None),
        "normal": (50, None),
        "valid": (0, 100),
        "neutral_at": (50,),
        "bands": (
            (50, "🟢", "Withings confirmed NHS: normal"),
            (0, "🟠", "Withings confirmed NHS: low"),
        ),
    },
    "Nerve Response Score (Withings)": {
        # API type196 is distinct from NHS158/159/167 and ESC229.
        "reference": "Provider-specific nerve response",
        "direction": "none",
    },
    "Skin Temperature (Withings)": {
        "reference": "Personal peripheral-temperature baseline",
        "valid": (None, None),
        "direction": "none",
    },
}


# Official API identifies these as NHS, not electrochemical conductance:
# https://developer.withings.com/developer-guide/v3/integration-guide/surveys/data-api/all-available-health-data-body-scan/
# NHS0–100, >50 normal, <50 low; final monthly confirmation adds confidence
# checks and is not equivalent to an arithmetic mean of individual foot values.
# The comparison flag below does not diagnose neuropathy from an API mean.
# https://support.withings.com/hc/en-us/articles/11888924491025-Body-Scan-Nerve-Health-Score-NHS
for _marker in (
    "Nerve Health Score Feet (Withings)",
    "Nerve Health Score Left Foot (Withings)",
    "Nerve Health Score Right Foot (Withings)",
):
    TARGETS[_marker] = {
        "reference": ">50 (NHS comparison)",
        "target": (50, None),
        "normal": (50, None),
        "valid": (0, 100),
        "neutral_at": (50,),
        "bands": (
            (50, "🟢", "Above the NHS comparison threshold; API mean"),
            (0, "🟡", "Below the NHS comparison threshold; API mean"),
        ),
    }


# Oura: higher average nocturnal HRV relative to one's own baseline generally
# indicates better recovery; the nightly mean comprises5-minute samples.
# https://support.ouraring.com/hc/en-us/articles/360025441974-Heart-Rate-Variability
# Withings: first/last90-minute means; higher sleep-end HRV generally indicates
# a more restorative night. Preserve each measurement window's own comparison.
# https://support.withings.com/hc/en-us/articles/35762631441681-Sleep-U-S-Nighttime-Heart-Rate-Variability-HRV
# Direction alone is not an unlimited target or an absolute population grade.
for _marker in (
    "Average HRV (Sleep)",
    "Sampled HRV During Primary Sleep (Oura)",
    "HRV at Sleep Start (Withings)",
    "HRV at Sleep End (Withings)",
):
    TARGETS[_marker] = {
        "reference": "Personal baseline; sustained recovery trend",
        "direction": "up",
    }


# Garmin's7-day average is compared with a trained personal baseline. Both
# unexpectedly high and low values can be unbalanced; high values can reflect
# overreaching. Do not reconstruct its baseline from monthly report means.
# https://www.garmin.com/en-NZ/garmin-technology/health-science/hrv-status/
for _marker in (
    "Average Nightly HRV (Garmin)",
    "7-day Average HRV (Garmin)",
):
    TARGETS[_marker] = {
        "reference": "Within personal HRV baseline (Balanced)",
        "direction": "none",
    }

for _marker in (
    "Max HRV",
    "Highest 5-minute Nightly HRV (Garmin)",
    "Sampled HRV During Sessions (Oura)",
):
    TARGETS[_marker] = {
        "reference": "Personal baseline for the same window",
        "direction": "none",
    }


# These are nighttime peripheral-temperature deviations, not core temperature.
# Zero is the actual provider baseline; no universal healthy ±cutoff is given.
# https://support.ouraring.com/hc/en-us/articles/360025587493-Body-Temperature
for _marker in (
    "Temperature Deviation (Oura)",
    "Temperature Trend Deviation (Oura)",
):
    TARGETS[_marker] = {
        "reference": "Near personal baseline (0)",
        "valid": (None, None),
        "direction": "zero",
    }

del _marker
