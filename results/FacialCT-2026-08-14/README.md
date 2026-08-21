# Facial CT — 2026-08-14

Original DICOM file-set for a non-contrast CT of the facial skeleton (`TK TWARZOCZASZKI`).

- Import `DICOMDIR` into a PACS or DICOM viewer. If the application does not support `DICOMDIR`, import the complete `IMAGE` directory instead.
- Keep `DICOMDIR` and the `IMAGE` hierarchy together; the directory records reference the original relative paths.
- The study contains 905 DICOM objects in 9 series, including four 1 mm reconstruction series, two topograms, the scanner protocol, and structured dose/acquisition reports.
- The source disc did not contain a narrative report. LUX MED issued the official report on 2026-08-20; a privacy-safe clinical transcription and English translation are included below.
- Legacy viewer applications and runtime files from the source disc are intentionally excluded.

## Official radiology report — 2026-08-20

- **Study:** Non-contrast CT of the facial skeleton
- **Study date:** 2026-08-14
- **Report date:** 2026-08-20
- **Scanner:** Siemens Somatom Go UP
- **Clinical indication:** Facial asymmetry; examination for qualification for surgery

This is a privacy-safe transcription of the clinical portion of the official LUX MED report. The source image is intentionally not included because it displays the patient's address, date of birth, PESEL, medical record identifiers, and certificate details.

### Original report — Polish

#### Opis badania radiologicznego

TK twarzoczaszki bez cm.

Obustronnie obecne kanały nerwu podoczodołowego w obrębie zatok szczękowych z kostnymi przegrodami tworzące komórki w obrębie zatoki komunikujące się z kompleksem U-P przy ujściach.

Niewielkie zgrubienia śluzówki we wszystkich zatokach obocznych nosa, największe w zatokach szczękowych.

Obustronnie obrzęknięta śluzówka kompleksów U-P z ich odcinkowymi niedrożnościami.

Keros 2.

Niewielkie lewowypukłe skrzywienie przegrody nosa.

Przewody nosowe drożne.

Ograniczenia kostne zatok bez cech lizy czy sklerotycznej przebudowy.

W obrębie tkanki podskórnej twarzoczaszki, głównie policzków, widoczne linijne smużaste zwapnienia — poiniekcyjne?

#### Wnioski

Obustronnie obecne kanały kostne nerwów podoczodołowych — wariant anatomiczny.

### English translation

#### Radiological description

Non-contrast CT of the facial skeleton.

Bilateral infraorbital nerve canals are present within the maxillary sinuses, with bony septa forming cells within the sinuses that communicate with the ostiomeatal complexes at the ostia.

Mild mucosal thickening is present in all paranasal sinuses, greatest in the maxillary sinuses.

The mucosa of both ostiomeatal complexes is swollen, with segmental obstruction.

Keros type II.

Slight left-convex deviation of the nasal septum.

The nasal passages are patent.

The bony boundaries of the sinuses show no signs of lysis or sclerotic remodelling.

Linear, streak-like calcifications are visible in the subcutaneous tissues of the face, mainly the cheeks—possibly post-injection.

#### Conclusion

Bilateral bony infraorbital nerve canals—an anatomical variant.

### Scope note

The report is a general facial CT interpretation. It does not include a formal orthodontic or orthognathic cephalometric analysis and does not quantify SNA, SNB, ANB, Wits appraisal, overjet, overbite, chin projection, or surgical movements.

### Patient-history correlation — not part of the official report

The patient reports previous medial facial injections with Sculptra (poly-L-lactic acid) and Radiesse (calcium hydroxylapatite). Radiesse is the more likely explanation for the reported linear, streak-like cheek calcifications: its calcium-hydroxylapatite particles are radiopaque, are clearly visible on CT, and characteristically appear as high-attenuation linear streaks or clumps. Sculptra can also be visible on CT but more commonly appears as soft-tissue attenuation with surrounding subcutaneous-fat stranding rather than mineral-density streaks. The location and morphology described by the radiologist therefore strongly support post-injection Radiesse deposits, assuming they correspond to the treated areas.

This imaging appearance alone does not establish a filler complication. Clinical review is appropriate if there are persistent hard or tender nodules, redness, swelling, pain, progressive asymmetry, or overlying skin changes.

References: [FDA Radiesse Instructions for Use](https://www.accessdata.fda.gov/cdrh_docs/pdf5/P050037C.pdf); [midface injectable-filler imaging review](https://pmc.ncbi.nlm.nih.gov/articles/PMC8051469/).

## Split ZIP archive

The archive is one ZIP file divided into three consecutive chunks so that it can be stored on GitHub:

1. [`FacialCT-2026-08-14.zip.001`](./FacialCT-2026-08-14.zip.001)
2. [`FacialCT-2026-08-14.zip.002`](./FacialCT-2026-08-14.zip.002)
3. [`FacialCT-2026-08-14.zip.003`](./FacialCT-2026-08-14.zip.003)

Download all three parts into the same directory and keep their filenames unchanged. Open or extract the `.zip.001` file with 7-Zip; it will read `.002` and `.003` automatically. If an archive application does not recognize the split set, concatenate the three files in numeric order to reconstruct `FacialCT-2026-08-14.zip`, then extract it normally.

After extraction, open or import `FacialCT-2026-08-14/DICOMDIR` in a PACS or DICOM viewer.
