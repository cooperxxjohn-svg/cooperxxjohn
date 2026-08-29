"""
Intelligent Extraction Engine
Orchestrates the complete extraction pipeline with all components
"""

import os
import time
import fitz  # PyMuPDF
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from pathlib import Path
import json

# Import all specialized processors
from image_processor import SmartImageProcessor, QualityScore
from document_analyzer import DocumentStructureAnalyzer, DocumentMap, ContentType
from table_extractor import IntelligentTableExtractor, BOQItem
from ocr_processor import AdvancedOCREngine, OCRResult
from vision_extractor import VisionBasedExtractor, DrawingData
from validation_engine import ValidationEngine, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Complete result from extraction pipeline"""
    boq_items: List[Dict]
    total_value: float
    line_items: int
    project_name: str
    project_type: str
    accuracy: str  # High/Medium/Low
    confidence: float  # 0-1
    processing_time: float  # seconds
    validation_result: Optional[Dict] = None
    extraction_methods: List[str] = None
    metadata: Dict = None

    def to_dict(self) -> Dict:
        return {
            'projectName': self.project_name,
            'projectType': self.project_type,
            'totalValue': self.total_value,
            'lineItems': self.line_items,
            'accuracy': self.accuracy,
            'confidence': self.confidence,
            'processingTime': self.processing_time,
            'boqItems': self.boq_items,
            'validation': self.validation_result,
            'extractionMethods': self.extraction_methods,
            'metadata': self.metadata
        }


class IntelligentExtractionEngine:
    """
    Main orchestrator for the intelligent extraction pipeline
    Coordinates all specialized processors for optimal results
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialize extraction engine

        Args:
            anthropic_api_key: API key for Claude (optional, uses env var if not provided)
        """
        self.api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')

        # Initialize all processors
        self.image_processor = SmartImageProcessor()
        self.document_analyzer = DocumentStructureAnalyzer()
        self.table_extractor = IntelligentTableExtractor()
        self.ocr_engine = AdvancedOCREngine()
        self.vision_extractor = VisionBasedExtractor(self.api_key)
        self.validator = ValidationEngine()

        logger.info("Intelligent Extraction Engine initialized")

    def process_construction_document(
        self,
        pdf_path: str,
        quick_mode: bool = False,
        max_pages: Optional[int] = None
    ) -> ExtractionResult:
        """
        Process a construction document with intelligent extraction

        Args:
            pdf_path: Path to PDF file
            quick_mode: If True, use faster but less thorough extraction
            max_pages: Maximum pages to process (None = all priority pages)

        Returns:
            ExtractionResult with complete BOQ data
        """
        start_time = time.time()
        extraction_methods = []

        logger.info(f"Starting intelligent extraction: {pdf_path}")
        logger.info(f"Quick mode: {quick_mode}, Max pages: {max_pages}")

        try:
            # Step 1: Analyze document structure
            logger.info("Step 1: Analyzing document structure...")
            doc_map = self.document_analyzer.analyze_document_structure(pdf_path)
            extraction_methods.append('structure_analysis')

            # Determine pages to process
            if max_pages:
                priority_pages = doc_map.processing_order[:max_pages]
            else:
                priority_pages = doc_map.processing_order

            logger.info(f"Processing {len(priority_pages)} priority pages")

            # Step 2: Extract from BOQ tables (CRITICAL priority)
            logger.info("Step 2: Extracting tables...")
            boq_items = []

            if doc_map.boq_pages:
                logger.info(f"Found {len(doc_map.boq_pages)} BOQ pages")
                boq_from_tables = self.table_extractor.extract_boq_from_pdf(
                    pdf_path, doc_map.boq_pages
                )
                boq_items.extend([item.to_dict() for item in boq_from_tables])
                extraction_methods.append('table_extraction')
                logger.info(f"Extracted {len(boq_from_tables)} items from tables")

            # Step 3: Extract from specification pages
            if not quick_mode and doc_map.specification_pages:
                logger.info("Step 3: Processing specification pages...")
                spec_boq_items = self._extract_from_specifications(
                    pdf_path, doc_map.specification_pages[:5]  # Limit to 5 pages
                )
                if spec_boq_items:
                    boq_items.extend(spec_boq_items)
                    extraction_methods.append('specification_extraction')

            # Step 4: Process drawings (if present)
            if not quick_mode and doc_map.drawing_pages:
                logger.info("Step 4: Processing architectural drawings...")
                drawing_items = self._extract_from_drawings(pdf_path, doc_map.drawing_pages[:3])
                if drawing_items:
                    boq_items.extend(drawing_items)
                    extraction_methods.append('vision_extraction')

            # Step 5: If we got very few items, try comprehensive OCR
            if len(boq_items) < 5:
                logger.warning(f"Only {len(boq_items)} items extracted, trying comprehensive OCR...")
                ocr_result = self.ocr_engine.process_scanned_document(pdf_path)

                if ocr_result.confidence > 0.6:
                    # Use Claude to parse OCR text
                    claude_items = self._parse_with_claude(ocr_result.text, os.path.basename(pdf_path))
                    if claude_items:
                        boq_items.extend(claude_items)
                        extraction_methods.append('ocr_with_claude')

            # Step 6: Deduplicate and merge
            logger.info("Step 6: Deduplicating and merging items...")
            boq_items = self._deduplicate_items(boq_items)

            # Step 7: Validate and score confidence
            logger.info("Step 7: Validating extraction...")
            validation_result = self.validator.validate_document(boq_items)

            # Step 8: Calculate totals
            total_value = sum(item.get('amount', 0) for item in boq_items)

            # Step 9: Identify project details
            project_name = self._identify_project_name(pdf_path, doc_map)
            project_type = self._identify_project_type(boq_items)

            # Determine accuracy based on confidence
            if validation_result.overall_confidence > 0.85:
                accuracy = "High"
            elif validation_result.overall_confidence > 0.65:
                accuracy = "Medium"
            else:
                accuracy = "Low"

            processing_time = round(time.time() - start_time, 2)

            result = ExtractionResult(
                boq_items=boq_items,
                total_value=round(total_value, 2),
                line_items=len(boq_items),
                project_name=project_name,
                project_type=project_type,
                accuracy=accuracy,
                confidence=validation_result.overall_confidence,
                processing_time=processing_time,
                validation_result=validation_result.to_dict(),
                extraction_methods=extraction_methods,
                metadata={
                    'total_pages': doc_map.total_pages,
                    'boq_pages': doc_map.boq_pages,
                    'drawing_pages': doc_map.drawing_pages,
                    'specification_pages': doc_map.specification_pages,
                    'sections': list(doc_map.sections.keys())
                }
            )

            logger.info(f"Extraction complete: {len(boq_items)} items, "
                       f"confidence: {validation_result.overall_confidence:.2f}, "
                       f"time: {processing_time}s")

            return result

        except Exception as e:
            logger.error(f"Error in extraction pipeline: {e}")
            import traceback
            traceback.print_exc()

            # Return minimal result
            return ExtractionResult(
                boq_items=[],
                total_value=0.0,
                line_items=0,
                project_name="Unknown Project",
                project_type="General Construction",
                accuracy="Low",
                confidence=0.0,
                processing_time=round(time.time() - start_time, 2),
                extraction_methods=[],
                metadata={'error': str(e)}
            )

    def _extract_from_specifications(self, pdf_path: str, pages: List[int]) -> List[Dict]:
        """Extract BOQ items from specification pages"""
        try:
            doc = fitz.open(pdf_path)
            spec_text = []

            for page_num in pages:
                if page_num < len(doc):
                    page = doc[page_num]
                    text = page.get_text()
                    spec_text.append(text)

            doc.close()

            combined_text = '\n\n'.join(spec_text)

            # Use Claude to parse specifications
            items = self._parse_specifications_with_claude(combined_text)

            return items

        except Exception as e:
            logger.error(f"Error extracting from specifications: {e}")
            return []

    def _extract_from_drawings(self, pdf_path: str, pages: List[int]) -> List[Dict]:
        """Extract BOQ items from architectural drawings"""
        items = []

        try:
            doc = fitz.open(pdf_path)

            for page_num in pages:
                if page_num < len(doc):
                    # Convert page to image
                    page = doc[page_num]
                    pix = page.get_pixmap(dpi=300)

                    # Save to temp file
                    temp_img = f"/tmp/drawing_{page_num}.png"
                    pix.save(temp_img)

                    # Extract with vision API
                    drawing_data = self.vision_extractor.extract_from_architectural_drawing(temp_img)

                    # Convert drawing data to BOQ items
                    for material in drawing_data.materials:
                        items.append({
                            'item': f'D{page_num}.{len(items)+1}',
                            'description': material.get('specification', material.get('material', '')),
                            'qty': material.get('quantity', 0),
                            'unit': material.get('unit', ''),
                            'rate': 0,  # To be filled in
                            'amount': 0
                        })

                    # Cleanup
                    try:
                        os.remove(temp_img)
                    except:
                        pass

            doc.close()

        except Exception as e:
            logger.error(f"Error extracting from drawings: {e}")

        return items

    def _parse_with_claude(self, text: str, filename: str) -> List[Dict]:
        """Use Claude to parse text and extract BOQ items"""
        try:
            from anthropic import Anthropic

            if not self.api_key:
                return []

            client = Anthropic(api_key=self.api_key)

            prompt = f"""Analyze this construction document text and extract BOQ items.

Text from {filename}:
{text[:15000]}

Extract all work items and return as JSON array:
[
  {{
    "item": "1.1",
    "description": "Excavation in foundation",
    "qty": 100.0,
    "unit": "cum",
    "rate": 500.0,
    "amount": 50000.0
  }}
]

Return ONLY the JSON array."""

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Parse JSON
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                response_text = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                response_text = response_text[start:end].strip()

            items = json.loads(response_text)

            return items if isinstance(items, list) else []

        except Exception as e:
            logger.error(f"Error parsing with Claude: {e}")
            return []

    def _parse_specifications_with_claude(self, spec_text: str) -> List[Dict]:
        """Parse specification text with Claude"""
        return self._parse_with_claude(spec_text, "specifications")

    def _deduplicate_items(self, items: List[Dict]) -> List[Dict]:
        """Remove duplicate items"""
        seen = {}
        unique_items = []

        for item in items:
            desc = item.get('description', '').lower().strip()

            if desc and desc not in seen:
                seen[desc] = True
                unique_items.append(item)

        return unique_items

    def _identify_project_name(self, pdf_path: str, doc_map: DocumentMap) -> str:
        """Try to identify project name from document"""
        try:
            # Check first page for title
            doc = fitz.open(pdf_path)
            if len(doc) > 0:
                first_page_text = doc[0].get_text()

                # Look for common patterns
                lines = first_page_text.split('\n')
                for line in lines[:10]:  # Check first 10 lines
                    if len(line) > 10 and len(line) < 100:
                        # Could be project name
                        if any(keyword in line.lower() for keyword in ['project', 'construction', 'work', 'tender']):
                            doc.close()
                            return line.strip()

            doc.close()
        except:
            pass

        # Default
        return Path(pdf_path).stem.replace('_', ' ').title()

    def _identify_project_type(self, boq_items: List[Dict]) -> str:
        """Identify project type from BOQ items"""
        # Count keywords in descriptions
        keywords = {
            'Residential': ['residential', 'house', 'apartment', 'flat', 'villa'],
            'Commercial': ['commercial', 'office', 'shop', 'mall', 'showroom'],
            'Infrastructure': ['road', 'bridge', 'highway', 'drainage', 'sewer'],
            'Industrial': ['factory', 'warehouse', 'industrial', 'plant'],
            'Institutional': ['school', 'hospital', 'college', 'government']
        }

        scores = {ptype: 0 for ptype in keywords.keys()}

        for item in boq_items:
            desc = item.get('description', '').lower()
            for ptype, kwords in keywords.items():
                for kw in kwords:
                    if kw in desc:
                        scores[ptype] += 1

        # Return highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)

        return "General Construction"


# Convenience function

def extract_boq(pdf_path: str, quick_mode: bool = False) -> ExtractionResult:
    """
    Quick extraction of BOQ from PDF

    Args:
        pdf_path: Path to PDF file
        quick_mode: If True, faster but less thorough

    Returns:
        ExtractionResult with BOQ data
    """
    engine = IntelligentExtractionEngine()
    return engine.process_construction_document(pdf_path, quick_mode=quick_mode)
