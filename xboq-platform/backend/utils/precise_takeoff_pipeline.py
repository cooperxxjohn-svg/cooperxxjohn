"""
Precise Takeoff Pipeline - Integration Example
Combines all Phase 1 modules for production-ready measurements

Workflow:
1. Detect scale from drawing
2. Extract OCR dimensions
3. Measure rooms with CV
4. Cross-validate all sources
5. Return validated measurements with confidence scores
"""

import cv2
import numpy as np
from typing import Dict, List
import logging

from utils.scale_detector import ScaleDetector
from utils.drawing_ocr import DrawingOCR
from utils.precise_measurement import PreciseMeasurement
from utils.measurement_validator import MeasurementValidator

logger = logging.getLogger(__name__)


class PreciseTakeoffPipeline:
    """
    End-to-end pipeline for precise takeoff measurements

    Combines:
    - Scale detection
    - OCR dimension extraction
    - Pixel-perfect CV measurements
    - Multi-source validation
    """

    def __init__(self):
        self.scale_detector = ScaleDetector()
        self.ocr = DrawingOCR()
        self.measurer = PreciseMeasurement()
        self.validator = MeasurementValidator()

    def process_floor_plan(self,
                          image_path: str,
                          room_boundaries: List[List[tuple]] = None,
                          llm_output: List[Dict] = None,
                          dpi: int = 300) -> Dict:
        """
        Complete floor plan processing with validation

        Args:
            image_path: Path to floor plan image
            room_boundaries: Optional pre-detected room boundaries
                            (from TF2DeepFloorplan or Claude API)
            llm_output: Optional LLM detected rooms (from Claude)
            dpi: Image DPI for scale calculation

        Returns:
            {
                'scale_info': {...},
                'rooms': [
                    {
                        'name': 'Living Room',
                        'area_sqft': 245.3,
                        'confidence': 'high',
                        'needs_review': False,
                        ...
                    }
                ],
                'summary': {
                    'total_rooms': 8,
                    'high_confidence': 6,
                    'needs_review': 2
                },
                'processing_time': 12.5
            }
        """
        import time
        start_time = time.time()

        logger.info(f"Starting precise takeoff pipeline: {image_path}")

        # Step 1: Detect scale
        logger.info("Step 1/4: Detecting scale...")
        scale_info = self.scale_detector.detect_scale_auto(image_path, dpi=dpi)
        self.measurer.set_scale(scale_info)

        logger.info(f"  ✓ Scale: {scale_info['scale_text']} ({scale_info['pixels_per_foot']:.1f} px/ft)")

        # Step 2: Extract OCR dimensions
        logger.info("Step 2/4: Extracting OCR dimensions...")
        ocr_dimensions = self.ocr.extract_dimensions(image_path)
        logger.info(f"  ✓ Found {len(ocr_dimensions)} dimensions via OCR")

        # Step 3: Measure rooms from boundaries
        logger.info("Step 3/4: Measuring rooms...")
        pixel_measurements = []

        if room_boundaries:
            for i, boundary in enumerate(room_boundaries):
                room_name = f"Room {i+1}"
                room = self.measurer.measure_room_from_polygon(boundary, room_name)
                pixel_measurements.append(room)

            logger.info(f"  ✓ Measured {len(pixel_measurements)} rooms")
        else:
            logger.warning("  ⚠ No room boundaries provided, skipping pixel measurement")
            logger.info("    Tip: Provide room_boundaries from TF2DeepFloorplan or Claude API")

        # Step 4: Cross-validate measurements
        logger.info("Step 4/4: Cross-validating measurements...")
        validation_result = self.validator.validate_room_measurements(
            pixel_measurements=pixel_measurements,
            ocr_dimensions=ocr_dimensions,
            llm_output=llm_output or []
        )

        logger.info(f"  ✓ Validation complete")
        logger.info(f"    High confidence: {validation_result['summary']['high_confidence']}/{validation_result['summary']['total_rooms']}")
        logger.info(f"    Needs review: {validation_result['summary']['needs_review']}")

        processing_time = time.time() - start_time

        return {
            'scale_info': scale_info,
            'rooms': validation_result['rooms'],
            'summary': validation_result['summary'],
            'ocr_dimensions': ocr_dimensions,
            'processing_time': round(processing_time, 2)
        }

    def process_with_manual_calibration(self,
                                       image_path: str,
                                       calibration_point1: tuple,
                                       calibration_point2: tuple,
                                       known_distance_feet: float,
                                       room_boundaries: List[List[tuple]]) -> Dict:
        """
        Process floor plan with manual scale calibration

        Use when auto-detection fails or user wants precise control

        Args:
            image_path: Floor plan image
            calibration_point1: (x, y) first point
            calibration_point2: (x, y) second point
            known_distance_feet: Real-world distance between points
            room_boundaries: Detected room boundaries

        Returns:
            Same as process_floor_plan()
        """
        # Manual calibration
        scale_info = self.scale_detector.calibrate_manual(
            calibration_point1,
            calibration_point2,
            known_distance_feet
        )

        self.measurer.set_scale(scale_info)

        # Extract OCR dimensions
        ocr_dimensions = self.ocr.extract_dimensions(image_path)

        # Measure rooms
        pixel_measurements = []
        for i, boundary in enumerate(room_boundaries):
            room = self.measurer.measure_room_from_polygon(boundary, f"Room {i+1}")
            pixel_measurements.append(room)

        # Validate
        validation_result = self.validator.validate_room_measurements(
            pixel_measurements,
            ocr_dimensions,
            []
        )

        return {
            'scale_info': scale_info,
            'rooms': validation_result['rooms'],
            'summary': validation_result['summary'],
            'ocr_dimensions': ocr_dimensions
        }


# Example usage
if __name__ == '__main__':
    print("="*70)
    print("PRECISE TAKEOFF PIPELINE EXAMPLE")
    print("="*70)

    # Initialize pipeline
    pipeline = PreciseTakeoffPipeline()

    # Example 1: Auto-detection (no image needed for demo)
    print("\n1. Auto-Detection Example:")
    print("   (Requires actual floor plan image)")
    print("   Usage:")
    print("   >>> pipeline = PreciseTakeoffPipeline()")
    print("   >>> result = pipeline.process_floor_plan('floor_plan.png', room_boundaries)")
    print("   >>> print(f\"Detected {result['summary']['total_rooms']} rooms\")")
    print("   >>> print(f\"High confidence: {result['summary']['high_confidence']}\")")

    # Example 2: Manual calibration
    print("\n2. Manual Calibration Example:")
    print("   User clicks two points they know are 20 feet apart")
    print("   >>> result = pipeline.process_with_manual_calibration(")
    print("   ...     image_path='floor_plan.png',")
    print("   ...     calibration_point1=(100, 200),")
    print("   ...     calibration_point2=(1600, 200),")
    print("   ...     known_distance_feet=20.0,")
    print("   ...     room_boundaries=detected_boundaries")
    print("   ... )")

    # Example 3: Integration with Claude API
    print("\n3. Integration with Claude API:")
    print("   Combine Claude room detection + CV precision")
    print("   >>> # Get rooms from Claude API")
    print("   >>> claude_rooms = claude_api.detect_rooms('floor_plan.png')")
    print("   >>>")
    print("   >>> # Extract room boundaries for precise measurement")
    print("   >>> room_boundaries = [room['boundary'] for room in claude_rooms]")
    print("   >>>")
    print("   >>> # Run precision pipeline")
    print("   >>> result = pipeline.process_floor_plan(")
    print("   ...     'floor_plan.png',")
    print("   ...     room_boundaries=room_boundaries,")
    print("   ...     llm_output=claude_rooms")
    print("   ... )")
    print("   >>>")
    print("   >>> # Get validated results")
    print("   >>> for room in result['rooms']:")
    print("   ...     if room['needs_review']:")
    print("   ...         print(f\"⚠️ {room['name']}: Review needed\")")
    print("   ...     else:")
    print("   ...         print(f\"✓ {room['name']}: {room['final_area_sqft']} sqft\")")

    print("\n" + "="*70)
    print("✅ PIPELINE READY FOR INTEGRATION")
    print("="*70 + "\n")
    print("Next steps:")
    print("1. Integrate with TF2DeepFloorplan for room boundary detection")
    print("2. Integrate with Claude API for initial room identification")
    print("3. Add to backend/modules/estimator.py")
    print("4. Create frontend review interface")
