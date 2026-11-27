"""Compact laboratory tables without changing categories or result data.

Clinical groups and selected follow-up tables limit empty date columns while
keeping each marker's history together. Renderers choose active dates per group.
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
    "Infectious Diseases": (
        "SARS-CoV-2 RT-PCR", frozenset({"SARS-CoV-2 RT-PCR"}),
    ),
    "Urine Chemistry": (
        "Creatinine & Cystine",
        frozenset({"Urine Creatinine", "Urine Cystine/Creatinine"}),
    ),
    "Immunology & Inflammation": (
        "Immune Markers & Antibodies",
        frozenset({
            "CRP (Conventional)", "Anti-TPO", "Anti-TG", "ASO", "IgA (Serum)",
            "tTG IgA", "DGP IgG",
            "Exocrine Pancreatic Cell Antibodies IgG", "ASCA IgG",
            "Intestinal Goblet Cell Antibodies IgG", "Atypical ANCA (aANCA) IgG",
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


_MAIN_GROUPS = {
    "Hormonal Panel": ("Additional Hormonal Markers", _HORMONE_GROUPS),
    "Metabolic Health": ("Additional Metabolic Markers", (
        ("Glucose & Insulin", frozenset({"Glucose", "HbA1c", "Insulin"})),
        ("Liver Function", frozenset({
            "ALT", "AST", "GGTP", "Bilirubin Total", "Bilirubin Direct", "ALP", "Albumin",
        })),
        ("Kidney Function", frozenset({"Creatinine", "Cystatin C", "eGFR"})),
    )),
    "Cardiac Health & Coagulation": ("Additional Cardiac Markers", (
        ("Lipids & Apolipoproteins", frozenset({
            "Cholesterol LDL", "Cholesterol Non-HDL", "Cholesterol HDL", "Cholesterol Total",
            "Triglycerides", "Lipoprotein (a)", "ApoA1", "ApoB",
        })),
        ("Cardiac Markers", frozenset({"Homocysteine", "NT-proBNP", "Myoglobin"})),
        ("Coagulation", frozenset({
            "D-dimer", "Fibrinogen", "INR", "APTT", "PT", "Prothrombin Index",
        })),
    )),
    "Micronutrients": ("Additional Micronutrient Markers", (
        ("Fat-Soluble Vitamins", frozenset({"Vitamin D3", "Vitamin A", "Vitamin E"})),
        ("Water-Soluble Vitamins", frozenset({
            "Vitamin B12", "Folic Acid", "Vitamin B6", "Vitamin B1", "Vitamin C",
        })),
        ("Iron Status", frozenset({"Ferritin", "Iron", "Transferrin"})),
        ("Major Minerals & Electrolytes", frozenset({
            "Magnesium", "Potassium", "Sodium", "Calcium (Total)", "Fosfor",
        })),
        ("Trace-Element Markers", frozenset({
            "Ceruloplasmin", "Iodine (Serum)", "Zinc", "Copper (Serum)",
        })),
    )),
}


def _main_groups(category, rows):
    if not rows:
        return []
    specification = _MAIN_GROUPS.get(category)
    if specification is None:
        return [{"title": None, "rows": rows}]

    additional_title, definitions = specification
    groups = []
    known_names = set()
    for title, names in definitions:
        known_names.update(names)
        selected = [row for row in rows if row[0] in names]
        if selected:
            groups.append({"title": title, "rows": selected})
    additional = [row for row in rows if row[0] not in known_names]
    if additional:
        groups.append({"title": additional_title, "rows": additional})
    return groups


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
    specification = _FOLLOWUP_GROUPS.get(category)
    if specification is None:
        return _main_groups(category, rows)

    followup_title, followup_names = specification
    main_rows = []
    followup_rows = []
    for row in rows:
        (followup_rows if row[0] in followup_names else main_rows).append(row)

    groups = _main_groups(category, main_rows)
    if followup_rows:
        groups.append({"title": followup_title, "rows": followup_rows})
    return groups
