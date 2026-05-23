"""
BOQ Generator Module
Extracts Bill of Quantities from tender documents
Original XBOQ functionality
"""

import json
import logging
from utils.pdf_processor import PDFProcessor
from utils.claude_client import ClaudeClient

logger = logging.getLogger(__name__)


class BOQGenerator:
    """
    Processes tender documents and generates Bill of Quantities using Claude AI
    """

    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.claude = ClaudeClient()
        logger.info("BOQ Generator initialized")

    def process(self, pdf_path: str) -> dict:
        """
        Main processing pipeline for tender documents

        Args:
            pdf_path: Path to tender PDF file

        Returns:
            dict with status and BOQ data
        """
        logger.info(f"Processing tender document: {pdf_path}")

        # Step 1: Extract text from PDF
        extracted_text = self.pdf_processor.extract_text_hybrid(pdf_path)

        if not extracted_text or len(extracted_text) < 100:
            logger.error("Failed to extract meaningful text from tender")
            return {
                "status": "error",
                "error": "Could not extract text from tender document"
            }

        logger.info(f"Extracted {len(extracted_text)} characters from tender")

        # Step 2: Send to Claude for BOQ generation
        boq_result = self._generate_boq_with_claude(extracted_text)

        return boq_result

    def _generate_boq_with_claude(self, extracted_text: str) -> dict:
        """
        Use Claude AI to generate structured BOQ from extracted text
        """
        logger.info("Sending to Claude for BOQ generation...")

        prompt = f"""You are an expert construction estimator. Extract a detailed Bill of Quantities from this tender document.

TENDER TEXT:
{extracted_text[:5000]}

Generate a comprehensive BOQ with items organized by category. Return ONLY valid JSON in this exact format:

{{
    "project_name": "Name of the project from tender",
    "tender_number": "Tender reference number if available",
    "sections": [
        {{
            "section_name": "SITE PREPARATION",
            "items": [
                {{
                    "item_no": 1,
                    "description": "Clear and grub site",
                    "unit": "Sq.m",
                    "quantity": 0,
                    "rate": 0,
                    "remarks": ""
                }}
            ]
        }},
        {{
            "section_name": "EARTHWORK",
            "items": [
                {{
                    "item_no": 2,
                    "description": "Excavation for foundation",
                    "unit": "Cu.m",
                    "quantity": 0,
                    "rate": 0,
                    "remarks": ""
                }}
            ]
        }}
    ],
    "summary": {{
        "total_items": 0,
        "total_sections": 0
    }}
}}

Extract ALL quantities, units, and descriptions from the tender document.
Organize by logical construction phases (site work, concrete, masonry, etc.).
Use standard units (Sq.m, Cu.m, No., Kg, Ton, etc.).
"""

        try:
            response_text = self.claude.generate(prompt, max_tokens=4000)

            # Try to parse as JSON
            try:
                boq_json = json.loads(response_text)
                logger.info("Successfully generated BOQ from Claude")
                return {
                    "status": "success",
                    "boq": boq_json,
                    "tool": "boq_generator"
                }
            except json.JSONDecodeError:
                # Return as text if not valid JSON
                logger.warning("Claude returned non-JSON response")
                return {
                    "status": "partial",
                    "boq": response_text,
                    "tool": "boq_generator"
                }

        except Exception as e:
            logger.error(f"Error with Claude: {e}")
            return {
                "status": "error",
                "error": str(e),
                "tool": "boq_generator"
            }
