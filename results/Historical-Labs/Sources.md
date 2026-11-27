# Historical laboratory sources

Reviewed from 11 supplied exports on 2026-11-21. They contain **13 unique observations from three specimen collection dates**: seven from 2015-01-14, one from 2022-03-17 and five from 2023-10-02. The November 2026 dates in the filenames identify downloads, not examinations.

The observations appear alongside later results in the normal Metabolic Health, Cardiac Health & Coagulation, Micronutrients and Infectious Diseases tables in `results.md` and `results.html`. The exact collection dates identify specimen results, not monthly averages. Existing row units, reference/goal displays and color rules remain the shared comparison scale; the original laboratory units, ranges and interpretation bands are preserved below. Decimal commas become decimal points; stored precision is preserved. The shared formatter removes all-zero fractions only for display. No source document prints a high/low flag for these observations, so report colors must not be read as original laboratory flags.

## Date and duplicate reconciliation

| Collection date | Unique results | Source reconciliation |
| :--- | ---: | :--- |
| 2015-01-14 | 7 | Three PDFs and one matching, undated CSV describe the same serum collection. The main panel was reported January 14, homocysteine January 15 and vitamin D January 16. The printed collection time `00:00` is retained as an unspecified time rather than a verified midnight collection. |
| 2022-03-17 | 1 | Three PDFs (two laboratory reports and an English certificate) and one CDA describe one swab and one negative SARS-CoV-2 RT-PCR. Collection was 19:32; the certificate/CDA specify 19:32:48. The performing-laboratory report was issued March 17 at 23:50:50; the main report was issued March 18 at 07:41:09. The CDA document timestamp in 2025 is not the collection date. |
| 2023-10-02 | 5 | The two-page PDF, CDA and undated CSV describe one serum lipid panel collected at 10:02. All five results are on PDF page 1; page 2 adds no observations. The CSV exposes different LDL precision, documented below. |

The two CSV files have no independent collection date. Their dates are established from matching PDF/CDA companions. Fasting status is not supplied for either serum panel. Duplicates are matched by specimen/date, test and report evidence; they are not additional measurements.

## 2015-01-14 serum results

| Report marker | Result | Source unit | Source reference / interpretation | Primary source page |
| :--- | ---: | :--- | :--- | :--- |
| Sodium | 141 | mmol/l | 136 - 145 | `wyniki-21_11_2026-16_16_31.pdf`, page 1 |
| Potassium | 4.2 | mmol/l | 3.5 - 5.1 | Same page |
| Calcium, total | 9.9 | mg/dl | 8.4 - 10.2 | Same page |
| Insulin | 16.4 | µIU/ml | 2.6 - 24.9 | Same page |
| Ferritin | 118.3 | ng/ml | 30.0 - 400.0 | Same page |
| Homocysteine | 10.74 | µmol/l | 0.00 - 12.00 | `wyniki-21_11_2026-16_16_25.pdf`, page 1 |
| Vitamin D, 25-OH | 18.40 | ng/ml | Deficiency &lt;10; insufficient 10-30; sufficient 30-100; toxicity &gt;100 | `wyniki-21_11_2026-16_16_21.pdf`, page 1 |

The vitamin D report provides interpretation categories rather than one reference interval. These historical categories remain documented here; its result joins the existing `Vitamin D3` comparison row. The CSV names this analyte `Witamina D3 metabolit 25(OH)`. Insulin uses chemiluminescence; ferritin uses Roche electrochemiluminescence on Cobas. The supplied panel has no glucose result, so it does not establish a paired HOMA-IR result. Display-unit aliases `uU/mL` for insulin and `umol/l` for homocysteine are numerically equivalent to the source `µIU/ml` and `µmol/l`; no numerical conversion is applied.

## 2022-03-17 SARS-CoV-2 RT-PCR

| Report marker | Result | Source unit | Source reference | Primary source page |
| :--- | :--- | :--- | :--- | :--- |
| SARS-CoV-2 RT-PCR | Negative | None printed | None printed | `wyniki-21_11_2026-16_17_33.pdf`, page 1 |

`Negatywny` is translated as `Negative`, preserving a completed qualitative result in Infectious Diseases. The comparison row uses the existing `Status` / `negative` convention; neither is an extra physical unit or a printed source interval. This result is never stored as numeric zero or a missing value.

The collection date is confirmed by the CDA's `documentationOf/serviceEvent/effectiveTime`, not its root document timestamp. The certificate and performing-laboratory copy confirm the same specimen. All four files count as one result.

## 2023-10-02 serum lipid panel

| Report marker | Result | Source unit | Source reference / recommendation | Method |
| :--- | ---: | :--- | :--- | :--- |
| Total cholesterol | 125 | mg/dl | 115 - 190 | Enzymatic-colorimetric, Cobas Pure |
| HDL cholesterol | 41 | mg/dl | &gt;40 | Enzymatic-colorimetric, Cobas Pure |
| Non-HDL cholesterol | 84 | mg/dl | &lt;130 moderate risk; &lt;100 high risk; &lt;85 very high risk; &lt;70 extreme risk | Calculated by the laboratory from measured values |
| LDL cholesterol | 73 | mg/dl | &lt;115 low risk; &lt;100 moderate risk; &lt;70 high risk; &lt;55 very high risk; &lt;40 extreme risk | Calculated by the laboratory using Friedewald |
| Triglycerides | 54 | mg/dl | &lt;150 fasting; &lt;175 non-fasting | Enzymatic-colorimetric, Cobas Pure |

All five values are on page 1 of `wyniki-21_11_2026-16_17_59.pdf`. The linked date note identifies LDL and non-HDL as **calculated**. They join the existing cholesterol rows as transcribed laboratory outputs, not new calculations performed by the report generator.

**LDL precision:** the PDF and CDA report `73mg/dl`, while `wyniki-21_11_2026-16_18_3.csv` reports `73,20mg/dl`. The displayed primary result remains `73`; the alternate `73.20` is retained here and in the source data. These representations are not counted separately, averaged or silently substituted. The CSV also preserves trailing decimals for some other values, such as total cholesterol `125,00` and non-HDL `84,00`, without a different numerical result.

The historical LDL/non-HDL targets do not establish a patient risk category, and fasting status is not given for the triglyceride recommendations. The source recommendations above remain unchanged. All five measurements use their existing comparison rows and shared report targets; importing these results does not replace any threshold or reference range.

## Source inventory

The linked originals below are included byte-for-byte. Their headers and metadata are unchanged. Names, addresses and personal/document identifiers are omitted only from the transcribed tables.

| Original filename | Pages | Collection | SHA-256 |
| :--- | :--- | :--- | :--- |
| [wyniki-21_11_2026-16_16_21.pdf](../wyniki-21_11_2026-16_16_21.pdf) | 1 | 2015-01-14 | `6a4160e4c4bf79f3167d67025e6e44660e9e096d98ee11fbc2c887f91a65b39c` |
| [wyniki-21_11_2026-16_16_25.pdf](../wyniki-21_11_2026-16_16_25.pdf) | 1 | 2015-01-14 | `5fc83fc3b93a378503559f2f645ccce8b5bb503bb04c9e5c7b7f65486ed1384c` |
| [wyniki-21_11_2026-16_16_31.pdf](../wyniki-21_11_2026-16_16_31.pdf) | 1 | 2015-01-14 | `0429e0a5129ceeb0c634488e13c574b13cd28b73abfa926d5a716145e552c9ae` |
| [wyniki-21_11_2026-16_17_1.csv](../wyniki-21_11_2026-16_17_1.csv) | CSV | 2015-01-14, matched | `81889e636e3a13b940821435191bceee1ca8d3f560203d80d55c5f2c2b4ff88a` |
| [wyniki-21_11_2026-16_17_30.cda](../wyniki-21_11_2026-16_17_30.cda) | CDA | 2022-03-17 | `4919aba282ef62e01ec00124077c2fc50d476766f1691a65bf8647069c3c281c` |
| [wyniki-21_11_2026-16_17_33.pdf](../wyniki-21_11_2026-16_17_33.pdf) | 1 | 2022-03-17 | `2525c99217a1e566167a09892cc585b4f848a0fe440e25e36ffada6b54013d69` |
| [wyniki-21_11_2026-16_17_35.pdf](../wyniki-21_11_2026-16_17_35.pdf) | 1 | 2022-03-17 | `6feda5e6659ad55846b931f2ec67ae2a09369d9a3c739970f7b38a4209621e9c` |
| [wyniki-21_11_2026-16_17_37.pdf](../wyniki-21_11_2026-16_17_37.pdf) | 1 | 2022-03-17 | `5d68c28de8b9e3092ba9615a02a9b41eb4ffcc846e3b42d804eda3b2c1a10570` |
| [wyniki-21_11_2026-16_17_59.pdf](../wyniki-21_11_2026-16_17_59.pdf) | 2 | 2023-10-02 | `f1f681e06a23b2c2b6a43f4900bcaf4a817a8f048c40cb8e7783f86803f13b99` |
| [wyniki-21_11_2026-16_18_1.cda](../wyniki-21_11_2026-16_18_1.cda) | CDA | 2023-10-02 | `845e713b531eea9b1a85bcd61e90af533557e7ca2b8783cc9b27967a20e2c4c5` |
| [wyniki-21_11_2026-16_18_3.csv](../wyniki-21_11_2026-16_18_3.csv) | CSV | 2023-10-02, matched | `dd00b2b90c577526bec4be8b0a7982fcc9f50804ff99b1772a876b65178f91b9` |

## Verification

All eight PDF pages were visually reviewed, including the second lipid-report page that contains no additional measurements. CSV values were reconciled against the PDFs. CDA observation values and specimen-event timestamps independently confirmed the PCR and lipid records. Several PDFs have unreliable extracted character mappings, so values were read from rendered pages rather than inferred from broken text extraction.
