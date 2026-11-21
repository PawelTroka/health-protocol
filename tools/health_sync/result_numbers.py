"""Parse whole reported numbers without deleting meaningful punctuation.

Results may contain a comparison, an approximation marker, or one trailing
parenthetical annotation. Counts, pairs, units, and free text are not scalars.
Comma decimals are accepted only when they cannot also be thousands grouping.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re


_NUMBER = r"[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][+-]?\d+)?"
_RESULT = re.compile(
    rf"\s*(?P<approximate>~)?\s*(?P<operator><=|>=|≤|≥|<|>)?\s*"
    rf"(?P<number>{_NUMBER})(?:\s*\([^()]*\))?\s*"
)
_RANGE = re.compile(
    rf"(?P<low>{_NUMBER})\s*[-–]\s*(?P<high>{_NUMBER})"
    rf"(?:\s*\([^()]*\))?"
)


@dataclass(frozen=True)
class ReportedNumber:
    value: Decimal
    operator: str = ""
    approximate: bool = False


def _decimal(literal):
    if "," in literal:
        mantissa = re.split("[eE]", literal, maxsplit=1)[0].lstrip("+-")
        whole, fraction = mantissa.split(",")
        # 1,234 could mean 1234 or 1.234. 1,5, 0,125 and 1234,567
        # do not match a thousands-grouping convention.
        if not fraction or (len(fraction) == 3 and 1 <= len(whole) <= 3 and whole != "0"):
            return None
        literal = literal.replace(",", ".")
    try:
        return Decimal(literal)
    except InvalidOperation:
        return None


def parse_result(value):
    """Return a scalar or bound with its operator intact, or None."""
    if not isinstance(value, str):
        return None
    match = _RESULT.fullmatch(value)
    if match is None or (match["approximate"] and match["operator"]):
        return None
    number = _decimal(match["number"])
    if number is None:
        return None
    operator = {"≤": "<=", "≥": ">="}.get(match["operator"], match["operator"] or "")
    return ReportedNumber(number, operator, bool(match["approximate"]))


def parse_reference(reference):
    """Return inclusive (low, high) limits or a single comparison/scalar."""
    if not isinstance(reference, str):
        return None
    primary = reference.split(";", 1)[0].split(":", 1)[0].strip()
    match = _RANGE.fullmatch(primary)
    if match is not None:
        low, high = _decimal(match["low"]), _decimal(match["high"])
        return (low, high) if low is not None and high is not None and low <= high else None
    result = parse_result(primary)
    return result if result is not None and not result.approximate else None
