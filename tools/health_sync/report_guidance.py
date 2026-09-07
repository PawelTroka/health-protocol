"""Source-specific display guidance, separate from the legacy health score.

References were checked on 2026-09-07; see results/Reference-Guide.md.
Provider bands describe recorded scores, including displayed monthly means.
They do not establish a diagnosis or a personalized treatment target.
"""

from decimal import Decimal, InvalidOperation
import re


VITALS = "Vitals & Functional Health"
NEUTRAL = ("#64748b", "⚪", "No health classification assigned")
GREEN = ("#008000", "🟢", "Within the provider reference range")
BLUE = ("#00008b", "🔵", "Within the provider target band")
YELLOW = ("#927000", "🟡", "Outside the provider comparison range")
ORANGE = ("#a84a00", "🟠", "Provider attention band")


def strict_number(value):
    """Parse one reported scalar; never turn counts, bounds or pairs into it."""
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"\s*~?\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))(?:\s*\([^()]*\))?\s*", value)
    if not match:
        return None
    try:
        return Decimal(match[1])
    except InvalidOperation:
        return None


def numerical_change(values):
    """Latest two nonmissing readings, in row units, with no health judgment."""
    pair = []
    for value in values:
        if value in {None, "", "-", "—"}:
            continue
        number = strict_number(value)
        if number is None:
            return "-"  # Pending/uninterpretable results block an older trend.
        pair.append(number)
        if len(pair) == 2:
            break
    if len(pair) != 2:
        return "-"
    delta = pair[0] - pair[1]
    if not delta:
        return "→ 0"
    text = format(abs(delta).normalize(), "f")
    return f"↑ +{text}" if delta > 0 else f"↓ -{text}"


def oura_score(marker):
    return marker in {"Sleep Score", "Readiness Score (Oura)", "Activity Score (Oura)"} or bool(
        re.fullmatch(r"(?:Sleep|Readiness|Activity) .+ Contributor Score \(Oura\)", marker)
    )


def guide_reference(category, marker, ref):
    """Return sourced display context; None leaves an existing reference intact."""
    if category != VITALS:
        return None
    if oura_score(marker):
        return "Oura: 70–<85 good; target 85–100; 60–<70 fair; <60 pay attention"
    references = {
        "Sleep Score (Withings)": "Withings: >75–100 high / target; 50–<75 medium; <50 low; 75 unspecified",
        "Visceral Fat Index": "Withings: 0–5 normal; target stay ≤5 (scale 0–20)",
        "Sleep Efficiency": "Oura: ≥85%; target ≥85% (comparison, not diagnosis)",
        "Sleep Latency": "Oura target: 15–20min; shorter is not always better",
        "Average Sleeping SpO2 (Oura)": "Oura: 95–100%; target within range",
        "Nerve Health Score": "Confirmed Withings NHS: >50 normal, <50 low; target normal",
        "Body Mass": "Interpret with BMI and composition; no fixed weight target",
        "Bone": "Withings male comparison: 3–5%; no clinical target established",
        "Body Water (Withings)": "Withings male comparison: 50–65%; no clinical target established",
        "Bone Mass (Withings)": "BIA bone estimate; not bone density; no clinical target",
        "Height": "Individual anatomy; no health target",
        "Waist Circumference (Narrowest Point)": "Narrowest-point method; standard waist cutoffs not applied",
        "Nighttime BP Pattern": "Reference / target: typical dipping",
        "Stress": "App reference: low/minor; no numeric target",
    }
    if marker in references:
        return references[marker]
    if ref not in {None, "", "-", "—"}:
        return None
    if "Circumference" in marker or marker == "Right Foot Length":
        return "Individual anatomy; no health target"
    if "HRV" in marker:
        return "Personal baseline; no universal HRV target"
    if marker.startswith("Nerve Health Score "):
        return "API foot score; confirmed-app cutoff not applied"
    if "Heart Rate" in marker or " HR" in marker or "PWV" in marker or marker == "Pulse Rate (Withings)":
        return "Method and activity context; compare personal baseline"
    if "Temperature" in marker:
        return "Device / personal baseline; no universal target"
    return None


def guide_status(category, marker, value):
    """Explicit provider bands only; no fallback assumption that data are normal."""
    if category == "Stool Analysis" and marker in {
        "Starch Grains", "Fat Droplets", "Fatty Acid Crystals", "Muscle Fibers", "Mucus",
    } and value in {"single in preparation", "few in preparation"}:
        return (YELLOW[0], YELLOW[1], "Reported against an absent reference; quantity not graded")
    if category != VITALS:
        return None
    text = str(value).strip().casefold()
    if marker == "Nighttime BP Pattern" and text == "typical dipping":
        return GREEN
    if marker == "Stress" and text in {"low", "minor"}:
        return ("#008000", "🟢", "App-reported low stress")
    number = strict_number(value)
    if number is None:
        return None
    if oura_score(marker) and 0 <= number <= 100:
        if number >= 85:
            return BLUE
        if number >= 70:
            return (GREEN[0], GREEN[1], "Oura: good")
        if number >= 60:
            return (YELLOW[0], YELLOW[1], "Oura: fair")
        return (ORANGE[0], ORANGE[1], "Oura: pay attention")
    if marker == "Sleep Score (Withings)" and 0 <= number <= 100:
        if number == 75:
            return None  # Current provider versions overlap their bands at 75.
        if number > 75:
            return (GREEN[0], GREEN[1], "Withings: high sleep score")
        if number >= 50:
            return (YELLOW[0], YELLOW[1], "Withings: medium sleep score")
        return (ORANGE[0], ORANGE[1], "Withings: low sleep score")
    if marker == "Visceral Fat Index" and 0 <= number <= 20:
        return GREEN if number <= 5 else (ORANGE[0], ORANGE[1], "Withings: high visceral fat index")
    if marker == "Sleep Efficiency" and 0 <= number <= 100:
        return GREEN if number >= 85 else YELLOW
    if marker == "Sleep Latency" and number >= 0:
        return BLUE if 15 <= number <= 20 else None
    if marker == "Average Sleeping SpO2 (Oura)" and 0 <= number <= 100:
        return GREEN if number >= 95 else YELLOW
    if marker == "Nerve Health Score" and 0 <= number <= 100:
        if number > 50:
            return GREEN
        if number < 50:
            return (ORANGE[0], ORANGE[1], "Withings confirmed NHS: low")
        return None  # The provider text does not resolve the exact boundary 50.
    return None
