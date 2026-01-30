"""
Process Construction Drawing Set - Generate BOQ from Multiple Drawings
Splits multi-page PDF and processes each drawing with Vision API
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict
import time
import logging

try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    print("ERROR: PyPDF2 not installed. Run: pip3 install PyPDF2")
    sys.exit(1)

try:
    from PIL import Image
    import fitz  # PyMuPDF
    HAVE_PYMUPDF = True
except ImportError:
    HAVE_PYMUPDF = False
    print("WARNING: PyMuPDF not available. Will use PyPDF2 only.")

from xboq_enhanced import XBOQEnhanced

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DrawingSetProcessor:
    """Process construction drawing sets and generate BOQ"""

    def __init__(self, anthropic_api_key: str = None):
        self.xboq = XBOQEnhanced(anthropic_api_key)

    def split_pdf_to_images(self, pdf_path: str, output_dir: str) -> List[str]:
        """
        Split PDF into individual page images for Vision API processing

        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save page images

        Returns:
            List of image file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        image_paths = []

        if HAVE_PYMUPDF:
            logger.info("Using PyMuPDF for high-quality image conversion")
            doc = fitz.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Render at high DPI for better OCR/Vision
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom = 144 DPI
                pix = page.get_pixmap(matrix=mat)

                image_path = os.path.join(output_dir, f"page_{page_num + 1:03d}.png")
                pix.save(image_path)
                image_paths.append(image_path)

                logger.info(f"  Converted page {page_num + 1}/{len(doc)} -> {image_path}")

            doc.close()

        else:
            # Fallback: Just split PDF pages (less ideal for Vision API)
            logger.info("Using PyPDF2 for PDF page splitting")
            reader = PdfReader(pdf_path)

            for page_num in range(len(reader.pages)):
                writer = PdfWriter()
                writer.add_page(reader.pages[page_num])

                page_pdf_path = os.path.join(output_dir, f"page_{page_num + 1:03d}.pdf")
                with open(page_pdf_path, 'wb') as f:
                    writer.write(f)

                image_paths.append(page_pdf_path)
                logger.info(f"  Split page {page_num + 1}/{len(reader.pages)} -> {page_pdf_path}")

        return image_paths

    def filter_drawing_pages(self, image_paths: List[str]) -> List[str]:
        """
        Filter out non-drawing pages (title, TOC, etc.)
        Uses the document analyzer to identify actual drawing pages

        Args:
            image_paths: List of all page images

        Returns:
            List of drawing page paths only
        """
        # For now, return all pages
        # In future, could use document_analyzer to filter
        logger.info(f"Processing all {len(image_paths)} pages as potential drawings")
        return image_paths

    def process_single_drawing(self, drawing_path: str) -> Dict:
        """
        Process a single construction drawing with Vision API

        Args:
            drawing_path: Path to drawing image/PDF

        Returns:
            Extraction result with components
        """
        logger.info(f"\nProcessing: {Path(drawing_path).name}")

        try:
            result = self.xboq.vision_extractor.extract_from_architectural_drawing(drawing_path)

            # Convert to standard format
            components = []
            if result.materials:
                for i, mat in enumerate(result.materials):
                    components.append({
                        'item': f'D{i+1}',
                        'description': mat.get('specification', mat.get('material', '')),
                        'qty': mat.get('quantity', 0),
                        'unit': mat.get('unit', ''),
                        'rate': 0,
                        'amount': 0,
                        'source': 'vision_api',
                        'drawing': Path(drawing_path).stem
                    })

            logger.info(f"  Extracted {len(components)} components from drawing")

            return {
                'success': True,
                'drawing': drawing_path,
                'components': components,
                'confidence': result.confidence,
                'rooms': result.rooms,
                'dimensions': result.dimensions
            }

        except Exception as e:
            logger.error(f"  Error processing drawing: {e}")
            return {
                'success': False,
                'drawing': drawing_path,
                'error': str(e),
                'components': []
            }

    def merge_results(self, drawing_results: List[Dict]) -> Dict:
        """
        Merge results from multiple drawings into single BOQ

        Args:
            drawing_results: List of individual drawing results

        Returns:
            Combined BOQ result
        """
        all_components = []

        for result in drawing_results:
            if result.get('success') and result.get('components'):
                all_components.extend(result['components'])

        logger.info(f"\nMerging results from {len(drawing_results)} drawings")
        logger.info(f"Total raw components: {len(all_components)}")

        # Deduplicate
        unique_components = self.xboq._deduplicate_components(all_components)
        logger.info(f"After deduplication: {len(unique_components)}")

        # Validate
        validation_result = self.xboq.validator.validate_document(unique_components)

        # Calculate BOQ
        boq = self.xboq._calculate_simple_boq(unique_components)

        return {
            'success': True,
            'total_drawings': len(drawing_results),
            'successful_drawings': len([r for r in drawing_results if r.get('success')]),
            'total_components': len(unique_components),
            'components': unique_components,
            'overall_confidence': validation_result.overall_confidence,
            'validation': validation_result.to_dict(),
            'boq': boq,
            'total_value': sum(c.get('amount', 0) for c in unique_components),
            'drawing_details': drawing_results
        }

    def process_drawing_set(self, pdf_path: str, output_dir: str = None) -> Dict:
        """
        Complete workflow: Process construction drawing set and generate BOQ

        Args:
            pdf_path: Path to multi-page PDF with construction drawings
            output_dir: Output directory for results

        Returns:
            Complete BOQ result
        """
        start_time = time.time()

        if output_dir is None:
            output_dir = f"drawing_set_output_{int(time.time())}"

        os.makedirs(output_dir, exist_ok=True)

        logger.info("=" * 80)
        logger.info("CONSTRUCTION DRAWING SET PROCESSOR")
        logger.info("=" * 80)
        logger.info(f"Input: {pdf_path}")
        logger.info(f"Output: {output_dir}")

        # Step 1: Split PDF into individual drawings
        logger.info("\n[1/4] Splitting PDF into individual drawings...")
        pages_dir = os.path.join(output_dir, 'pages')
        page_images = self.split_pdf_to_images(pdf_path, pages_dir)
        logger.info(f"Created {len(page_images)} page images")

        # Step 2: Filter to drawing pages only
        logger.info("\n[2/4] Filtering drawing pages...")
        drawing_pages = self.filter_drawing_pages(page_images)
        logger.info(f"Identified {len(drawing_pages)} drawing pages")

        # Step 3: Process each drawing with Vision API
        logger.info("\n[3/4] Processing drawings with Vision API...")
        drawing_results = []
        for i, drawing_path in enumerate(drawing_pages):
            logger.info(f"\nDrawing {i+1}/{len(drawing_pages)}")
            result = self.process_single_drawing(drawing_path)
            drawing_results.append(result)

        # Step 4: Merge and generate final BOQ
        logger.info("\n[4/4] Generating final BOQ...")
        final_result = self.merge_results(drawing_results)

        # Add metadata
        final_result['processing_time'] = round(time.time() - start_time, 2)
        final_result['input_file'] = pdf_path
        final_result['output_directory'] = output_dir

        # Save result
        result_file = os.path.join(output_dir, 'final_boq.json')
        with open(result_file, 'w') as f:
            json.dump(final_result, f, indent=2)

        logger.info("=" * 80)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total Drawings: {final_result['total_drawings']}")
        logger.info(f"Successful: {final_result['successful_drawings']}")
        logger.info(f"Total Components: {final_result['total_components']}")
        logger.info(f"Overall Confidence: {final_result['overall_confidence']:.2%}")
        logger.info(f"Processing Time: {final_result['processing_time']}s")
        logger.info(f"\nResults saved to: {result_file}")

        return final_result


def main():
    """Command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Process construction drawing set and generate BOQ'
    )
    parser.add_argument('pdf_path', help='Path to construction drawing PDF')
    parser.add_argument('--output', default=None, help='Output directory')
    parser.add_argument('--api-key', help='Anthropic API key')

    args = parser.parse_args()

    # Initialize processor
    processor = DrawingSetProcessor(anthropic_api_key=args.api_key)

    # Process drawing set
    result = processor.process_drawing_set(args.pdf_path, args.output)

    # Print summary
    print(f"\n✅ BOQ Generation Complete!")
    print(f"Components: {result['total_components']}")
    print(f"Confidence: {result['overall_confidence']:.2%}")
    print(f"Total Value: ₹{result['total_value']:,.2f}")


if __name__ == '__main__':
    main()
