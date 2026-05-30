# PDF Toolkit

![Python](https://img.shields.io/badge/Python-3.x-blue) ![pypdf](https://img.shields.io/badge/library-pypdf-green) ![CLI](https://img.shields.io/badge/interface-CLI-lightgrey)

A command-line PDF utility built with `pypdf`. Supports merging, splitting, text extraction, page rotation, and watermarking — all from the terminal.

## Features

- **Merge** — combine multiple PDFs into one
- **Split** — extract pages individually or as a combined range
- **Extract text** — dump readable text from selected pages to a `.txt` file
- **Rotate** — rotate all or specific pages by 90°, 180°, or 270°
- **Watermark** — overlay a watermark PDF onto every page

## Requirements

```bash
pip install pypdf
```

Requires Python 3.x. No other dependencies.

## Usage

### Merge PDFs

```bash
python pdf_toolkit.py merge file1.pdf file2.pdf file3.pdf -o merged.pdf
```

Sample Output:
```bash
$ python pdf_toolkit.py merge samples/pdf-1.pdf samples/pdf-3.pdf samples/pdf-4.pdf -o samples/combined_report.pdf
Ignoring wrong pointing object 8 0 (offset 0)
Added: samples/pdf-1.pdf (1 pages)
Ignoring wrong pointing object 8 0 (offset 0)
Added: samples/pdf-3.pdf (3 pages)
Added: samples/pdf-4.pdf (4 pages)

✓ Successfully merged 3 files (8 total pages) into 'samples/combined_report.pdf'
```

### Split a PDF

```bash
# Extract pages 1–3 and page 5 into a single file
python pdf_toolkit.py split document.pdf --pages "1-3,5" -o extracted.pdf

# Save each page as its own file
python pdf_toolkit.py split document.pdf --mode single -d output_dir/
```

Sample Output:
```bash
$ python pdf_toolkit.py split samples/pdf-4.pdf --pages "1,3" -o samples/extracted.pdf
Input PDF: samples/pdf-4.pdf (4 pages)
  Extracted 1 pages -> samples/extracted.pdf
  Extracted 2 pages -> samples/extracted.pdf

✓ Successfully extracted 2 pages.
```

```bash
$ python pdf_toolkit.py split samples/pdf-4.pdf --pages "1,3" --mode single -d samples
Input PDF: samples/pdf-4.pdf (4 pages)
  Extracted page 1 -> samples\pdf-4_page_1.pdf
  Extracted page 3 -> samples\pdf-4_page_3.pdf

✓ Successfully extracted 2 pages.
```

### Extract text

```bash
# All pages
python pdf_toolkit.py extract-text document.pdf -o output.txt

# Specific pages
python pdf_toolkit.py extract-text document.pdf --pages "1-3,6" -o output.txt
```

Sample Output:
```bash
$ python pdf_toolkit.py extract-text samples/pdf-1.pdf -o samples/output.txt
✓ Text extracted from 1 page(s) and saved to 'samples/output.txt'
```

```bash
$ python pdf_toolkit.py extract-text samples/pdf-4.pdf --pages "1,3" -o samples/output.txt
✓ Text extracted from 2 page(s) and saved to 'samples/output.txt'
```

### Rotate pages

```bash
# Rotate pages 2–4 by 90 degrees
python pdf_toolkit.py rotate document.pdf --pages "2-4" --angle 90 -o rotated.pdf

# Rotate all pages by 180 degrees
python pdf_toolkit.py rotate document.pdf --angle 180
```

Sample Output:
```bash
$ python pdf_toolkit.py rotate samples/pdf-4.pdf --pages "2-4" --angle 90 -o samples/rotated.pdf
✓ Rotated 3 page(s) by 90° -> 'samples/rotated.pdf'
```

```bash
$ python pdf_toolkit.py rotate samples/pdf-3.pdf --angle 180
Ignoring wrong pointing object 8 0 (offset 0)
Ignoring wrong pointing object 8 0 (offset 0)
✓ Rotated 3 page(s) by 180° -> 'samples\pdf-3_rotated_180.pdf'
```

### Apply a watermark

```bash
python pdf_toolkit.py watermark document.pdf -w watermark.pdf -o watermarked.pdf
```

```bash
$ python pdf_toolkit.py watermark samples/pdf-3.pdf -w samples/watermark.pdf -o samples/watermarked.pdf
Ignoring wrong pointing object 8 0 (offset 0)
Ignoring wrong pointing object 8 0 (offset 0)
✓ Watermark applied to 3 page(s) -> 'samples/watermarked.pdf'
```

## Command reference

| Command        | Required args         | Options                                                      |
|----------------|-----------------------|--------------------------------------------------------------|
| `merge`        | `files...` (2+)       | `-o` output filename                                         |
| `split`        | `file`                | `--pages`, `--mode` (single/combined), `-o`, `-d` output dir |
| `extract-text` | `file`                | `--pages`, `-o` output `.txt`                                |
| `rotate`       | `file`, `--angle`     | `--pages`, `-o`                                              |
| `watermark`    | `file`, `-w` watermark PDF | `-o`                                                    |

### Page range syntax

The `--pages` flag accepts comma-separated ranges:

| Input       | Meaning           |
|-------------|-------------------|
| `1-3`       | Pages 1, 2, 3     |
| `-4`        | Pages 1 through 4 |
| `6-`        | Page 6 to last    |
| `2,4,9`     | Pages 2, 4, 9     |
| `1-3,5,8-`  | Mixed ranges      |

## Notes

- Watermarks must be supplied as a PDF file — the first page is used as the overlay
- Text extraction depends on the PDF being text-based (not a scanned image)
- Default output filenames are auto-generated if `-o` is omitted (e.g., `document_rotated_90.pdf`)
- `pypdf` may print warnings like `Ignoring wrong pointing object` for malformed PDFs — this is expected and does not affect output