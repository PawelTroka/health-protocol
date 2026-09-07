"""Editorial presentation of vitals, preserving every original row and value.

The main view prioritizes a compact overview; placement is not a medical utility
rating. Provider definitions stay separate. Known names have a stable order and
new measurements default to details until deliberately added to the overview.
This module neither reads source files nor modifies measurements or row objects.
"""


_MAIN_GROUPS = (
    (
        "Body composition",
        "Weight and composition, including bone percentage and the visceral fat index.",
        (
            "Body Mass", "BMI", "Body Fat", "Muscle", "Bone", "Visceral Fat Index",
        ),
    ),
    (
        "Body measurements",
        "Self-reported sizes, with dated snapshots and measurement methods identified in the source notes.",
        (
            "Height", "Waist Circumference (Narrowest Point)", "Hip Circumference",
            "Chest Circumference", "Shoulder Circumference", "Neck Circumference",
            "Right Upper Arm Circumference (Flexed)", "Right Forearm Circumference",
            "Right Wrist Circumference", "Right Thigh Circumference", "Right Calf Circumference",
            "Right Ankle Circumference", "Right Above-Ankle Circumference",
            "Right Foot Length", "Head Circumference",
        ),
    ),
    (
        "Heart and circulation",
        "Blood pressure, pulse-wave velocity, heart rate and recorded ECG classifications.",
        (
            "Blood Pressure", "PWV", "Estimated PWV (Oura)",
            "Average Sleeping HR (Oura)",
            "Mean Nightly Lowest HR (Oura)", "ECG AF Classification (Withings)",
        ),
    ),
    (
        "Sleep and breathing",
        "Sleep duration, stages, continuity, breathing and oxygen measurements.",
        (
            "Sleep Duration", "Time in Bed", "Sleep Efficiency", "Sleep Latency",
            "Sleep Score", "REM Sleep", "Deep Sleep", "Light Sleep (Oura)",
            "Awake Time During Sleep (Oura)", "Respiratory Rate (Sleep)",
            "Average Sleeping SpO2 (Oura)", "Sleep Apnea AHI",
            "Breathing Disturbance Index (Oura)", "Snoring Duration (Withings)",
        ),
    ),
    (
        "Recovery and stress",
        "Nightly HRV, readiness and the recorded stress and resilience summaries.",
        (
            "Average HRV (Sleep)", "Readiness Score (Oura)",
            "Stress Day Summary (Oura)", "High Stress Time (Oura)",
            "High Recovery Time (Oura)", "Resilience Level (Oura)",
        ),
    ),
    (
        "Activity and fitness",
        "Fitness estimates, daily activity and recorded workout summaries retain their source notes.",
        (
            "VO2max", "VO2 Max (Oura)", "VO2max (Withings)", "Steps (Oura)",
            "Activity Score (Oura)", "Active Duration (Withings)",
            "High Activity Time (Oura)", "Medium Activity Time (Oura)",
            "Low Activity Time (Oura)", "Sedentary Time (Oura)",
            "Active Energy (Oura)", "Total Energy Expenditure (Oura)",
            "Duration per Recorded Workout (Oura)", "Distance per Recorded Workout (Oura)",
        ),
    ),
    (
        "Nerve health and temperature",
        "The confirmed app score, separate API foot score and temperature readings retain their source notes.",
        (
            "Nerve Health Score", "Nerve Health Score Feet (Withings)",
            "Temperature", "Temperature Deviation (Oura)",
        ),
    ),
)

_DETAIL_GROUPS = (
    ("Body composition details",
     "Mass measurements, body segments, water compartments and recorded height."),
    ("Heart and circulation details",
     "Additional heart-rate measurements and event-specific readings from each source."),
    ("Sleep and breathing details",
     "Additional sleep summaries, breathing ranges and recorded sleep events."),
    ("Recovery and temperature details",
     "Additional HRV and temperature observations retain their original definitions."),
    ("Nerve health details",
     "Left and right foot API scores remain separate from the confirmed app score."),
    ("Activity and workout details",
     "Additional activity totals, intensity zones, targets and workout measurements."),
    ("Score contributors and changes",
     "The individual contributors and changes supplied alongside device scores."),
    ("Sensor samples",
     "Sample-based heart-rate, HRV, motion and MET measurements remain available separately."),
    ("Device codes and classifications",
     "Additional recorded device labels and codes, with their source notes."),
    ("Model estimates",
     "Device-reported age and metabolic estimates retain their specific model definitions."),
    ("Manual and historical observations",
     "Original manual observations and snapshots retain their dates and source notes."),
    ("Additional measurements",
     "Further measurements are retained here as they become available."),
)

_LEGACY_NAMES = {
    "Resting Heart Rate", "Sleeping Heart Rate", "Maximum Heart Rate",
    "ECG Rhythm", "ECG Heart Rate", "Heart Sounds", "Nighttime BP Dip",
    "Nighttime BP Pattern", "Max HRV", "Stress",
    "Cardiovascular Age Difference (Oura)",
}
_MODEL_NAMES = {
    "Cardiovascular Age (Oura)", "Vascular Age (Withings)",
    "Metabolic Age (Withings)", "Basal Metabolic Rate (Withings)",
}
_DEVICE_NAMES = {
    "Heart Sounds Classification (Withings)", "PPG AF Classification (Withings)",
    "Breathing Disturbance Intensity (Withings)",
    "Breathing Quality Assessment (Withings)", "Core Body Temperature Status (Withings)",
}
_BODY_NAMES = {
    "Lean Mass (Withings)", "Body Water (Withings)", "Water Mass (Withings)",
    "Intracellular Water (Withings)", "Extracellular Water (Withings)",
    "Bone Mass (Withings)", "Height (Withings)",
}
_HEART_NAMES = {
    "Average Daily HR (Withings)",
    "Pulse Rate (Withings)", "ECG Recorded Heart Rate (Withings)",
    "Average Sleeping HR (Withings)", "Mean Nightly Lowest HR (Withings)",
    "Mean Nightly Highest HR (Withings)", "Mean Daily Lowest HR (Withings)",
    "Mean Daily Highest HR (Withings)",
}
_SLEEP_NAMES = {
    "Sleep Duration (Withings)", "Time in Bed (Withings)",
    "Sleep Efficiency (Withings)", "Sleep Latency (Withings)", "Sleep Score (Withings)",
    "REM Sleep (Withings)", "Deep Sleep (Withings)", "Light Sleep (Withings)",
    "Awake Duration (Withings)", "Wake After Sleep Onset (Withings)",
    "Wakeup Count (Withings)", "Wakeup Latency (Withings)", "Out of Bed Count (Withings)",
    "REM Episode Count (Withings)", "Snoring Episode Count (Withings)",
    "Sleeping Movement Duration (Withings)", "Sleeping Movement Score (Withings)",
    "Restless Periods During Sleep (Oura)", "Respiratory Rate During Sleep (Withings)",
    "Minimum Sleeping Respiratory Rate (Withings)", "Maximum Sleeping Respiratory Rate (Withings)",
}
_RECOVERY_NAMES = {
    "HRV at Sleep Start (Withings)", "HRV at Sleep End (Withings)", "Skin Temperature (Withings)",
    "Temperature Trend Deviation (Oura)",
}
_ACTIVITY_NAMES = {
    "Steps (Withings)", "Active Calories (Withings)", "Total Calories (Withings)",
    "Distance (Withings)", "Floors Climbed (Withings)", "Light Activity Duration (Withings)",
    "Moderate Activity Duration (Withings)", "Intense Activity Duration (Withings)",
    "HR Light Zone Duration (Withings)", "HR Moderate Zone Duration (Withings)",
    "HR Intense Zone Duration (Withings)", "HR Maximal Zone Duration (Withings)",
    "Equivalent Walking Distance (Oura)", "Average MET Minutes (Oura)",
    "High Activity MET Minutes (Oura)", "Medium Activity MET Minutes (Oura)",
    "Low Activity MET Minutes (Oura)", "Sedentary MET Minutes (Oura)",
    "Resting Time (Oura)", "Non-wear Time (Oura)", "Inactivity Alerts (Oura)",
    "Activity Energy Target (Oura)", "Activity Distance Target (Oura)",
    "Distance Remaining to Activity Target (Oura)", "Energy per Recorded Workout (Oura)",
    "Duration per Recorded Session (Oura)",
}


def _detail_title(name):
    if name in _LEGACY_NAMES:
        return "Manual and historical observations"
    if name.startswith("Sampled "):
        return "Sensor samples"
    if " Contributor Score (" in name or name in {
        "Primary Sleep Readiness Score Change (Oura)", "Primary Sleep Score Change (Oura)",
    }:
        return "Score contributors and changes"
    if name in _MODEL_NAMES:
        return "Model estimates"
    if name in _DEVICE_NAMES:
        return "Device codes and classifications"
    if name in _BODY_NAMES or name.startswith(("Fat Mass", "Fat-Free Mass", "Muscle Mass")):
        return "Body composition details"
    if name in {"Nerve Health Score Left Foot (Withings)", "Nerve Health Score Right Foot (Withings)"}:
        return "Nerve health details"
    for names, title in (
        (_HEART_NAMES, "Heart and circulation details"),
        (_SLEEP_NAMES, "Sleep and breathing details"),
        (_RECOVERY_NAMES, "Recovery and temperature details"),
        (_ACTIVITY_NAMES, "Activity and workout details"),
    ):
        if name in names:
            return title
    return "Additional measurements"


def layout(rows):
    """Group rows by their unchanged first-column names, retaining every object.

    Main groups precede secondary groups. Main rows follow the explicit overview
    order; detail rows are alphabetical. Empty groups are omitted. Duplicate input
    names are retained as separate rows rather than silently deduplicated.
    """
    groups = [
        {"title": title, "description": description, "details": False, "rows": []}
        for title, description, _ in _MAIN_GROUPS
    ] + [
        {"title": title, "description": description, "details": True, "rows": []}
        for title, description in _DETAIL_GROUPS
    ]
    by_title = {group["title"]: group for group in groups}
    overview = {name: (title, index)
                for title, _, names in _MAIN_GROUPS for index, name in enumerate(names)}
    for row in rows:
        name = row[0]
        title = overview[name][0] if name in overview else _detail_title(name)
        by_title[title]["rows"].append(row)
    for group in groups:
        group["rows"].sort(key=(lambda row: row[0].casefold()) if group["details"]
                           else (lambda row: overview[row[0]][1]))
    return [group for group in groups if group["rows"]]


def counts(groups):
    """Return overview, secondary-detail and total row counts for a layout."""
    main = sum(len(group["rows"]) for group in groups if not group["details"])
    details = sum(len(group["rows"]) for group in groups if group["details"])
    return {"main": main, "details": details, "total": main + details}
