"""
Drawing OCR Module - Extract Dimensions and Annotations
Uses keras-ocr for technical drawing text extraction
Specialized for construction drawings (dimensions, notes, labels)
"""

import re
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Try to import keras-ocr (optional dependency)
try:
    import keras_ocr
    KERAS_OCR_AVAILABLE = True
except ImportError:
    KERAS_OCR_AVAILABLE = False
    logger.warning("keras-ocr not installed. OCR features will be limited. Install with: pip install keras-ocr")


class DrawingOCR:
    """
    Extract text from technical construction drawings

    Features:
    - Dimension extraction ("12'-6\"", "2440mm", "10'x12'")
    - Annotation extraction (notes, labels, callouts)
    - Room labels
    - Scale text detection
    """

    def __init__(self):
        """Initialize OCR pipeline"""
        self.pipeline = None

        if KERAS_OCR_AVAILABLE:
            try:
                logger.info("Initializing keras-ocr pipeline (downloads models on first run ~200MB)...")
                self.pipeline = keras_ocr.pipeline.Pipeline()
                logger.info("✓ keras-ocr pipeline ready")
            except Exception as e:
                logger.error(f"Failed to initialize keras-ocr: {e}")
                self.pipeline = None
        else:
            logger.warning("keras-ocr not available, dimension extraction will be limited")

    def extract_text(self, image_path: str) -> List[Dict[str, any]]:
        """
        Extract all text from drawing with bounding boxes

        Args:
            image_path: Path to drawing image (PDF page converted to image)

        Returns:
            List of {text, box, confidence}

        Example:
            [
                {'text': "12'-6\"", 'box': [[x1,y1], [x2,y2], ...], 'confidence': 0.95},
                {'text': "LIVING ROOM", 'box': [[x1,y1], ...], 'confidence': 0.88}
            ]
        """
        if not self.pipeline:
            logger.warning("OCR pipeline not available")
            return []

        try:
            # Read image
            if isinstance(image_path, str):
                image = keras_ocr.tools.read(image_path)
            else:
                # Already a numpy array
                image = image_path

            # Run OCR
            prediction_groups = self.pipeline.recognize([image])
            predictions = prediction_groups[0]  # First (and only) image

            # Format results
            results = []
            for text, box in predictions:
                results.append({
                    'text': text,
                    'box': box.tolist(),
                    'center': self._get_box_center(box),
                    'confidence': 1.0  # keras-ocr doesn't provide confidence scores
                })

            logger.info(f"Extracted {len(results)} text elements")
            return results

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return []

    def extract_dimensions(self, image_path: str) -> List[Dict[str, any]]:
        """
        Extract only dimension strings from drawing

        Supports formats:
        - Imperial: 12'-6", 15', 18", 10'x12'
        - Metric: 2440mm, 244cm, 2.44m
        - Mixed: 12' 6\"

        Returns:
            List of {
                'text': '12\'-6"',
                'value_feet': 12.5,
                'value_meters': 3.81,
                'value_inches': 150,
                'box': [[x1,y1], ...],
                'center': (x, y),
                'format': 'imperial'
            }
        """
        all_text = self.extract_text(image_path)

        dimensions = []

        # Regex patterns for common dimension formats
        dimension_patterns = [
            # Imperial feet-inches
            (r"(\d+)'-(\d+)\"", 'imperial'),           # 12'-6"
            (r"(\d+)'\s*-\s*(\d+)\"", 'imperial'),     # 12' - 6"
            (r"(\d+)'\s+(\d+)\"", 'imperial'),         # 12' 6"
            (r"(\d+)\s*'\s*(\d+)\s*\"", 'imperial'),   # 12 ' 6 "

            # Imperial feet only
            (r"(\d+)'", 'imperial_feet'),               # 15'

            # Imperial inches only
            (r"(\d+)\"", 'imperial_inches'),            # 18"

            # Metric millimeters
            (r"(\d+)\s*mm", 'metric_mm'),               # 2440mm, 2440 mm

            # Metric centimeters
            (r"(\d+)\s*cm", 'metric_cm'),               # 244cm

            # Metric meters (with decimal)
            (r"(\d+\.\d+)\s*m", 'metric_m'),            # 2.44m
            (r"(\d+)\s*m", 'metric_m'),                 # 2m

            # Area/dimensions (e.g., "10'x12'", "10x12")
            (r"(\d+)'\s*x\s*(\d+)'", 'area_imperial'),  # 10'x12'
            (r"(\d+)\s*x\s*(\d+)", 'area_generic'),     # 10x12
        ]

        for item in all_text:
            text = item['text']
            matched = False

            # Try each pattern
            for pattern, format_type in dimension_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Parse dimension
                    value_feet, value_meters, value_inches = self._parse_dimension(text, format_type, match)

                    if value_feet > 0 or value_meters > 0:
                        dimensions.append({
                            'text': text,
                            'value_feet': value_feet,
                            'value_meters': value_meters,
                            'value_inches': value_inches,
                            'box': item['box'],
                            'center': item['center'],
                            'format': format_type,
                            'confidence': item.get('confidence', 1.0)
                        })
                        matched = True
                        break

            if not matched:
                # Check if it's a number that could be a dimension
                if re.match(r'^\d+\.?\d*$', text.strip()):
                    # Just a number - could be dimension without units
                    try:
                        value = float(text.strip())
                        if 1 <= value <= 1000:  # Reasonable range for dimensions
                            dimensions.append({
                                'text': text,
                                'value_feet': value,  # Assume feet
                                'value_meters': value * 0.3048,
                                'value_inches': value * 12,
                                'box': item['box'],
                                'center': item['center'],
                                'format': 'unitless',
                                'confidence': 0.5  # Lower confidence for unitless
                            })
                    except:
                        pass

        logger.info(f"Extracted {len(dimensions)} dimensions from {len(all_text)} text elements")
        return dimensions

    def _parse_dimension(self, text: str, format_type: str, match: re.Match) -> Tuple[float, float, float]:
        """
        Convert dimension string to numeric values

        Returns:
            (feet, meters, inches)
        """
        try:
            if format_type == 'imperial':
                # 12'-6" format
                feet = int(match.group(1))
                inches = int(match.group(2))
                total_feet = feet + (inches / 12.0)
                total_inches = feet * 12 + inches
                total_meters = total_feet * 0.3048
                return total_feet, total_meters, total_inches

            elif format_type == 'imperial_feet':
                # 15' format
                feet = int(match.group(1))
                inches = feet * 12
                meters = feet * 0.3048
                return float(feet), meters, inches

            elif format_type == 'imperial_inches':
                # 18" format
                inches = int(match.group(1))
                feet = inches / 12.0
                meters = feet * 0.3048
                return feet, meters, float(inches)

            elif format_type == 'metric_mm':
                # 2440mm format
                mm = int(match.group(1))
                meters = mm / 1000.0
                feet = meters / 0.3048
                inches = feet * 12
                return feet, meters, inches

            elif format_type == 'metric_cm':
                # 244cm format
                cm = int(match.group(1))
                meters = cm / 100.0
                feet = meters / 0.3048
                inches = feet * 12
                return feet, meters, inches

            elif format_type == 'metric_m':
                # 2.44m format
                meters = float(match.group(1))
                feet = meters / 0.3048
                inches = feet * 12
                return feet, meters, inches

            elif format_type == 'area_imperial':
                # 10'x12' - return first dimension
                feet = int(match.group(1))
                inches = feet * 12
                meters = feet * 0.3048
                return float(feet), meters, inches

            elif format_type == 'area_generic':
                # 10x12 - assume feet
                value = int(match.group(1))
                inches = value * 12
                meters = value * 0.3048
                return float(value), meters, inches

        except Exception as e:
            logger.warning(f"Failed to parse dimension '{text}': {e}")

        return 0.0, 0.0, 0.0

    def _get_box_center(self, box: np.ndarray) -> Tuple[int, int]:
        """Calculate center point of bounding box"""
        if isinstance(box, list):
            box = np.array(box)
        center_x = int(np.mean(box[:, 0]))
        center_y = int(np.mean(box[:, 1]))
        return (center_x, center_y)

    def extract_room_labels(self, image_path: str) -> List[Dict[str, any]]:
        """
        Extract room labels from floor plan

        Looks for common room names:
        - LIVING ROOM, BEDROOM, KITCHEN, etc.

        Returns:
            List of {text, center, box, type}
        """
        all_text = self.extract_text(image_path)

        # Common room keywords
        room_keywords = [
            'LIVING', 'BEDROOM', 'KITCHEN', 'BATHROOM', 'DINING',
            'GARAGE', 'OFFICE', 'CLOSET', 'HALLWAY', 'ENTRY',
            'FOYER', 'LAUNDRY', 'UTILITY', 'MASTER', 'GUEST',
            'FAMILY', 'GREAT', 'POWDER', 'PANTRY', 'MUD'
        ]

        room_labels = []

        for item in all_text:
            text_upper = item['text'].upper()

            # Check if text contains room keyword
            for keyword in room_keywords:
                if keyword in text_upper:
                    room_labels.append({
                        'text': item['text'],
                        'text_normalized': text_upper,
                        'center': item['center'],
                        'box': item['box'],
                        'type': 'room_label',
                        'keyword': keyword
                    })
                    break

        logger.info(f"Found {len(room_labels)} room labels")
        return room_labels

    def find_dimension_near_point(self, dimensions: List[Dict], point: Tuple[int, int],
                                 max_distance: int = 100) -> Optional[Dict]:
        """
        Find dimension closest to a given point

        Useful for:
        - Finding dimension for a specific wall
        - Matching OCR dimensions to detected room boundaries

        Args:
            dimensions: List from extract_dimensions()
            point: (x, y) coordinate
            max_distance: Maximum pixel distance to search

        Returns:
            Closest dimension dict or None
        """
        if not dimensions:
            return None

        closest = None
        min_dist = float('inf')

        for dim in dimensions:
            center = dim['center']
            dist = np.sqrt((center[0] - point[0])**2 + (center[1] - point[1])**2)

            if dist < min_dist and dist <= max_distance:
                min_dist = dist
                closest = dim

        return closest


# Testing
if __name__ == '__main__':
    print("="*70)
    print("DRAWING OCR TEST")
    print("="*70)

    if not KERAS_OCR_AVAILABLE:
        print("\n❌ keras-ocr not installed")
        print("Install with: pip install keras-ocr")
        exit(1)

    ocr = DrawingOCR()

    # Test dimension parsing
    print("\n1. Dimension Parsing Test:")

    test_dimensions = [
        "12'-6\"",      # Feet-inches
        "15'",          # Feet only
        "18\"",         # Inches only
        "2440mm",       # Millimeters
        "244cm",        # Centimeters
        "2.44m",        # Meters
        "10'x12'",      # Area
        "12' - 6\"",    # Space variant
        "12 ' 6 \"",    # Space variant
    ]

    for dim_text in test_dimensions:
        # Test different formats
        for pattern, fmt in [
            (r"(\d+)'-(\d+)\"", 'imperial'),
            (r"(\d+)'", 'imperial_feet'),
            (r"(\d+)\"", 'imperial_inches'),
            (r"(\d+)mm", 'metric_mm'),
            (r"(\d+)cm", 'metric_cm'),
            (r"(\d+\.\d+)m", 'metric_m'),
            (r"(\d+)'\s*x\s*(\d+)'", 'area_imperial'),
        ]:
            match = re.search(pattern, dim_text)
            if match:
                feet, meters, inches = ocr._parse_dimension(dim_text, fmt, match)
                if feet > 0 or meters > 0:
                    print(f"   '{dim_text}' → {feet:.2f} ft = {meters:.2f} m = {inches:.0f} in")
                break

    print("\n" + "="*70)
    print("✅ DRAWING OCR MODULE READY")
    print("="*70 + "\n")
    print("Note: To test with actual images, provide a floor plan image path")
    print("Example: ocr.extract_dimensions('floor_plan.png')")
