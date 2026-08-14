# Facial CT — 2026-08-14

Original DICOM file-set for a non-contrast CT of the facial skeleton (`TK TWARZOCZASZKI`).

- Import `DICOMDIR` into a PACS or DICOM viewer. If the application does not support `DICOMDIR`, import the complete `IMAGE` directory instead.
- Keep `DICOMDIR` and the `IMAGE` hierarchy together; the directory records reference the original relative paths.
- The study contains 905 DICOM objects in 9 series, including four 1 mm reconstruction series, two topograms, the scanner protocol, and structured dose/acquisition reports.
- The disc does not contain a radiologist's narrative report. Obtain that report separately from LUX MED and provide it alongside this file-set.
- Legacy viewer applications and runtime files from the source disc are intentionally excluded.

## GitHub archive parts

The four ZIP files next to this directory are independent archives sized for normal GitHub storage. Download all four and extract each into the same parent directory, allowing their shared `FacialCT-2026-08-14` folder to merge. Then open or import `FacialCT-2026-08-14/DICOMDIR`.
