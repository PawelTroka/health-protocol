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

    val_clean = re.sub(r'[^\d.<>]', '', val_str.split('(')[0]) 
    if not val_clean: return None
    
    try:
        val = float(re.sub(r'[<> ]', '', val_clean))
    except ValueError:
        return None

    m_range = re.match(r'([\d.]+)\s*-\s*([\d.]+)', ref_range)
    if m_range:
        low = float(m_range.group(1))
        high = float(m_range.group(2))
        target = (low + high) / 2.0
        half_width = (high - low) / 2.0
        if half_width == 0: return 0
        dist = abs(val - target) 
        score = dist / half_width 
        return score

    m_less = re.match(r'<\s*([\d.]+)', ref_range)
    if m_less:
        limit = float(m_less.group(1))
        if val <= limit:
            return (val / limit) * 1.0 
        else:
            return 1.0 + (val - limit) / limit

    m_more = re.match(r'>\s*([\d.]+)', ref_range)
    if m_more:
        limit = float(m_more.group(1))
        optimum = limit * 2.0
        if val >= limit:
            if val >= optimum: return 0.0
            return 1.0 - ((val - limit) / (optimum - limit))
        else:
            return 1.0 + ((limit - val) / limit)
            
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
data = {
    "Morphology": [
        ("Hemoglobin", "15.40", "16.00", "15.70", "g/dL", "13.0 - 18.0"),
        ("Hematocrit", "45.9", "46.6", "47.1", "%", "40 - 52"),
        ("Erythrocytes", "5.20", "5.37", "5.31", "10^6/µl", "4.5 - 6.5"),
        ("MCV", "87.8", "86.8", "88.7", "fL", "80 - 98"),
        ("MCH", "29.4", "29.8", "29.6", "pg", "27 - 32"),
        ("MCHC", "33.6", "34.3", "33.3", "g/dL", "31 - 37"),
        ("RDW-CV", "12.5", "12.9", "12.9", "%", "11.5 - 14.5"),
        ("RDW-SD", "40.8", "-", "41.7", "fL", "35.1 - 43.9"),
        ("Leukocytes", "7.7", "5.5", "9.1", "10^3/µl", "4.0 - 11.0"),
        ("Neutrophils", "2.3", "2.22", "3.83", "10^9/L", "1.9 - 7"),
        ("Neutrophils %", "30.50", "40.30", "42.10", "%", "45 - 70"),
        ("Lymphocytes", "3.9", "2.3", "3.6", "10^9/L", "1.5 - 4.5"),
        ("Lymphocytes %", "50.3", "40.9", "39.5", "%", "25 - 45"),
        ("Monocytes", "0.9", "0.56", "1.01", "10^9/L", "0.1 - 0.9"),
        ("Monocytes %", "11.9", "10.1", "11.1", "%", "2 - 9"),
        ("Eosinophils", "0.5", "0.42", "0.55", "10^9/L", "< 0.5"),
        ("Eosinophils %", "6.5", "7.6", "6.0", "%", "0.00 - 5.00"),
        ("Basophils", "0.1", "0.05", "0.08", "10^9/L", "0.00 - 0.10"),
        ("Basophils %", "0.7", "0.9", "0.9", "%", "0.00 - 1.00"),
        ("Immature Granulocytes", "0.0", "0.01", "0.04", "10^9/L", "< 0.04"),
        ("Immature Granulocytes %", "0.1", "0.2", "0.4", "%", "0.0 - 0.5"),
        ("Platelets", "265", "228", "305", "10^3/µl", "150 - 400"),
        ("PCT", "0.30", "-", "0.31", "%", "0.12 - 0.36"),
        ("PDW", "13.8", "-", "10.9", "fL", "9.8 - 16.1"),
        ("MPV", "11.3", "10.6", "10.0", "fL", "7 - 12"),
        ("P-LCR", "35.3", "-", "-", "%", "19.2 - 47")
    ],
    "Urinalysis (General)": [
        ("Color", "light yellow", "light yellow", "-", "", "-"),
        ("Transparency", "clear", "clear", "-", "", "clear"),
        ("Specific Gravity", "1.015", "1.015", "-", "g/ml", "1.005 - 1.03"),
        ("pH", "5.5", "6.0", "-", "", "5 - 8"),
        ("Protein", "not detected", "not detected", "-", "mg/dL", "not detected"),
        ("Glucose", "not detected", "not detected", "-", "mg/dL", "not detected"),
        ("Bilirubin", "not detected", "not detected", "-", "", "not detected"),
        ("Urobilinogen", "normal", "normal", "-", "mg/dL", "normal"),
        ("Ketones", "not detected", "not detected", "-", "mg/dL", "not detected"),
        ("Nitrites", "not detected", "not detected", "-", "", "not detected"),
        ("Leukocytes (Strip)", "not detected", "not detected", "-", "leu/uL", "not detected"),
        ("Erythrocytes (Strip)", "not detected", "not detected", "-", "ery/uL", "not detected")
    ],
    "Urinalysis (Sediment)": [
        ("Squamous Epithelium", "< 30.0", "rare", "-", "/uL", "< 30.0"),
        ("Transitional Epithelium", "< 6.0", "rare", "-", "/uL", "< 6.0"),
        ("Renal Epithelium", "< 1.0", "absent", "-", "/uL", "< 1.0"),
        ("Leukocytes", "< 20.0", "0-8", "-", "/uL", "< 20.0"),
        ("Leukocyte Aggregates", "absent", "-", "-", "", "absent"),
        ("Erythrocytes", "< 20.0", "0-3", "-", "/uL", "< 20.0"),
        ("Hyaline Casts", "< 2.0", "absent", "-", "/uL", "< 2.0"),
        ("Pathological Casts", "absent", "absent", "-", "", "absent"),
        ("Crystals", "absent", "few", "-", "", "absent"),
        ("Bacteria", "< 30.0", "absent", "-", "/uL", "< 30.0"),
        ("Yeast", "< 30.0", "absent", "-", "/uL", "< 30.0"),
        ("Sperm", "< 10.0", "-", "-", "/uL", "< 10.0"),
        ("Mucus", "< 10.0", "rare", "-", "/uL", "< 10.0")
    ],
    "Metabolic Health": [
        ("Glucose", "84", "89", "70", "mg/dl", "70 - 99"),
        ("HbA1c", "5.18", "5.3", "-", "%", "4.8 - 5.9"),
        ("Insulin", "11.2", "8.9", "-", "µU/mL", "2.6 - 24.9"),
        ("ALT", "12", "14", "-", "U/L", "< 41"),
        ("AST", "20", "25", "-", "U/L", "< 40"),
        ("GGTP", "14", "18", "18", "U/L", "< 60"),
        ("Bilirubin Total", "0.20", "0.39", "-", "mg/dL", "< 1.20"),
        ("ALP", "-", "89", "-", "U/L", "40 - 129"),
        ("LDH", "123", "-", "-", "U/L", "< 250"),
        ("Creatinine", "0.93", "0.93", "-", "mg/dl", "0.70 - 1.20"),
        ("eGFR", ">60", ">60", "-", "ml/min/1.73m^2", "> 60.0"),
        ("Uric Acid", "3.2", "4.1", "-", "mg/dl", "3.4 - 7.0")
    ],
    "Cardiac Health & Coagulation": [
        ("Cholesterol LDL", "76", "74", "75", "mg/dl", "< 115"),
        ("Cholesterol HDL", "43", "35", "-", "mg/dL", "> 40"),
        ("Cholesterol Total", "138", "119", "-", "mg/dL", "< 190"),
        ("Triglycerides", "98", "48", "56", "mg/dL", "< 150"),
        ("Lipoprotein (a)", "< 7.00", "-", "-", "nmol/l", "< 75"),
        ("Homocysteine", "-", "6.60", "6.50", "umol/l", "< 15.0"),
        ("NT-proBNP", "22.9", "22.9", "< 10.0", "pg/ml", "< 125"),
        ("Creatine Kinase (CK)", "153", "-", "-", "U/L", "20 - 200"),
        ("Myoglobin", "24.30", "42.60", "-", "ng/ml", "23 - 72"),
        ("D-dimer", "< 190", "< 190", "< 190", "ng/ml", "< 500"),
        ("INR", "0.94", "-", "-", "", "0.80 - 1.20"),
        ("APTT", "31.6", "-", "-", "sec", "22.0 - 34.0"),
        ("PT", "11.4", "-", "-", "sec", "10.0 - 15.0")
    ],
    "Micronutrients": [
        ("Vitamin D3", "26.3", "52.5", "37.9", "ng/ml", "30 - 50"),
        ("Vitamin B12", "562", "928", "-", "pg/ml", "197 - 771"),
        ("Ferritin", "78", "134", "-", "ng/ml", "30 - 400"),
        ("Iron", "41", "98", "-", "µg/dl", "59 - 150"),
        ("Folic Acid", "8.5", "17.0", "-", "ng/ml", "3.9 - 26.8"),
        ("Magnesium", "1.90", "2.13", "-", "mg/dl", "1.60 - 2.60"),
        ("Potassium", "4.2", "3.8", "-", "mmol/l", "3.5 - 5.1"),
        ("Sodium", "140", "-", "-", "mmol/l", "136 - 145"),
        ("Calcium (Total)", "9.88", "9.88", "-", "mg/dL", "8.60 - 10.00"),
        ("Fosfor", "4.83", "3.7", "-", "mg/dL", "2.5 - 4.5"),
        ("Zinc", "-", "22.07", "-", "µmol/l", "9 - 18"),
        ("Vitamin B6", "-", "58.6", "-", "µg/l", "5.7 - 55.1"),
        ("Vitamin B1", "-", "69.1", "-", "µg/l", "33.1 - 60.7"),
        ("Vitamin A", "-", "0.47", "-", "mg/l", "0.3 - 0.7"),
        ("Vitamin E", "-", "9.5", "-", "mg/l", "5 - 20")
    ],
    "Immunology & Inflammation": [
        ("CRP (hs)", "0.448", "< 0.15", "not detected", "mg/l", "< 5.0"),
        ("IL-6", "-", "1.6", "-", "pg/ml", "< 7.0"),
        ("Calprotectin", "0.43", "0.41", "-", "µg/mL", "< 2.0"),
        ("Anti-TPO", "12.30", "-", "-", "IU/ml", "< 34.0"),
        ("Anti-TG", "13.10", "-", "-", "IU/ml", "< 115.0"),
        ("ASO", "209", "-", "-", "IU/mL", "< 200")
    ],
    "Tumor Markers": [
        ("PSA Total", "0.16", "0.195", "-", "ng/mL", "< 4.0"),
        ("CEA", "2.9", "2.2", "-", "ng/ml", "< 5.0"),
        ("AFP", "2.84", "2.0", "-", "IU/ml", "< 5.8"),
        ("CA 19-9", "3.8", "5.5", "-", "U/ml", "< 34.0"),
        ("S-100", "-", "0.05", "-", "µg/l", "< 0.15")
    ],
    "Infectious Diseases": [
        ("HIV", "Non-reactive", "Non-reactive", "Non-reactive", "Status", "Non-reactive"),
        ("HBs Ag", "221.00", "203.00", "-", "Immune", "> 10"),
        ("HCV", "Non-reactive", "Non-reactive", "Non-reactive", "Status", "Non-reactive"),
        ("Syphilis (WR)", "Non-reactive", "Non-reactive", "-", "Status", "Non-reactive"),
        ("Chlamydia IgG", "< 5.0", "< 5.0", "negative", "Status", "Non-reactive"),
        ("Chlamydia IgM", "-", "2.7", "2.7", "Status", "< 9"),
        ("HSV IgG", "-", "1.35", "1.7", "Index", "< 0.9"),
        ("HSV IgM", "-", "negative", "negative", "Status", "Non-reactive")
    ],
    "Heavy Metals (Urine)": [
        ("Arsenic", "-", "30.8", "-", "µg/l", "< 15.0"),
        ("Cadmium", "-", "0.1", "-", "ug/l", "< 0.8"),
        ("Chromium", "-", "0.2", "-", "ug/l", "< 0.6"),
        ("Nickel", "-", "0.2", "-", "µg/l", "< 3.0"),
        ("Copper", "-", "3.15", "-", "µg/l", "2.0 - 80.0")
    ],
    "Proteinogram": [
        ("Albumin", "62.3", "-", "-", "%", "55.8 - 66.1"),
        ("Alpha-1 Globulin", "2.9", "-", "-", "%", "2.9 - 4.9"),
        ("Alpha-2 Globulin", "7.0", "-", "-", "%", "7.1 - 11.8"),
        ("Beta-1 Globulin", "5.9", "-", "-", "%", "4.7 - 7.2"),
        ("Beta-2 Globulin", "4.9", "-", "-", "%", "3.2 - 6.5"),
        ("Gamma Globulin", "17.0", "-", "-", "%", "11.1 - 18.8")
    ],
    "Hormonal Panel": [
        ("Testosterone (Total)", "27.50", "28.60", "28.70", "nmol/l", "8.64 - 29.00"),
        ("Testosterone (Free)", "-", "19.17", "-", "pg/ml", "9.10 - 32.20"),
        ("Estradiol (E2)", "141", "188", "176", "pmol/l", "41 - 159"),
        ("Prolactin", "24.00", "9.64", "22.70", "ng/mL", "4.04 - 15.20"),
        ("Cortisol", "17.4", "17.1", "-", "µg/dl", "4.8 - 19.5"),
        ("TSH", "3.17", "1.68", "3.54", "mIU/L", "0.27 - 4.20"),
        ("Free T3 (FT3)", "4.54", "4.29", "5.57", "pmol/L", "3.10 - 6.80"),
        ("Free T4 (FT4)", "16.30", "20.67", "17.70", "pmol/L", "11.90 - 21.60"),
        ("LH", "10.20", "4.46", "-", "mIU/mL", "1.70 - 8.60"),
        ("FSH", "3.0", "1.6", "3.0", "mIU/mL", "1.5 - 12.4"),
        ("SHBG", "43.2", "35.0", "34.3", "nmol/L", "18.3 - 54.1"),
        ("DHEA-SO4", "97.7", "124.0", "111.0", "µg/dl", "88.9 - 427"),
        ("Progesterone", "1.390", "1.370", "-", "nmol/l", "< 0.474"),
        ("17-OH Progesterone", "-", "1.59", "2.31", "ng/ml", "0.37 - 2.87"),
        ("IGF-1", "229", "201", "-", "ng/ml", "61 - 271"),
        ("HCG-Beta", "< 0.200", "-", "-", "mIU/mL", "< 2.60")
    ]
}

# Category-specific notes
category_notes = {
    "Hormonal Panel": "Progesterone is likely elevated due to daily intake of 0.5mg dutasteride. Prolactin elevation is likely due to high sexual activity prior to testing.",
    "Heavy Metals (Urine)": "Arsenic elevation is likely due to high consumption of salmon."
}

def generate_html_report():
    html = "<html><head><style>"
    html += "body { font-family: sans-serif; padding: 20px; }"
    html += "table { border-collapse: collapse; width: 100%; margin-bottom: 10px; }"
    html += "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }"
    html += "th { background-color: #f2f2f2; }"
    html += ".note { font-size: 0.9em; color: #555; margin-bottom: 20px; font-style: italic; }"
    html += "</style></head><body>"
    html += "<h1>Health Protocol: Lab Results Comparison</h1>"
    # Patient info removed
    
    for category, rows in data.items():
        # Check if 2025 columns have any data
        has_v2 = any(row[1] not in ["-", "—", None, ""] for row in rows)
        has_v3 = any(row[2] not in ["-", "—", None, ""] for row in rows)
        
        html += f"<h2>{category}</h2>"
        html += "<table><tr><th></th><th>2026-01</th>"
        if has_v2: html += "<th>2025-05</th>"
        if has_v3: html += "<th>2025-01</th>"
        html += "<th>Unit</th><th><i>Reference</i></th></tr>"
        
        for row in rows:
            name, v1, v2, v3, unit, ref = row
            
            # Use specific formatter for Urinalysis
            if "Urinalysis" in category:
                c1 = format_cell_html_urine(v1, ref)
                c2 = format_cell_html_urine(v2, ref) if has_v2 else ""
                c3 = format_cell_html_urine(v3, ref) if has_v3 else ""
            else:
                c1 = format_cell_html(v1, ref)
                c2 = format_cell_html(v2, ref) if has_v2 else ""
                c3 = format_cell_html(v3, ref) if has_v3 else ""
            
            html += f"<tr><td><b>{name}</b></td><td>{c1}</td>"
            if has_v2: html += f"<td>{c2}</td>"
            if has_v3: html += f"<td>{c3}</td>"
            html += f"<td>{unit}</td><td>{ref}</td></tr>"
        html += "</table>"
        
        if category in category_notes:
            html += f"<p class='note'>{category_notes[category]}</p>"
    
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

    html += "</body></html>"
    
    with open("results.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_md_report():
    md = "# Health Protocol: Lab Results Comparison\n\n"
    # Patient info removed

    for category, rows in data.items():
        has_v2 = any(row[2] not in ["-", "—", None, ""] for row in rows)
        has_v3 = any(row[3] not in ["-", "—", None, ""] for row in rows)
        
        md += f"## {category}\n\n"
        
        # Build Header
        header = "|  | 2026-01 |"
        sep = "| :--- | :--- |"
        if has_v2:
            header += " 2025-05 |"
            sep += " :--- |"
        if has_v3:
            header += " 2025-01 |"
            sep += " :--- |"
        header += " Unit | *Reference* |"
        sep += " :--- | :--- |"
        
        md += header + "\n" + sep + "\n"
        
        for row in rows:
            name, v1, v2, v3, unit, ref = row
            
            # Use specific formatter for Urinalysis
            if "Urinalysis" in category:
                c1 = format_cell_md_urine(v1, ref)
                c2 = format_cell_md_urine(v2, ref) if has_v2 else ""
                c3 = format_cell_md_urine(v3, ref) if has_v3 else ""
            else:
                c1 = format_cell_md(v1, ref)
                c2 = format_cell_md(v2, ref) if has_v2 else ""
                c3 = format_cell_md(v3, ref) if has_v3 else ""
            
            line = f"| **{name}** | {c1} |"
            if has_v2: line += f" {c2} |"
            if has_v3: line += f" {c3} |"
            line += f" {unit} | {ref} |"
            md += line + "\n"
        
        if category in category_notes:
            md += f"\n> **Note:** {category_notes[category]}\n"
            
        md += "\n"

    # Legend
    md += "### 🎨 Color Legend\n"
    md += "*   🔵 **Blue**: Optimal / Good\n"
    md += "*   🟢 **Green**: Safe / Normal\n"
    md += "*   🟡 **Yellow**: Caution\n"
    md += "*   🟠 **Orange**: Borderline / Limit\n"
    md += "*   🔴 **Red**: Abnormal / Critical\n\n"
    md += "> **Note:** See `results.html` for detailed color gradients.\n"

    with open("results.md", "w", encoding="utf-8") as f:
        f.write(md)

# Run both
generate_html_report()
generate_md_report()