"""Check the physical pillbox source against the active README, without generating files.

This is a deliberately bounded parser for this repository's slot and product-link
notation, not a Markdown parser or a medical/formulation validator. Unsupported
notation fails instead of silently skipping a physical entry. See tools/README.md.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import runpy
import sys


ROOT = Path(__file__).resolve().parents[1]
TIMINGS = {"Morning": "M", "Lunch": "L", "Before workout": "B",
           "During workout": "IW", "After workout": "A", "Evening": "E"}
PAGE_CODES = [
    [f"{prefix}.{number}" for number in range(start, stop + 1)]
    for prefix, start, stop in [
        ("M", 1, 9), ("M", 10, 18), ("L", 1, 9), ("L", 10, 18),
        ("E", 1, 9), ("E", 10, 18), ("B", 1, 9), ("A", 1, 9),
    ]
]
PHYSICAL_CODES = {code for page in PAGE_CODES for code in page}
ROW = re.compile(r"^- (?:[🥇🥈🥉] )?\*\*(?P<code>[^*]+)\*\*\s+(?P<body>.+)$")
SLOT_ROW = re.compile(
    r"^\s*(?:(?:[-+*>|]|\d+[.)])\s*)*(?:\[[ xX]\]\s*)?(?:[🥇🥈🥉]\s*)?"
    r"(?:\*\*|__|`)?[A-Z]{1,3}\.[1-9]\d*"
)
CODE = re.compile(r"(M|L|B|IW|A|E)\.([1-9]\d?)(?:-([1-9]\d?)|\.([12]))?\Z")
POWDER = re.compile(r"(?:M|L|B|IW|A|E)\.0(?:\.[1-9]\d*)*\Z")
PILL_COUNT = r"(?P<count>[1-9]\d*)\s*(?P<form>pills?|capsules?|tablets?|softgels?)"
DISPLAY_QTY = re.compile(PILL_COUNT + r"(?:\s*/\s*(?P<period>day|week))?\Z")
SOURCE_QTY = re.compile(r"(?<!\w)" + PILL_COUNT + r"\b")
SOURCE_FREQUENCY = re.compile(
    r"^(?:[—–-]\s*)?" + PILL_COUNT
    + r"\s*(?:/\s*(?P<period>day|week)\b|(?P<adverb>daily|weekly)\b|per\s+(?P<per>day|week)\b)"
)
QUANTITY = re.compile(
    r"(?<![\w.,])(?P<number>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"\s*(?P<unit>bln\s+CFU|mln\s+CFU|mln\s+heat-inactivated\s+cells|"
    r"bln|mln|mcg|µg|μg|mg|g|IU|CFU|GalU|FCC)\b"
)


class NotationError(ValueError):
    """Input does not use the notation this checker can verify."""


@dataclass(frozen=True)
class Entry:
    code: str
    label: str
    count: int
    empty: bool
    details: str
    line: int
    instructions: str
    total_count: int


def text(value: str) -> str:
    """Normalize whitespace and number/unit spacing, preserving wording and units."""
    value = QUANTITY.sub(lambda match: match["number"] + " ".join(match["unit"].split()), value)
    return " ".join(value.split())


def split_outer(value: str, separator: str) -> list[str]:
    """Split outside parentheses; reject unbalanced parenthetical identity/dose text."""
    depth = 0
    start = 0
    parts = []
    for index, char in enumerate(value):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise NotationError(f"unbalanced parentheses in {value!r}")
        elif char == separator and depth == 0:
            parts.append(value[start:index].strip())
            start = index + 1
    if depth:
        raise NotationError(f"unbalanced parentheses in {value!r}")
    parts.append(value[start:].strip())
    return parts


def annotations(value: str) -> tuple[str, list[str]]:
    """Separate quantity-bearing parentheses from product identity parentheses.

    For example, (Glycinate) remains in the name, while (Magnesium 72mg)
    is separately checked against the guide's dose or note field.
    """
    split_outer(value, "\0")  # Validate balanced parentheses first.
    depth = 0
    start = 0
    spans = []
    for index, char in enumerate(value):
        if char == "(":
            if depth == 0:
                start = index
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0 and QUANTITY.search(value[start + 1:index]):
                spans.append((start, index + 1))
    notes = [value[start + 1:stop - 1] for start, stop in spans]
    for start, stop in reversed(spans):
        value = value[:start] + " " + value[stop:]
    return text(value), notes


def headline(label: str) -> tuple[str, list[tuple[str, str]], list[str]]:
    """Return the exact product name, ordered component doses, and dose annotations."""
    label, notes = annotations(label)
    names = []
    doses = []
    for component in split_outer(label, "+"):
        match = QUANTITY.search(component)
        if not match:
            names.append(component)
            continue
        name = component[:match.start()].strip()
        dose = component[match.start():]
        # A non-quantified trailing brand stays part of the identity, e.g.
        # "Lactase 10,000FCC (Intoleran)" -> "Lactase (Intoleran)".
        trailing = re.search(r"\s+(\([^()]+\))$", dose)
        if trailing:
            name += " " + trailing[1]
            dose = dose[:trailing.start()]
        if not name:
            raise NotationError(f"missing product/component name in {label!r}")
        names.append(name)
        doses.append((text(name), text(dose)))
    if not all(names):
        raise NotationError(f"empty component in {label!r}")
    return text(" + ".join(names)), doses, notes


def product_link(body: str) -> tuple[str, str]:
    """Read one leading inline link, including a balanced, closed URL target."""
    match = re.match(r"\[([^\[\]\n]+)\]\(https?://", body)
    if not match:
        raise NotationError("expected a leading product link")
    depth = 1
    for index in range(match.end(), len(body)):
        char = body[index]
        if char.isspace():
            raise NotationError("unsupported whitespace inside product URL")
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                # Comparison links are not instructions or evidence of pill form.
                tail = re.sub(r"\[[^\]]*\]\([^)]*\)", "", body[index + 1:])
                return match[1], tail.strip()
    raise NotationError("product link is missing its closing parenthesis")


def check_visible_section(lines: list[str], start: int, stop: int) -> None:
    """Reject hidden/fenced active content; this grammar is a visible list only."""
    fence = None
    comment = False
    for index, line in enumerate(lines[:stop]):
        if index == start - 1 and (fence or comment):
            raise NotationError("README: Supplements and drugs heading is inside a fence/comment")
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if start <= index and (marker or "<!--" in line or "-->" in line):
            raise NotationError(f"README:{index + 1}: fences/comments are unsupported in the active supplement section")
        if marker and not comment:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        if not fence:
            for token in re.findall(r"<!--|-->", line):
                comment = token == "<!--"


def parse_readme(readme: str) -> dict[str, Entry]:
    lines = readme.splitlines()
    headings = [index for index, line in enumerate(lines)
                if re.fullmatch(r"## (?:\d+\. )?Supplements and drugs", line)]
    if len(headings) != 1:
        raise NotationError("expected one 'Supplements and drugs' level-two heading")
    start = headings[0] + 1
    stop = next((index for index in range(start, len(lines)) if lines[index].startswith("## ")), len(lines))
    check_visible_section(lines, start, stop)
    entries = {}
    timing = None
    order = {prefix: [] for prefix in TIMINGS.values()}
    for index in range(start, stop):
        line = lines[index]
        if line.startswith("### "):
            timing = TIMINGS.get(line[4:])
        match = ROW.fullmatch(line)
        if not match:
            if SLOT_ROW.match(line):
                raise NotationError(f"README:{index + 1}: unsupported slot-bearing row; use the canonical '- **code**' notation")
            continue
        code, body = match["code"], match["body"]
        if POWDER.fullmatch(code):
            if code.split(".")[0] != timing:
                raise NotationError(f"README:{index + 1}: powder {code} is under the wrong timing heading")
            continue
        parsed = CODE.fullmatch(code)
        if not parsed:
            raise NotationError(f"README:{index + 1}: unsupported physical code {code!r}")
        prefix, first, last, part = parsed.groups()
        if prefix != timing:
            raise NotationError(f"README:{index + 1}: {code} is under the wrong timing heading")
        first, last = int(first), int(last or first)
        if last < first:
            raise NotationError(f"README:{index + 1}: reversed range {code}")
        physical = [f"{prefix}.{number}" for number in range(first, last + 1)]
        if not set(physical) <= PHYSICAL_CODES:
            raise NotationError(f"README:{index + 1}: {code} is outside the physical organizer")
        multiplier = re.match(r"([1-9]\d*)x\s+", body)
        count = int(multiplier[1]) if multiplier else 1
        body = body[multiplier.end():] if multiplier else body
        empty = body == "(empty)"
        if empty:
            if multiplier or len(physical) != 1 or part:
                raise NotationError(f"README:{index + 1}: empty compartments need one whole-slot code")
            label = "EMPTY"
            instructions = ""
        else:
            try:
                label, instructions = product_link(body)
            except NotationError as error:
                raise NotationError(f"README:{index + 1}: {code}: {error}") from error
        if count % len(physical):
            raise NotationError(f"README:{index + 1}: {count} pills cannot be distributed equally across {code}")
        details = []
        following = index + 1
        while following < stop and lines[following].startswith("  "):
            details.append(re.sub(r"<sup>.*?</sup>", "", lines[following]))
            following += 1
        for physical_code in physical:
            leaf = f"{physical_code}.{part}" if part else physical_code
            if leaf in entries:
                raise NotationError(f"README:{index + 1}: duplicate entry {leaf}")
            entries[leaf] = Entry(leaf, label, count // len(physical), empty, " ".join(details),
                                  index + 1, instructions, count)
            order[prefix].append((int(physical_code.split(".")[1]), int(part or 0)))
    for prefix, slots in order.items():
        if slots != sorted(slots):
            raise NotationError(f"README: {prefix} entries are not in slot/subslot order")
    occupied = {code.rsplit(".", 1)[0] if code.count(".") == 2 else code for code in entries}
    if occupied != PHYSICAL_CODES:
        raise NotationError(f"README: missing physical compartments: {', '.join(sorted(PHYSICAL_CODES - occupied))}")
    for code in PHYSICAL_CODES:
        shared = [f"{code}.1", f"{code}.2"]
        if any(part in entries for part in shared):
            if code in entries or not all(part in entries for part in shared):
                raise NotationError(f"README: {code} must have either a whole-slot entry or both .1/.2 entries")
    return entries


def contains_phrase(phrase: str, source: str) -> bool:
    # An exact amount must not be a substring, denominator, range endpoint, or
    # bound. Whitespace around '/', a dash, or 'to' does not change that meaning.
    source = text(source)
    phrase = text(phrase)
    pattern = r"(?<![\w.,])" + re.escape(phrase) + r"(?![\w.])"
    trailing_count = next((match for match in QUANTITY.finditer(phrase)
                           if match.end() == len(phrase) and match["unit"] in {"bln", "mln"}), None)
    for match in re.finditer(pattern, source):
        before, after = source[:match.start()], source[match.end():]
        # A bare count is not a prefix alias for a qualified biological unit.
        if trailing_count and re.match(r"\s+(?:CFU|heat-inactivated\s+cells)\b", after):
            continue
        if re.search(r"[/<>≤≥≈~]\s*$|\d[\w.,]*\s*(?:[-‐‑‒–—−]|\bto)\s*$", before):
            continue
        if re.match(r"\s*(?:/|\bper\b|(?:[-‐‑‒–—−±]|\bto\b)\s*[~≈]?\s*\d)", after):
            continue
        return True
    return False


def check_quantity(entry: Entry, cell: dict) -> list[str]:
    """Validate every rendered qty string instead of trusting same_slot_count alone."""
    quantity = cell.get("qty", "")
    if not isinstance(quantity, str):
        return ["qty must be a string"]
    quantity = quantity.strip()
    if entry.empty:
        return [] if quantity in {"", "Available compartment"} else ["empty qty must be blank or 'Available compartment'"]
    if not quantity:
        return []
    match = DISPLAY_QTY.fullmatch(quantity)
    if not match:
        return [f"unsupported rendered qty {quantity!r}; expected a pill count with optional /day or /week"]
    errors = []
    count, form, period = int(match["count"]), match["form"].removesuffix("s"), match["period"]
    if count != entry.count:
        errors.append(f"rendered qty count: README {entry.count}; guide {count}")
    # Capsule/tablet/softgel identity cannot be recovered from a bare '3x'.
    # Check explicit active-entry forms, and disclose that limitation otherwise.
    forms = {source["form"].removesuffix("s") for source in SOURCE_QTY.finditer(entry.instructions)}
    if forms and forms != {form}:
        errors.append(f"rendered qty form {form!r} differs from explicit README form(s) {sorted(forms)}")
    if period:
        source = SOURCE_FREQUENCY.match(entry.instructions)
        source_period = None
        if source:
            source_period = source["period"] or source["per"] or {"daily": "day", "weekly": "week"}.get(source["adverb"])
        if (not source or source_period != period or int(source["count"]) != entry.total_count
                or source["form"].removesuffix("s") != form):
            errors.append(f"rendered qty /{period} lacks a matching explicit count/form/frequency instruction in the active README row")
    return errors


def check_product(entry: Entry, cell: dict) -> list[str]:
    errors = []
    name, expected_doses, source_notes = headline(entry.label)
    if text(cell.get("name", "")) != name:
        errors.append(f"name: README {name!r}; guide {cell.get('name')!r}")
    actual_dose, guide_notes = annotations(cell.get("dose", ""))
    if not actual_dose:
        errors.append("dose: guide has no primary dose")
    elif not QUANTITY.search(actual_dose):
        errors.append(f"dose: no supported quantity/unit in {actual_dose!r}")
    elif not expected_doses:
        # Some blend headlines carry no amount (e.g. Curcumin); in that case
        # the displayed dose must occur as an exact phrase in this row's details.
        if not contains_phrase(actual_dose, entry.details):
            errors.append(f"dose: {actual_dose!r} is absent from the README entry's formulation details")
    elif len(expected_doses) == 1:
        expected = expected_doses[0][1]
        # The guide uses bullets/newlines between constituents such as EPA/DHA.
        if text(actual_dose.replace("•", " ")) != expected:
            errors.append(f"dose: README {expected!r}; guide {actual_dose!r}")
    else:
        # Combination products retain ordered ingredient doses. The guide may
        # label a dose with an unambiguous suffix ("K1" for "Vitamin K1").
        parts = [part.strip() for part in re.split(r"[•\n]", cell.get("dose", "")) if part.strip()]
        if len(parts) != len(expected_doses):
            errors.append("dose: number of combination-product doses differs")
        else:
            for actual, (ingredient, expected) in zip(parts, expected_doses):
                actual = text(actual)
                match = QUANTITY.search(actual)
                label = actual[:match.start()].strip() if match else ""
                dose = actual[match.start():] if match else ""
                matches = [name for name, _ in expected_doses
                           if name == label or name.endswith(" " + label)] if label else []
                if dose != expected or (label and matches != [ingredient]):
                    errors.append(f"dose: expected {ingredient} {expected!r}; guide {actual!r}")
    guide_text = cell.get("dose", "") + " • " + cell.get("note", "")
    for annotation in source_notes:
        if not contains_phrase(annotation, guide_text):
            errors.append(f"dose annotation: README {annotation!r} is absent from guide dose/note")
    for annotation in guide_notes:
        if not contains_phrase(annotation, entry.label + " " + entry.details):
            errors.append(f"dose annotation: guide {annotation!r} is absent from the README entry")
    return errors


def validate(readme: str, pages: list[dict]) -> list[str]:
    """Return actionable parity errors. Neither input is modified."""
    errors = []
    try:
        entries = parse_readme(readme)
    except NotationError as error:
        return [str(error)]
    if not isinstance(pages, list) or len(pages) != 8:
        return ["guide: expected exactly eight pages"]
    leaves = {}
    for page_number, (page, codes) in enumerate(zip(pages, PAGE_CODES), 1):
        cells = page.get("cells", []) if isinstance(page, dict) else []
        if not isinstance(cells, list) or len(cells) != 9:
            errors.append(f"guide page {page_number}: expected nine physical cells")
            continue
        for position, (cell, code) in enumerate(zip(cells, codes), 1):
            if not isinstance(cell, dict):
                errors.append(f"guide page {page_number}, cell {position}: expected a cell dictionary")
                continue
            if cell.get("code") != code:
                errors.append(f"guide page {page_number}, cell {position}: expected slot {code}; got {cell.get('code')!r}")
            parts = cell.get("parts")
            if cell.get("kind") == "shared":
                if not isinstance(parts, list) or len(parts) != 2:
                    errors.append(f"{code}: shared cell needs exactly two parts")
                    continue
                expected_parts = [f"{code}.1", f"{code}.2"]
                if [part.get("code") if isinstance(part, dict) else None for part in parts] != expected_parts:
                    errors.append(f"{code}: shared part codes/order must be {expected_parts}")
            else:
                if parts is not None:
                    errors.append(f"{code}: non-shared cell must not contain parts")
                parts = [cell]
            for part in parts:
                if not isinstance(part, dict) or not isinstance(part.get("code"), str):
                    errors.append(f"{code}: invalid leaf entry")
                    continue
                leaf = part["code"]
                if leaf in leaves:
                    errors.append(f"{leaf}: duplicate guide entry")
                leaves[leaf] = part
    for code in sorted(entries.keys() - leaves.keys()):
        errors.append(f"{code}: README entry is missing from guide")
    for code in sorted(leaves.keys() - entries.keys()):
        errors.append(f"{code}: guide entry is absent from README")
    for code in sorted(entries.keys() & leaves.keys()):
        entry, cell = entries[code], leaves[code]
        count = cell.get("same_slot_count", 1)
        if type(count) is not int or count < 1 or count != entry.count:
            errors.append(f"{code}: multiplier: README {entry.count}x; guide {count!r}x")
        kind = cell.get("kind", "active")
        if not isinstance(kind, str) or kind not in {"active", "rx", "warning", "empty"}:
            errors.append(f"{code}: unsupported leaf kind {kind!r}")
        if (kind == "empty") != entry.empty:
            errors.append(f"{code}: empty/occupied state differs")
            continue
        errors.extend(f"{code}: {error}" for error in check_quantity(entry, cell))
        if not all(isinstance(cell.get(field, ""), str) for field in ("name", "dose", "note")):
            errors.append(f"{code}: name/dose/note must be strings")
            continue
        if entry.empty:
            if cell.get("name") != "EMPTY" or cell.get("dose") or cell.get("note"):
                errors.append(f"{code}: an empty cell must say EMPTY and have no dose/note")
            continue
        try:
            errors.extend(f"{code} (README:{entry.line}): {error}" for error in check_product(entry, cell))
        except NotationError as error:
            errors.append(f"{code}: {error}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="trusted repository checkout to check (default: this script's repository)")
    args = parser.parse_args(argv)
    try:
        readme = (args.root / "README.md").read_text(encoding="utf-8")
        # We do not call build_document(). run_path still executes top-level
        # Python; --root must point to trusted source, not untrusted input.
        pages = runpy.run_path(str(args.root / "tools/generate_pillbox_guide.py"))["PAGES"]
        errors = validate(readme, pages)
    except (OSError, ImportError, KeyError, SyntaxError) as error:
        print(f"Unable to check pillbox source: {error}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Pillbox parity FAILED ({len(errors)} errors).", file=sys.stderr)
        return 1
    print("Pillbox parity OK: 8 pages, 72 physical cells; names, headline doses, counts, qty fields and empty states agree.")
    print("Scope: source data only; unstated pill forms, note prose, conditions, icons and rendered DOCX still require review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
