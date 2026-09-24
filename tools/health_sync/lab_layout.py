"""Compact laboratory tables without changing category, order, or result data.

Selected follow-up markers use a smaller table so their extra dates do not add
empty columns to the main panel. Renderers choose active dates for each group.
Unrecognized metrics remain visible until deliberately assigned to a group.
"""


ANA_ENA_MARKERS = (
    "DFS70", "AMA-M2", "Ribosomal Protein P", "Histones", "Nucleosomes", "dsDNA",
    "PCNA", "Centromere B", "Jo-1", "PM-Scl100", "Scl-70", "SS-B",
    "Ro-52 Recombinant", "SS-A Native (60kDa)", "Sm", "Sm, RNP/Sm",
)


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
            "tTG IgA", "DGP IgG",
            "Rheumatoid Factor (RF)", "Anti-CCP", "ANA IIFT", "TSH Receptor Antibodies (TRAb)",
            "Complement C3", "Complement C4",
        }),
    ),
    "Proteinogram": (
        "Concentrations",
        frozenset({
            "Total Protein", "Albumin (Concentration)", "Alpha-1 Globulin (Concentration)",
            "Alpha-2 Globulin (Concentration)", "Beta-1 Globulin (Concentration)",
            "Beta-2 Globulin (Concentration)", "Gamma Globulin (Concentration)",
        }),
    ),
}


_HORMONE_GROUPS = (
    ("Reproductive Hormones & Markers", frozenset({
        "Testosterone (Total)", "Testosterone (Free)", "DHT", "Estradiol (E2)",
        "Prolactin", "LH", "FSH", "SHBG", "Progesterone",
    })),
    ("Adrenal Hormones & Precursors", frozenset({
        "Cortisol", "DHEA-SO4", "17-OH Progesterone", "17-Hydroxypregnenolone",
    })),
    ("Growth Axis", frozenset({"IGF-1"})),
    ("Thyroid Function", frozenset({"TSH", "Free T3 (FT3)", "Free T4 (FT4)"})),
)


def lab_groups(category, rows):
    """Return nonempty ``{title, rows}`` groups retaining every original row.

    Titles are presentation only: callers must retain ``category`` for scoring,
    references, and notes. Rows keep their original order within each table, and
    a ``None`` title means the category heading already identifies the table.
    """
    rows = list(rows)
    if not rows:
        return []
    if category == "Immunology & Inflammation":
        immunoblot = [row for row in rows if row[0] in ANA_ENA_MARKERS]
        if immunoblot:
            remaining = [row for row in rows if row[0] not in ANA_ENA_MARKERS]
            return lab_groups(category, remaining) + [{"title": "ANA/ENA Immunoblot", "rows": immunoblot}]
    if category == "Hormonal Panel":
        groups = []
        known_names = set()
        for title, names in _HORMONE_GROUPS:
            known_names.update(names)
            selected = [row for row in rows if row[0] in names]
            if selected:
                groups.append({"title": title, "rows": selected})
        additional = [row for row in rows if row[0] not in known_names]
        if additional:
            groups.append({"title": "Additional Hormonal Markers", "rows": additional})
        return groups

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
            "title": None,
            "rows": main_rows,
        })
    if followup_rows:
        groups.append({"title": followup_title, "rows": followup_rows})
    return groups
