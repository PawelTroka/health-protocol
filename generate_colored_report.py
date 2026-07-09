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

def low_good_target(reference, optimal_max, high_limit, low_limit=None):
    target = {
        "reference": reference,
        "type": "low_good",
        "optimal_max": optimal_max,
        "high_limit": high_limit,
    }
    if low_limit is not None:
        target["low_limit"] = low_limit
    return target

def high_good_target(reference, low_limit, optimal_min, high_limit=None):
    target = {
        "reference": reference,
        "type": "high_good",
        "low_limit": low_limit,
        "optimal_min": optimal_min,
    }
    if high_limit is not None:
        target["high_limit"] = high_limit
    return target

def optimal_range_target(reference, low_limit, optimal_min, optimal_max, high_limit):
    return {
        "reference": reference,
        "type": "optimal_range",
        "low_limit": low_limit,
        "optimal_min": optimal_min,
        "optimal_max": optimal_max,
        "high_limit": high_limit,
    }

def high_good_range_target(reference, low_limit, optimal_min, optimal_max, high_limit):
    return {
        "reference": reference,
        "type": "high_good_range",
        "low": low_limit,
        "optimal_min": optimal_min,
        "optimal_max": optimal_max,
        "high_limit": high_limit,
    }

def blood_pressure_target(reference, systolic, diastolic):
    return {
        "reference": reference,
        "type": "blood_pressure",
        "systolic": systolic,
        "diastolic": diastolic,
    }

target_overrides = {
    # Morphology
    ("Morphology", "Hemoglobin"): optimal_range_target("13.0 - 18.0; target 14.0 - 16.2", 13.0, 14.0, 16.2, 18.0),
    ("Morphology", "Hematocrit"): optimal_range_target("40 - 52; target 42 - 48", 40.0, 42.0, 48.0, 52.0),
    ("Morphology", "Erythrocytes"): optimal_range_target("4.5 - 6.5; target 4.8 - 5.6", 4.5, 4.8, 5.6, 6.5),
    ("Morphology", "MCV"): optimal_range_target("80 - 98; target 84 - 92", 80.0, 84.0, 92.0, 98.0),
    ("Morphology", "MCH"): optimal_range_target("27 - 32; target 29 - 31", 27.0, 29.0, 31.0, 32.0),
    ("Morphology", "MCHC"): optimal_range_target("31 - 37; target 33 - 35", 31.0, 33.0, 35.0, 37.0),
    ("Morphology", "RDW-CV"): low_good_target("11.5 - 14.5; target <= 13.2", 13.2, 14.5, 10.5),
    ("Morphology", "RDW-SD"): optimal_range_target("35.1 - 43.9; target 36 - 42", 35.1, 36.0, 42.0, 43.9),
    ("Morphology", "Leukocytes"): optimal_range_target("4.0 - 11.0; target 4.5 - 8.0", 4.0, 4.5, 8.0, 11.0),
    ("Morphology", "Neutrophils"): optimal_range_target("1.9 - 7; target 2.0 - 5.0", 1.9, 2.0, 5.0, 7.0),
    ("Morphology", "Neutrophils %"): optimal_range_target("45 - 70; target 45 - 60", 40.0, 45.0, 60.0, 70.0),
    ("Morphology", "Lymphocytes"): optimal_range_target("1.5 - 4.5; target 1.5 - 3.5", 1.5, 1.5, 3.5, 4.5),
    ("Morphology", "Lymphocytes %"): optimal_range_target("25 - 45; target 25 - 40", 25.0, 25.0, 40.0, 45.0),
    ("Morphology", "Monocytes"): optimal_range_target("0.1 - 0.9; target 0.2 - 0.8", 0.1, 0.2, 0.8, 0.9),
    ("Morphology", "Monocytes %"): optimal_range_target("2 - 9; target 2 - 8", 2.0, 2.0, 8.0, 9.0),
    ("Morphology", "Eosinophils"): low_good_target("< 0.5; target <= 0.3", 0.3, 0.5),
    ("Morphology", "Eosinophils %"): low_good_target("0.00 - 5.00; target <= 3.0", 3.0, 5.0),
    ("Morphology", "Basophils"): low_good_target("0.00 - 0.10; target <= 0.08", 0.08, 0.10),
    ("Morphology", "Basophils %"): low_good_target("0.00 - 1.00; target <= 0.8", 0.8, 1.0),
    ("Morphology", "Immature Granulocytes"): low_good_target("< 0.04; target 0", 0.0, 0.04),
    ("Morphology", "Immature Granulocytes %"): low_good_target("0.0 - 0.5; target <= 0.3", 0.3, 0.5),
    ("Morphology", "Platelets"): optimal_range_target("150 - 400; target 180 - 300", 150.0, 180.0, 300.0, 400.0),
    ("Morphology", "PCT"): optimal_range_target("0.12 - 0.36; target 0.18 - 0.32", 0.12, 0.18, 0.32, 0.36),
    ("Morphology", "PDW"): optimal_range_target("9.8 - 16.1; target 10 - 14", 9.8, 10.0, 14.0, 16.1),
    ("Morphology", "MPV"): optimal_range_target("7 - 12; target 8 - 11", 7.0, 8.0, 11.0, 12.0),
    ("Morphology", "P-LCR"): optimal_range_target("19.2 - 47; target 20 - 40", 19.2, 20.0, 40.0, 47.0),

    # Vitals, body composition, sleep, and wearables
    ("Vitals & Functional Health", "Blood Pressure"): blood_pressure_target(
        "< 120 / < 80; target 100-115 / 60-75",
        {"low_limit": 90.0, "optimal_min": 100.0, "optimal_max": 115.0, "high_limit": 120.0},
        {"low_limit": 55.0, "optimal_min": 60.0, "optimal_max": 75.0, "high_limit": 80.0},
    ),
    ("Vitals & Functional Health", "Nighttime BP Dip"): optimal_range_target("10 - 20; target 10 - 20", 0.0, 10.0, 20.0, 25.0),
    ("Vitals & Functional Health", "Resting Heart Rate"): optimal_range_target("60 - 100; target 50 - 70", 40.0, 50.0, 70.0, 100.0),
    ("Vitals & Functional Health", "Sleeping Heart Rate"): optimal_range_target("40 - 80; target 45 - 60", 35.0, 45.0, 60.0, 80.0),
    ("Vitals & Functional Health", "ECG Heart Rate"): optimal_range_target("50 - 100; target 50 - 80", 40.0, 50.0, 80.0, 100.0),
    ("Vitals & Functional Health", "PWV"): low_good_target("< 10; target < 7", 7.0, 10.0),
    ("Vitals & Functional Health", "VO2max"): high_good_target("> 35; target >= 45", 35.0, 45.0),
    ("Vitals & Functional Health", "Respiratory Rate (Sleep)"): optimal_range_target("12 - 20; target 12 - 16", 10.0, 12.0, 16.0, 20.0),
    ("Vitals & Functional Health", "BMI"): optimal_range_target("18.5 - 24.9; target 20 - 24.9", 18.5, 20.0, 24.9, 30.0),
    ("Vitals & Functional Health", "Body Fat"): optimal_range_target("10 - 20; target 10 - 15", 8.0, 10.0, 15.0, 20.0),
    ("Vitals & Functional Health", "Muscle"): high_good_target("> 70; target >= 75", 70.0, 75.0),
    ("Vitals & Functional Health", "Temperature"): optimal_range_target("36.1 - 37.2; target 36.5 - 37.0", 36.1, 36.5, 37.0, 37.2),
    ("Vitals & Functional Health", "Sleep Apnea AHI"): low_good_target("< 5; target < 5", 5.0, 10.0),
    ("Vitals & Functional Health", "Sleep Duration"): high_good_range_target(">= 7; target 7 - 9", 5.0, 7.0, 9.0, 10.5),
    ("Vitals & Functional Health", "REM Sleep"): optimal_range_target("1.5 - 2.3; target 20 - 25% of sleep", 0.8, 1.5, 2.3, 3.0),
    ("Vitals & Functional Health", "Deep Sleep"): optimal_range_target("about 1 - 2; target 1 - 2", 0.5, 1.0, 2.0, 3.0),

    # Metabolic, liver, kidney
    ("Metabolic Health", "Glucose"): optimal_range_target("70 - 99; target 70 - 85", 70.0, 70.0, 85.0, 99.0),
    ("Metabolic Health", "HbA1c"): optimal_range_target("4.8 - 5.9; target 4.8 - 5.3", 4.8, 4.8, 5.3, 5.9),
    ("Metabolic Health", "Insulin"): low_good_target("2.6 - 24.9; target 2.6 - 8", 8.0, 24.9, 2.6),
    ("Metabolic Health", "ALT"): low_good_target("< 41; target <= 20", 20.0, 41.0),
    ("Metabolic Health", "AST"): optimal_range_target("< 40; target 15 - 30", 10.0, 15.0, 30.0, 40.0),
    ("Metabolic Health", "GGTP"): low_good_target("< 60; target <= 20", 20.0, 60.0),
    ("Metabolic Health", "Bilirubin Total"): optimal_range_target("< 1.20; target 0.3 - 1.0", 0.1, 0.3, 1.0, 1.2),
    ("Metabolic Health", "Bilirubin Direct"): low_good_target("< 0.3; target <= 0.2", 0.2, 0.3),
    ("Metabolic Health", "ALP"): optimal_range_target("40 - 129; target 50 - 90", 40.0, 50.0, 90.0, 129.0),
    ("Metabolic Health", "LDH"): optimal_range_target("< 250; target 120 - 200", 100.0, 120.0, 200.0, 250.0),
    ("Metabolic Health", "Albumin"): high_good_target("35.00 - 52.00; target 45 - 52", 35.0, 45.0, 52.0),
    ("Metabolic Health", "Creatinine"): optimal_range_target("0.70 - 1.20; target 0.80 - 1.10", 0.70, 0.80, 1.10, 1.20),
    ("Metabolic Health", "Cystatin C"): optimal_range_target("0.51 - 1.05; target 0.60 - 0.90", 0.51, 0.60, 0.90, 1.05),
    ("Metabolic Health", "eGFR"): high_good_range_target("> 60.0; target 90 - 120", 60.0, 90.0, 120.0, 130.0),
    ("Metabolic Health", "Uric Acid"): optimal_range_target("3.4 - 7.0; target 3.5 - 5.5", 3.4, 3.5, 5.5, 7.0),

    # Cardiac health
    ("Cardiac Health & Coagulation", "Cholesterol LDL"): low_good_target("< 115; target < 70", 70.0, 115.0),
    ("Cardiac Health & Coagulation", "Cholesterol Non-HDL"): low_good_target("< 130; target < 100", 100.0, 130.0),
    ("Cardiac Health & Coagulation", "Cholesterol HDL"): high_good_range_target("> 40; target 55 - 80", 40.0, 55.0, 80.0, 100.0),
    ("Cardiac Health & Coagulation", "Cholesterol Total"): optimal_range_target("< 190; target 120 - 170", 100.0, 120.0, 170.0, 190.0),
    ("Cardiac Health & Coagulation", "Triglycerides"): low_good_target("< 150; target < 80", 80.0, 150.0),
    ("Cardiac Health & Coagulation", "Lipoprotein (a)"): low_good_target("< 75; target < 30", 30.0, 75.0),
    ("Cardiac Health & Coagulation", "Homocysteine"): low_good_target("< 15.0; target < 8", 8.0, 15.0),
    ("Cardiac Health & Coagulation", "NT-proBNP"): low_good_target("< 125; target < 50", 50.0, 125.0),
    ("Cardiac Health & Coagulation", "Creatine Kinase (CK)"): low_good_target("20 - 200; target <= 200", 200.0, 350.0),
    ("Cardiac Health & Coagulation", "Myoglobin"): optimal_range_target("28.00 - 72.00; target 28 - 50", 28.0, 28.0, 50.0, 72.0),
    ("Cardiac Health & Coagulation", "D-dimer"): low_good_target("< 500; target < 250", 250.0, 500.0),
    ("Cardiac Health & Coagulation", "Fibrinogen"): optimal_range_target("2.0 - 4.0; target 2.0 - 3.2", 2.0, 2.0, 3.2, 4.0),
    ("Cardiac Health & Coagulation", "INR"): optimal_range_target("0.80 - 1.20; target 0.9 - 1.1", 0.8, 0.9, 1.1, 1.2),
    ("Cardiac Health & Coagulation", "APTT"): optimal_range_target("22.0 - 34.0; target 26 - 34", 22.0, 26.0, 34.0, 38.0),
    ("Cardiac Health & Coagulation", "PT"): optimal_range_target("10.0 - 15.0; target 10 - 13", 10.0, 10.0, 13.0, 15.0),
    ("Cardiac Health & Coagulation", "Prothrombin Index"): optimal_range_target("80 - 120; target 90 - 110", 80.0, 90.0, 110.0, 120.0),

    # Micronutrients
    ("Micronutrients", "Vitamin D3"): optimal_range_target("30 - 50; target 35 - 50", 30.0, 35.0, 50.0, 50.0),
    ("Micronutrients", "Vitamin B12"): optimal_range_target("197 - 771; target 400 - 900", 197.0, 400.0, 900.0, 1100.0),
    ("Micronutrients", "Ferritin"): optimal_range_target("30 - 400; target 50 - 150", 30.0, 50.0, 150.0, 400.0),
    ("Micronutrients", "Iron"): optimal_range_target("59 - 150; target 80 - 150", 59.0, 80.0, 150.0, 180.0),
    ("Micronutrients", "Transferrin"): optimal_range_target("2.00 - 3.60; target 2.2 - 3.2", 2.0, 2.2, 3.2, 3.6),
    ("Micronutrients", "Ceruloplasmin"): optimal_range_target("0.15 - 0.30; target 0.20 - 0.30", 0.15, 0.20, 0.30, 0.35),
    ("Micronutrients", "Folic Acid"): optimal_range_target("3.9 - 26.8; target 8 - 20", 3.9, 8.0, 20.0, 26.8),
    ("Micronutrients", "Magnesium"): optimal_range_target("1.60 - 2.60; target 2.0 - 2.3", 1.6, 2.0, 2.3, 2.6),
    ("Micronutrients", "Potassium"): optimal_range_target("3.5 - 5.1; target 4.0 - 4.8", 3.5, 4.0, 4.8, 5.1),
    ("Micronutrients", "Sodium"): optimal_range_target("136 - 145; target 138 - 142", 136.0, 138.0, 142.0, 145.0),
    ("Micronutrients", "Calcium (Total)"): optimal_range_target("8.60 - 10.00; target 9.0 - 9.8", 8.6, 9.0, 9.8, 10.0),
    ("Micronutrients", "Fosfor"): optimal_range_target("2.5 - 4.5; target 3.0 - 4.0", 2.5, 3.0, 4.0, 4.5),
    ("Micronutrients", "Zinc"): optimal_range_target("9 - 18; target 11 - 18", 9.0, 11.0, 18.0, 22.0),
    ("Micronutrients", "Vitamin B6"): optimal_range_target("5.7 - 55.1; target 10 - 50", 5.7, 10.0, 50.0, 55.1),
    ("Micronutrients", "Vitamin B1"): optimal_range_target("33.1 - 60.7; target 33.1 - 55", 33.1, 33.1, 55.0, 60.7),
    ("Micronutrients", "Vitamin A"): optimal_range_target("0.3 - 0.7; target 0.4 - 0.7", 0.3, 0.4, 0.7, 0.8),
    ("Micronutrients", "Vitamin E"): optimal_range_target("5 - 20; target 8 - 18", 5.0, 8.0, 18.0, 20.0),
    ("Micronutrients", "Vitamin C"): optimal_range_target("4 - 15; target 6 - 15", 4.0, 6.0, 15.0, 20.0),

    # Inflammation, tumor, infectious, toxicology
    ("Immunology & Inflammation", "CRP (hs)"): low_good_target("< 5.0; target < 1", 1.0, 5.0),
    ("Immunology & Inflammation", "IL-6"): low_good_target("< 7.0; target < 2", 2.0, 7.0),
    ("Immunology & Inflammation", "Calprotectin"): low_good_target("< 2.0; target < 1", 1.0, 2.0),
    ("Immunology & Inflammation", "Anti-TPO"): low_good_target("< 34.0; target < 9", 9.0, 34.0),
    ("Immunology & Inflammation", "Anti-TG"): low_good_target("< 115.0; target < 20", 20.0, 115.0),
    ("Immunology & Inflammation", "ASO"): low_good_target("< 200; target < 200", 200.0, 200.0),
    ("Tumor Markers", "PSA Total"): low_good_target("< 4.0; target < 1.0", 1.0, 4.0),
    ("Tumor Markers", "PSA Free/Total Ratio"): high_good_target("> 25; target >= 25", 25.0, 25.0),
    ("Tumor Markers", "CEA"): low_good_target("< 5.0; target < 3", 3.0, 5.0),
    ("Tumor Markers", "AFP (ng/ml)"): low_good_target("< 7.0; target < 5", 5.0, 7.0),
    ("Tumor Markers", "AFP (IU/ml)"): low_good_target("< 5.8; target < 5", 5.0, 5.8),
    ("Tumor Markers", "CA 19-9"): low_good_target("< 34.0; target < 20", 20.0, 34.0),
    ("Tumor Markers", "S-100"): low_good_target("< 0.15; target < 0.10", 0.10, 0.15),
    ("Toxicology (Urine)", "Arsenic"): low_good_target("< 15.0; target < 15", 15.0, 15.0),
    ("Toxicology (Urine)", "Cadmium"): low_good_target("< 0.8; target < 0.2", 0.2, 0.8),
    ("Toxicology (Urine)", "Chromium"): low_good_target("< 0.6; target < 0.6", 0.6, 0.6),
    ("Toxicology (Urine)", "Nickel"): low_good_target("< 3.0; target < 1.0", 1.0, 3.0),
    ("Toxicology (Urine)", "Glyphosate"): low_good_target("< 1.40; target < 1.40", 1.4, 1.4),

    # Hormones
    ("Hormonal Panel", "Testosterone (Total)"): high_good_range_target("9.2 - 33.0; target 20 - 33", 9.2, 20.0, 33.0, 40.0),
    ("Hormonal Panel", "Testosterone (Free)"): optimal_range_target("9.10 - 32.20; target 15 - 30", 9.1, 15.0, 30.0, 32.2),
    ("Hormonal Panel", "Estradiol (E2)"): optimal_range_target("41 - 159; target 70 - 160", 41.0, 70.0, 160.0, 160.0),
    ("Hormonal Panel", "Prolactin"): optimal_range_target("4.04 - 15.20; target 5 - 15", 4.04, 5.0, 15.0, 20.0),
    ("Hormonal Panel", "Cortisol"): optimal_range_target("4.8 - 19.5; target 8 - 18", 4.8, 8.0, 18.0, 19.5),
    ("Hormonal Panel", "TSH"): optimal_range_target("0.27 - 4.20; target 0.5 - 2.5", 0.27, 0.5, 2.5, 4.2),
    ("Hormonal Panel", "Free T3 (FT3)"): optimal_range_target("3.10 - 6.80; target 4.5 - 6.2", 3.1, 4.5, 6.2, 6.8),
    ("Hormonal Panel", "Free T4 (FT4)"): optimal_range_target("11.90 - 21.60; target 14 - 18", 11.9, 14.0, 18.0, 21.6),
    ("Hormonal Panel", "LH"): optimal_range_target("1.70 - 8.60; target 2 - 8", 1.7, 2.0, 8.0, 8.6),
    ("Hormonal Panel", "FSH"): optimal_range_target("1.5 - 12.4; target 1.5 - 6", 1.5, 1.5, 6.0, 12.4),
    ("Hormonal Panel", "SHBG"): optimal_range_target("18.3 - 54.1; target 25 - 50", 18.3, 25.0, 50.0, 54.1),
    ("Hormonal Panel", "DHEA-SO4"): optimal_range_target("88.9 - 427; target 150 - 350", 88.9, 150.0, 350.0, 427.0),
    ("Hormonal Panel", "Progesterone"): low_good_target("< 0.474; target < 0.474", 0.474, 0.474),
    ("Hormonal Panel", "17-OH Progesterone"): optimal_range_target("0.37 - 2.87; target 0.7 - 2.5", 0.37, 0.7, 2.5, 2.87),
    ("Hormonal Panel", "IGF-1"): optimal_range_target("61 - 271; target 100 - 220", 61.0, 100.0, 220.0, 271.0),
    ("Hormonal Panel", "HCG-Beta"): low_good_target("< 2.60; target < 1", 1.0, 2.6),
}

no_score_markers = {
    ("Vitals & Functional Health", "Body Mass"),
    ("Vitals & Functional Health", "Height"),
    ("Vitals & Functional Health", "Maximum Heart Rate"),
    ("Vitals & Functional Health", "Nerve Health Score"),
    ("Vitals & Functional Health", "Max HRV"),
    ("Urine Culture", "Colony Count"),
    ("Urine Culture", "Penicillin"),
    ("Urine Culture", "Levofloxacin"),
    ("Urine Culture", "Vancomycin"),
    ("Urine Culture", "Trimethoprim/Sulfamethoxazole"),
    ("Urine Culture", "Nitrofurantoin"),
}

def numeric_from_result(val_str):
    val_clean = re.sub(r'[^\d.<>-]', '', val_str.split('(')[0])
    if not val_clean:
        return None

    try:
        return float(re.sub(r'[<> ]', '', val_clean))
    except ValueError:
        return None

def numeric_pair_from_result(val_str):
    numbers = re.findall(r'\d+(?:\.\d+)?', val_str)
    if len(numbers) < 2:
        return None
    return float(numbers[0]), float(numbers[1])

def calculate_high_good_range_score(val, target):
    low = target["low"]
    optimal_min = target["optimal_min"]
    optimal_max = target["optimal_max"]
    high_limit = target.get("high_limit")

    if val < low:
        return 1.0 + ((low - val) / low) if low != 0 else 1.0

    if val < optimal_min:
        span = optimal_min - low
        if span <= 0:
            return 0.4
        return 1.0 - (((val - low) / span) * 0.6)

    if val <= optimal_max:
        return 0.35

    if high_limit is None:
        return 0.8

    if val <= high_limit:
        span = high_limit - optimal_max
        if span <= 0:
            return 1.2
        return 0.8 + (((val - optimal_max) / span) * 0.4)

    return 1.2 + ((val - high_limit) / high_limit) if high_limit != 0 else 1.2

def relative_distance(value, limit):
    return value / abs(limit) if limit != 0 else 1.0

def calculate_low_good_score(val, target):
    low_limit = target.get("low_limit")
    optimal_max = target["optimal_max"]
    high_limit = target["high_limit"]

    if low_limit is not None and val < low_limit:
        return 1.0 + relative_distance(low_limit - val, low_limit)

    if val <= optimal_max:
        return 0.35

    span = high_limit - optimal_max
    if val <= high_limit:
        if span <= 0:
            return 1.0
        return 0.35 + (((val - optimal_max) / span) * 0.65)

    return 1.0 + relative_distance(val - high_limit, high_limit)

def calculate_high_good_score(val, target):
    low_limit = target["low_limit"]
    optimal_min = target["optimal_min"]
    high_limit = target.get("high_limit")

    if high_limit is not None and val > high_limit:
        return 1.0 + relative_distance(val - high_limit, high_limit)

    if val >= optimal_min:
        return 0.35

    if val >= low_limit:
        span = optimal_min - low_limit
        if span <= 0:
            return 1.0
        return 1.0 - (((val - low_limit) / span) * 0.65)

    return 1.0 + relative_distance(low_limit - val, low_limit)

def calculate_optimal_range_score(val, target):
    low_limit = target["low_limit"]
    optimal_min = target["optimal_min"]
    optimal_max = target["optimal_max"]
    high_limit = target["high_limit"]

    if val < low_limit:
        return 1.0 + relative_distance(low_limit - val, low_limit)

    if val < optimal_min:
        span = optimal_min - low_limit
        if span <= 0:
            return 0.35
        return 1.0 - (((val - low_limit) / span) * 0.65)

    if val <= optimal_max:
        return 0.35

    if val <= high_limit:
        span = high_limit - optimal_max
        if span <= 0:
            return 1.0
        return 0.35 + (((val - optimal_max) / span) * 0.65)

    return 1.0 + relative_distance(val - high_limit, high_limit)

def calculate_target_score(val, target):
    target_type = target["type"]

    if target_type == "high_good_range":
        return calculate_high_good_range_score(val, target)
    if target_type == "low_good":
        return calculate_low_good_score(val, target)
    if target_type == "high_good":
        return calculate_high_good_score(val, target)
    if target_type == "optimal_range":
        return calculate_optimal_range_score(val, target)

    return None

def calculate_blood_pressure_score(val_str, target):
    pair = numeric_pair_from_result(val_str)
    if pair is None:
        return None

    systolic, diastolic = pair
    systolic_score = calculate_optimal_range_score(systolic, target["systolic"])
    diastolic_score = calculate_optimal_range_score(diastolic, target["diastolic"])
    return max(systolic_score, diastolic_score)

def target_reference(category, marker, ref):
    target = target_overrides.get((category, marker))
    if target:
        return target["reference"]
    return ref

def calculate_score(val_str, ref_range, category=None, marker=None):
    if val_str in ["-", "—", None, ""]:
        return None
    if (category, marker) in no_score_markers:
        return None

    target = target_overrides.get((category, marker))
    if target:
        if target["type"] == "blood_pressure":
            return calculate_blood_pressure_score(val_str, target)
        val = numeric_from_result(val_str)
        if val is None:
            return None
        score = calculate_target_score(val, target)
        if score is not None:
            return score
        
    # Textual Perfect Matches
    text_val = val_str.lower().strip()
    if text_val in ["non-reactive", "negative", "not detected", "absent", "normal", "normal sinus rhythm", "minor"]:
        return 0.0
    if text_val.startswith("normal "):
        return 0.0
    if text_val in ["positive", "reactive", "detected", "present"]:
        return 3.0

    # Handle exact matches like "< 30.0" and "< 30.0"
    if val_str.strip() == ref_range.strip() and "<" in val_str:
        return 0.0

    val = numeric_from_result(val_str)
    if val is None:
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

def format_cell_html(val, ref, category=None, marker=None):
    score = calculate_score(val, ref, category, marker)
    if score is None:
        return val
    color, _ = get_color_hex(score)
    target = target_overrides.get((category, marker))
    arrow = "" if target and target["type"] == "blood_pressure" else get_direction(val, ref)
    suffix = f" {arrow}" if arrow else ""
    return f'<span style="color:{color}; font-weight:bold;">{val}{suffix}</span>'

def format_cell_md(val, ref, category=None, marker=None):
    score = calculate_score(val, ref, category, marker)
    if score is None:
        return val
    _, emoji = get_color_hex(score)
    target = target_overrides.get((category, marker))
    arrow = "" if target and target["type"] == "blood_pressure" else get_direction(val, ref)
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

def trend_score(value, ref, category, marker=None):
    if value in missing_values or ref in missing_values or ref == "-":
        return None

    score = calculate_score(value, ref, category, marker)
    if score is not None:
        return score

    text_value = value.lower().strip()
    optimal_terms = [
        "not detected", "absent", "normal", "clear", "negative", "non-reactive", "neg",
        "light yellow", "yellow", "pale yellow"
    ]
    bad_terms = ["present", "detected", "cloudy", "turbid", "bloody", "positive", "reactive"]

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

def target_directional_percent_delta(current_val, previous_val, target):
    if previous_val == 0:
        return None

    current_score = calculate_target_score(current_val, target)
    previous_score = calculate_target_score(previous_val, target)
    if current_score is None or previous_score is None:
        return None

    # Directional trend only adds signal when the value moves in the intended
    # direction without worsening the target score.
    if current_score > previous_score + 1e-9:
        return None

    target_type = target["type"]
    if target_type == "low_good":
        return (previous_val - current_val) / abs(previous_val)

    if target_type == "high_good":
        high_limit = target.get("high_limit")
        if high_limit is not None and current_val > high_limit:
            return None
        return (current_val - previous_val) / abs(previous_val)

    if target_type == "high_good_range":
        if current_val > target["optimal_max"]:
            return None
        return (current_val - previous_val) / abs(previous_val)

    return None

def directional_percent_delta(current, previous, ref, category=None, marker=None):
    current_val = numeric_value(current)
    previous_val = numeric_value(previous)
    if current_val is None or previous_val is None or previous_val == 0:
        return None

    target = target_overrides.get((category, marker))
    if target:
        return target_directional_percent_delta(current_val, previous_val, target)

    if re.match(r'<\s*([-\d.]+)', ref):
        return (previous_val - current_val) / abs(previous_val)

    if re.match(r'>\s*([-\d.]+)', ref):
        return (current_val - previous_val) / abs(previous_val)

    return None

def classify_trend(values, ref, category, marker=None):
    comparable = []
    for value in values:
        score = trend_score(value, ref, category, marker)
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
    percent_delta = directional_percent_delta(current_value, previous_value, ref, category, marker)

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

def format_trend_html(values, ref, category, marker=None):
    trend = classify_trend(values, ref, category, marker)
    if trend is None:
        return "-"

    definition = trend_definitions[trend]
    return definition["emoji"]

def format_trend_md(values, ref, category, marker=None):
    trend = classify_trend(values, ref, category, marker)
    if trend is None:
        return "-"

    definition = trend_definitions[trend]
    return definition["emoji"]

def category_has_trends(rows, category):
    for row in rows:
        name, values, _, ref = split_result_row(row)
        if classify_trend(values, ref, category, name) is not None:
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
    "Vitals & Functional Health": [
        ("Blood Pressure", "108/70", "-", "-", "-", "mmHg", "< 120 / < 80"),
        ("Nighttime BP Dip", "16.7", "-", "-", "-", "%", "10 - 20"),
        ("Resting Heart Rate", "~65", "-", "-", "-", "bpm", "60 - 100"),
        ("Sleeping Heart Rate", "56", "-", "-", "-", "bpm", "40 - 80"),
        ("Maximum Heart Rate", "180", "-", "-", "-", "bpm", "-"),
        ("ECG Rhythm", "normal sinus rhythm", "-", "-", "-", "Status", "normal sinus rhythm"),
        ("ECG Heart Rate", "68", "-", "-", "-", "bpm", "50 - 100"),
        ("Heart Sounds", "normal (no signs of valvular heart disease)", "-", "-", "-", "Status", "normal"),
        ("PWV", "6.1", "-", "-", "-", "m/s", "< 10"),
        ("VO2max", "43", "-", "-", "-", "ml/kg/min", "> 35"),
        ("Respiratory Rate (Sleep)", "12.4", "-", "-", "-", "/min", "12 - 20"),
        ("Body Mass", "83", "-", "-", "-", "kg", "-"),
        ("Height", "180", "-", "-", "-", "cm", "-"),
        ("BMI", "25.6", "-", "-", "-", "kg/m^2", "18.5 - 24.9"),
        ("Body Fat", "17.4", "-", "-", "-", "%", "10 - 20"),
        ("Muscle", "78.6", "-", "-", "-", "%", "> 70"),
        ("Temperature", "36.9", "-", "-", "-", "C", "36.1 - 37.2"),
        ("Sleep Apnea AHI", "2", "-", "-", "-", "events/h", "< 5"),
        ("Nerve Health Score", "70", "-", "-", "-", "score", "-"),
        ("Max HRV", "48", "-", "-", "-", "ms", "-"),
        ("Sleep Duration", "8", "-", "-", "-", "h", ">= 7"),
        ("REM Sleep", "2", "-", "-", "-", "h", "1.5 - 2.3"),
        ("Deep Sleep", "1", "-", "-", "-", "h", "about 1 - 2"),
        ("Stress", "minor", "-", "-", "-", "", "low/minor")
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
    "Urine Culture": [
        ("Urine Culture", "positive", "-", "-", "-", "Status", "negative"),
        ("Colony Count", "2 x 10^4", "-", "-", "-", "CFU/mL", "-"),
        ("Streptococcus agalactiae", "detected", "-", "-", "-", "Status", "not detected"),
        ("Penicillin", "susceptible", "-", "-", "-", "", "-"),
        ("Levofloxacin", "susceptible (increased exposure)", "-", "-", "-", "", "-"),
        ("Vancomycin", "susceptible", "-", "-", "-", "", "-"),
        ("Trimethoprim/Sulfamethoxazole", "susceptible", "-", "-", "-", "", "-"),
        ("Nitrofurantoin", "susceptible", "-", "-", "-", "", "-")
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
        ("Cystatin C", "0.80", "-", "-", "-", "mg/l", "0.51 - 1.05"),
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
        ("Myoglobin", "33.40", "24.30", "42.60", "-", "ng/ml", "28.00 - 72.00"),
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
        ("IL-6", "<1.5", "< 1.5", "1.6", "-", "pg/ml", "< 7.0"),
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
        ("Chlamydia IgM", "2.0", "2.7", "2.7", "2.7", "NTU", "< 9"),
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
    "Stool Culture": [
        ("Salmonella species", "negative", "-", "-", "-", "Status", "negative"),
        ("Shigella species", "negative", "-", "-", "-", "Status", "negative"),
        ("Yersinia species", "negative", "-", "-", "-", "Status", "negative"),
        ("Aeromonas species", "negative", "-", "-", "-", "Status", "negative"),
        ("Plesiomonas species", "negative", "-", "-", "-", "Status", "negative")
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
    "Vitals & Functional Health": [
        {
            "text": "BMI is included as a population screening metric but is interpreted in context of body fat and muscle percentage, not as a standalone body-composition diagnosis.",
            "markers": [
                {"rows": ["Body Mass", "Height", "BMI", "Body Fat", "Muscle"], "target": "value", "dates": ["2026-07"]},
            ],
        },
        {
            "text": "Maximum heart rate, max HRV, and nerve health score are device- or context-dependent metrics, so they are tracked but intentionally not scored against a universal clinical target.",
            "markers": [
                {"rows": ["Maximum Heart Rate", "Max HRV", "Nerve Health Score"], "target": "value", "dates": ["2026-07"]},
            ],
        },
    ],
    "Urinalysis (General)": [
        {
            "text": "Specific gravity trend likely reflects high hydration plus extremely low salt intake for the looksmaxxing goal of reducing facial puffiness.",
            "markers": [
                {"row": "Specific Gravity", "target": "trend"},
            ],
        },
    ],
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
    "Urine Culture": [
        {
            "text": "The 2026-07 urine culture was reported positive, with Streptococcus agalactiae growth at 2 x 10^4 CFU/mL.",
            "markers": [
                {"rows": ["Urine Culture", "Colony Count", "Streptococcus agalactiae"], "target": "value", "dates": ["2026-07"]},
            ],
        },
        {
            "text": "Susceptibility follows the PDF's EUCAST 16.0 interpretation: levofloxacin is susceptible only with increased exposure, and the nitrofurantoin result applies to uncomplicated UTI and not to other nitrofuran drugs.",
            "markers": [
                {"rows": ["Levofloxacin", "Nitrofurantoin"], "target": "value", "dates": ["2026-07"]},
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
            "text": "Total testosterone is scored with a high-normal male target: high-normal natural values are treated as favorable rather than automatically adverse.",
            "markers": [
                {"row": "Testosterone (Total)", "target": "trend"},
                {"row": "Testosterone (Total)", "target": "value", "dates": ["2026-07"]},
            ],
        },
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
            display_ref = target_reference(category, name, ref)
            
            # Use specific formatter for Urinalysis
            if "Urinalysis" in category:
                cells = [format_cell_html_urine(values[idx], ref) for idx in active_indexes]
            else:
                cells = [format_cell_html(values[idx], display_ref, category, name) for idx in active_indexes]
            
            html += f"<tr><td><b>{name}</b></td>"
            if include_trend:
                trend_cell = format_trend_html(values, display_ref, category, name)
                trend_cell = add_note_sup_html(trend_cell, note_numbers(category, name, "trend"))
                html += f"<td>{trend_cell}</td>"
            for idx, cell in zip(active_indexes, cells):
                cell = add_note_sup_html(cell, note_numbers(category, name, "value", date_columns[idx]))
                html += f"<td>{cell}</td>"
            html += f"<td>{unit}</td><td>{display_ref}</td></tr>"
        html += "</table>"
        html += render_result_notes_html(category)
    
    # Add Imaging Section
    html += imaging_data.replace("## ", "<h2>").replace("### ", "<h3>").replace("\n- ", "<br>• ").replace("\n", "<br>")

    # Legend
    html += "<h3>🎨 Color Legend</h3><ul>"
    html += "<li><span style='color:#00008b; font-weight:bold;'>● Dark Blue</span>: Target / low-risk</li>"
    html += "<li><span style='color:#00bfff; font-weight:bold;'>● Light Blue</span>: Near target / good</li>"
    html += "<li><span style='color:#006400; font-weight:bold;'>● Dark Green</span>: Acceptable</li>"
    html += "<li><span style='color:#32cd32; font-weight:bold;'>● Light Green</span>: Normal but not ideal</li>"
    html += "<li><span style='color:#ffd700; font-weight:bold;'>● Yellow</span>: Watch / mild deviation</li>"
    html += "<li><span style='color:#ffa500; font-weight:bold;'>● Light Orange</span>: Concern / significant deviation</li>"
    html += "<li><span style='color:#ff4500; font-weight:bold;'>● Dark Orange</span>: Major deviation</li>"
    html += "<li><span style='color:#dc3545; font-weight:bold;'>● Light Red</span>: Severe abnormality</li>"
    html += "<li><span style='color:#8b0000; font-weight:bold;'>● Dark Red</span>: Critical</li>"
    html += "</ul>"
    html += "<p class='note'>Single-result colors use marker-specific health targets when available, otherwise the lab reference range or qualitative reference. Blue does not mean higher or lower is always better; capped high-good targets are used where current evidence supports an upper comfort band.</p>"

    html += "<h3>Trend Legend</h3><ul>"
    for label, definition in trend_definitions.items():
        html += f"<li><span style='font-weight:bold;'>{definition['emoji']} {label}</span>: {definition['description'].capitalize()}</li>"
    html += "<li><b>-</b>: not enough comparable completed results</li>"
    html += "</ul>"
    html += "<p class='note'>Trend compares the latest completed result with the previous completed result using the health-target score; lower score is better. For directional targets, a directional improvement of at least 7.5% also counts as slight improvement.</p>"

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
            display_ref = target_reference(category, name, ref)
            
            # Use specific formatter for Urinalysis
            if "Urinalysis" in category:
                cells = [format_cell_md_urine(values[idx], ref) for idx in active_indexes]
            else:
                cells = [format_cell_md(values[idx], display_ref, category, name) for idx in active_indexes]
            
            line = f"| **{name}** |"
            if include_trend:
                trend_cell = format_trend_md(values, display_ref, category, name)
                trend_cell = add_note_sup_md(trend_cell, note_numbers(category, name, "trend"))
                line += f" {trend_cell} |"
            for idx, cell in zip(active_indexes, cells):
                cell = add_note_sup_md(cell, note_numbers(category, name, "value", date_columns[idx]))
                line += f" {cell} |"
            line += f" {unit} | {display_ref} |"
            md += line + "\n"
        md += render_result_notes_md(category)
            
        md += "\n"

    # Add Imaging Section
    md += imaging_data + "\n"

    # Legend
    md += "### 🎨 Color Legend\n"
    md += "*   🔵 **Target / low-risk**: At target or very close to target\n"
    md += "*   🟢 **Acceptable / normal**: Clinically acceptable but not ideal target\n"
    md += "*   🟡 **Watch**: Mild meaningful deviation from target or range\n"
    md += "*   🟠 **Concern**: Significant deviation from target or range\n"
    md += "*   🔴 **Critical**: Severe or critical deviation\n\n"
    md += "> **Color method:** Single-result emojis use marker-specific health targets when available, otherwise the lab reference range or qualitative reference. Blue does not mean higher or lower is always better; capped high-good targets are used where current evidence supports an upper comfort band.\n\n"
    md += "### Trend Legend\n"
    for label, definition in trend_definitions.items():
        md += f"*   {definition['emoji']} **{label}**: {definition['description'].capitalize()}\n"
    md += "*   **-**: Not enough comparable completed results\n\n"
    md += "> **Trend method:** Compares the latest completed result with the previous completed result using the health-target score; lower score is better. For directional targets, a directional improvement of at least 7.5% also counts as slight improvement.\n\n"
    md += "> **Note:** See `results.html` for detailed color gradients.\n"

    with open("results.md", "w", encoding="utf-8") as f:
        f.write(md)

# Run both
generate_html_report()
generate_md_report()
