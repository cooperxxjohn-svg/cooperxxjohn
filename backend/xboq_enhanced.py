"""
XBOQ Enhanced - Maximum Accuracy Pipeline
Combines specialized RCC extraction with intelligent multi-method processing
"""

import os
import sys
import time
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Import intelligent modules
from image_processor import SmartImageProcessor, QualityScore
from document_analyzer import DocumentStructureAnalyzer, ContentType
from table_extractor import IntelligentTableExtractor
from ocr_processor import AdvancedOCREngine
from vision_extractor import VisionBasedExtractor
from validation_engine import ValidationEngine

# Import existing XBOQ modules (if available)
try:
    from drawing_extractor import DrawingExtractor
    HAVE_DRAWING_EXTRACTOR = True
except ImportError:
    HAVE_DRAWING_EXTRACTOR = False

try:
    from boq_calculator import BOQCalculator
    HAVE_BOQ_CALCULATOR = True
except ImportError:
    HAVE_BOQ_CALCULATOR = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class XBOQEnhanced:
    """
    Enhanced XBOQ pipeline with intelligent multi-method extraction

    Features:
    - Document structure analysis (skip irrelevant pages)
    - Quality assessment and enhancement
    - Multi-method extraction with fallbacks
    - Confidence scoring per field
    - IS 456 / CPWD validation
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize all processors"""
        self.api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')

        # Initialize intelligent processors
        self.image_processor = SmartImageProcessor()
        self.document_analyzer = DocumentStructureAnalyzer()
        self.table_extractor = IntelligentTableExtractor()
        self.ocr_engine = AdvancedOCREngine()
        self.vision_extractor = VisionBasedExtractor(self.api_key)
        self.validator = ValidationEngine()

        # Initialize specialized extractors (if available)
        if HAVE_DRAWING_EXTRACTOR:
            self.drawing_extractor = DrawingExtractor(self.api_key)
        else:
            self.drawing_extractor = None

        if HAVE_BOQ_CALCULATOR:
            self.boq_calculator = BOQCalculator()
        else:
            self.boq_calculator = None

        logger.info("XBOQ Enhanced initialized with all processors")

    def process_drawing_intelligent(
        self,
        drawing_path: str,
        quick_mode: bool = False
    ) -> Dict:
        """
        Process a single construction drawing with maximum accuracy

        Args:
            drawing_path: Path to PDF or image file
            quick_mode: If True, skip some intensive checks

        Returns:
            Dictionary with components, BOQ, confidence scores
        """
        start_time = time.time()

        logger.info(f"Processing: {drawing_path}")

        try:
            # Step 1: Analyze document structure (if PDF)
            doc_map = None
            if drawing_path.lower().endswith('.pdf'):
                logger.info("Step 1: Analyzing document structure...")
                doc_map = self.document_analyzer.analyze_document_structure(drawing_path)
                logger.info(f"  Found {doc_map.total_pages} pages")
                logger.info(f"  BOQ pages: {doc_map.boq_pages}")
                logger.info(f"  Drawing pages: {doc_map.drawing_pages}")
                logger.info(f"  Specification pages: {len(doc_map.specification_pages)}")

            # Step 2: Quality assessment and enhancement
            logger.info("Step 2: Quality assessment...")
            if not drawing_path.lower().endswith('.pdf'):
                quality = self.image_processor.assess_quality(drawing_path)
                logger.info(f"  Quality score: {quality.overall_score:.2f}")
                logger.info(f"  Blur: {quality.blur_score:.2f}, Contrast: {quality.contrast_score:.2f}")

                if quality.needs_enhancement:
                    logger.info("  Enhancing image quality...")
                    enhanced_path = drawing_path.replace('.', '_enhanced.')
                    drawing_path = self.image_processor.auto_enhance(
                        drawing_path, enhanced_path, quality
                    )

            # Step 3: Multi-method extraction
            logger.info("Step 3: Multi-method extraction...")

            components = []
            extraction_methods = []
            confidences = []

            # Method 1: Specialized RCC extractor (if available)
            if self.drawing_extractor and not quick_mode:
                try:
                    logger.info("  Method 1: Specialized RCC extraction...")
                    rcc_components = self._extract_with_specialized(drawing_path)
                    if rcc_components:
                        components.extend(rcc_components)
                        extraction_methods.append('specialized_rcc')
                        confidences.append(0.95)  # High confidence for specialized
                        logger.info(f"    Extracted {len(rcc_components)} RCC components")
                except Exception as e:
                    logger.warning(f"    Specialized extraction failed: {e}")

            # Method 2: Table extraction
            if drawing_path.lower().endswith('.pdf'):
                try:
                    logger.info("  Method 2: Table extraction...")
                    table_pages = doc_map.boq_pages if doc_map else None
                    boq_items = self.table_extractor.extract_boq_from_pdf(
                        drawing_path, table_pages
                    )
                    if boq_items:
                        table_components = [item.to_dict() for item in boq_items]
                        components.extend(table_components)
                        extraction_methods.append('table_extraction')
                        confidences.append(0.92)
                        logger.info(f"    Extracted {len(boq_items)} items from tables")
                except Exception as e:
                    logger.warning(f"    Table extraction failed: {e}")

            # Method 3: Vision API for drawings
            try:
                logger.info("  Method 3: Vision API extraction...")
                vision_data = self.vision_extractor.extract_from_architectural_drawing(
                    drawing_path
                )
                if vision_data.materials:
                    vision_components = [
                        {
                            'item': f'V{i+1}',
                            'description': mat.get('specification', mat.get('material', '')),
                            'qty': mat.get('quantity', 0),
                            'unit': mat.get('unit', ''),
                            'rate': 0,
                            'amount': 0,
                            'source': 'vision_api'
                        }
                        for i, mat in enumerate(vision_data.materials)
                    ]
                    components.extend(vision_components)
                    extraction_methods.append('vision_api')
                    confidences.append(vision_data.confidence)
                    logger.info(f"    Extracted {len(vision_components)} components via Vision")
            except Exception as e:
                logger.warning(f"    Vision API failed: {e}")

            # Method 4: OCR fallback for scanned documents
            if not quick_mode and len(components) < 5:
                try:
                    logger.info("  Method 4: OCR fallback...")
                    ocr_result = self.ocr_engine.process_scanned_document(drawing_path)
                    if ocr_result.confidence > 0.6:
                        # Parse OCR text to extract components
                        ocr_components = self._parse_ocr_text(ocr_result.text)
                        if ocr_components:
                            components.extend(ocr_components)
                            extraction_methods.append('ocr')
                            confidences.append(ocr_result.confidence)
                            logger.info(f"    Extracted {len(ocr_components)} components via OCR")
                except Exception as e:
                    logger.warning(f"    OCR failed: {e}")

            # Step 4: Deduplicate and merge
            logger.info("Step 4: Deduplicating components...")
            components = self._deduplicate_components(components)
            logger.info(f"  Final component count: {len(components)}")

            # Step 5: Validate and score confidence
            logger.info("Step 5: Validation and confidence scoring...")
            validation_result = self.validator.validate_document(components)

            # Step 6: Calculate BOQ
            logger.info("Step 6: Calculating BOQ...")
            if self.boq_calculator:
                try:
                    boq = self.boq_calculator.calculate(components)
                except:
                    boq = self._calculate_simple_boq(components)
            else:
                boq = self._calculate_simple_boq(components)

            processing_time = round(time.time() - start_time, 2)

            # Compile result
            result = {
                'success': True,
                'components': components,
                'total_components': len(components),
                'boq': boq,
                'total_value': sum(item.get('amount', 0) for item in components),
                'extraction_methods': extraction_methods,
                'overall_confidence': validation_result.overall_confidence,
                'validation': validation_result.to_dict(),
                'processing_time': processing_time,
                'metadata': {
                    'document_pages': doc_map.total_pages if doc_map else 1,
                    'boq_pages': doc_map.boq_pages if doc_map else [],
                    'drawing_pages': doc_map.drawing_pages if doc_map else [],
                }
            }

            logger.info(f"Processing complete in {processing_time}s")
            logger.info(f"  Components: {len(components)}")
            logger.info(f"  Confidence: {validation_result.overall_confidence:.2f}")
            logger.info(f"  Total value: ₹{result['total_value']:,.2f}")

            return result

        except Exception as e:
            logger.error(f"Error processing drawing: {e}")
            import traceback
            traceback.print_exc()

            return {
                'success': False,
                'error': str(e),
                'components': [],
                'total_components': 0,
                'processing_time': round(time.time() - start_time, 2)
            }

    def _extract_with_specialized(self, drawing_path: str) -> List[Dict]:
        """Use specialized RCC extractor"""
        if not self.drawing_extractor:
            return []

        try:
            # Call specialized extractor
            result = self.drawing_extractor.extract(drawing_path)

            # Convert to standard format
            components = []
            for comp in result.get('components', []):
                components.append({
                    'item': comp.get('id', ''),
                    'description': comp.get('description', ''),
                    'qty': comp.get('quantity', 0),
                    'unit': comp.get('unit', ''),
                    'rate': comp.get('rate', 0),
                    'amount': comp.get('amount', 0),
                    'specification': comp.get('specification', ''),
                    'source': 'specialized_rcc'
                })

            return components
        except Exception as e:
            logger.error(f"Specialized extraction error: {e}")
            return []

    def _parse_ocr_text(self, text: str) -> List[Dict]:
        """Parse OCR text to extract components"""
        # Simple parsing - can be enhanced
        components = []
        lines = text.split('\n')

        for line in lines:
            # Look for quantity + unit patterns
            import re
            match = re.search(r'(\d+\.?\d*)\s*(cum|sqm|rmt|kg|nos|m)', line, re.IGNORECASE)
            if match:
                qty = float(match.group(1))
                unit = match.group(2).lower()

                # Extract description (text before quantity)
                desc = line[:match.start()].strip()
                if len(desc) > 5:
                    components.append({
                        'item': f'OCR{len(components)+1}',
                        'description': desc,
                        'qty': qty,
                        'unit': unit,
                        'rate': 0,
                        'amount': 0,
                        'source': 'ocr'
                    })

        return components

    def _deduplicate_components(self, components: List[Dict]) -> List[Dict]:
        """Remove duplicate components"""
        seen = {}
        unique = []

        for comp in components:
            desc = comp.get('description', '').lower().strip()

            if desc and desc not in seen:
                seen[desc] = True
                unique.append(comp)

        return unique

    def _calculate_simple_boq(self, components: List[Dict]) -> Dict:
        """Simple BOQ calculation"""
        # Group by category
        categories = {}

        for comp in components:
            desc = comp.get('description', '')

            # Determine category
            category = 'General'
            if any(word in desc.lower() for word in ['excavation', 'earthwork']):
                category = 'Earthwork'
            elif any(word in desc.lower() for word in ['concrete', 'rcc', 'pcc']):
                category = 'Concrete Work'
            elif any(word in desc.lower() for word in ['brick', 'masonry', 'block']):
                category = 'Masonry'
            elif any(word in desc.lower() for word in ['steel', 'reinforcement', 'rebar']):
                category = 'Reinforcement'
            elif any(word in desc.lower() for word in ['plaster', 'finishing']):
                category = 'Finishing'

            if category not in categories:
                categories[category] = []

            categories[category].append(comp)

        return {
            'categories': categories,
            'total_items': len(components),
            'total_value': sum(comp.get('amount', 0) for comp in components)
        }

    def process_batch(
        self,
        drawing_paths: List[str],
        output_dir: str = 'output',
        progress_callback = None
    ) -> List[Dict]:
        """
        Process multiple drawings in batch

        Args:
            drawing_paths: List of paths to process
            output_dir: Output directory for results
            progress_callback: Function(progress, message) for updates

        Returns:
            List of results
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []

        for i, path in enumerate(drawing_paths):
            progress = (i + 1) / len(drawing_paths) * 100

            if progress_callback:
                progress_callback(progress, f"Processing {Path(path).name}")

            logger.info(f"\n{'='*80}")
            logger.info(f"Processing {i+1}/{len(drawing_paths)}: {path}")
            logger.info(f"{'='*80}")

            result = self.process_drawing_intelligent(path)
            results.append(result)

            # Save individual result
            output_file = Path(output_dir) / f"{Path(path).stem}_result.json"
            import json
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)

            logger.info(f"Saved result to {output_file}")

        # Save summary
        summary = {
            'total_processed': len(drawing_paths),
            'successful': len([r for r in results if r.get('success', False)]),
            'failed': len([r for r in results if not r.get('success', False)]),
            'total_components': sum(r.get('total_components', 0) for r in results),
            'average_confidence': sum(r.get('overall_confidence', 0) for r in results) / len(results) if results else 0,
            'results': results
        }

        summary_file = Path(output_dir) / 'batch_summary.json'
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"\n{'='*80}")
        logger.info(f"BATCH COMPLETE")
        logger.info(f"  Total: {summary['total_processed']}")
        logger.info(f"  Successful: {summary['successful']}")
        logger.info(f"  Failed: {summary['failed']}")
        logger.info(f"  Avg Confidence: {summary['average_confidence']:.2f}")
        logger.info(f"{'='*80}\n")

        return results


def main():
    """Command-line interface for XBOQ Enhanced"""
    import argparse

    parser = argparse.ArgumentParser(description='XBOQ Enhanced - Maximum Accuracy BOQ Extraction')
    parser.add_argument('drawing_path', help='Path to PDF or image file')
    parser.add_argument('--api-key', help='Anthropic API key (or set ANTHROPIC_API_KEY env var)')
    parser.add_argument('--quick', action='store_true', help='Quick mode (faster, less thorough)')
    parser.add_argument('--output', default='output', help='Output directory')

    args = parser.parse_args()

    # Initialize
    xboq = XBOQEnhanced(anthropic_api_key=args.api_key)

    # Process
    result = xboq.process_drawing_intelligent(
        args.drawing_path,
        quick_mode=args.quick
    )

    # Save result
    os.makedirs(args.output, exist_ok=True)
    output_file = Path(args.output) / f"{Path(args.drawing_path).stem}_result.json"

    import json
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\nResult saved to: {output_file}")
    print(f"Success: {result['success']}")
    print(f"Components: {result['total_components']}")
    print(f"Confidence: {result.get('overall_confidence', 0):.2f}")
    print(f"Processing time: {result['processing_time']}s")


if __name__ == '__main__':
    main()
