"""
Vision-Based Extractor
Uses Claude Vision API to analyze architectural drawings and complex images
"""

from anthropic import Anthropic
from typing import Dict, List, Optional
from dataclasses import dataclass
import base64
import json
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class DrawingData:
    """Data extracted from architectural drawing"""
    rooms: List[Dict]
    materials: List[Dict]
    dimensions: List[Dict]
    total_area: float
    special_requirements: List[str]
    confidence: float
    raw_analysis: str

    def to_dict(self) -> Dict:
        return {
            'rooms': self.rooms,
            'materials': self.materials,
            'dimensions': self.dimensions,
            'total_area': self.total_area,
            'special_requirements': self.special_requirements,
            'confidence': self.confidence
        }


@dataclass
class MeasurementData:
    """Measurements extracted from image"""
    measurements: List[Dict]
    unit: str
    confidence: float

    def to_dict(self) -> Dict:
        return {
            'measurements': self.measurements,
            'unit': self.unit,
            'confidence': self.confidence
        }


class VisionBasedExtractor:
    """
    Extract data from architectural drawings and complex images using Claude Vision API
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialize Vision Extractor

        Args:
            anthropic_api_key: Anthropic API key (or uses ANTHROPIC_API_KEY env var)
        """
        api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')

        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set. Vision extraction will not work.")
            self.client = None
        else:
            self.client = Anthropic(api_key=api_key)

    def extract_from_architectural_drawing(self, image_path: str) -> DrawingData:
        """
        Analyze architectural drawing and extract structured data

        Args:
            image_path: Path to drawing image

        Returns:
            DrawingData with extracted information
        """
        if not self.client:
            raise Exception("Anthropic API client not initialized. Set ANTHROPIC_API_KEY.")

        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.standard_b64encode(f.read()).decode('utf-8')

            # Determine media type
            media_type = self._get_media_type(image_path)

            # Prepare prompt
            prompt = """Analyze this architectural/construction drawing and extract detailed information.

Please identify and extract:

1. **Rooms/Spaces**:
   - Name of each room
   - Dimensions (length x width)
   - Area calculation
   - Purpose/function

2. **Materials Specified**:
   - Type of material (walls, flooring, roofing, etc.)
   - Material specification (e.g., "230mm brick wall", "RCC roof", "Vitrified tiles")
   - Quantity/area where specified
   - Unit of measurement

3. **Dimensions**:
   - Overall building dimensions
   - Individual room dimensions
   - Height measurements
   - Any other critical measurements

4. **Total Areas**:
   - Built-up area
   - Carpet area
   - Any other area calculations visible

5. **Special Requirements**:
   - Any notes or annotations
   - Special specifications
   - Construction techniques mentioned
   - Material grades (if specified)

Return your analysis as a JSON object with this exact structure:
{
  "rooms": [
    {
      "name": "Living Room",
      "length": 5.0,
      "width": 4.0,
      "area": 20.0,
      "unit": "sqm",
      "purpose": "Living space"
    }
  ],
  "materials": [
    {
      "type": "Wall",
      "material": "230mm brick wall",
      "specification": "Class designation 7.5 FPS bricks in CM 1:6",
      "quantity": 100.0,
      "unit": "sqm"
    }
  ],
  "dimensions": [
    {
      "element": "Overall building",
      "measurement": "15m x 10m",
      "value": 15.0,
      "unit": "m"
    }
  ],
  "total_area": 150.0,
  "special_requirements": [
    "Provide waterproofing for terrace",
    "Use earthquake-resistant design"
  ]
}

Important:
- If dimension/area is not clearly visible, estimate based on visible information
- Use standard units: m (meters), sqm (square meters), cum (cubic meters)
- Be as specific as possible with material specifications
- If information is not available, use empty arrays
- Return ONLY the JSON object, no additional text"""

            # Call Claude Vision API
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            # Extract response
            response_text = message.content[0].text

            # Parse JSON
            analysis_data = self._parse_json_response(response_text)

            # Create DrawingData object
            drawing_data = DrawingData(
                rooms=analysis_data.get('rooms', []),
                materials=analysis_data.get('materials', []),
                dimensions=analysis_data.get('dimensions', []),
                total_area=analysis_data.get('total_area', 0.0),
                special_requirements=analysis_data.get('special_requirements', []),
                confidence=0.85,  # High confidence for vision API
                raw_analysis=response_text
            )

            logger.info(f"Extracted drawing data: {len(drawing_data.rooms)} rooms, "
                       f"{len(drawing_data.materials)} materials, total area: {drawing_data.total_area}")

            return drawing_data

        except Exception as e:
            logger.error(f"Error extracting from architectural drawing: {e}")
            # Return empty DrawingData
            return DrawingData(
                rooms=[],
                materials=[],
                dimensions=[],
                total_area=0.0,
                special_requirements=[],
                confidence=0.0,
                raw_analysis=str(e)
            )

    def extract_measurements_from_image(self, image_path: str) -> MeasurementData:
        """
        Extract measurements from construction image

        Args:
            image_path: Path to image with measurements

        Returns:
            MeasurementData with extracted measurements
        """
        if not self.client:
            raise Exception("Anthropic API client not initialized. Set ANTHROPIC_API_KEY.")

        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.standard_b64encode(f.read()).decode('utf-8')

            media_type = self._get_media_type(image_path)

            prompt = """Extract all measurements and dimensions from this image.

Look for:
- Length, width, height measurements
- Area calculations
- Thickness specifications
- Distance markers
- Any numeric values with units

Return as JSON:
{
  "measurements": [
    {
      "element": "Wall",
      "value": 5.0,
      "unit": "m",
      "context": "Length of north wall"
    }
  ],
  "unit": "m"
}

Return ONLY the JSON object."""

            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            response_text = message.content[0].text
            data = self._parse_json_response(response_text)

            return MeasurementData(
                measurements=data.get('measurements', []),
                unit=data.get('unit', 'm'),
                confidence=0.8
            )

        except Exception as e:
            logger.error(f"Error extracting measurements: {e}")
            return MeasurementData(measurements=[], unit='m', confidence=0.0)

    def extract_annotations(self, image_path: str) -> List[str]:
        """
        Extract text annotations and notes from construction image

        Args:
            image_path: Path to image

        Returns:
            List of extracted annotations
        """
        if not self.client:
            raise Exception("Anthropic API client not initialized. Set ANTHROPIC_API_KEY.")

        try:
            with open(image_path, 'rb') as f:
                image_data = base64.standard_b64encode(f.read()).decode('utf-8')

            media_type = self._get_media_type(image_path)

            prompt = """Extract all text annotations, notes, and labels from this construction drawing/image.

Include:
- Hand-written notes
- Printed labels
- Material specifications
- Construction notes
- Any other text visible in the image

Return as simple JSON array:
{
  "annotations": ["annotation 1", "annotation 2", ...]
}

Return ONLY the JSON."""

            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            response_text = message.content[0].text
            data = self._parse_json_response(response_text)

            annotations = data.get('annotations', [])
            logger.info(f"Extracted {len(annotations)} annotations")

            return annotations

        except Exception as e:
            logger.error(f"Error extracting annotations: {e}")
            return []

    def analyze_construction_image(self, image_path: str, context: Optional[str] = None) -> Dict:
        """
        General-purpose construction image analysis

        Args:
            image_path: Path to image
            context: Optional context about what to look for

        Returns:
            Dictionary with analysis results
        """
        if not self.client:
            raise Exception("Anthropic API client not initialized. Set ANTHROPIC_API_KEY.")

        try:
            with open(image_path, 'rb') as f:
                image_data = base64.standard_b64encode(f.read()).decode('utf-8')

            media_type = self._get_media_type(image_path)

            base_prompt = """Analyze this construction-related image and extract relevant information.

Identify:
1. What type of document/image is this? (drawing, photo, diagram, etc.)
2. What construction elements are visible?
3. Any measurements, specifications, or quantities
4. Materials mentioned or shown
5. Any important details for BOQ estimation

Provide structured analysis as JSON."""

            if context:
                prompt = f"{base_prompt}\n\nAdditional context: {context}\n\nReturn analysis as JSON."
            else:
                prompt = base_prompt

            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            response_text = message.content[0].text

            # Try to parse as JSON, fallback to text
            try:
                analysis = self._parse_json_response(response_text)
            except:
                analysis = {'analysis': response_text}

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {'error': str(e)}

    def _get_media_type(self, image_path: str) -> str:
        """Determine media type from file extension"""
        ext = image_path.lower().split('.')[-1]
        media_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        return media_types.get(ext, 'image/jpeg')

    def _parse_json_response(self, response_text: str) -> Dict:
        """Parse JSON from Claude response"""
        # Remove markdown code blocks if present
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            response_text = response_text[start:end].strip()
        elif '```' in response_text:
            start = response_text.find('```') + 3
            end = response_text.find('```', start)
            response_text = response_text[start:end].strip()

        return json.loads(response_text)


# Convenience functions

def extract_drawing_data(image_path: str, api_key: Optional[str] = None) -> DrawingData:
    """Quick extraction from architectural drawing"""
    extractor = VisionBasedExtractor(api_key)
    return extractor.extract_from_architectural_drawing(image_path)


def extract_measurements(image_path: str, api_key: Optional[str] = None) -> MeasurementData:
    """Quick measurement extraction"""
    extractor = VisionBasedExtractor(api_key)
    return extractor.extract_measurements_from_image(image_path)


def analyze_image(image_path: str, api_key: Optional[str] = None, context: Optional[str] = None) -> Dict:
    """Quick image analysis"""
    extractor = VisionBasedExtractor(api_key)
    return extractor.analyze_construction_image(image_path, context)
