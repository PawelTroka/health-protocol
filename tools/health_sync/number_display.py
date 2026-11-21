"""Compact whole-number measurements without changing their stored precision."""

import re


_NUMBER = r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?"
_SCALAR = rf"(?:~\s*)?(?:[<>]=?|[≤≥])?\s*{_NUMBER}"
_RANGE = rf"{_SCALAR}(?:\s*[-–—]\s*{_SCALAR})?"
_EXPRESSION = rf"{_RANGE}(?:\s*/\s*{_RANGE})?(?:\s*%)?"
_MEASUREMENT = re.compile(
    rf"(?P<value>\s*{_EXPRESSION})(?P<annotation>\s*\([^()\r\n]*\))?(?P<space>\s*)"
)
_REFERENCE_CLAUSE = re.compile(
    rf"(?P<prefix>\s*(?:(?:target|goal)\s+)?)"
    rf"(?P<value>{_EXPRESSION})(?P<annotation>\s*\([^()\r\n]*\))?"
    rf"(?P<label>\s*:[^;\r\n]*)?(?P<space>\s*)"
)
_WHOLE_DECIMAL = re.compile(r"(?<![\w.])([+-]?)(\d*)\.0+(?![\d.])")


def _compact_expression(value):
    return _WHOLE_DECIMAL.sub(lambda match: match[1] + (match[2] or "0"), value)


def compact_measurement(value):
    """Remove an all-zero fraction from numeric cells, keeping annotations literal.

    Nonzero fractions keep their precision. Full-string matching protects dates,
    clock times, product versions, source links and unrecognized mixed labels.
    This is presentation only: callers must score and compare the original value.
    """
    if not isinstance(value, str):
        return value
    match = _MEASUREMENT.fullmatch(value)
    if match is None:
        return value
    return (_compact_expression(match["value"]) + (match["annotation"] or "")
            + match["space"])


def compact_reference(value):
    """Compact numeric ranges/limits and explicit target clauses, not prose."""
    if not isinstance(value, str):
        return value
    clauses = [_REFERENCE_CLAUSE.fullmatch(clause) for clause in value.split(";")]
    if not all(clauses):
        return value
    parts = []
    for clause in clauses:
        annotation = clause["annotation"] or ""
        if re.fullmatch(r"\s*\((?:goal|target)\s+[^()]+\)", annotation):
            start = annotation.index("(") + 1
            annotation = annotation[:start] + compact_reference(annotation[start:-1]) + ")"
        parts.append(clause["prefix"] + _compact_expression(clause["value"]) + annotation
                     + (clause["label"] or "") + clause["space"])
    return ";".join(parts)
