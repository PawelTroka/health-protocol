"""Explicit exceptions to monthly means for clocks, event rates and totals."""

from decimal import Decimal, ROUND_HALF_UP
import math
import re


CLOCK_METRICS = {
    f"{name} ({provider})"
    for provider in ("Oura", "Withings")
    for name in ("Bedtime", "Wake-up Time", "Sleep Midpoint")
}
VARIABILITY_METRICS = {
    f"Sleep Midpoint Variability ({provider})": f"Sleep Midpoint ({provider})"
    for provider in ("Oura", "Withings")
}
EVENT_RATE_METRICS = {
    "Short Sleep Nights (Oura)", "Short Sleep Nights (Withings)",
    "AHI ≥5 Nights (Withings)",
}
TOTAL_METRICS = {"Recorded Short-Sleep Periods (Oura)", "Recorded Short-Sleep Duration (Oura)"}


def aggregation_for(metric):
    if metric in CLOCK_METRICS:
        return "circular_mean_local_time"
    if metric in VARIABILITY_METRICS:
        return "circular_standard_deviation_minutes"
    if metric in TOTAL_METRICS:
        return "sum_of_daily_totals"
    return "mean_of_daily_means"


def circular_summary(minutes):
    """Return a local-clock mean and population circular SD, both in minutes."""
    angles = [float(value) * math.tau / 1440 for value in minutes]
    sine = sum(math.sin(value) for value in angles) / len(angles)
    cosine = sum(math.cos(value) for value in angles) / len(angles)
    resultant = min(1, math.hypot(sine, cosine))
    if resultant < 1e-10:
        return None, None  # Opposite/uniform times do not define a mean clock.
    mean = (math.atan2(sine, cosine) % math.tau) * 1440 / math.tau
    sd = math.sqrt(max(0.0, -2 * math.log(resultant))) * 1440 / math.tau
    return mean, sd


def clock_text(minutes):
    rounded = int(Decimal(str(minutes)).quantize(Decimal(1), rounding=ROUND_HALF_UP)) % 1440
    return f"{rounded // 60:02d}:{rounded % 60:02d}"


def valid_clock(value):
    return isinstance(value, str) and re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value) is not None


def report_value(metric, entry):
    if metric in EVENT_RATE_METRICS:
        return f"{entry['value']} ({entry['n_matching_days']}/{entry['n_days']})"
    return entry["value"]
