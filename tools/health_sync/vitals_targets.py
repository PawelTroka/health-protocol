"""Evidence-based display targets; no device data, I/O or diagnoses.

References and distinctions between clinical, provider and practical targets
are recorded in results/Reference-Guide.md. Rules grade the stated target,
not an invented universal optimum at the midpoint of every reference range.
"""

from datetime import date
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import re

from .activity_targets import TARGETS as ACTIVITY_TARGETS
from .recovery_targets import TARGETS as RECOVERY_TARGETS
from .sleep_targets import TARGETS as SLEEP_TARGETS


COLORS = {"🔵": "#00008b", "🟢": "#008000", "🟡": "#927000",
          "🟠": "#a84a00", "🔴": "#b22319", "⚪": "#64748b"}
MISSING = {None, "", "-", "—"}

CATEGORIES = {
    "ECG AF Classification (Withings)": {
        "Negative": ("🔵", 1), "Positive": ("🟠", 0),
    },
    "Stress Day Summary (Oura)": {
        "Restored": ("🔵", 2), "Normal": ("🟢", 1), "Stressful": ("🟡", 0),
    },
    "Resilience Level (Oura)": {
        "Exceptional": ("🔵", 4), "Strong": ("🔵", 3), "Solid": ("🟢", 2),
        "Adequate": ("🟡", 1), "Limited": ("🟠", 0),
    },
    "HRV Status (Garmin)": {
        "Balanced": ("🟢", 3), "Unbalanced": ("🟡", 2), "Low": ("🟠", 1), "Poor": ("🔴", 0),
    },
}
CATEGORY_REFERENCES = {
    "ECG AF Classification (Withings)": "Negative",
    "Stress Day Summary (Oura)": "Normal / Restored",
    "Resilience Level (Oura)": "Solid or better; target Strong–Exceptional",
    "HRV Status (Garmin)": "Balanced within personal baseline",
}


def classification_parts(marker, value):
    """Color recognized labels without treating counts or codes as scores."""
    categories = CATEGORIES.get(marker, {})
    parts = []
    for text in str(value).split("; "):
        match = re.fullmatch(r"(.+): (\d+)", text)
        info = categories.get(match[1]) if match else None
        parts.append((text, (COLORS[info[0]], info[0], match[1]) if info else None))
    return parts


def classification_trend(values, marker):
    """Compare label proportions by ordered dominance, never mean API codes."""
    categories = CATEGORIES.get(marker)
    if not categories:
        return None
    distributions = []
    for value in values:
        if value in MISSING:
            continue
        counts = {}
        for part in str(value).split("; "):
            match = re.fullmatch(r"(.+): (\d+)", part)
            if not match or match[1] not in categories:
                return "-"
            rank = categories[match[1]][1]
            counts[rank] = counts.get(rank, 0) + int(match[2])
        total = sum(counts.values())
        if not total:
            return "-"
        distributions.append({rank: Fraction(count, total) for rank, count in counts.items()})
        if len(distributions) == 2:
            break
    if len(distributions) != 2:
        return "-"
    current, previous = distributions
    ranks = sorted({rank for _, rank in categories.values()})[1:]
    changes = [sum(count for rank, count in current.items() if rank >= cut)
               - sum(count for rank, count in previous.items() if rank >= cut) for cut in ranks]
    if all(change >= 0 for change in changes) and any(change > 0 for change in changes):
        return "🟢"
    if all(change <= 0 for change in changes) and any(change < 0 for change in changes):
        return "🟡"
    return "⚪"


def number(value):
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"\s*~?\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))(?:\s*\([^()]*\))?\s*", value)
    try:
        return Decimal(match[1]) if match else None
    except InvalidOperation:
        return None


def within(value, interval, open_bounds=(False, False)):
    low, high = interval
    return ((low is None or (value > Decimal(str(low)) if open_bounds[0] else value >= Decimal(str(low))))
            and (high is None or (value < Decimal(str(high)) if open_bounds[1] else value <= Decimal(str(high)))))


def distance(value, interval):
    low, high = interval
    if low is not None and value < Decimal(str(low)):
        return Decimal(str(low)) - value
    if high is not None and value > Decimal(str(high)):
        return value - Decimal(str(high))
    return Decimal(0)


OURA_SCORE = {
    "reference": "70–100; target 85–100", "valid": (0, 100), "direction": "up",
    "bands": ((85, "🔵", "Oura: optimal"), (70, "🟢", "Oura: good"),
              (60, "🟡", "Oura: fair"), (0, "🟠", "Oura: pay attention")),
}

# Withings defines whole-body muscle (not DXA appendicular lean mass), bone
# and water as percentages. Male 20–39 comparison bands apply to this report.
BODY_TARGETS = {
    "Body Mass": {"reference": "59.9–80.7; BMI-derived target 64.8–80.7",
                  "normal": (18.5, 24.9), "target": (20, 24.9),
                  "transform": ("scale", 1 / 1.8 ** 2)},
    "BMI": {"reference": "18.5–24.9; target 20–24.9", "normal": (18.5, 24.9), "target": (20, 24.9)},
    "Body Fat": {"reference": "8–20; practical target 10–15", "normal": (8, 20), "target": (10, 15), "valid": (0, 100)},
    "Muscle": {"reference": "75–89", "target": (75, 89), "valid": (0, 100),
               "trend_target": (89, 89), "trend_guard": (None, 89), "trend_min_change": 0.2},
    "Bone": {"reference": "3–5", "target": (3, 5), "valid": (0, 100),
             "trend_target": (5, 5), "trend_guard": (None, 5), "trend_min_change": 0.1},
    "Body Water (Withings)": {"reference": "50–65", "target": (50, 65), "valid": (0, 100)},
    "Lean Mass (Withings)": {"reference": "80–92; practical target 85–90", "normal": (80, 92), "target": (85, 90), "valid": (0, 100)},
    "Visceral Fat Index": {"reference": "0–5", "target": (0, 5), "valid": (0, 20),
                          "outside_emoji": "🟠", "direction": "down", "trend_min_change": 0.1},
}
for marker, pct, band, normal in (
    ("Fat Mass (Withings)", "10–15", (10, 15), (8, 20)),
    ("Bone Mass (Withings)", "3–5", (3, 5), (3, 5)),
    ("Muscle Mass (Withings)", "75–89", (75, 89), (75, 89)),
    ("Fat-Free Mass (Withings)", "85–90", (85, 90), (80, 92)),
    ("Water Mass (Withings)", "50–65", (50, 65), (50, 65)),
):
    comparison = f"{normal[0]}–{normal[1]}%; target {pct}%" if normal != band else f"{pct}%"
    BODY_TARGETS[marker] = {"reference": f"{comparison} of body mass", "target": band, "normal": normal,
                           "transform": ("ratio", "Body Mass", 100)}

# Percentages can rise through fat loss while tissue mass stays unchanged.
# Compare kg rows in kg; retain the ratio only for their value status.
for marker, floor in (("Bone Mass (Withings)", 0.05), ("Muscle Mass (Withings)", 0.2),
                      ("Fat-Free Mass (Withings)", 0.2)):
    BODY_TARGETS[marker].update(trend_raw=True, direction="up", trend_min_change=floor,
                                trend_guard=(None, BODY_TARGETS[marker]["target"][1]))
for segment in ("Left Arm", "Right Arm", "Left Leg", "Right Leg", "Torso"):
    BODY_TARGETS[f"Muscle Mass - {segment} (Withings)"] = {
        "reference": "Maintain / build muscle", "direction": "up",
        "trend_min_change": 0.05, "trend_min_relative_change": 0.01,
    }

# Retain existing protocol HR targets, now also applying to exact resting /
# overnight counterparts. Do not apply them to daytime averages or maxima.
HEART_TARGETS = {}
for marker in ("Sleeping Heart Rate", "Average Sleeping HR (Oura)", "Average Sleeping HR (Withings)",
               "Mean Nightly Lowest HR (Oura)", "Mean Nightly Lowest HR (Withings)",
               "Sampled HR During Primary Sleep (Oura)", "Sampled Sleeping HR (Oura)"):
    HEART_TARGETS[marker] = {"reference": "40–100; practical target 45–60", "normal": (40, 100), "target": (45, 60),
                             "trend_target": (45, 45), "trend_guard": (45, None), "trend_min_change": 0.5}
for marker in ("Resting Heart Rate", "Resting HR (Garmin)", "Sampled Rest HR (Oura)"):
    HEART_TARGETS[marker] = {"reference": "40–100; practical target 50–70", "normal": (40, 100), "target": (50, 70),
                             "trend_target": (50, 50), "trend_guard": (50, None), "trend_min_change": 0.5}
for marker in ("ECG Heart Rate", "ECG Recorded Heart Rate (Withings)", "Pulse Rate (Withings)"):
    HEART_TARGETS[marker] = {"reference": "50–100; practical target 50–80", "normal": (50, 100), "target": (50, 80),
                             "trend_target": (50, 50), "trend_guard": (50, None), "trend_min_change": 0.5}
for marker in ("PWV", "Estimated PWV (Oura)"):
    HEART_TARGETS[marker] = {"reference": "<10; practical target <7", "normal": (0, 10), "target": (0, 7),
                             "normal_open": (False, True), "target_open": (False, True),
                             "valid": (0.01, None), "direction": "down", "trend_min_change": 0.1}
for marker in ("Cardiovascular Age (Oura)", "Vascular Age (Withings)", "Metabolic Age (Withings)"):
    HEART_TARGETS[marker] = {"reference": "Below chronological age", "direction": "down"}
HEART_TARGETS["Cardiovascular Age Difference (Oura)"] = {
    "reference": "Within ±5; target ≤−6", "normal": (-5, 5), "target": (None, -6),
    "valid": (None, None), "direction": "down",
    "bands": ((6, "🟡", "Oura: above chronological age"), (-5, "🟢", "Oura: aligned"),
              (-1000, "🔵", "Oura: below chronological age")),
}

TARGETS = {**BODY_TARGETS, **HEART_TARGETS, **SLEEP_TARGETS, **RECOVERY_TARGETS, **ACTIVITY_TARGETS}


def rule_for(marker):
    if marker in {"Sleep Score", "Readiness Score (Oura)", "Activity Score (Oura)",
                  "Resilience Daytime Recovery Contributor Score (Oura)",
                  "Resilience Sleep Recovery Contributor Score (Oura)"} or re.fullmatch(
                      r"(?:Sleep|Readiness|Activity) .+ Contributor Score \(Oura\)", marker or ""):
        return OURA_SCORE
    return TARGETS.get(marker)


def reference(marker):
    if marker in CATEGORY_REFERENCES:
        return CATEGORY_REFERENCES[marker]
    rule = rule_for(marker)
    return rule["reference"] if rule else None


def matched_days(entries):
    """Prove equal observation days, never infer pairing from equal counts alone."""
    if not entries or any(not entry for entry in entries):
        return False
    if not entries[0].get("provider") or len({entry.get("provider") for entry in entries}) != 1:
        return False
    if len({entry["n_records"] for entry in entries if "n_records" in entry}) > 1:
        return False
    days = [entry.get("observed_days") for entry in entries]
    if all(days):
        return all(value == days[0] for value in days)
    # Older summaries can prove a shared uninterrupted interval without a
    # day list. Gapped intervals need the new explicit coverage metadata.
    intervals = [(entry.get("first_day"), entry.get("last_day"), entry.get("n_days")) for entry in entries]
    if len(set(intervals)) != 1:
        return False
    first, last, count = intervals[0]
    try:
        return count == (date.fromisoformat(last) - date.fromisoformat(first)).days + 1
    except (TypeError, ValueError):
        return False


def evaluated_value(marker, value, context=None):
    rule = rule_for(marker)
    val = number(value)
    if not rule or val is None or not within(val, rule.get("valid", (0, None))):
        return None
    transform = rule.get("transform")
    if not transform:
        return val
    if transform[0] == "scale":
        return val * Decimal(str(transform[1]))
    if not context:
        return None
    if transform[0] == "ratio":
        other = context.get(transform[1], {})
        divisor = number(other.get("value"))
        if divisor is None or divisor <= 0 or not matched_days([context.get(marker), other]):
            return None
        ratio = val / divisor * Decimal(str(transform[2]))
        return ratio if 0 <= ratio <= 100 else None
    if transform[0] == "sum":
        entries = [context.get(name, {}) for name, _ in transform[1]]
        values = [number(entry.get("value")) for entry in entries]
        if not matched_days([context.get(marker), *entries]) or any(v is None or v < 0 for v in values):
            return None
        return sum(v * Decimal(str(factor)) for v, (_, factor) in zip(values, transform[1]))
    raise ValueError(f"Unknown vitals transform: {transform}")


def status(marker, value, context=None):
    rule = rule_for(marker)
    val = evaluated_value(marker, value, context)
    if not rule or val is None or val in rule.get("neutral_at", ()):
        return None
    for minimum, emoji, label in rule.get("bands", ()):
        if val >= Decimal(str(minimum)):
            return COLORS[emoji], emoji, label
    target = rule.get("target")
    normal = rule.get("normal", target)
    if target is None and normal is None:
        return None
    if target and within(val, target, rule.get("target_open", (False, False))):
        emoji = "🔵" if normal != target else "🟢"
        label = "Within the stated target" if normal != target else "Within the stated comparison range"
    elif normal and within(val, normal, rule.get("normal_open", (False, False))):
        emoji, label = "🟢", "Within the comparison range; outside the practical target"
    else:
        emoji, label = rule.get("outside_emoji", "🟡"), "Outside the stated comparison range"
    return COLORS[emoji], emoji, label


def trend(values, marker, contexts=None):
    """Separate value ranges from trend direction and modest display floors."""
    rule = rule_for(marker)
    if not rule:
        return None
    pair = []
    raw_pair = []
    for idx, raw in enumerate(values):
        if raw in MISSING:
            continue
        val = evaluated_value(marker, raw, contexts[idx] if contexts and idx < len(contexts) else None)
        if val is None:
            return "-"  # Never skip an unknown newest result to grade older data.
        pair.append(val)
        raw_pair.append(number(raw))
        if len(pair) == 2:
            break
    if len(pair) != 2:
        return "-"
    current, previous = pair
    comparison_current, comparison_previous = pair
    raw_current, raw_previous = raw_pair
    raw_delta = raw_current - raw_previous
    # These are display sensitivity settings, not statistical significance,
    # clinical minimum important differences or device accuracy claims.
    floor = max(Decimal(str(rule.get("trend_min_change", 0))),
                abs(raw_previous) * Decimal(str(rule.get("trend_min_relative_change", 0))))
    if abs(raw_delta) < floor:
        return "⚪"
    if abs(current - previous) < Decimal(str(rule.get("trend_min_evaluated_change", 0))):
        return "⚪"
    direction = rule.get("direction", "target")
    target = rule.get("trend_target", rule.get("target"))
    if rule.get("trend_raw"):
        # Do not reward increasing tissue estimates beyond the comparison's
        # upper bound. Outside that bound, compare distance back to the range.
        upper = rule["target"][1]
        if upper is not None and (current > upper or previous > upper):
            direction = "target"
            # A lower tissue estimate must not become a gain just because its
            # share moves back toward the percentage comparison range.
            if raw_delta < 0 and distance(current, target) < distance(previous, target):
                return "⚪"
        else:
            current, previous = raw_current, raw_previous
    if direction == "none":
        return "⚪"
    if direction == "up":
        change = current - previous
    elif direction == "down":
        change = previous - current
    elif direction == "zero":
        change = abs(previous) - abs(current)
    elif target:
        change = distance(previous, target) - distance(current, target)
    else:
        return "⚪"
    if rule.get("trend_agreement") and change * raw_delta < 0:
        return "⚪"  # More stage share from less total sleep is not more stage time.
    guard = rule.get("trend_guard")
    if guard and (not within(comparison_current, guard) or not within(comparison_previous, guard)):
        # Crossing beyond a lower-HR or upper-composition guard is never an
        # improvement simply because the new value is nearer the endpoint.
        change = distance(comparison_previous, guard) - distance(comparison_current, guard)
    # This is a display direction, not significance or a clinical effect size.
    return "🟢" if change > 0 else "🟡" if change < 0 else "⚪"
