"""Sourced activity comparisons, separate from measured result values.

These are practical or provider targets, not diagnostic reference intervals.
The report evaluator must establish identical observed days before applying a
sum transform. It must not combine providers or treat a missing component as 0.
"""


TARGETS = {}

# Cohort evidence supports a practical target near 8,000 steps/day; 7,000 is
# already associated with substantial benefit. Display thresholds do not imply
# abrupt risk changes, and values above the target are not penalized.
# https://www.nature.com/articles/s41467-026-71652-0 (April 2026)
# https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2783711
for _marker in ("Steps (Oura)", "Steps (Withings)", "Steps (Garmin)"):
    TARGETS[_marker] = {
        "reference": "≥7000; practical target ≥8000/day",
        "target": (8000, None),
        "normal": (7000, None),
    }

# Oura inactivity includes passive standing, unlike the research definition of
# sedentary behavior. These thresholds therefore use the provider's own bands.
# Oura identifies 5–8 hours or less as favorable and >12 hours as attention.
# https://support.ouraring.com/hc/en-us/articles/360055901214-Activity-Contributors
TARGETS["Sedentary Time (Oura)"] = {
    "reference": "≤8; practical target ≤5",
    "target": (None, 5),
    "normal": (None, 8),
    "valid": (0, 24),
}
TARGETS["Inactivity Alerts (Oura)"] = {
    "reference": "0; break up prolonged inactivity",
    "target": (None, 0),
}

# Canadian guidance recommends several hours of light movement. A 2025/2026
# UK Biobank cohort supports an observational comparison around 3.5–6 hours.
# Applying it to consumer-ring classification is a practical extrapolation;
# more movement should replace inactivity, not necessary sleep or exercise.
# Saturate at 6 hours rather than suggesting unlimited benefit or harm above it.
# https://pubmed.ncbi.nlm.nih.gov/41201595/
# https://csepguidelines.ca/wp-content/uploads/2022/05/24HMovementGuidelines-Adults-18-64-ENG.pdf
TARGETS["Low Activity Time (Oura)"] = {
    "reference": "≥3.5; practical target ~6 (observational)",
    "target": (6, None),
    "normal": (3.5, None),
    "valid": (0, 24),
}

# WHO alternatives must be assessed together: 150–300 moderate minutes/week,
# or 75–150 vigorous minutes/week, or an equivalent mixture. These targets are
# their daily-mean equivalents, not claims that every observed week meets them.
# Oura stores hours; Withings/Garmin store minutes. Garmin vigorous minutes are
# doubled only in the combined total, so the source component gets factor 2.
# https://www.ncbi.nlm.nih.gov/books/NBK566046/
# https://support.withings.com/hc/en-us/articles/4403953413777-What-are-Active-minutes
# https://www8.garmin.com/manuals/webhelp/GUID-4205DB9F-0ACD-4AC2-86A8-957F27150AE4/EN-US/GUID-63522E07-AD5E-4D2D-B680-3129A2300238.html
_INTENSITY_COMPONENTS = (
    (("Medium Activity Time (Oura)", 60), ("High Activity Time (Oura)", 120)),
    (("Moderate Activity Duration (Withings)", 1),
     ("Intense Activity Duration (Withings)", 2)),
    (("Moderate Intensity Minutes (Garmin)", 1),
     ("Vigorous Intensity Minutes (Garmin)", 2)),
)
for _components in _INTENSITY_COMPONENTS:
    _rule = {
        "reference": "Combined M+2V: ≥21.4; target 42.9 min/day",
        "target": (300 / 7, None),
        "normal": (150 / 7, None),
        "transform": ("sum", _components),
    }
    for _marker, _factor in _components:
        TARGETS[_marker] = dict(_rule)

# Withings Active Duration is the unweighted M+V total. Grade the corresponding
# combined exercise volume from its explicit intensity components, rather than
# comparing that unweighted value to a moderate-only minimum.
TARGETS["Active Duration (Withings)"] = {
    "reference": "Combined M+2V: ≥21.4; target 42.9 min/day",
    "target": (300 / 7, None),
    "normal": (150 / 7, None),
    "transform": ("sum", _INTENSITY_COMPONENTS[1]),
}

# These MET-minute fields are sums within intensity classes. Oura's training
# volume contributor uses the combined medium+high total: 750/week comparison,
# 2,000/week maximum-score benchmark. Low/sedentary/average MET fields are not
# interchangeable with this dose and intentionally have no such target.
# https://support.ouraring.com/hc/en-us/articles/360055901214-Activity-Contributors
# https://api.ouraring.com/v2/static/json/openapi-1.37.json
_MET_COMPONENTS = (
    ("Medium Activity MET Minutes (Oura)", 1),
    ("High Activity MET Minutes (Oura)", 1),
)
for _marker, _factor in _MET_COMPONENTS:
    TARGETS[_marker] = {
        "reference": "Combined medium+high: ≥107.1; target 285.7 MET-min/day",
        "target": (2000 / 7, None),
        "normal": (750 / 7, None),
        "transform": ("sum", _MET_COMPONENTS),
    }

# This is attainment of the readiness-adjusted device goal, not a fixed health
# dose. Negative distance means the goal was exceeded; no extra reward follows.
# https://support.ouraring.com/hc/en-us/articles/360055901214-Activity-Contributors
TARGETS["Distance Remaining to Activity Target (Oura)"] = {
    "reference": "≤0; daily activity goal achieved",
    "target": (None, 0),
    "valid": (None, None),
}

# Preserve the report's established practical VO2 target while extending its
# directional evaluation to equivalent provider-specific rows. Absolute age/
# sex norms vary; higher measured fitness has favorable outcome associations.
# https://pmc.ncbi.nlm.nih.gov/articles/PMC6324439/
# https://support.ouraring.com/hc/en-us/articles/28336620578835-Cardio-Capacity-VO2-Max
for _marker in ("VO2max", "VO2 Max (Oura)", "VO2max (Withings)",
                "VO2 Max Running (Garmin)", "VO2 Max Cycling (Garmin)"):
    TARGETS[_marker] = {
        "reference": ">35; practical target ≥45",
        "target": (45, None),
        "normal": (35, None),
        "normal_open": (True, False),
        "direction": "up",
    }

for _marker in ("Morning Acute Training Load (Garmin)", "Acute Training Load (Garmin)",
                "Chronic Training Load (Garmin)", "Training Load per Workout (Garmin)"):
    TARGETS[_marker] = {"reference": "Personal training range and recovery", "direction": "none"}
TARGETS["Acute/Chronic Training Load Ratio (Garmin)"] = {
    # Garmin manuals show0.8–1.4 green and1.5 high; current support rounds the
    # upper boundary to1.5. Leave the disputed boundary ungraded.
    "reference": "Garmin balanced 0.8–<1.5", "target": (0.8, 1.5),
    "target_open": (False, True), "neutral_at": (1.5,), "trend_min_change": 0.05,
}
for _marker in ("Aerobic Training Effect per Workout (Garmin)", "Anaerobic Training Effect per Workout (Garmin)"):
    TARGETS[_marker] = {
        "reference": "2 maintain; 3–4 improve; 5 overreach", "valid": (0, 5), "direction": "none",
        "bands": ((5, "🟠", "Garmin: overreaching training effect"),
                  (4, "🔵", "Garmin: highly improving training effect"),
                  (3, "🟢", "Garmin: improving training effect"),
                  (2, "🟢", "Garmin: maintaining training effect")),
    }
for _zone in range(1, 6):
    TARGETS[f"Workout HR Zone {_zone} Duration (Garmin)"] = {
        "reference": "Per recorded workout day; balance intensity", "direction": "none",
    }
TARGETS["Fitness Age (Garmin)"] = {"reference": "Below chronological age", "direction": "down"}
TARGETS["Achievable Fitness Age (Garmin)"] = {"reference": "Garmin model goal", "direction": "none"}

# Per-workout duration/distance/energy are event averages, not weekly volume.
# Calorie totals and goal settings depend on size, energy balance and recovery.
# Withings light activity can include <3-MET passive behavior. None receives an
# invented independent optimum or an unconditional more-is-better direction.

del _marker, _factor, _components, _rule
