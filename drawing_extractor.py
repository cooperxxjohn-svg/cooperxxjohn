"""
Drawing Extractor - AI-Powered Construction Drawing Analysis
Uses Claude's Vision API to extract quantities and dimensions from PDF drawings

This module processes construction drawings and extracts structured data
that can be converted into BOQ line items.
"""

import anthropic
import base64
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from decimal import Decimal
from dataclasses import dataclass, asdict
import PyPDF2
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


@dataclass
class ExtractedDimension:
    """Represents a dimension extracted from drawing"""
    element_type: str  # e.g., "beam", "column", "wall", "slab"
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    thickness: Optional[float] = None
    diameter: Optional[float] = None
    count: int = 1
    location: str = ""
    drawing_reference: str = ""
    confidence: float = 1.0
    unit: str = "m"
    remarks: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExtractedMaterial:
    """Represents material specification from drawing"""
    material_type: str
    grade: Optional[str] = None
    specification: str = ""
    quantity: Optional[float] = None
    unit: str = ""
    location: str = ""
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DrawingExtractionResult:
    """Complete result of drawing extraction"""
    drawing_name: str
    drawing_number: str
    drawing_type: str  # plan, section, elevation, detail
    scale: Optional[str] = None
    dimensions: List[ExtractedDimension] = None
    materials: List[ExtractedMaterial] = None
    notes: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.dimensions is None:
            self.dimensions = []
        if self.materials is None:
            self.materials = []
        if self.notes is None:
            self.notes = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict:
        return {
            'drawing_name': self.drawing_name,
            'drawing_number': self.drawing_number,
            'drawing_type': self.drawing_type,
            'scale': self.scale,
            'dimensions': [d.to_dict() for d in self.dimensions],
            'materials': [m.to_dict() for m in self.materials],
            'notes': self.notes,
            'metadata': self.metadata
        }


class DrawingExtractor:
    """
    Extracts structured data from construction drawings using Claude Vision API
    """

    # Prompt template for Claude Vision API
    EXTRACTION_PROMPT = """You are an expert civil engineer analyzing a construction drawing.
Extract all relevant information for creating a Bill of Quantities (BOQ).

Please analyze this construction drawing and extract the following information in JSON format:

{
  "drawing_info": {
    "drawing_number": "string - drawing number/ID",
    "drawing_type": "string - plan/section/elevation/detail",
    "scale": "string - drawing scale",
    "title": "string - drawing title"
  },
  "dimensions": [
    {
      "element_type": "string - type of element (beam/column/wall/slab/foundation/etc)",
      "length": number in meters,
      "width": number in meters,
      "height": number in meters,
      "thickness": number in meters (if applicable),
      "diameter": number in meters (for circular elements),
      "count": integer - number of similar elements,
      "location": "string - location/grid reference",
      "remarks": "string - any additional notes"
    }
  ],
  "materials": [
    {
      "material_type": "string - concrete/steel/brick/etc",
      "grade": "string - grade (M20, Fe500, etc)",
      "specification": "string - full specification",
      "location": "string - where used",
      "quantity": number (if specified),
      "unit": "string - unit of measurement"
    }
  ],
  "notes": ["array of important notes/specifications from drawing"],
  "text_annotations": ["any other relevant text found on drawing"]
}

IMPORTANT INSTRUCTIONS:
1. Extract ALL dimensions shown on the drawing
2. Identify element types accurately (beams, columns, slabs, walls, foundations)
3. Convert all dimensions to METERS (from mm, cm, or other units)
4. Note the material specifications (concrete grade, steel grade, etc.)
5. Include grid references or location identifiers
6. If multiple similar elements exist, note the count
7. Extract any notes about specifications or standards
8. Be precise with numbers - these will be used for cost estimation

Return ONLY valid JSON without any markdown formatting or code blocks."""

    def __init__(self, api_key: str):
        """
        Initialize drawing extractor

        Args:
            api_key: Anthropic API key for Claude
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude with vision

    def extract_from_pdf(
        self,
        pdf_path: Union[str, Path],
        page_numbers: Optional[List[int]] = None,
        dpi: int = 300
    ) -> List[DrawingExtractionResult]:
        """
        Extract data from PDF drawing

        Args:
            pdf_path: Path to PDF file
            page_numbers: Specific pages to process (None = all pages)
            dpi: DPI for PDF to image conversion

        Returns:
            List of extraction results, one per page
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        logger.info(f"Processing PDF: {pdf_path}")

        # Convert PDF to images
        try:
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=page_numbers[0] if page_numbers else None,
                last_page=page_numbers[-1] if page_numbers else None
            )
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            raise

        results = []
        for page_num, image in enumerate(images, start=1):
            logger.info(f"Processing page {page_num}/{len(images)}")
            try:
                result = self._extract_from_image(image, pdf_path.stem, page_num)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process page {page_num}: {e}")
                # Continue with other pages

        return results

    def _extract_from_image(
        self,
        image,
        drawing_name: str,
        page_number: int
    ) -> DrawingExtractionResult:
        """
        Extract data from a single image using Claude Vision API

        Args:
            image: PIL Image object
            drawing_name: Name of the drawing
            page_number: Page number

        Returns:
            DrawingExtractionResult
        """
        # Convert image to base64
        import io
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Call Claude Vision API
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": self.EXTRACTION_PROMPT
                            }
                        ],
                    }
                ],
            )

            # Parse response
            response_text = message.content[0].text

            # Clean response if it has markdown code blocks
            response_text = response_text.strip()
            if response_text.startswith('```'):
                # Remove markdown code blocks
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])

            extracted_data = json.loads(response_text)

            # Convert to structured result
            result = self._parse_extraction_result(
                extracted_data,
                drawing_name,
                page_number
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response: {message.content[0].text}")
            raise
        except Exception as e:
            logger.error(f"Vision API call failed: {e}")
            raise

    def _parse_extraction_result(
        self,
        data: dict,
        drawing_name: str,
        page_number: int
    ) -> DrawingExtractionResult:
        """
        Parse raw extraction data into structured result

        Args:
            data: Raw JSON data from Claude
            drawing_name: Drawing name
            page_number: Page number

        Returns:
            DrawingExtractionResult
        """
        drawing_info = data.get('drawing_info', {})

        # Parse dimensions
        dimensions = []
        for dim_data in data.get('dimensions', []):
            try:
                dimension = ExtractedDimension(
                    element_type=dim_data.get('element_type', 'unknown'),
                    length=dim_data.get('length'),
                    width=dim_data.get('width'),
                    height=dim_data.get('height'),
                    thickness=dim_data.get('thickness'),
                    diameter=dim_data.get('diameter'),
                    count=dim_data.get('count', 1),
                    location=dim_data.get('location', ''),
                    drawing_reference=f"{drawing_name}_p{page_number}",
                    remarks=dim_data.get('remarks', '')
                )
                dimensions.append(dimension)
            except Exception as e:
                logger.warning(f"Failed to parse dimension: {e}")

        # Parse materials
        materials = []
        for mat_data in data.get('materials', []):
            try:
                material = ExtractedMaterial(
                    material_type=mat_data.get('material_type', ''),
                    grade=mat_data.get('grade'),
                    specification=mat_data.get('specification', ''),
                    quantity=mat_data.get('quantity'),
                    unit=mat_data.get('unit', ''),
                    location=mat_data.get('location', '')
                )
                materials.append(material)
            except Exception as e:
                logger.warning(f"Failed to parse material: {e}")

        return DrawingExtractionResult(
            drawing_name=drawing_name,
            drawing_number=drawing_info.get('drawing_number', f"{drawing_name}_p{page_number}"),
            drawing_type=drawing_info.get('drawing_type', 'unknown'),
            scale=drawing_info.get('scale'),
            dimensions=dimensions,
            materials=materials,
            notes=data.get('notes', []),
            metadata={
                'page_number': page_number,
                'text_annotations': data.get('text_annotations', [])
            }
        )

    def extract_from_image_file(
        self,
        image_path: Union[str, Path]
    ) -> DrawingExtractionResult:
        """
        Extract data from image file (PNG, JPG, etc.)

        Args:
            image_path: Path to image file

        Returns:
            DrawingExtractionResult
        """
        from PIL import Image

        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        image = Image.open(image_path)
        return self._extract_from_image(image, image_path.stem, 1)

    def batch_process(
        self,
        file_paths: List[Union[str, Path]],
        output_dir: Optional[Union[str, Path]] = None
    ) -> List[DrawingExtractionResult]:
        """
        Process multiple drawing files

        Args:
            file_paths: List of file paths
            output_dir: Optional directory to save extraction results as JSON

        Returns:
            List of all extraction results
        """
        all_results = []

        for file_path in file_paths:
            file_path = Path(file_path)
            logger.info(f"Processing: {file_path}")

            try:
                if file_path.suffix.lower() == '.pdf':
                    results = self.extract_from_pdf(file_path)
                elif file_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                    results = [self.extract_from_image_file(file_path)]
                else:
                    logger.warning(f"Unsupported file type: {file_path.suffix}")
                    continue

                all_results.extend(results)

                # Save individual results if output_dir specified
                if output_dir:
                    output_dir = Path(output_dir)
                    output_dir.mkdir(exist_ok=True, parents=True)

                    for i, result in enumerate(results):
                        output_file = output_dir / f"{file_path.stem}_page{i+1}_extraction.json"
                        with open(output_file, 'w') as f:
                            json.dump(result.to_dict(), f, indent=2)
                        logger.info(f"Saved extraction: {output_file}")

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                continue

        return all_results


def get_extraction_summary(results: List[DrawingExtractionResult]) -> dict:
    """
    Get summary statistics from extraction results

    Args:
        results: List of extraction results

    Returns:
        Summary dictionary
    """
    total_dimensions = sum(len(r.dimensions) for r in results)
    total_materials = sum(len(r.materials) for r in results)

    element_types = {}
    for result in results:
        for dim in result.dimensions:
            element_types[dim.element_type] = element_types.get(dim.element_type, 0) + dim.count

    material_types = {}
    for result in results:
        for mat in result.materials:
            key = f"{mat.material_type} {mat.grade}" if mat.grade else mat.material_type
            material_types[key] = material_types.get(key, 0) + 1

    return {
        'total_drawings': len(results),
        'total_dimensions_extracted': total_dimensions,
        'total_materials_identified': total_materials,
        'element_type_summary': element_types,
        'material_type_summary': material_types,
        'drawing_types': [r.drawing_type for r in results]
    }
