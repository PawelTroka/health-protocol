"""Compact laboratory tables without changing category, order, or result data.

Selected follow-up markers use a smaller table so their extra dates do not add
empty columns to the main panel. Renderers choose active dates for each group.
Unknown metrics remain in the main table until deliberately assigned elsewhere.
"""


_FOLLOWUP_GROUPS = {
    "Cardiac Health & Coagulation": (
        "Creatine Kinase (CK)", frozenset({"Creatine Kinase (CK)"}),
    ),
    "Metabolic Health": (
        "LDH & Uric Acid", frozenset({"LDH", "Uric Acid"}),
    ),
    "Micronutrients": (
        "Selenium", frozenset({"Selenium"}),
    ),
    "Immunology & Inflammation": (
        "Immune Markers & Antibodies",
        frozenset({
            "CRP (Conventional)", "Anti-TPO", "Anti-TG", "ASO", "IgA (Serum)",
            "Rheumatoid Factor (RF)", "Anti-CCP", "TSH Receptor Antibodies (TRAb)",
            "Complement C3", "Complement C4",
        }),
    ),
    "Hormonal Panel": (
        "Thyroid Hormones", frozenset({"TSH", "Free T3 (FT3)", "Free T4 (FT4)"}),
    ),
}


def lab_groups(category, rows):
    """Return nonempty ``{title, rows}`` groups retaining every original row.

    Titles are presentation only: callers must retain ``category`` for scoring,
    references, and notes. Rows keep their original order within each table, and
    a ``None`` title means the category heading already identifies the table.
    """
    rows = list(rows)
    if not rows:
        return []
    specification = _FOLLOWUP_GROUPS.get(category)
    if specification is None:
        return [{"title": None, "rows": rows}]

    followup_title, followup_names = specification
    main_rows = []
    followup_rows = []
    for row in rows:
        (followup_rows if row[0] in followup_names else main_rows).append(row)

    groups = []
    if main_rows:
        groups.append({
            "title": "Sex Hormones" if category == "Hormonal Panel" else None,
            "rows": main_rows,
        })
    if followup_rows:
        groups.append({"title": followup_title, "rows": followup_rows})
    return groups
