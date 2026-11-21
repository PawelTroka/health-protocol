"""Historical observations mapped to the normal laboratory comparison rows.

Values and source units/ranges preserve the original reports. Display units are
numerically equivalent aliases of the existing rows. The ordinary report's
shared targets remain the comparison scale; source ranges are documented in
results/Historical-Labs/Sources.md alongside the unchanged original exports.
"""


HISTORICAL_LABS_SOURCE = "results/Historical-Labs/Sources.md"

HISTORICAL_LABS = (
    {"date": "2023-10-02", "category": "Cardiac Health & Coagulation", "marker": "Cholesterol Total",
     "value": "125", "unit": "mg/dL", "source_unit": "mg/dl", "source_reference": "115 - 190"},
    {"date": "2023-10-02", "category": "Cardiac Health & Coagulation", "marker": "Cholesterol HDL",
     "value": "41", "unit": "mg/dL", "source_unit": "mg/dl", "source_reference": ">40"},
    {"date": "2023-10-02", "category": "Cardiac Health & Coagulation", "marker": "Cholesterol Non-HDL",
     "value": "84", "unit": "mg/dL", "source_unit": "mg/dl",
     "source_reference": "<130 (moderate risk); <100 (high); <85 (very high); <70 (extreme)",
     "calculated": True},
    {"date": "2023-10-02", "category": "Cardiac Health & Coagulation", "marker": "Cholesterol LDL",
     "value": "73", "unit": "mg/dl", "source_unit": "mg/dl",
     "source_reference": "<115 (low risk); <100 (moderate); <70 (high); <55 (very high); <40 (extreme)",
     "calculated": True, "alternate_csv_value": "73.20"},
    {"date": "2023-10-02", "category": "Cardiac Health & Coagulation", "marker": "Triglycerides",
     "value": "54", "unit": "mg/dL", "source_unit": "mg/dl",
     "source_reference": "<150 (fasting); <175 (non-fasting)"},
    {"date": "2022-03-17", "category": "Infectious Diseases", "marker": "SARS-CoV-2 RT-PCR",
     "value": "Negative", "unit": "Status", "source_unit": None, "source_reference": None},
    {"date": "2015-01-14", "category": "Micronutrients", "marker": "Sodium",
     "value": "141", "unit": "mmol/l", "source_unit": "mmol/l", "source_reference": "136 - 145"},
    {"date": "2015-01-14", "category": "Micronutrients", "marker": "Potassium",
     "value": "4.2", "unit": "mmol/l", "source_unit": "mmol/l", "source_reference": "3.5 - 5.1"},
    {"date": "2015-01-14", "category": "Micronutrients", "marker": "Calcium (Total)",
     "value": "9.9", "unit": "mg/dL", "source_unit": "mg/dl", "source_reference": "8.4 - 10.2"},
    {"date": "2015-01-14", "category": "Metabolic Health", "marker": "Insulin",
     "value": "16.4", "unit": "uU/mL", "source_unit": "µIU/ml", "source_reference": "2.6 - 24.9"},
    {"date": "2015-01-14", "category": "Micronutrients", "marker": "Ferritin",
     "value": "118.3", "unit": "ng/ml", "source_unit": "ng/ml", "source_reference": "30.0 - 400.0"},
    {"date": "2015-01-14", "category": "Cardiac Health & Coagulation", "marker": "Homocysteine",
     "value": "10.74", "unit": "umol/l", "source_unit": "µmol/l", "source_reference": "0.00 - 12.00"},
    {"date": "2015-01-14", "category": "Micronutrients", "marker": "Vitamin D3",
     "value": "18.40", "unit": "ng/ml", "source_unit": "ng/ml",
     "source_reference": "<10 deficient; 10-30 insufficient; 30-100 sufficient; >100 toxic"},
)
