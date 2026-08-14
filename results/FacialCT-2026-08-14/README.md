# Facial CT — 2026-08-14

Original DICOM file-set for a non-contrast CT of the facial skeleton (`TK TWARZOCZASZKI`).

- Import `DICOMDIR` into a PACS or DICOM viewer. If the application does not support `DICOMDIR`, import the complete `IMAGE` directory instead.
- Keep `DICOMDIR` and the `IMAGE` hierarchy together; the directory records reference the original relative paths.
- The study contains 905 DICOM objects in 9 series, including four 1 mm reconstruction series, two topograms, the scanner protocol, and structured dose/acquisition reports.
- The disc does not contain a radiologist's narrative report. Obtain that report separately from LUX MED and provide it alongside this file-set.
- Legacy viewer applications and runtime files from the source disc are intentionally excluded.

## Split ZIP archive

The archive is one ZIP file divided into three consecutive chunks so that it can be stored on GitHub:

1. [`FacialCT-2026-08-14.zip.001`](./FacialCT-2026-08-14.zip.001)
2. [`FacialCT-2026-08-14.zip.002`](./FacialCT-2026-08-14.zip.002)
3. [`FacialCT-2026-08-14.zip.003`](./FacialCT-2026-08-14.zip.003)

Download all three parts into the same directory and keep their filenames unchanged. Open or extract the `.zip.001` file with 7-Zip; it will read `.002` and `.003` automatically. If an archive application does not recognize the split set, concatenate the three files in numeric order to reconstruct `FacialCT-2026-08-14.zip`, then extract it normally.

After extraction, open or import `FacialCT-2026-08-14/DICOMDIR` in a PACS or DICOM viewer.
