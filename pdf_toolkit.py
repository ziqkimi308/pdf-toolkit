#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

try:
	from pypdf import PdfReader, PdfWriter, Transformation
	PYPDF_AVAILABLE = True
except ImportError:
	PYPDF_AVAILABLE = False
	print("Error: pypdf library required. Install with: pip install pypdf", file=sys.stderr)
	sys.exit(1)

# Utility functions

def validate_pdf(filepath: str) -> bool:
	"""
	Validate that a given file path points to a valid PDF.

    Checks performed:
    - File exists at the given path.
    - Path refers to a regular file (not a directory).
    - File can be opened and parsed by PdfReader (basic integrity check).

    Args:
        filepath (str): Path to the PDF file to validate.

    Returns:
        bool: True if the file exists, is a regular file, and can be read as a PDF. False otherwise, with an error message printed to stderr.

	"""

	path = Path(filepath)
	if not path.exists():
		print(f"Error: File not found: {filepath}", file=sys.stderr)
		return False
	if not path.is_file():
		print(f"Error: Not a file: {filepath}", file=sys.stderr)
		return False
	
	try:
		PdfReader(path)
		return True
	except Exception as e:
		print(f"Error: Invalid o corrupted PDF: {filepath} ({e})", file=sys.stderr)
		return False
	
def get_output_path(input_path: str, suffix: str, output: str | None = None) -> str:
	"""
	Generate an output PDF file path based on an input file.

    Behavior:
    - If `output` is provided, return it directly (may be relative, absolute, or just a filename).
    - If `output` is None, construct a new filename in the same directory as `input_path`,
      using the stem plus the given suffix, with `.pdf` extension.

    Example:
        get_output_path("docs/report.pdf", "signed")
        -> "docs/report_signed.pdf"

        get_output_path("docs/report.pdf", "signed", "custom.pdf")
        -> "custom.pdf"

    Returns:
        str: Path string (relative or absolute depending on input/output).

	"""

	if output:
		return output
	p = Path(input_path)
	return str(p.parent / f"{p.stem}_{suffix}.pdf")

# args handling functions

# merge
def handle_merge(args):
	"""
	Merge multiple PDF files into a single output file.

    Behavior:
    - Requires at least two input PDF files.
    - Validates each file before processing.
    - Iterates through all pages of each input file, adding them to a PdfWriter.
    - Finalizes the merge by writing all collected pages into one output PDF.

    Args:
        args: Parsed command-line arguments containing:
            - files (list[str]): Paths to input PDF files.
            - output (str | None): Optional output filename. Defaults to 'merged.pdf'.

    Returns:
        int: Exit code (0 for success, 1 for error).

	"""

	# min 2 pdf
	if len(args.files) < 2:
		print("Error: At least two PDF files are required for merging.", file=sys.stderr)
		return 1

	# validate all pdf
	for pdf_file in args.files:
		if not validate_pdf(pdf_file):
			return 1
	
	writer = PdfWriter()
	total_pages = 0

	# PdfWriter() works similar to Eloquent query builder
	# We keep chaining the query with add_page() and finalize with write()
	for pdf_file in args.files:
		reader = PdfReader(pdf_file)
		for page in reader.pages:
			writer.add_page(page)
			total_pages += 1
		print(f"Added: {pdf_file} ({len(reader.pages)} pages)")
	
	output = args.output or "merged.pdf"

	try:
		with open(output, 'wb') as file:
			writer.write(file)
		print(f"\n✓ Successfully merged {len(args.files)} files ({total_pages} total pages) into '{output}'")
	except Exception as e:
		print(f"Error writing output file: {e}", file=sys.stderr)
		return 1

	return 0

# split
def handle_split(args):
	"""
	Split a PDF into separate files based on selected pages.

    Behavior:
    - Validates the input PDF file.
    - Parses the --pages argument to determine which pages to extract.
    - Supports ranges (e.g., '1-3'), open-ended ranges ('-4', '6-'), and individual pages ('2,4,9').
    - Operates in two modes:
        * 'single': Creates one output file per extracted page.
        * else: Creates a single output file containing all extracted pages.
    - Writes extracted pages to the specified output directory.

    Args:
        args: Parsed command-line arguments containing:
            - file (str): Path to the input PDF.
            - pages (str | None): Page selection string.
            - mode (str): Extraction mode ('single' or combined).
            - output_dir (str | None): Directory for output files.
            - output (str | None): Optional output filename for combined mode.

    Returns:
        int: Exit code (0 for success, 1 for error).

	"""

	if not validate_pdf(args.file):
		return 1
	
	reader = PdfReader(args.file)
	total_pages = len(reader.pages)
	print(f"Input PDF: {args.file} ({total_pages} pages)")

	# Example inputs
	# --pages 1-2,5-8,10 or -4 or 6- or 2,4,9
	pages_to_extract = []
	if args.pages:
		for part in args.pages.split(','): # [1-2, 5-8, 10]
			part = part.strip()
			if '-' in part:
				start, end = part.split('-') # 1, 2
				start = int(start) if start else 1
				end = int(end) if end else total_pages
				pages_to_extract.extend(range(start, end+1)) # +1 for inclusivity
			else:
				pages_to_extract.append(int(part))
	
	# Create output path
	output_dir = Path(args.output_dir) if args.output_dir else Path(args.file).parent
	output_dir.mkdir(parents=True, exist_ok=True)

	base_name = Path(args.file).stem

	extracted_count = 0

	if args.mode == 'single':
		for page_num in pages_to_extract:
			
			# safety guard
			if page_num < 1 or page_num > total_pages:
				print(f"Warning: Page {page_num} out of range, skipping.")
				continue
			
			# chain the pdfwriter query
			writer = PdfWriter()
			writer.add_page(reader.pages[page_num - 1]) # page 1 index 0

			# serialize using write()
			# The main difference is here
			# Single mode creates a new file for each page (e.g. report_page_1.pdf, report_page_2.pdf, report_page_3.pdf)
			out_file = output_dir / f"{base_name}_page_{page_num}.pdf"
			with open(out_file, 'wb') as f:
				writer.write(f)
			print(f"  Extracted page {page_num} -> {out_file}")
			extracted_count += 1

	else:
		writer = PdfWriter()
		for page_num in pages_to_extract:

			# safety guard
			if page_num < 1 or page_num > total_pages:
				print(f"Warning: Page {page_num} out of range, skipping.")
				continue

			writer.add_page(reader.pages[page_num - 1])

			# The main difference is here
			# The logic in else writes all selected pages into the same file (e.g. report_extracted.pdf).
			# And the writer is initialized outside of loop
			out_file = args.output or str(output_dir / f"{base_name}_extracted.pdf")
			with open(out_file, 'wb') as f:
				writer.write(f)
			print(f"  Extracted {len(writer.pages)} pages -> {out_file}")

			extracted_count = len(writer.pages)
	
	print(f"\n✓ Successfully extracted {extracted_count} pages.")
	return 0

# handle extract text
def handle_extract_text(args):
	"""
	Extract text content from selected pages of a PDF.

    Behavior:
    - Validates the input PDF file.
    - Parses the --pages argument to determine which pages to process.
    - Extracts text from each selected page using PdfReader.
    - Handles cases where no text is extractable.
    - Writes extracted text to a .txt file, with page headers for clarity.

    Args:
        args: Parsed command-line arguments containing:
            - file (str): Path to the input PDF.
            - pages (str | None): Page selection string. Defaults to all pages if omitted.
            - output (str | None): Optional output filename. Defaults to '<stem>_text.txt'.

    Returns:
        int: Exit code (0 for success, 1 for error).

	"""

	# validate pdf
	if not validate_pdf(args.file):
		return 1

	reader = PdfReader(args.file)
	total_pages = len(reader.pages)

	# Example optional --pages argument
	# --pages 1-2,5-8,10 or -4 or 6- or 2,4,9
	pages = args.pages
	if pages:
		page_nums = []
		# split turns string into list even for single number like -4
		for part in pages.split(','):
			part = part.strip()
			if '-' in part:
				start, end = part.split("-")
				start = int(start) if start else 1
				end = int(end) if end else total_pages
				page_nums.extend(range(start, end+1))
			else:
				page_nums.append(int(part))
	else:
		page_nums = list(range(1, total_pages + 1))

	# actual extract
	all_text = []
	for page_num in page_nums:

		# safety guard 
		if page_num < 1 or page_num > total_pages:
			print(f"Warning: Page {page_num} out of range, skipping.")
			continue
		
		page = reader.pages[page_num - 1] # page = index + 1
		text = page.extract_text() # Pypdf extract function

		if text:
			all_text.append(f"--- Page {page_num} ---\n{text}\n")
		else:
			all_text.append(f"--- Page {page_num} ---\n[No extractable text]\n")
	
	# if all_text empty, means no extraction occurs
	if not all_text:
		print("No text extracted.", file=sys.stderr)
		return 1
	
	output = args.output or f"{Path(args.file).stem}_text.txt"

	try:
		with open(output, 'w', encoding='utf-8') as file:
			file.write('\n'.join(all_text))
		print(f"✓ Text extracted from {len(page_nums)} page(s) and saved to '{output}'")

	except Exception as e:
		print(f"Error writing output file: {e}", file=sys.stderr)
		return 1
	
	return 0

def handle_rotate(args):
	"""
    Rotate pages in a PDF file by a specified angle.

    Behavior:
    - Validates the input PDF file.
    - Parses the --pages argument to determine which pages to rotate.
    - Supports ranges (e.g., '1-3'), open-ended ranges ('-4', '6-'), 
      and individual pages ('2,4,9').
    - If no --pages argument is provided, rotates ALL pages.
    - Rotates selected pages by the specified angle (must be multiple of 90).
    - Keeps non-selected pages unchanged.
    - Writes the rotated PDF to an output file.

    Args:
        args: Parsed command-line arguments containing:
            - file (str): Path to the input PDF.
            - angle (int): Rotation angle in degrees (90, 180, 270, or -90, -180, -270).
            - pages (str | None): Optional page selection string. 
              Defaults to all pages if omitted.
            - output (str | None): Optional output filename. 
              Defaults to '<stem>_rotated_<angle>.pdf'.

    Returns:
        int: Exit code (0 for success, 1 for error).

    Example:
        # Rotate pages 1-3 by 90 degrees
        python pdf_tool.py rotate document.pdf --angle 90 --pages 1-3

        # Rotate only page 5 by 180 degrees
        python pdf_tool.py rotate document.pdf --angle 180 --pages 5

        # Rotate all pages by -90 degrees
        python pdf_tool.py rotate document.pdf --angle -90\
		
    """

	# validate pdf
	if not validate_pdf(args.file):
		return 1
	
	reader = PdfReader(args.file)
	writer = PdfWriter()

	total_pages = len(reader.pages)
	pages_to_rotate = []
	# If user provide --pages argument
	pages = args.pages
	if pages:
		for part in pages.split(","):
			part = part.strip()
			if '-' in part:
				start, end = part.split("-")
				start = int(start) if start else 1
				end = int(end) if end else total_pages
				pages_to_rotate.extend(range(start, end+1))
			else:
				pages_to_rotate.append(int(part))
	else:
		pages_to_rotate = list(range(1, total_pages + 1))

	for i, page in enumerate(reader.pages, start=1):
		if i in pages_to_rotate:
			page.rotate(args.angle)
		writer.add_page(page) # add_page is pypdf function
	
	output = args.output or get_output_path(args.file, f"rotated_{args.angle}")
	with open(output, 'wb') as file:
		writer.write(file)
	print(f"✓ Rotated {len(pages_to_rotate)} page(s) by {args.angle}° -> '{output}'")

	return 0