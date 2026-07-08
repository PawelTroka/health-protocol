import re

def lerp(a, b, t):
    return int(a + (b - a) * t)

def get_color_hex(score):
    # Palette Definition
    # 0.0 - 1.0: INSIDE RANGE (Blue -> Green)
    # 1.0 - 2.0: JUST OUTSIDE (Yellow)
    # 2.0 - 3.0: SIGNIFICANTLY OUTSIDE (Orange)
    # > 3.0: CRITICAL (Red)

    stops = [
        (0.00, (0, 0, 139), "🔵"),      # Dark Blue (Optimal)
        (0.40, (0, 191, 255), "🔵"),    # Light Blue (Good)
        (0.70, (0, 128, 0), "🟢"),      # Dark Green (Normal)
        (1.00, (50, 205, 50), "🟢"),    # Light Green (Limit of Normal)
        (1.20, (255, 215, 0), "🟡"),    # Yellow (Just Outside)
        (2.00, (255, 165, 0), "🟠"),    # Orange (Significant Deviation)
        (3.00, (255, 69, 0), "🟠"),     # Dark Orange (High Deviation)
        (3.50, (220, 53, 69), "🔴"),    # Red (Critical)
        (4.50, (139, 0, 0), "🔴")       # Dark Red
    ]

    if score < 0: score = 0
    
    # Find the two stops we are between
    lower = stops[0]
    upper = stops[-1]
    
    for s in stops:
        if s[0] <= score:
            lower = s
        if s[0] >= score:
            upper = s
            break
            
    # Interpolate Color
    if lower == upper:
        r, g, b = lower[1]
    else:
        t = (score - lower[0]) / (upper[0] - lower[0])
        c1 = lower[1]
        c2 = upper[1]
        r = lerp(c1[0], c2[0], t)
        g = lerp(c1[1], c2[1], t)
        b = lerp(c1[2], c2[2], t)

    hex_color = f"#{r:02x}{g:02x}{b:02x}"
    
    # Determine Emoji strictly by zone
    if score <= 0.6:
        emoji = "🔵" # Optimal/Good
    elif score <= 1.00001:
        emoji = "🟢" # Normal
    elif score <= 2.0:
        emoji = "🟡" # Caution (Widened)
    elif score <= 3.0:
        emoji = "🟠" # Warning (Shifted)
    else:
        emoji = "🔴" # Critical (Shifted)
    
    return hex_color, emoji

def get_direction(val_str, ref_range):
    if val_str in ["-", "—", None, ""]:
        return None
        
    val_clean = re.sub(r'[^\d.<>]', '', val_str.split('(')[0]) 
    if not val_clean: return None
    
    try:
        val = float(re.sub(r'[<> ]', '', val_clean))
    except ValueError:
        return None

    # Parse Reference Range
    m_range = re.match(r'([\d.]+)\s*-\s*([\d.]+)', ref_range)
    if m_range:
        low = float(m_range.group(1))
        high = float(m_range.group(2))
        if val < low: return "↓"
        if val > high: return "↑"
        return ""

    m_less = re.match(r'<\s*([\d.]+)', ref_range)
    if m_less:
        limit = float(m_less.group(1))
        if val > limit: return "↑"
        return ""

    m_more = re.match(r'>\s*([\d.]+)', ref_range)
    if m_more:
        limit = float(m_more.group(1))
        if val < limit: return "↓"
        return ""
            
    return ""

def calculate_score(val_str, ref_range):
    if val_str in ["-", "—", None, ""]:
        return None
        
    # Textual Perfect Matches
    text_val = val_str.lower().strip()
    if text_val in ["non-reactive", "negative", "not detected", "absent"]:
        return 0.0

    # Handle exact matches like "< 30.0" and "< 30.0"
    if val_str.strip() == ref_range.strip() and "<" in val_str:
        return 0.0

    val_clean = re.sub(r'[^\d.<>-]', '', val_str.split('(')[0]) 
    if not val_clean: return None
    
    try:
        val = float(re.sub(r'[<> ]', '', val_clean))
    except ValueError:
        return None

    m_range = re.match(r'([-\d.]+)\s*-\s*([-\d.]+)', ref_range)
    if m_range:
        low = float(m_range.group(1))
        high = float(m_range.group(2))
        target = (low + high) / 2.0
        half_width = (high - low) / 2.0
        if half_width == 0: return 0
        dist = abs(val - target) 
        score = dist / half_width 
        return score

    m_less = re.match(r'<\s*([-\d.]+)', ref_range)
    if m_less:
        limit = float(m_less.group(1))
        if val <= limit:
            return (val / limit) * 1.0 if limit != 0 else 0.0
        else:
            return 1.0 + (val - limit) / limit if limit != 0 else 1.0

    m_more = re.match(r'>\s*([-\d.]+)', ref_range)
    if m_more:
        limit = float(m_more.group(1))
        optimum = limit * 2.0
        if val >= limit:
            if val >= optimum: return 0.0
            return 1.0 - ((val - limit) / (optimum - limit))
        else:
            return 1.0 + ((limit - val) / limit) if limit != 0 else 1.0
            
    return 0.5 

def format_cell_html(val, ref):
    score = calculate_score(val, ref)
    if score is None:
        return val
    color, _ = get_color_hex(score)
    arrow = get_direction(val, ref)
    suffix = f" {arrow}" if arrow else ""
    return f'<span style="color:{color}; font-weight:bold;">{val}{suffix}</span>'

def format_cell_md(val, ref):
    score = calculate_score(val, ref)
    if score is None:
        return val
    _, emoji = get_color_hex(score)
    arrow = get_direction(val, ref)
    suffix = f" {arrow}" if arrow else ""
    return f'{emoji} {val}{suffix}'

def format_urinalysis_value(val_str, ref_range):
    if val_str in ["-", "—", None, ""]:
        return None
    
    # Qualitative / Textual Checks
    text_val = val_str.lower().strip()
    
    # Optimal / Perfect values (Blue)
    optimal_terms = [
        "not detected", "absent", "normal", "clear", "negative", "non-reactive", "neg", 
        "light yellow", "yellow", "pale yellow", "słomkowy"
    ]
    if any(term in text_val for term in optimal_terms):
        return "#00008b", "🔵" # Dark Blue (Optimal)
        
    # Bad / Abnormal values (Red)
    bad_terms = ["present", "detected", "cloudy", "turbid", "bloody", "obecne", "liczne", "mętny", "krwisty"]
    if any(term in text_val for term in bad_terms):
        return "#dc3545", "🔴" # Red

    # Numeric checks for specific gravity, ph etc.
    try:
        # Simple float parse
        val = float(re.sub(r'[^\d.]', '', val_str.replace(',', '.')))
        
        # pH
        if "5 - 8" in ref_range:
            if 5.0 <= val <= 8.0: return "#006400", "🟢"
            return "#ffa500", "🟠"
            
        # Specific Gravity
        if "1.005 - 1.03" in ref_range:
            if 1.005 <= val <= 1.030: return "#006400", "🟢"
            return "#ffa500", "🟠"
            
    except:
        pass

    return "#000000", "" # Default black, no emoji

def format_cell_html_urine(val, ref):
    result = format_urinalysis_value(val, ref)
    if result is None:
        return val
    color, _ = result
    return f'<span style="color:{color}; font-weight:bold;">{val}</span>'

def format_cell_md_urine(val, ref):
    result = format_urinalysis_value(val, ref)
    if result is None:
        return val
    _, emoji = result
    return f'{emoji} {val}'

# Data Reorganized
# Using "-" for missing values as requested
date_columns = ["2026-07", "2026-01", "2025-05", "2025-01"]
missing_values = {"-", None, ""}

def split_result_row(row):
    expected_len = 1 + len(date_columns) + 2
    if len(row) != expected_len:
        raise ValueError(f"Unexpected row shape for {row[0]!r}: expected {expected_len}, got {len(row)}")
    values = row[1:1 + len(date_columns)]
    unit = row[1 + len(date_columns)]
    ref = row[2 + len(date_columns)]
    return row[0], values, unit, ref

def active_date_indexes(rows):
    return [
        idx
        for idx in range(len(date_columns))
        if any(split_result_row(row)[1][idx] not in missing_values for row in rows)
    ]

trend_definitions = {
    "Breakthrough": {
        "description": "Vast improvement",
        "emoji": "💎",
    },
    "Major Improvement": {
        "description": "Strong improvement",
        "emoji": "🔵",
    },
    "Improvement": {
        "description": "Slight improvement",
        "emoji": "🟢",
    },
    "Stable": {
        "description": "Mostly stable",
        "emoji": "⚪",
    },
    "Mild Worsening": {
        "description": "Slight worsening",
        "emoji": "🟡",
    },
    "Major Decline": {
        "description": "Strong worsening",
        "emoji": "🟠",
    },
    "Critical Decline": {
        "description": "Severe worsening",
        "emoji": "🔴",
    },
}

slight_improvement_score_delta = 0.06
slight_worsening_score_delta = 0.12
slight_directional_improvement_percent_delta = 0.075

def trend_score(value, ref, category):
    if value in missing_values or ref in missing_values or ref == "-":
        return None

    score = calculate_score(value, ref)
    if score is not None:
        return score

    text_value = value.lower().strip()
    optimal_terms = [
        "not detected", "absent", "normal", "clear", "negative", "non-reactive", "neg",
        "light yellow", "yellow", "pale yellow"
    ]
    bad_terms = ["present", "detected", "cloudy", "turbid", "bloody"]

    if any(term in text_value for term in optimal_terms):
        return 0.0
    if any(term in text_value for term in bad_terms):
        return 3.0

    return None

def numeric_value(value):
    if value in missing_values:
        return None

    val_clean = re.sub(r'[^\d.<>-]', '', value.split('(')[0])
    if not val_clean:
        return None

    try:
        return float(re.sub(r'[<> ]', '', val_clean))
    except ValueError:
        return None

def directional_percent_delta(current, previous, ref):
    current_val = numeric_value(current)
    previous_val = numeric_value(previous)
    if current_val is None or previous_val is None or previous_val == 0:
        return None

    if re.match(r'<\s*([-\d.]+)', ref):
        return (previous_val - current_val) / abs(previous_val)

    if re.match(r'>\s*([-\d.]+)', ref):
        return (current_val - previous_val) / abs(previous_val)

    return None

def classify_trend(values, ref, category):
    comparable = []
    for value in values:
        score = trend_score(value, ref, category)
        if score is not None:
            comparable.append((value, score))
        if len(comparable) == 2:
            break

    if len(comparable) < 2:
        return None

    # Scores are health-distance values: lower is better, higher is worse.
    current_value, current_score = comparable[0]
    previous_value, previous_score = comparable[1]
    delta = previous_score - current_score
    percent_delta = directional_percent_delta(current_value, previous_value, ref)

    if delta >= 1.00:
        return "Breakthrough"
    if delta >= 0.30:
        return "Major Improvement"

    if delta <= -1.00:
        return "Critical Decline"
    if delta <= -0.30:
        return "Major Decline"

    if delta >= slight_improvement_score_delta:
        return "Improvement"
    if percent_delta is not None and percent_delta >= slight_directional_improvement_percent_delta:
        return "Improvement"

    if delta <= -slight_worsening_score_delta:
        return "Mild Worsening"

    return "Stable"

def format_trend_html(values, ref, category):
    trend = classify_trend(values, ref, category)
    if trend is None:
        return "-"

    definition = trend_definitions[trend]
    return definition["emoji"]

def format_trend_md(values, ref, category):
    trend = classify_trend(values, ref, category)
    if trend is None:
        return "-"

    definition = trend_definitions[trend]
    return definition["emoji"]

def category_has_trends(rows, category):
    for row in rows:
        _, values, _, ref = split_result_row(row)
        if classify_trend(values, ref, category) is not None:
            return True
    return False

def note_numbers(category, row_name, target, date=None):
    numbers = []
    for number, note in enumerate(result_notes.get(category, []), start=1):
        for marker in note["markers"]:
            rows = marker.get("rows", [marker.get("row")])
            targets = marker.get("targets", [marker.get("target")])
            dates = marker.get("dates")

            if row_name not in rows or target not in targets:
                continue
            if target == "value" and dates is not None and date not in dates:
                continue

            numbers.append(number)
            break
    return numbers

def note_sup_html(numbers):
    if not numbers:
        return ""
    return f"<sup>{','.join(str(number) for number in numbers)}</sup>"

def add_note_sup_html(cell, numbers):
    sup = note_sup_html(numbers)
    if not sup:
        return cell

    match = re.match(r'^(\S+)(.*)$', cell)
    if match:
        leading, rest = match.groups()
        if leading in {"🔵", "🟢", "🟡", "🟠", "🔴", "⚪", "💎"}:
            return f"{leading}{sup}{rest}"

    cell = cell.replace(" ↑</span>", f"{sup} ↑</span>")
    cell = cell.replace(" ↓</span>", f"{sup} ↓</span>")
    if sup in cell:
        return cell

    return f"{cell}{sup}"

def note_sup_md(numbers):
    if not numbers:
        return ""
    return f"<sup>{','.join(str(number) for number in numbers)}</sup>"

def add_note_sup_md(cell, numbers):
    sup = note_sup_md(numbers)
    if not sup:
        return cell

    match = re.match(r'^(\S+)(\s+.*)$', cell)
    if match:
        leading, rest = match.groups()
        if leading in {"🔵", "🟢", "🟡", "🟠", "🔴", "⚪", "💎"}:
            return f"{leading}{sup}{rest}"

    return f"{cell}{sup}"

def render_result_notes_html(category):
    notes = result_notes.get(category, [])
    if not notes:
        return ""

    html = "<div class='table-notes'>"
    for number, note in enumerate(notes, start=1):
        html += f"<p><sup>{number}</sup> {note['text']}</p>"
    html += "</div>"
    return html

def render_result_notes_md(category):
    notes = result_notes.get(category, [])
    if not notes:
        return ""

    md = "\n**Notes:**\n"
    for number, note in enumerate(notes, start=1):
        md += f"<sup>{number}</sup> {note['text']}\n"
    return md

data = {
    "Biological Age": [
        ("Biological Age", "-", "29.0", "-", "-", "years", "< 34.9"),
        ("Chronological Age", "-", "34.9", "-", "-", "years", "-"),
        ("Age Difference", "-", "-5.9", "-", "-", "years", "-10.0 - 0.0"),
        ("Relative Difference", "-", "-16.9", "-", "-", "%", "-30.0 - 0.0"),
        ("Relative Difference (>18)", "-", "-34.9", "-", "-", "%", "-50.0 - 0.0")
    ],
    "Morphology": [
        ("Hemoglobin", "15.80", "15.40", "16.00", "15.70", "g/dL", "13.0 - 18.0"),
        ("Hematocrit", "45.9", "45.9", "46.6", "47.1", "%", "40 - 52"),
        ("Erythrocytes", "5.3", "5.20", "5.37", "5.31", "10^6/ul", "4.5 - 6.5"),
        ("MCV", "86.8", "87.8", "86.8", "88.7", "fL", "80 - 98"),
        ("MCH", "29.9", "29.4", "29.8", "29.6", "pg", "27 - 32"),
        ("MCHC", "34.4", "33.6", "34.3", "33.3", "g/dL", "31 - 37"),
        ("RDW-CV", "13.4", "12.5", "12.9", "12.9", "%", "11.5 - 14.5"),
        ("RDW-SD", "42.0", "40.8", "-", "41.7", "fL", "35.1 - 43.9"),
        ("Leukocytes", "7.0", "7.7", "5.5", "9.1", "10^3/ul", "4.0 - 11.0"),
        ("Neutrophils", "2.7", "2.3", "2.22", "3.83", "10^9/L", "1.9 - 7"),
        ("Neutrophils %", "39.10", "30.50", "40.30", "42.10", "%", "45 - 70"),
        ("Lymphocytes", "2.9", "3.9", "2.3", "3.6", "10^9/L", "1.5 - 4.5"),
        ("Lymphocytes %", "41.6", "50.3", "40.9", "39.5", "%", "25 - 45"),
        ("Monocytes", "0.7", "0.9", "0.56", "1.01", "10^9/L", "0.1 - 0.9"),
        ("Monocytes %", "10.4", "11.9", "10.1", "11.1", "%", "2 - 9"),
        ("Eosinophils", "0.5", "0.5", "0.42", "0.55", "10^9/L", "< 0.5"),
        ("Eosinophils %", "7.7", "6.5", "7.6", "6.0", "%", "0.00 - 5.00"),
        ("Basophils", "0.1", "0.1", "0.05", "0.08", "10^9/L", "0.00 - 0.10"),
        ("Basophils %", "0.9", "0.7", "0.9", "0.9", "%", "0.00 - 1.00"),
        ("Immature Granulocytes", "0.0", "0.0", "0.01", "0.04", "10^9/L", "< 0.04"),
        ("Immature Granulocytes %", "0.3", "0.1", "0.2", "0.4", "%", "0.0 - 0.5"),
        ("Platelets", "230.0", "265", "228", "305", "10^3/ul", "150 - 400"),
        ("PCT", "0.25", "0.30", "-", "0.31", "%", "0.12 - 0.36"),
        ("PDW", "14.1", "13.8", "-", "10.9", "fL", "9.8 - 16.1"),
        ("MPV", "11.0", "11.3", "10.6", "10.0", "fL", "7 - 12"),
        ("P-LCR", "33.4", "35.3", "-", "-", "%", "19.2 - 47")
    ],
    "Urinalysis (General)": [
        ("Color", "light yellow", "light yellow", "light yellow", "-", "", "-"),
        ("Transparency", "clear", "clear", "clear", "-", "", "clear"),
        ("Specific Gravity", "1.008", "1.015", "1.015", "-", "g/ml", "1.005 - 1.03"),
        ("pH", "5.5", "5.5", "6.0", "-", "", "5 - 8"),
        ("Protein", "not detected", "not detected", "not detected", "-", "mg/dL", "not detected"),
        ("Glucose", "not detected", "not detected", "not detected", "-", "mg/dL", "not detected"),
        ("Bilirubin", "not detected", "not detected", "not detected", "-", "", "not detected"),
        ("Urobilinogen", "normal", "normal", "normal", "-", "mg/dL", "normal"),
        ("Ketones", "not detected", "not detected", "not detected", "-", "mg/dL", "not detected"),
        ("Nitrites", "not detected", "not detected", "not detected", "-", "", "not detected"),
        ("Leukocytes (Strip)", "not detected", "not detected", "not detected", "-", "leu/uL", "not detected"),
        ("Erythrocytes (Strip)", "not detected", "not detected", "not detected", "-", "ery/uL", "not detected")
    ],
    "Urinalysis (Sediment)": [
        ("Squamous Epithelium", "-", "< 30.0", "rare", "-", "/uL", "< 30.0"),
        ("Transitional Epithelium", "-", "< 6.0", "rare", "-", "/uL", "< 6.0"),
        ("Renal Epithelium", "-", "< 1.0", "absent", "-", "/uL", "< 1.0"),
        ("Leukocytes", "-", "< 20.0", "0-8", "-", "/uL", "< 20.0"),
        ("Leukocyte Aggregates", "-", "absent", "-", "-", "", "absent"),
        ("Erythrocytes", "-", "< 20.0", "0-3", "-", "/uL", "< 20.0"),
        ("Hyaline Casts", "-", "< 2.0", "absent", "-", "/uL", "< 2.0"),
        ("Pathological Casts", "-", "absent", "absent", "-", "", "absent"),
        ("Crystals", "-", "absent", "few", "-", "", "absent"),
        ("Bacteria", "-", "< 30.0", "absent", "-", "/uL", "< 30.0"),
        ("Yeast", "-", "< 30.0", "absent", "-", "/uL", "< 30.0"),
        ("Sperm", "-", "< 10.0", "-", "-", "/uL", "< 10.0"),
        ("Mucus", "-", "< 10.0", "rare", "-", "/uL", "< 10.0")
    ],
    "Urine Chemistry": [
        ("Urine Creatinine", "63.1", "-", "-", "-", "mg/dL", "39.0 - 259.0"),
        ("Urine Albumin (Microalbuminuria)", "<3", "-", "-", "-", "mg/l", "< 20.0"),
        ("Urine Protein", "0.06", "-", "-", "-", "g/L", "< 0.15"),
        ("Urine Amylase", "98", "-", "-", "-", "U/L", "16 - 491"),
        ("Urine Potassium", "7.12", "-", "-", "-", "mmol/l", "20.00 - 80.00"),
        ("Urine Sodium", "15.5", "-", "-", "-", "mmol/l", "54.0 - 150.0"),
        ("Urine Urea", "2249", "-", "-", "-", "mg/dl", "1714 - 3565"),
        ("Urine Calcium", "11.3", "-", "-", "-", "mg/dl", "6.8 - 21.3"),
        ("Urine Magnesium", "7.1", "-", "-", "-", "mg/dl", "0.4 - 1.4"),
        ("Urine Phosphate", "26.40", "-", "-", "-", "mg/dl", "40.00 - 136.00"),
        ("Urine Chloride", "11", "-", "-", "-", "mmol/L", "46 - 168")
    ],
    "Metabolic Health": [
        ("Glucose", "86", "84", "89", "70", "mg/dl", "70 - 99"),
        ("HbA1c", "5.3", "5.18", "5.3", "-", "%", "4.8 - 5.9"),
        ("Insulin", "8.6", "11.2", "8.9", "-", "uU/mL", "2.6 - 24.9"),
        ("ALT", "18", "12", "14", "-", "U/L", "< 41"),
        ("AST", "33", "20", "25", "-", "U/L", "< 40"),
        ("GGTP", "18", "14", "18", "18", "U/L", "< 60"),
        ("Bilirubin Total", "0.61", "0.20", "0.39", "-", "mg/dL", "< 1.20"),
        ("Bilirubin Direct", "0.33", "-", "-", "-", "mg/dL", "< 0.3"),
        ("ALP", "76", "-", "89", "-", "U/L", "40 - 129"),
        ("LDH", "152", "123", "-", "-", "U/L", "< 250"),
        ("Albumin", "48.90", "-", "-", "-", "g/l", "35.00 - 52.00"),
        ("Creatinine", "0.96", "0.93", "0.93", "-", "mg/dl", "0.70 - 1.20"),
        ("eGFR", "101.5", ">60", ">60", "-", "ml/min/1.73m^2", "> 60.0"),
        ("Uric Acid", "3.8", "3.2", "4.1", "-", "mg/dl", "3.4 - 7.0")
    ],
    "Cardiac Health & Coagulation": [
        ("Cholesterol LDL", "68", "76", "74", "75", "mg/dl", "< 115"),
        ("Cholesterol Non-HDL", "81", "96", "-", "-", "mg/dL", "< 130"),
        ("Cholesterol HDL", "38", "43", "35", "-", "mg/dL", "> 40"),
        ("Cholesterol Total", "118", "138", "119", "-", "mg/dL", "< 190"),
        ("Triglycerides", "57", "98", "48", "56", "mg/dL", "< 150"),
        ("Lipoprotein (a)", "7.16", "< 7.00", "-", "-", "nmol/l", "< 75"),
        ("Homocysteine", "-", "6.74", "6.60", "6.50", "umol/l", "< 15.0"),
        ("NT-proBNP", "14.6", "22.9", "22.9", "< 10.0", "pg/ml", "< 125"),
        ("Creatine Kinase (CK)", "222", "153", "-", "-", "U/L", "20 - 200"),
        ("Myoglobin", "-", "24.30", "42.60", "-", "ng/ml", "23 - 72"),
        ("D-dimer", "-", "< 190", "< 190", "< 190", "ng/ml", "< 500"),
        ("Fibrinogen", "3.1", "-", "-", "-", "g/l", "2.0 - 4.0"),
        ("INR", "0.98", "0.94", "-", "-", "", "0.80 - 1.20"),
        ("APTT", "-", "31.6", "-", "-", "sec", "22.0 - 34.0"),
        ("PT", "12.4", "11.4", "-", "-", "sec", "10.0 - 15.0"),
        ("Prothrombin Index", "102", "-", "-", "-", "%", "80 - 120")
    ],
    "Micronutrients": [
        ("Vitamin D3", "46.0", "26.3", "52.5", "37.9", "ng/ml", "30 - 50"),
        ("Vitamin B12", "859", "562", "928", "-", "pg/ml", "197 - 771"),
        ("Ferritin", "42", "78", "134", "-", "ng/ml", "30 - 400"),
        ("Iron", "125", "41", "98", "-", "ug/dl", "59 - 150"),
        ("Transferrin", "3.00", "3.00", "-", "-", "g/l", "2.00 - 3.60"),
        ("Ceruloplasmin", "0.20", "-", "-", "-", "g/L", "0.15 - 0.30"),
        ("Folic Acid", "21.1", "8.5", "17.0", "-", "ng/ml", "3.9 - 26.8"),
        ("Magnesium", "2.07", "1.90", "2.13", "-", "mg/dl", "1.60 - 2.60"),
        ("Potassium", "4.0", "4.2", "3.8", "-", "mmol/l", "3.5 - 5.1"),
        ("Sodium", "139", "140", "-", "-", "mmol/l", "136 - 145"),
        ("Calcium (Total)", "9.58", "9.88", "9.88", "-", "mg/dL", "8.60 - 10.00"),
        ("Fosfor", "3.10", "4.83", "3.7", "-", "mg/dL", "2.5 - 4.5"),
        ("Zinc", "-", "13.90", "22.07", "-", "umol/l", "9 - 18"),
        ("Vitamin B6", "-", "-", "58.6", "-", "ug/l", "5.7 - 55.1"),
        ("Vitamin B1", "-", "33.6", "69.1", "-", "ug/l", "33.1 - 60.7"),
        ("Vitamin A", "-", "0.47", "0.47", "-", "mg/l", "0.3 - 0.7"),
        ("Vitamin E", "-", "11.0", "9.5", "-", "mg/l", "5 - 20"),
        ("Vitamin C", "-", "4.6", "-", "-", "ug/ml", "4 - 15")
    ],
    "Immunology & Inflammation": [
        ("CRP (hs)", "0.611", "0.448", "< 0.15", "not detected", "mg/l", "< 5.0"),
        ("IL-6", "-", "< 1.5", "1.6", "-", "pg/ml", "< 7.0"),
        ("Calprotectin", "-", "0.43", "0.41", "-", "ug/mL", "< 2.0"),
        ("Anti-TPO", "<9", "12.30", "-", "-", "IU/ml", "< 34.0"),
        ("Anti-TG", "16.80", "13.10", "-", "-", "IU/ml", "< 115.0"),
        ("ASO", "-", "209", "-", "-", "IU/mL", "< 200")
    ],
    "Tumor Markers": [
        ("PSA Total", "0.15", "0.16", "0.195", "-", "ng/mL", "< 4.0"),
        ("PSA Free", "0.033", "-", "-", "-", "ng/mL", "-"),
        ("PSA Free/Total Ratio", "22.05", "-", "-", "-", "%", "> 25"),
        ("CEA", "3.0", "2.9", "2.2", "-", "ng/ml", "< 5.0"),
        ("AFP (ng/ml)", "1.99", "2.84", "-", "-", "ng/ml", "< 7.0"),
        ("AFP (IU/ml)", "-", "-", "2.0", "-", "IU/ml", "< 5.8"),
        ("CA 19-9", "4.6", "3.8", "5.5", "-", "U/ml", "< 34.0"),
        ("S-100", "-", "0.09", "0.05", "-", "ug/l", "< 0.15")
    ],
    "Infectious Diseases": [
        ("HIV", "Non-reactive", "Non-reactive", "Non-reactive", "Non-reactive", "Status", "Non-reactive"),
        ("Anti-HBs", "181.00", "221.00", "203.00", "-", "IU/l", "> 10"),
        ("HCV", "Non-reactive", "Non-reactive", "Non-reactive", "Non-reactive", "Status", "Non-reactive"),
        ("Syphilis (WR)", "Non-reactive", "Non-reactive", "Non-reactive", "-", "Status", "Non-reactive"),
        ("Chlamydia IgG", "< 5.0", "< 5.0", "< 5.0", "negative", "AU/ml", "< 9"),
        ("Chlamydia IgM", "-", "2.7", "2.7", "2.7", "Status", "< 9"),
        ("HSV IgG", "-", "0.79", "1.35", "1.7", "Index", "< 0.9"),
        ("HSV IgM", "-", "< 0.5", "negative", "negative", "Index", "< 0.9")
    ],
    "Toxicology (Urine)": [
        ("Arsenic", "-", "11.8", "30.8", "-", "ug/l", "< 15.0"),
        ("Cadmium", "-", "0.1", "0.1", "-", "ug/l", "< 0.8"),
        ("Chromium", "-", "1.0", "0.2", "-", "ug/l", "< 0.6"),
        ("Nickel", "-", "0.5", "0.2", "-", "ug/l", "< 3.0"),
        ("Copper", "-", "4.26", "3.15", "-", "ug/l", "2.0 - 80.0"),
        ("Glyphosate", "-", "< 0.60", "-", "-", "ng/ml", "< 1.40")
    ],
    "Stool Analysis": [
        ("Stool pH", "8.0", "-", "-", "-", "", "6.5 - 7.5"),
        ("Reducing Substances", "0.25", "-", "-", "-", "%", "< 0.25"),
        ("Starch Grains", "few in preparation", "-", "-", "-", "", "absent"),
        ("Fat Droplets", "single in preparation", "-", "-", "-", "", "absent"),
        ("Fatty Acid Crystals", "few in preparation", "-", "-", "-", "", "absent"),
        ("Muscle Fibers", "single in preparation", "-", "-", "-", "", "absent"),
        ("Mucus", "few in preparation", "-", "-", "-", "", "absent"),
        ("Leukocytes on Mucus", "present", "-", "-", "-", "", "absent"),
        ("Parasites (Stool Ova)", "negative", "-", "-", "-", "Status", "negative"),
        ("Amoeba (Cysts/Trophozoites)", "not detected", "-", "-", "-", "Status", "not detected")
    ],
    "Proteinogram": [
        ("Albumin", "-", "62.3", "-", "-", "%", "55.8 - 66.1"),
        ("Alpha-1 Globulin", "-", "2.9", "-", "-", "%", "2.9 - 4.9"),
        ("Alpha-2 Globulin", "-", "7.0", "-", "-", "%", "7.1 - 11.8"),
        ("Beta-1 Globulin", "-", "5.9", "-", "-", "%", "4.7 - 7.2"),
        ("Beta-2 Globulin", "-", "4.9", "-", "-", "%", "3.2 - 6.5"),
        ("Gamma Globulin", "-", "17.0", "-", "-", "%", "11.1 - 18.8")
    ],
    "Hormonal Panel": [
        ("Testosterone (Total)", "32.10", "27.50", "28.60", "28.70", "nmol/l", "8.64 - 29.00"),
        ("Testosterone (Free)", "-", "-", "19.17", "-", "pg/ml", "9.10 - 32.20"),
        ("Estradiol (E2)", "213", "141", "188", "176", "pmol/l", "41 - 159"),
        ("Prolactin", "14.90", "24.00", "9.64", "22.70", "ng/mL", "4.04 - 15.20"),
        ("Cortisol", "17.4", "17.4", "17.1", "-", "ug/dl", "4.8 - 19.5"),
        ("TSH", "4.57", "3.17", "1.68", "3.54", "mIU/L", "0.27 - 4.20"),
        ("Free T3 (FT3)", "5.47", "4.54", "4.29", "5.57", "pmol/L", "3.10 - 6.80"),
        ("Free T4 (FT4)", "19.80", "16.30", "20.67", "17.70", "pmol/L", "11.90 - 21.60"),
        ("LH", "7.39", "10.20", "4.46", "-", "mIU/mL", "1.70 - 8.60"),
        ("FSH", "2.1", "3.0", "1.6", "3.0", "mIU/mL", "1.5 - 12.4"),
        ("SHBG", "54.7", "43.2", "35.0", "34.3", "nmol/L", "18.3 - 54.1"),
        ("DHEA-SO4", "92.9", "97.7", "124.0", "111.0", "ug/dl", "88.9 - 427"),
        ("Progesterone", "0.842", "1.390", "1.370", "-", "nmol/l", "< 0.474"),
        ("17-OH Progesterone", "-", "-", "1.59", "2.31", "ng/ml", "0.37 - 2.87"),
        ("IGF-1", "158", "229", "201", "-", "ng/ml", "61 - 271"),
        ("HCG-Beta", "< 0.200", "< 0.200", "-", "-", "mIU/mL", "< 2.60")
    ]
}

# Non-tabular data sections
imaging_data = """## Structural & Diagnostic Imaging

### 🩻 Radiological Imaging (CT/RTG/CBCT)
- **2024-05-06 RTG Head (Lateral)**: Cephalometric X-ray [results/RTG/H1.jpg]
- **2024-05-06 RTG Teeth (Panoramic)**: Pantomogram [results/RTG/P2.jpg]
- **2025-10-27 Dental CBCT / CT Head**: 3D Visualization of lower jaw and teeth [results/DentalCBCT]

### 🩺 Ultrasound & Surgical Outcomes
- **Epigastric Hernia (Linea Alba) Surgery**:
  - **Before (USG 2025-01-07)**: 8x8mm hernia gate with small intestine loop [results/Ultrasound/HearniaLineaAlbea1.pdf]
  - **After (USG 2026-05-19)**: Post-operative state, no features of hernia, linea alba width ~4cm [results/Ultrasound/HearniaLineaAlbeaFixed2.pdf]
"""

result_notes = {
    "Morphology": [
        {
            "text": "Eosinophils may reflect an unidentified allergy still under investigation, or may be related to IBS-U.",
            "markers": [
                {"rows": ["Eosinophils", "Eosinophils %"], "target": "value", "dates": ["2026-07", "2026-01", "2025-05", "2025-01"]},
                {"rows": ["Eosinophils %"], "target": "trend"},
            ],
        },
    ],
    "Urine Chemistry": [
        {
            "text": "High urine magnesium likely reflects magnesium supplementation; similar to B12, toxicity risk is generally low, but supplementation will be reduced or adjusted.",
            "markers": [
                {"row": "Urine Magnesium", "target": "value", "dates": ["2026-07"]},
            ],
        },
        {
            "text": "Low urine potassium, sodium, phosphate, and chloride likely reflect high hydration plus extremely low salt intake for the looksmaxxing goal of reducing facial puffiness.",
            "markers": [
                {"rows": ["Urine Potassium", "Urine Sodium", "Urine Phosphate", "Urine Chloride"], "target": "value", "dates": ["2026-07"]},
            ],
        },
    ],
    "Metabolic Health": [
        {
            "text": "Liver-marker trends worsened after adding isotretinoin and Fo-Ti. Fo-Ti is being discontinued, so these are expected to improve on follow-up.",
            "markers": [
                {"rows": ["ALT", "AST", "Bilirubin Total"], "target": "trend"},
                {"row": "Bilirubin Direct", "target": "value", "dates": ["2026-07"]},
            ],
        },
    ],
    "Cardiac Health & Coagulation": [
        {
            "text": "CK is elevated in the context of a new intensive training block with high volume, progressive overload, running, and other workouts.",
            "markers": [
                {"row": "Creatine Kinase (CK)", "target": "trend"},
                {"row": "Creatine Kinase (CK)", "target": "value", "dates": ["2026-07"]},
            ],
        },
    ],
    "Micronutrients": [
        {
            "text": "Vitamin B12 went above range, likely from supplementation. B12 toxicity is generally low, but the plan is to lower the supplementation dose.",
            "markers": [
                {"row": "Vitamin B12", "target": "trend"},
                {"row": "Vitamin B12", "target": "value", "dates": ["2026-07", "2025-05"]},
            ],
        },
    ],
    "Toxicology (Urine)": [
        {
            "text": "The 2025-05 arsenic elevation was likely due to high salmon consumption.",
            "markers": [
                {"row": "Arsenic", "target": "trend"},
                {"row": "Arsenic", "target": "value", "dates": ["2025-05"]},
            ],
        },
    ],
    "Stool Analysis": [
        {
            "text": "Abnormal stool findings are attributed to IBS-U.",
            "markers": [
                {"rows": ["Stool pH", "Starch Grains", "Fat Droplets", "Fatty Acid Crystals", "Muscle Fibers", "Mucus", "Leukocytes on Mucus"], "target": "value", "dates": ["2026-07"]},
            ],
        },
    ],
    "Hormonal Panel": [
        {
            "text": "Estradiol is likely higher due to higher body fat after multiple surgeries; the plan is to return to very low body fat to drive it down again.",
            "markers": [
                {"row": "Estradiol (E2)", "target": "trend"},
                {"row": "Estradiol (E2)", "target": "value", "dates": ["2026-07", "2025-05", "2025-01"]},
            ],
        },
        {
            "text": "Prior prolactin elevations were likely due to high sexual activity before testing.",
            "markers": [
                {"row": "Prolactin", "target": "value", "dates": ["2026-01", "2025-01"]},
            ],
        },
        {
            "text": "TSH and FT4 trends may be unreliable because of very poor sleep, about 5 hours before testing, very high biotin intake, and possibly excessive iodine intake; still investigating and planning improvements.",
            "markers": [
                {"rows": ["TSH", "Free T4 (FT4)"], "target": "trend"},
                {"rows": ["TSH", "Free T4 (FT4)"], "target": "value", "dates": ["2026-07"]},
            ],
        },
        {
            "text": "Progesterone remains elevated because of ongoing daily 0.5 mg dutasteride use.",
            "markers": [
                {"row": "Progesterone", "target": "value", "dates": ["2026-07", "2026-01", "2025-05"]},
            ],
        },
    ],
}

def generate_html_report():
    html = "<html><head><style>"
    html += "body { font-family: sans-serif; padding: 20px; }"
    html += "table { border-collapse: collapse; width: 100%; margin-bottom: 10px; }"
    html += "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }"
    html += "th { background-color: #f2f2f2; }"
    html += ".note { font-size: 0.9em; color: #555; margin-bottom: 20px; font-style: italic; }"
    html += ".table-notes { font-size: 0.9em; color: #555; margin: -4px 0 20px; }"
    html += ".table-notes p { margin: 3px 0; }"
    html += "sup { font-size: 0.75em; }"
    html += "</style></head><body>"
    html += "<h1>Health Protocol: Lab Results Comparison</h1>"
    # Patient info removed
    
    for category, rows in data.items():
        
        active_indexes = active_date_indexes(rows)
        include_trend = category_has_trends(rows, category)

        html += f"<h2>{category}</h2>"
        html += "<table><tr><th></th>"
        if include_trend:
            html += "<th>Trend</th>"
        for idx in active_indexes:
            html += f"<th>{date_columns[idx]}</th>"
        html += "<th>Unit</th><th><i>Reference</i></th></tr>"
        
        for row in rows:
            name, values, unit, ref = split_result_row(row)
            
            # Use specific formatter for Urinalysis
            if "Urinalysis" in category:
                cells = [format_cell_html_urine(values[idx], ref) for idx in active_indexes]
            else:
                cells = [format_cell_html(values[idx], ref) for idx in active_indexes]
            
            html += f"<tr><td><b>{name}</b></td>"
            if include_trend:
                trend_cell = format_trend_html(values, ref, category)
                trend_cell = add_note_sup_html(trend_cell, note_numbers(category, name, "trend"))
                html += f"<td>{trend_cell}</td>"
            for idx, cell in zip(active_indexes, cells):
                cell = add_note_sup_html(cell, note_numbers(category, name, "value", date_columns[idx]))
                html += f"<td>{cell}</td>"
            html += f"<td>{unit}</td><td>{ref}</td></tr>"
        html += "</table>"
        html += render_result_notes_html(category)
    
    # Add Imaging Section
    html += imaging_data.replace("## ", "<h2>").replace("### ", "<h3>").replace("\n- ", "<br>• ").replace("\n", "<br>")

    # Legend
    html += "<h3>🎨 Color Legend</h3><ul>"
    html += "<li><span style='color:#00008b; font-weight:bold;'>● Dark Blue</span>: Optimal / Good</li>"
    html += "<li><span style='color:#006400; font-weight:bold;'>● Dark Green</span>: Safe</li>"
    html += "<li><span style='color:#32cd32; font-weight:bold;'>● Light Green</span>: Normal</li>"
    html += "<li><span style='color:#ffd700; font-weight:bold;'>● Yellow</span>: Caution</li>"
    html += "<li><span style='color:#ffa500; font-weight:bold;'>● Light Orange</span>: Borderline</li>"
    html += "<li><span style='color:#ff4500; font-weight:bold;'>● Dark Orange</span>: Limit</li>"
    html += "<li><span style='color:#dc3545; font-weight:bold;'>● Light Red</span>: Abnormal</li>"
    html += "<li><span style='color:#8b0000; font-weight:bold;'>● Dark Red</span>: Critical</li>"
    html += "</ul>"

    html += "<h3>Trend Legend</h3><ul>"
    for label, definition in trend_definitions.items():
        html += f"<li><span style='font-weight:bold;'>{definition['emoji']} {label}</span>: {definition['description'].capitalize()}</li>"
    html += "<li><b>-</b>: not enough comparable completed results</li>"
    html += "</ul>"
    html += "<p class='note'>Trend compares the latest completed result with the previous completed result using the reference-range health score; lower score is better. For one-sided targets (&lt; or &gt;), a directional improvement of at least 7.5% also counts as slight improvement.</p>"

    html += "</body></html>"
    
    with open("results.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_md_report():
    md = "# Health Protocol: Lab Results Comparison\n\n"
    # Patient info removed

    for category, rows in data.items():
        
        active_indexes = active_date_indexes(rows)
        include_trend = category_has_trends(rows, category)

        md += f"## {category}\n\n"
        
        # Build Header
        header = "|  |"
        sep = "| :--- |"
        if include_trend:
            header += " Trend |"
            sep += " :--- |"
        for idx in active_indexes:
            header += f" {date_columns[idx]} |"
            sep += " :--- |"
        header += " Unit | *Reference* |"
        sep += " :--- | :--- |"
        
        md += header + "\n" + sep + "\n"
        
        for row in rows:
            name, values, unit, ref = split_result_row(row)
            
            # Use specific formatter for Urinalysis
            if "Urinalysis" in category:
                cells = [format_cell_md_urine(values[idx], ref) for idx in active_indexes]
            else:
                cells = [format_cell_md(values[idx], ref) for idx in active_indexes]
            
            line = f"| **{name}** |"
            if include_trend:
                trend_cell = format_trend_md(values, ref, category)
                trend_cell = add_note_sup_md(trend_cell, note_numbers(category, name, "trend"))
                line += f" {trend_cell} |"
            for idx, cell in zip(active_indexes, cells):
                cell = add_note_sup_md(cell, note_numbers(category, name, "value", date_columns[idx]))
                line += f" {cell} |"
            line += f" {unit} | {ref} |"
            md += line + "\n"
        md += render_result_notes_md(category)
            
        md += "\n"

    # Add Imaging Section
    md += imaging_data + "\n"

    # Legend
    md += "### 🎨 Color Legend\n"
    md += "*   🔵 **Blue**: Optimal / Good\n"
    md += "*   🟢 **Green**: Safe / Normal\n"
    md += "*   🟡 **Yellow**: Caution\n"
    md += "*   🟠 **Orange**: Borderline / Limit\n"
    md += "*   🔴 **Red**: Abnormal / Critical\n\n"
    md += "### Trend Legend\n"
    for label, definition in trend_definitions.items():
        md += f"*   {definition['emoji']} **{label}**: {definition['description'].capitalize()}\n"
    md += "*   **-**: Not enough comparable completed results\n\n"
    md += "> **Trend method:** Compares the latest completed result with the previous completed result using the reference-range health score; lower score is better. For one-sided targets (< or >), a directional improvement of at least 7.5% also counts as slight improvement.\n\n"
    md += "> **Note:** See `results.html` for detailed color gradients.\n"

    with open("results.md", "w", encoding="utf-8") as f:
        f.write(md)

# Run both
generate_html_report()
generate_md_report()
