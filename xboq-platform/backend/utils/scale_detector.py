"""
Scale Detection & Calibration Module
Automatically detect drawing scale or allow manual calibration
Converts pixel measurements to real-world units (feet, meters)
"""

import re
import cv2
import numpy as np
import pytesseract
from typing import Optional, Tuple, Dict
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ScaleDetector:
    """
    Detect and calibrate drawing scale for accurate measurements

    Supports:
    - Architectural scales (1/4" = 1'-0", 1/8" = 1'-0", etc.)
    - Metric scales (1:50, 1:100, 1:200, etc.)
    - Manual calibration (user clicks two points with known distance)
    """

    # Common architectural scales (inches per foot)
    ARCHITECTURAL_SCALES = {
        '1/16': 1/16,
        '1/8': 1/8,
        '3/16': 3/16,
        '1/4': 1/4,
        '3/8': 3/8,
        '1/2': 1/2,
        '3/4': 3/4,
        '1': 1,
        '1-1/2': 1.5,
        '3': 3
    }

    # Common metric scales (ratio)
    METRIC_SCALES = {
        '1:20': 1/20,
        '1:25': 1/25,
        '1:50': 1/50,
        '1:75': 1/75,
        '1:100': 1/100,
        '1:125': 1/125,
        '1:200': 1/200,
        '1:250': 1/250,
        '1:500': 1/500
    }

    def __init__(self):
        self.scale_text = None
        self.pixels_per_foot = None
        self.pixels_per_meter = None
        self.scale_type = None  # 'architectural' or 'metric'
        self.confidence = 0.0

    def detect_scale_auto(self, image_path: str, dpi: int = 300) -> Dict:
        """
        Automatically detect scale from drawing using OCR

        Args:
            image_path: Path to floor plan image
            dpi: Image DPI (dots per inch) - default 300

        Returns:
            {
                'scale_text': '1/4" = 1\'-0"',
                'pixels_per_foot': 96.0,
                'pixels_per_meter': 315.0,
                'scale_type': 'architectural',
                'confidence': 0.85,
                'method': 'auto_detected'
            }
        """
        logger.info(f"Auto-detecting scale from: {image_path}")

        # Read image
        if isinstance(image_path, str):
            image = cv2.imread(image_path)
        else:
            image = image_path  # Already loaded

        if image is None:
            logger.error(f"Failed to load image: {image_path}")
            return self._default_scale(dpi)

        # Extract text from image using OCR
        scale_text = self._extract_scale_text(image)

        if scale_text:
            # Parse scale text and calculate ratios
            result = self._parse_scale_text(scale_text, dpi)
            if result['confidence'] > 0.5:
                logger.info(f"✓ Scale detected: {result['scale_text']} (confidence: {result['confidence']:.2f})")
                return result

        # Fallback: assume common scale
        logger.warning("Could not detect scale automatically, using default 1/4\" = 1'-0\"")
        return self._default_scale(dpi)

    def _extract_scale_text(self, image: np.ndarray) -> Optional[str]:
        """
        Extract scale text from drawing using OCR
        Looks in typical locations: bottom right, title block
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Focus on bottom 20% of image (where scale is usually located)
        h, w = gray.shape
        bottom_section = gray[int(h * 0.8):, :]

        # Enhance contrast
        enhanced = cv2.equalizeHist(bottom_section)

        # OCR
        try:
            text = pytesseract.image_to_string(enhanced)

            # Look for scale patterns in OCR output
            scale_patterns = [
                r'(\d+/\d+)"\s*=\s*\d+\'-\d+"',  # 1/4" = 1'-0"
                r'(\d+/\d+)"\s*=\s*\d+\'',        # 1/4" = 1'
                r'SCALE\s*:?\s*(\d+/\d+)',        # SCALE: 1/4
                r'1\s*:\s*(\d+)',                  # 1:50 (metric)
                r'SCALE\s*1\s*:\s*(\d+)',         # SCALE 1:50
            ]

            for pattern in scale_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Found scale text
                    scale_text = match.group(0)
                    logger.debug(f"Found scale text: {scale_text}")
                    return scale_text

        except Exception as e:
            logger.warning(f"OCR failed: {e}")

        return None

    def _parse_scale_text(self, scale_text: str, dpi: int) -> Dict:
        """
        Parse scale text and calculate pixels per foot/meter

        Examples:
        - "1/4\" = 1'-0\"" → architectural, 1/4 inch = 1 foot
        - "SCALE: 1/8" → architectural, 1/8 inch = 1 foot
        - "1:50" → metric, 1 unit = 50 units
        """
        # Architectural scale pattern: 1/4" = 1'-0"
        arch_match = re.search(r'(\d+/\d+)"\s*=\s*(\d+)\'-(\d+)"', scale_text)
        if arch_match:
            fraction = arch_match.group(1)
            feet = int(arch_match.group(2))
            inches = int(arch_match.group(3))

            # Parse fraction
            num, denom = map(int, fraction.split('/'))
            inches_on_paper = num / denom

            # Calculate real-world distance in inches
            real_inches = (feet * 12) + inches

            # Calculate pixels per foot
            # At scale 1/4" = 1'-0":
            # 1/4 inch on paper = 1 foot real-world
            # At 300 DPI: 1 inch on paper = 300 pixels
            # So: (1/4 * 300) pixels = 1 foot
            pixels_for_scale_unit = inches_on_paper * dpi
            pixels_per_foot = pixels_for_scale_unit / feet if feet > 0 else pixels_for_scale_unit

            # For 1/4" = 1'-0" at 300 DPI:
            # 0.25 * 300 = 75 pixels = 1 foot
            # But we want pixels per foot, so: 75 pixels/foot
            # Actually: (1/4 inch * 300 DPI) = 75 pixels represents 1 foot

            # Correct calculation:
            # If 1/4" on paper = 1' in reality
            # Then 1" on paper = 4' in reality
            # At 300 DPI: 300 pixels = 4 feet
            # So: pixels_per_foot = 300 / 4 = 75
            scale_ratio = real_inches / (inches_on_paper * 12)  # feet per inch on paper
            pixels_per_foot = dpi / scale_ratio

            return {
                'scale_text': scale_text,
                'pixels_per_foot': pixels_per_foot,
                'pixels_per_meter': pixels_per_foot * 3.28084,  # 1 meter = 3.28084 feet
                'scale_type': 'architectural',
                'confidence': 0.85,
                'method': 'auto_detected',
                'dpi': dpi
            }

        # Metric scale pattern: 1:50
        metric_match = re.search(r'1\s*:\s*(\d+)', scale_text)
        if metric_match:
            ratio = int(metric_match.group(1))

            # At scale 1:50
            # 1 unit on paper = 50 units in reality
            # At 300 DPI: 1 inch on paper = 300 pixels
            # 1 inch = 25.4mm
            # So: 300 pixels = 25.4mm on paper = 25.4 * 50 = 1270mm = 1.27m in reality
            # pixels_per_meter = 300 / 1.27 = 236.22

            # Correct:
            # 1 inch on paper (300 pixels at 300 DPI) = 25.4mm
            # At 1:50 scale, 25.4mm on paper = 25.4 * 50 = 1270mm = 1.27m real
            # So: 300 pixels = 1.27 meters
            # pixels_per_meter = 300 / 1.27 = 236.22

            mm_per_inch = 25.4
            pixels_per_inch = dpi
            mm_on_paper = mm_per_inch  # 1 inch
            mm_real = mm_on_paper * ratio
            meters_real = mm_real / 1000
            pixels_per_meter = pixels_per_inch / meters_real

            return {
                'scale_text': scale_text,
                'pixels_per_foot': pixels_per_meter / 3.28084,
                'pixels_per_meter': pixels_per_meter,
                'scale_type': 'metric',
                'confidence': 0.80,
                'method': 'auto_detected',
                'dpi': dpi
            }

        # Could not parse
        return {
            'scale_text': None,
            'pixels_per_foot': None,
            'pixels_per_meter': None,
            'scale_type': None,
            'confidence': 0.0,
            'method': 'failed'
        }

    def _default_scale(self, dpi: int = 300) -> Dict:
        """
        Return default scale when auto-detection fails
        Default: 1/4" = 1'-0" (common architectural scale)
        """
        # 1/4" = 1'-0" means:
        # 0.25 inches on paper = 1 foot in reality
        # 1 inch on paper = 4 feet in reality
        # At 300 DPI: 300 pixels = 4 feet
        # pixels_per_foot = 300 / 4 = 75

        pixels_per_foot = dpi / 4  # For 1/4" scale

        return {
            'scale_text': '1/4" = 1\'-0" (assumed)',
            'pixels_per_foot': pixels_per_foot,
            'pixels_per_meter': pixels_per_foot * 3.28084,
            'scale_type': 'architectural',
            'confidence': 0.3,
            'method': 'default',
            'dpi': dpi
        }

    def calibrate_manual(self, point1: Tuple[int, int], point2: Tuple[int, int],
                        known_distance_feet: float) -> Dict:
        """
        Manual calibration: user clicks two points with known distance

        Args:
            point1: (x1, y1) pixel coordinates
            point2: (x2, y2) pixel coordinates
            known_distance_feet: Real-world distance in feet

        Returns:
            Scale calibration dict

        Example:
            User clicks two corners of a room they know is 20 feet wide
            point1 = (100, 200)
            point2 = (1600, 200)
            known_distance_feet = 20.0

            → pixels_per_foot = 1500 / 20 = 75
        """
        # Calculate pixel distance
        x1, y1 = point1
        x2, y2 = point2
        pixel_distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

        # Calculate pixels per foot
        pixels_per_foot = pixel_distance / known_distance_feet

        logger.info(f"Manual calibration: {pixel_distance:.1f} pixels = {known_distance_feet} feet")
        logger.info(f"→ pixels_per_foot = {pixels_per_foot:.2f}")

        return {
            'scale_text': f'Manual calibration ({known_distance_feet} ft)',
            'pixels_per_foot': pixels_per_foot,
            'pixels_per_meter': pixels_per_foot * 3.28084,
            'scale_type': 'manual',
            'confidence': 1.0,
            'method': 'manual_calibration',
            'calibration_points': {
                'point1': point1,
                'point2': point2,
                'pixel_distance': pixel_distance,
                'known_distance_feet': known_distance_feet
            }
        }

    def pixels_to_feet(self, pixels: float, scale_info: Dict) -> float:
        """Convert pixels to feet using scale info"""
        if scale_info['pixels_per_foot'] is None or scale_info['pixels_per_foot'] == 0:
            logger.warning("Invalid scale, cannot convert pixels to feet")
            return 0.0
        return pixels / scale_info['pixels_per_foot']

    def pixels_to_meters(self, pixels: float, scale_info: Dict) -> float:
        """Convert pixels to meters using scale info"""
        if scale_info['pixels_per_meter'] is None or scale_info['pixels_per_meter'] == 0:
            logger.warning("Invalid scale, cannot convert pixels to meters")
            return 0.0
        return pixels / scale_info['pixels_per_meter']

    def feet_to_pixels(self, feet: float, scale_info: Dict) -> float:
        """Convert feet to pixels using scale info"""
        if scale_info['pixels_per_foot'] is None:
            logger.warning("Invalid scale, cannot convert feet to pixels")
            return 0.0
        return feet * scale_info['pixels_per_foot']


# Testing
if __name__ == '__main__':
    print("="*70)
    print("SCALE DETECTOR TEST")
    print("="*70)

    detector = ScaleDetector()

    # Test 1: Default scale
    print("\n1. Default Scale (1/4\" = 1'-0\" at 300 DPI):")
    default = detector._default_scale(dpi=300)
    print(f"   pixels_per_foot: {default['pixels_per_foot']}")
    print(f"   10 feet = {detector.feet_to_pixels(10, default):.1f} pixels")
    print(f"   750 pixels = {detector.pixels_to_feet(750, default):.1f} feet")

    # Test 2: Parse scale text
    print("\n2. Parse Architectural Scale:")
    scale_text = '1/4" = 1\'-0"'
    result = detector._parse_scale_text(scale_text, dpi=300)
    print(f"   Text: {scale_text}")
    print(f"   pixels_per_foot: {result['pixels_per_foot']:.2f}")

    # Test 3: Parse metric scale
    print("\n3. Parse Metric Scale:")
    scale_text = '1:50'
    result = detector._parse_scale_text(scale_text, dpi=300)
    print(f"   Text: {scale_text}")
    print(f"   pixels_per_meter: {result['pixels_per_meter']:.2f}")

    # Test 4: Manual calibration
    print("\n4. Manual Calibration:")
    result = detector.calibrate_manual(
        point1=(100, 200),
        point2=(1600, 200),
        known_distance_feet=20.0
    )
    print(f"   Pixel distance: {result['calibration_points']['pixel_distance']:.1f}")
    print(f"   Known distance: {result['calibration_points']['known_distance_feet']} feet")
    print(f"   pixels_per_foot: {result['pixels_per_foot']:.2f}")

    print("\n" + "="*70)
    print("✅ SCALE DETECTOR TESTS COMPLETE")
    print("="*70 + "\n")
