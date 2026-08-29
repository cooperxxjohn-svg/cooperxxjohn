"""
PDF Processing Utilities
Shared between BOQ Generator and Construction Estimator
"""

import logging
import PyPDF2
from pdf2image import convert_from_path
import pytesseract

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Handles PDF text extraction with hybrid approach:
    1. Try searchable PDF extraction (PyPDF2)
    2. Fallback to OCR (Tesseract) for image-based PDFs
    """

    def __init__(self, max_pages: int = 100):
        self.max_pages = max_pages
        logger.info("PDF Processor initialized")

    def extract_text_from_searchable_pdf(self, pdf_path: str) -> str:
        """
        Extract text from searchable PDF using PyPDF2
        """
        logger.info("Attempting searchable PDF extraction...")
        text = ""

        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = min(len(pdf_reader.pages), self.max_pages)

                logger.info(f"PDF has {len(pdf_reader.pages)} pages, processing {num_pages}")

                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()

                    if page_text:
                        text += f"\n--- PAGE {page_num + 1} ---\n{page_text}\n"
                        logger.info(f"Extracted text from page {page_num + 1}")

        except Exception as e:
            logger.error(f"Error in searchable extraction: {e}")

        return text

    def extract_text_with_ocr(self, pdf_path: str) -> str:
        """
        Extract text using OCR (Tesseract) for image-based PDFs
        """
        logger.info("Attempting OCR extraction...")
        text = ""

        try:
            images = convert_from_path(
                pdf_path,
                first_page=1,
                last_page=self.max_pages
            )

            logger.info(f"Converted PDF to {len(images)} images for OCR")

            for page_num, image in enumerate(images):
                logger.info(f"Processing page {page_num + 1} with Tesseract OCR...")
                page_text = pytesseract.image_to_string(image, lang='eng')

                if page_text.strip():
                    text += f"\n--- PAGE {page_num + 1} ---\n{page_text}\n"
                    logger.info(f"OCR extracted text from page {page_num + 1}")

        except Exception as e:
            logger.error(f"Error in OCR extraction: {e}")

        return text

    def extract_text_hybrid(self, pdf_path: str) -> str:
        """
        Hybrid approach: Try searchable first, fallback to OCR
        """
        logger.info(f"Starting hybrid extraction for: {pdf_path}")

        # Try searchable extraction first
        text = self.extract_text_from_searchable_pdf(pdf_path)

        # If we got minimal text, try OCR
        if len(text) < 500:
            logger.info("Searchable extraction returned minimal text, trying OCR...")
            ocr_text = self.extract_text_with_ocr(pdf_path)
            text = text + ocr_text if text else ocr_text

        logger.info(f"Total extracted: {len(text)} characters")
        return text
