"""Source-faithful GA-map classifications, separate from generic health scoring.

Source: results/6399110771-sig.pdf, pages 1-6 (sample 2026-07-07).
The 336 chart-cell colors were checked against PDF vectors and rendered pixels.
Positions are ordered chart columns, not percentages or numerical risk units.
Only dark green is the reference-population range; light green is a distinct
lab association band. The report does not establish therapeutic targets.
"""

import re


# Each string spans positions -3, -2, -1, 0, +1, +2, +3.
# R = red, O = orange, L = light green, G = dark green, X = uncolored.
marker_bands = {
    300: "ROLGORX",
    206: "ROLGOXX",
    100: "XXOGOOO",
    302: "XRLGOOR",
    305: "RLLGOOR",
    331: "XROGLLO",
    201: "XROGLLX",
    202: "XXXGLLO",
    205: "XXLGLOO",
    207: "XXXGLLO",
    208: "XXOGLLL",
    209: "XXXGLLL",
    210: "XXOGLOO",
    306: "XXOGLLX",
    316: "XXXGLOO",
    323: "XXXGLOO",
    332: "XXOGLXX",
    103: "XXOGOOO",
    319: "XXXGLOR",
    320: "XXLGOOR",
    321: "XXXGLLO",
    325: "XXOGLLO",
    326: "XXXGLLO",
    327: "XXLGLOR",
    701: "XXOGLOR",
    304: "XXXGLOO",
    307: "XXXGLLX",
    308: "XXXGOXX",
    310: "XXXGLOX",
    312: "XXOGLOO",
    313: "XXXGLLL",
    314: "XRLGLLO",
    315: "XXOGLLO",
    317: "ROLGLXX",
    318: "ROLGLOX",
    330: "RLLGOOX",
    322: "XXXGLLO",
    324: "XXXGLOR",
    203: "XXXGLOR",
    500: "XXXGORR",
    502: "XXXGORR",
    504: "XXXGLRR",
    101: "XXLGLRX",
    311: "XXXGLLO",
    328: "XXXGLOO",
    329: "XXXGLOO",
    501: "XXXGRXX",
    601: "XXXGLXX",
}

# Validate the full identifier and name; an ID prefix alone is insufficient.
_MARKER_NAMES = {
    300: "Various Bacillota",
    206: "Various Bacteroidota",
    100: "Various Actinomycetota",
    302: "Various Bacilli",
    305: "Various Clostridia & Negativicutes",
    331: "Various Bacillales & Lachnospirales",
    201: "Alistipes spp.",
    202: "Alistipes onderdonkii",
    205: "Bacteroides xylanisolvens",
    207: "Bacteroides stercoris",
    208: "Bacteroides zoogleoformans",
    209: "Parabacteroides johnsonii",
    210: "Parabacteroides spp.",
    306: "[Clostridium] methylpentosum",
    316: "[Eubacterium] siraeum",
    323: "Ruminococcus bromii",
    332: "[Bacteroides] pectinophilus",
    103: "Bifidobacteriaceae",
    319: "Pediococcus & Ligilactobacillus ruminis",
    320: "Lactobacillaceae",
    321: "Lactobacillus acidophilus & L. acetotolerans",
    325: "Streptococcus agalactiae & Blautia wexlerae",
    326: "Streptococcus thermophilus, S. gordonii & S. sanguinis",
    327: "Streptococcus salivarius group & S. mutans",
    701: "Akkermansia muciniphila",
    304: "Catenibacterium mitsuokai",
    307: "Clostridium sp. L2-50",
    308: "Coprobacillus cateniformis",
    310: "Dialister spp.",
    312: "Dorea spp., Blautia faecicola & Mediterraneibacter massiliensis",
    313: "Holdemanella biformis",
    314: "Anaerobutyricum hallii & A. soehngenii",
    315: "Agathobacter rectalis",
    317: "Faecalibacterium prausnitzii",
    318: "Various Lachnospiraceae & Clostridiaceae",
    330: "Various Veillonellales, Lachnospirales & Eubacteriales",
    322: "Phascolarctobacterium faecium",
    324: "Ruminococcus gnavus",
    203: "Bacteroides fragilis",
    500: "Various Pseudomonadota",
    502: "Enterobacter, Cronobacter, Citrobacter & Salmonella",
    504: "Escherichia, Shigella, Citrobacter koseri",
    101: "Various Actinomycetaceae & Corynebacteriaceae",
    311: "Dialister invisus & Megasphaera micronuciformis",
    328: "Streptococcus mitis group",
    329: "Streptococcus viridans group",
    501: "Acinetobacter junii",
    601: "Metamycoplasma spp.",
}
_MARKER_IDS = {f"{key} - {name}": key for key, name in _MARKER_NAMES.items()}
_GROUP_NAMES = frozenset({
    "A1. Major intestinal bacterial groups",
    "A2. Diverse intestinal bacterial populations",
    "B1. Animal-product-associated bacteria",
    "C1. Complex-carbohydrate degraders",
    "C2. Lactic acid bacteria and probiotics",
    "D1. Akkermansia / mucosal-integrity marker",
    "D2. Main short-chain fatty acid producers",
    "E1. Ruminococcus gnavus marker",
    "E2. Bacteroides fragilis marker",
    "E3. Facultative anaerobes",
    "E4. Oral-colonizing bacteria",
    "E5. Urogenital, respiratory and skin-associated bacteria",
})

_BAND_STATUS = {
    "G": ("#32CD32", "🟢", "lab reference profile"),
    "L": ("#ADFF2F", "🟢", "small lab association"),
    "O": ("#FFA500", "🟠", "moderate lab association"),
    "R": ("#FF4500", "🔴", "high lab association"),
    "X": ("#808080", "⚪", "outside the lab's stated detection range"),
}
# These colors are the separate five-band index graphic on page 1.
_INDEX_STATUS = {
    1: ("#4CB814", "🟢", "no dysbiosis (lab classification)"),
    2: ("#7CCA53", "🟢", "no dysbiosis (lab classification)"),
    3: ("#FFB80E", "🟡", "mild dysbiosis (lab classification)"),
    4: ("#EC5514", "🟠", "severe dysbiosis (lab classification)"),
    5: ("#F21918", "🔴", "severe dysbiosis (lab classification)"),
}


def microbiota_status(marker_name, value):
    """Return source classification (hex, emoji, label), or None if unknown.

    This is a lab chart classification, not a generic score or trend rating.
    Only exact registered names and valid reported values are interpreted.
    """
    text = str(value).strip()
    if marker_name == "Dysbiosis Index":
        match = re.fullmatch(r"([1-5])(?: \((no|mild|severe) dysbiosis\))?", text)
        if not match:
            return None
        index = int(match.group(1))
        expected = "no" if index < 3 else "mild" if index == 3 else "severe"
        if match.group(2) is not None and match.group(2) != expected:
            return None
        return _INDEX_STATUS[index]
    if marker_name == "Bacterial Diversity":
        if text == "As expected":
            return "#32CD32", "🟢", "as expected (lab classification)"
        return None
    if marker_name in _GROUP_NAMES:
        if text == "Within reference profile":
            return "#32CD32", "🟢", "within reference profile (lab classification)"
        if text == "Slightly altered":
            return "#FFA500", "🟠", "slightly altered (lab classification)"
        return None
    marker_id = _MARKER_IDS.get(marker_name)
    if marker_id is None or not re.fullmatch(r"(?:0|[+-]?[1-3])", text):
        return None
    position = int(text)
    return _BAND_STATUS[marker_bands[marker_id][position + 3]]


def microbiota_reference(marker_name, originalref):
    """Return the concise source reference for a known marker."""
    if marker_name in _MARKER_IDS:
        return "0"
    if marker_name in _GROUP_NAMES:
        return "Within reference profile"
    if marker_name == "Dysbiosis Index":
        return "1–2"
    if marker_name == "Bacterial Diversity":
        return "As expected"
    return originalref
