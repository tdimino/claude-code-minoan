#!/usr/bin/env python3
"""
Mistral OCR PDF to Markdown Converter
Uses Mistral's dedicated OCR model (mistral-ocr-latest) for high-accuracy document processing.

API: https://docs.mistral.ai/capabilities/document_ai/basic_ocr
"""

import argparse
import base64
import logging
import os
import sys
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

try:
    from mistralai import Mistral
except ImportError:
    logger.error("mistralai not installed. Run: uv pip install mistralai --system")
    sys.exit(1)


def encode_pdf_to_base64(pdf_path: str) -> str:
    """Encode PDF file to base64 string."""
    logger.debug(f"Encoding PDF to base64: {pdf_path}")
    with open(pdf_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def ocr_pdf_with_mistral(pdf_path: str, api_key: str, pages: str = None) -> str:
    """
    OCR a PDF using Mistral's dedicated OCR API (mistral-ocr-latest).

    Args:
        pdf_path: Path to the PDF file
        api_key: Mistral API key
        pages: Optional page range (e.g., "1-10" or "5,7,9") - Note: currently processes full document

    Returns:
        Markdown text extracted from the PDF
    """
    client = Mistral(api_key=api_key)

    # Check file size
    file_size = os.path.getsize(pdf_path)
    file_size_mb = file_size / 1024 / 1024
    logger.info(f"File size: {file_size_mb:.1f}MB")

    if file_size > 50 * 1024 * 1024:  # 50MB limit
        logger.warning(f"Large file ({file_size_mb:.1f}MB). Consider using --chunked for files over 50MB.")

    # Encode PDF to base64
    logger.info(f"Encoding PDF: {pdf_path}")
    start_encode = time.time()
    pdf_base64 = encode_pdf_to_base64(pdf_path)
    logger.info(f"Encoding completed in {time.time() - start_encode:.1f}s")

    # Prepare the data URL
    data_url = f"data:application/pdf;base64,{pdf_base64}"

    logger.info("Starting OCR with mistral-ocr-latest...")
    start_ocr = time.time()

    try:
        # Use the dedicated OCR endpoint
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": data_url
            },
            include_image_base64=False  # Don't include images to save bandwidth
        )

        ocr_time = time.time() - start_ocr
        logger.info(f"OCR completed in {ocr_time:.1f}s")

        # Extract markdown from all pages
        markdown_parts = []
        total_pages = len(ocr_response.pages)
        logger.info(f"Processed {total_pages} pages")

        for page in ocr_response.pages:
            page_num = page.index + 1
            markdown_parts.append(f"<!-- Page {page_num} -->")
            markdown_parts.append(page.markdown)

            # Log any hyperlinks found
            if hasattr(page, 'hyperlinks') and page.hyperlinks:
                logger.debug(f"Page {page_num}: {len(page.hyperlinks)} hyperlinks found")

            # Log any tables found
            if hasattr(page, 'tables') and page.tables:
                logger.debug(f"Page {page_num}: {len(page.tables)} tables found")

        # Log usage info if available
        if hasattr(ocr_response, 'usage_info') and ocr_response.usage_info:
            logger.info(f"Usage: {ocr_response.usage_info}")

        return "\n\n".join(markdown_parts)

    except Exception as e:
        logger.error(f"OCR API error: {e}")
        raise


def ocr_pdf_chunked(pdf_path: str, api_key: str, chunk_size: int = 20) -> str:
    """
    OCR a large PDF by processing it in chunks.

    Args:
        pdf_path: Path to the PDF file
        api_key: Mistral API key
        chunk_size: Number of pages per chunk

    Returns:
        Combined Markdown text from all chunks
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF not installed. Run: uv pip install pymupdf --system")
        sys.exit(1)

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    logger.info(f"PDF has {total_pages} pages, processing in chunks of {chunk_size}...")

    all_text = []
    temp_dir = Path("/tmp/mistral_ocr_chunks")
    temp_dir.mkdir(exist_ok=True)

    total_chunks = (total_pages + chunk_size - 1) // chunk_size

    for chunk_num, start in enumerate(range(0, total_pages, chunk_size), 1):
        end = min(start + chunk_size, total_pages)
        chunk_path = temp_dir / f"chunk_{start}_{end}.pdf"

        # Extract pages to new PDF
        logger.info(f"Chunk {chunk_num}/{total_chunks}: Extracting pages {start + 1}-{end}")
        chunk_doc = fitz.open()
        chunk_doc.insert_pdf(doc, from_page=start, to_page=end - 1)
        chunk_doc.save(str(chunk_path))
        chunk_doc.close()

        try:
            chunk_text = ocr_pdf_with_mistral(str(chunk_path), api_key)
            all_text.append(f"<!-- Pages {start + 1}-{end} -->\n\n{chunk_text}")
            logger.info(f"Chunk {chunk_num}/{total_chunks}: Success")
        except Exception as e:
            logger.error(f"Chunk {chunk_num}/{total_chunks} failed: {e}")
            all_text.append(f"<!-- Pages {start + 1}-{end}: OCR FAILED - {e} -->\n")

        # Clean up chunk
        try:
            chunk_path.unlink()
        except:
            pass

    doc.close()

    # Clean up temp directory if empty
    try:
        temp_dir.rmdir()
    except:
        pass

    return "\n\n---\n\n".join(all_text)


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF to Markdown using Mistral OCR (mistral-ocr-latest)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf                    # OCR entire PDF
  %(prog)s document.pdf -o output.md       # Save to specific file
  %(prog)s document.pdf --output-dir /path/to/dir  # Save to specific directory
  %(prog)s document.pdf --pages 1-50       # OCR specific pages (note: currently processes full doc)
  %(prog)s large.pdf --chunked             # Process large PDF in chunks
  %(prog)s large.pdf --chunked --chunk-size 10  # Custom chunk size
  %(prog)s document.pdf -v                 # Verbose/debug output
        """
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("-o", "--output", help="Output Markdown file (default: same name as PDF)")
    parser.add_argument("-d", "--output-dir", help="Output directory (overrides -o)")
    parser.add_argument("--pages", help="Page range to OCR (e.g., '1-10' or '5,7,9') - note: currently processes full document")
    parser.add_argument("--chunked", action="store_true", help="Process large PDFs in chunks")
    parser.add_argument("--chunk-size", type=int, default=20, help="Pages per chunk (default: 20)")
    parser.add_argument("--api-key", help="Mistral API key (default: $MISTRAL_API_KEY)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Get API key
    api_key = args.api_key or os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        logger.error("No API key. Set MISTRAL_API_KEY or use --api-key")
        sys.exit(1)

    # Validate PDF exists
    pdf_path = Path(args.pdf_path).resolve()
    if not pdf_path.exists():
        logger.error(f"File not found: {pdf_path}")
        sys.exit(1)

    # Determine output path
    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / (pdf_path.stem + "-mistral.md")
    elif args.output:
        output_path = Path(args.output).resolve()
    else:
        output_path = pdf_path.with_name(pdf_path.stem + "-mistral.md")

    # Log configuration
    logger.info("=" * 60)
    logger.info("Mistral OCR - PDF to Markdown Converter")
    logger.info("=" * 60)
    logger.info(f"Input:  {pdf_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Model:  mistral-ocr-latest")
    logger.info(f"Chunked: {args.chunked}")
    if args.chunked:
        logger.info(f"Chunk size: {args.chunk_size} pages")
    logger.info("-" * 60)

    # Run OCR
    start_time = time.time()
    try:
        if args.chunked:
            markdown = ocr_pdf_chunked(str(pdf_path), api_key, args.chunk_size)
        else:
            markdown = ocr_pdf_with_mistral(str(pdf_path), api_key, args.pages)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save output
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# {pdf_path.stem}\n\n")
            f.write(f"*OCR by Mistral mistral-ocr-latest*\n\n")
            f.write("---\n\n")
            f.write(markdown)

        total_time = time.time() - start_time
        output_size = output_path.stat().st_size

        logger.info("-" * 60)
        logger.info(f"SUCCESS!")
        logger.info(f"Output: {output_path}")
        logger.info(f"Size:   {output_size:,} bytes ({output_size/1024:.1f} KB)")
        logger.info(f"Time:   {total_time:.1f}s")
        logger.info("=" * 60)

    except Exception as e:
        import traceback
        logger.error("-" * 60)
        logger.error(f"FAILED: {e}")
        logger.error("-" * 60)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
