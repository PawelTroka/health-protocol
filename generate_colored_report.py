import re

def lerp(a, b, t):
    return int(a + (b - a) * t)

def get_color_hex(score):
    # Palette Definition (Score -> Color)
    # 0.0: Optimal (Center)
    # 1.0: Limit of Normal
    # >1.0: Abnormal
    
    # Stops:
    # 0.00: Dark Blue
    # 0.25: Light Blue
    # 0.50: Teal / Green
    # 0.75: Yellow
    # 1.00: Light Orange (Limit)
    # 1.25: Dark Orange
    # 1.50: Light Red
    # 2.00: Dark Red
    
    stops = [
        (0.00, (0, 0, 139)),      # Dark Blue
        (0.25, (0, 191, 255)),    # Deep Sky Blue (Light Blue)
        (0.50, (32, 201, 151)),   # Teal
        (0.75, (255, 215, 0)),    # Gold / Yellow
        (1.00, (255, 165, 0)),    # Orange (Light Orange)
        (1.25, (255, 69, 0)),     # Orange Red (Dark Orange)
        (1.50, (220, 53, 69)),    # Red (Light Red / Standard Red)
        (2.00, (139, 0, 0))       # Dark Red
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
            
    if lower == upper:
        r, g, b = lower[1]
    else:
        # Interpolate
        t = (score - lower[0]) / (upper[0] - lower[0])
        c1 = lower[1]
        c2 = upper[1]
        
        r = lerp(c1[0], c2[0], t)
        g = lerp(c1[1], c2[1], t)
        b = lerp(c1[2], c2[2], t)

    return f"#{r:02x}{g:02x}{b:02x}"

def calculate_score(val_str, ref_range):
    if val_str == "—" or val_str is None:
        return None
        
    # Extract numeric value
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
        
        target = (low + high) / 2.0
        half_width = (high - low) / 2.0
        
        if half_width == 0: return 0 # Avoid div by zero
        
        dist = abs(val - target)
        score = dist / half_width 
        return score

    # Limit "< A"
    m_less = re.match(r'<\s*([\d.]+)', ref_range)
    if m_less:
        limit = float(m_less.group(1))
        if val <= limit:
            # 0 to limit maps to 0.0 to 1.0 (Blue to Orange)
            # But usually < X means 0 is good. 
            # Let's say 0 is Optimal (0.0), Limit is 1.0.
            return (val / limit) * 1.0 
        else:
            # Above limit
            return 1.0 + (val - limit) / limit

    # Limit "> A"
    m_more = re.match(r'>\s*([\d.]+)', ref_range)
    if m_more:
        limit = float(m_more.group(1))
        # > 60. Optimal is higher.
        # Let's arbitrarily say limit*2 is "perfect" (0.0)
        # and limit is 1.0.
        optimum = limit * 2.0
        
        if val >= limit:
            if val >= optimum: return 0.0
            # Map limit..optimum to 1.0..0.0
            return 1.0 - ((val - limit) / (optimum - limit))
        else:
            # Below limit (Bad)
            # 1.0 + distance relative to limit
            return 1.0 + ((limit - val) / limit)
            
    return 0.5 

def format_cell(val, ref):
    score = calculate_score(val, ref)
    if score is None:
        return val
    
    color = get_color_hex(score)
    # Using font tag for better compatibility if spans fail
    return f'<font color="{color}"><b>{val}</b></font>'

# Data
data = {
    "Hormonal Panel": [
        ("Prolactin", "24.00", "9.64", "22.70", "ng/mL", "4.04 - 15.20"),
        ("LH", "10.20", "4.46", "—", "mIU/mL", "1.70 - 8.60"),
        ("Progesterone", "1.390", "1.370", "—", "nmol/l", "< 0.474"),
        ("Testosterone (Free)", "—", "19.17", "—", "pg/ml", "9.10 - 32.20"),
        ("Testosterone (Total)", "—", "28.60", "28.70", "nmol/l", "8.64 - 29.00"),
        ("Estradiol (E2)", "141", "188", "176", "pmol/l", "41 - 159"),
        ("FSH", "3.0", "1.6", "3.0", "mIU/mL", "1.5 - 12.4"),
        ("TSH", "—", "1.68", "3.54", "mIU/L", "0.27 - 4.20"),
        ("17-OH Progesterone", "—", "1.59", "2.31", "ng/ml", "0.37 - 2.87"),
        ("Free T3 (FT3)", "—", "4.29", "5.57", "pmol/L", "3.10 - 6.80"),
        ("Free T4 (FT4)", "—", "16.30", "17.70", "pmol/L", "11.90 - 21.60"),
        ("SHBG", "—", "43.2", "34.3", "nmol/L", "18.3 - 54.1"),
        ("DHEA-SO4", "—", "97.7", "111.0", "µg/dl", "88.9 - 427"),
        ("HCG-Beta", "< 0.200", "—", "—", "mIU/mL", "< 2.60"),
        ("Insulin", "—", "8.9", "—", "µU/mL", "2.6 - 24.9"),
        ("IGF-1", "—", "201", "—", "ng/ml", "61 - 271"),
        ("Cortisol", "—", "17.4", "—", "µg/dl", "4.8 - 19.5")
    ],
    "Biochemistry & Metabolism": [
        ("Fosfor", "4.83", "3.83", "—", "mg/dL", "2.5 - 4.5"),
        ("Lipoprotein (a)", "< 7.00", "—", "—", "nmol/l", "< 75"),
        ("Vitamin D3", "—", "52.5", "37.9", "ng/ml", "30 - 50"),
        ("Homocysteine", "—", "6.60", "6.50", "umol/l", "< 15.0"),
        ("Glucose", "—", "84", "70", "mg/dl", "70 - 99"),
        ("HbA1c", "—", "5.3", "—", "%", "4.8 - 5.9"),
        ("Bilirubin Total", "0.20", "0.39", "—", "mg/dL", "< 1.20"),
        ("LDH", "123", "—", "—", "U/L", "< 250"),
        ("GGTP", "14", "18", "18", "U/L", "< 60"),
        ("AST", "—", "25", "—", "U/L", "< 40"),
        ("ALT", "—", "14", "—", "U/L", "< 41"),
        ("ALP", "—", "89", "—", "U/L", "40 - 129"),
        ("Calcium (Total)", "—", "9.88", "—", "mg/dL", "8.60 - 10.00"),
        ("Magnesium", "—", "2.13", "—", "mg/dl", "1.60 - 2.60"),
        ("Creatinine", "—", "0.93", "—", "mg/dl", "0.70 - 1.20"),
        ("eGFR", "—", ">60", "—", "ml/min/1.73m^2", "> 60.0"),
        ("Cholesterol Total", "—", "119", "—", "mg/dL", "< 190"),
        ("Cholesterol HDL", "—", "43", "—", "mg/dL", "> 40"),
        ("Cholesterol LDL", "—", "74", "75", "mg/dl", "< 115"),
        ("Triglycerides", "—", "48", "56", "mg/dL", "< 150"),
        ("Potassium", "—", "3.8", "—", "mmol/l", "3.5 - 5.1"),
        ("Sodium", "—", "140", "—", "mmol/l", "136 - 145"),
        ("Uric Acid", "—", "4.1", "—", "mg/dl", "3.4 - 7.0"),
        ("Zinc", "—", "22.07", "—", "µmol/l", "9 - 18"),
        ("Vitamin B6", "—", "58.6", "—", "µg/l", "5.7 - 55.1"),
        ("Vitamin B1", "—", "69.1", "—", "µg/l", "33.1 - 60.7"),
        ("Vitamin E", "—", "9.5", "—", "mg/l", "5 - 20"),
        ("Vitamin A", "—", "0.47", "—", "mg/l", "0.3 - 0.7"),
        ("Vitamin B12", "—", "928", "—", "pg/ml", "197 - 771"),
        ("Folic Acid", "—", "17.0", "—", "ng/ml", "3.9 - 26.8"),
        ("Ferritin", "—", "134", "—", "ng/ml", "30 - 400"),
        ("Iron", "—", "98", "—", "µg/dl", "59 - 150"),
        ("Myoglobin", "—", "42.60", "—", "ng/ml", "23 - 72"),
        ("Calprotectin", "—", "0.41", "—", "µg/mL", "< 2.0"),
        ("IL-6", "—", "1.6", "—", "pg/ml", "< 7.0")
    ],
    "Immunology & Tumor Markers": [
        ("ASO", "209", "—", "—", "IU/mL", "< 200"),
        ("Anti-TG", "13.10", "—", "—", "IU/ml", "< 115.0"),
        ("Anti-TPO", "12.30", "—", "—", "IU/ml", "< 34.0"),
        ("CEA", "2.9", "2.2", "—", "ng/ml", "< 5.0"),
        ("AFP", "2.84", "2.0", "—", "IU/ml", "< 5.8"),
        ("CA 19-9", "3.8", "5.5", "—", "U/ml", "< 34.0"),
        ("PSA Total", "0.16", "0.195", "—", "ng/mL", "< 4.0"),
        ("S-100", "—", "0.05", "—", "µg/l", "< 0.15"),
        ("CRP (hs)", "—", "0.448", "< 0.15", "mg/l", "< 5.0")
    ],
    "Coagulation & Cardiac": [
        ("APTT", "31.6", "—", "—", "sec", "22.0 - 34.0"),
        ("INR", "0.94", "—", "—", "", "0.80 - 1.20"),
        ("PT", "11.4", "—", "—", "sec", "10.0 - 15.0"),
        ("D-dimer", "—", "< 190", "< 190", "ng/ml", "< 500"),
        ("NT-proBNP", "—", "22.9", "< 10.0", "pg/ml", "< 125")
    ],
    "Proteinogram (2026-01)": [
        ("Albumin", "62.3", "—", "—", "%", "55.8 - 66.1"),
        ("Alpha-1 Globulin", "2.9", "—", "—", "%", "2.9 - 4.9"),
        ("Alpha-2 Globulin", "7.0", "—", "—", "%", "7.1 - 11.8"),
        ("Beta-1 Globulin", "5.9", "—", "—", "%", "4.7 - 7.2"),
        ("Beta-2 Globulin", "4.9", "—", "—", "%", "3.2 - 6.5"),
        ("Gamma Globulin", "17.0", "—", "—", "%", "11.1 - 18.8")
    ],
    "Infectious Diseases & Urine": [
        ("HBs Ag", "221.00", "203.00", "—", "Immune", "> 10"),
        ("HCV", "Non-reactive", "Non-reactive", "Non-reactive", "Status", "Neg"),
        ("Syphilis (WR)", "Non-reactive", "Non-reactive", "—", "Status", "Neg"),
        ("Chlamydia IgG", "Negative", "Negative", "Negative", "Status", "Neg"),
        ("Chlamydia IgM", "—", "5.8", "2.7", "Status", "< 9"),
        ("HSV IgG", "—", "1.35", "1.7", "Index", "< 0.9"),
        ("HSV IgM", "—", "Negative", "Negative", "Status", "Neg"),
        ("HIV", "—", "—", "Non-reactive", "Status", "Neg"),
        ("Arsenic (Urine)", "—", "30.8", "—", "µg/l", "< 15.0"),
        ("Cadmium (Urine)", "—", "0.1", "—", "ug/l", "< 0.8"),
        ("Chromium (Urine)", "—", "0.2", "—", "ug/l", "< 0.6"),
        ("Nickel (Urine)", "—", "0.2", "—", "µg/l", "< 3.0"),
        ("Copper (Urine)", "—", "3.15", "—", "µg/l", "2.0 - 80.0")
    ],
    "Morphology (2025-05)": [
        ("Leukocytes", "—", "5.5", "9.1", "10^3/µl", "4.0 - 11.0"),
        ("Erythrocytes", "—", "5.37", "5.31", "10^6/µl", "4.5 - 6.5"),
        ("Hemoglobin", "—", "16.0", "15.7", "g/dL", "13.0 - 18.0"),
        ("Hematocrit", "—", "46.6", "47.1", "%", "40 - 52"),
        ("Platelets", "—", "228", "305", "10^3/µl", "150 - 400")
    ]
}

# Generate Markdown
md = "# Health Protocol: Lab Results Comparison\n\n"
md += "**Patient:** Paweł Troka  \n**DOB:** 14-02-1991\n\n"
md += "### 🎨 Color Legend\n"
md += "*   <font color=\"#00008b\"><b>● Dark Blue</b></font>: Optimal / Perfect Center\n"
md += "*   <font color=\"#00bfff\"><b>● Light Blue</b></font>: Good / Near Center\n"
md += "*   <font color=\"#20c997\"><b>● Teal</b></font>: Safe Zone\n"
md += "*   <font color=\"#ffd700\"><b>● Yellow</b></font>: Approaching Limit\n"
md += "*   <font color=\"#ffa500\"><b>● Light Orange</b></font>: At Limit / Borderline\n"
md += "*   <font color=\"#ff4500\"><b>● Dark Orange</b></font>: Slight Deviation\n"
md += "*   <font color=\"#dc3545\"><b>● Light Red</b></font>: Abnormal\n"
md += "*   <font color=\"#8b0000\"><b>● Dark Red</b></font>: Critical / High Deviation\n\n"

for category, rows in data.items():
    md += f"## {category}\n\n"
    md += "| Test Name | 2026-01 | 2025-05 | 2025-01 | Unit | Reference Range |\n"
    md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    
    for row in rows:
        name, v1, v2, v3, unit, ref = row
        
        # Determine Ref Range column value (skip for Morphology/Inf if static)
        # We use the 'ref' passed in tuple
        
        c1 = format_cell(v1, ref)
        c2 = format_cell(v2, ref)
        c3 = format_cell(v3, ref)
        
        md += f"| **{name}** | {c1} | {c2} | {c3} | {unit} | {ref} |\n"
    
    md += "\n"

with open("results.md", "w", encoding="utf-8") as f:
    f.write(md)
