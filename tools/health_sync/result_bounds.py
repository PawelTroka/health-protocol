"""Compare reported limits without treating a detection limit as a measurement."""

from dataclasses import dataclass
from decimal import Decimal
import re


_NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_VALUE = re.compile(rf"(?P<operator><=|>=|≤|≥|<|>)?\s*(?P<number>{_NUMBER})")
_RANGE = re.compile(rf"(?P<low>{_NUMBER})\s*[-–]\s*(?P<high>{_NUMBER})")
_NEGATIVE_INFINITY = Decimal("-Infinity")
_POSITIVE_INFINITY = Decimal("Infinity")


@dataclass(frozen=True)
class _Interval:
    low: Decimal
    high: Decimal
    low_closed: bool
    high_closed: bool
    bounded: bool = False


def _value_interval(value):
    if not isinstance(value, str):
        return None
    match = _VALUE.fullmatch(value.strip())
    if match is None:
        return None
    number = Decimal(match["number"])
    operator = match["operator"]
    if operator in {"<", "<=", "≤"}:
        return _Interval(_NEGATIVE_INFINITY, number, False, operator != "<", True)
    if operator in {">", ">=", "≥"}:
        return _Interval(number, _POSITIVE_INFINITY, operator != ">", False, True)
    return _Interval(number, number, True, True)


def _reference_interval(reference):
    if not isinstance(reference, str):
        return None
    # Report references may append a target or a qualitative band label.
    primary = reference.split(";", 1)[0].split(":", 1)[0].strip()
    match = _RANGE.fullmatch(primary)
    if match is not None:
        low, high = Decimal(match["low"]), Decimal(match["high"])
        return _Interval(low, high, True, True) if low <= high else None
    return _value_interval(primary)


def _strictly_before(left, right):
    return left.high < right.low or (
        left.high == right.low and not (left.high_closed and right.low_closed)
    )


def is_bounded(value):
    """Whether a value is a valid one-sided numeric limit."""
    interval = _value_interval(value)
    return interval is not None and interval.bounded


def bound_within_reference(value, reference):
    """Return True inside, False wholly outside, or None if uncertain.

    Values may be exact scalars or one-sided limits. No nonnegative floor is
    invented for an upper limit, and endpoints retain strict/inclusive meaning.
    """
    observed, expected = _value_interval(value), _reference_interval(reference)
    if observed is None or expected is None:
        return None
    lower_inside = observed.low > expected.low or (
        observed.low == expected.low and (not observed.low_closed or expected.low_closed)
    )
    upper_inside = observed.high < expected.high or (
        observed.high == expected.high and (not observed.high_closed or expected.high_closed)
    )
    if lower_inside and upper_inside:
        return True
    if _strictly_before(observed, expected) or _strictly_before(expected, observed):
        return False
    return None


def bounded_comparison(current, previous):
    """Return proven numeric ordering, an identical bound, or None.

    'same_bound' means the same reported limit, not identical measurements.
    'lower' and 'higher' describe numbers, not whether health improved.
    """
    current_interval, previous_interval = _value_interval(current), _value_interval(previous)
    if current_interval is None or previous_interval is None:
        return None
    if current_interval.bounded and current_interval == previous_interval:
        return "same_bound"
    if _strictly_before(current_interval, previous_interval):
        return "lower"
    if _strictly_before(previous_interval, current_interval):
        return "higher"
    return None
