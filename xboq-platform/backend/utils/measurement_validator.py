"""
Measurement Validation Module
Cross-validates measurements from multiple sources:
1. Pixel measurements (CV models)
2. OCR dimensions (from drawing)
3. LLM output (Claude API)

Flags discrepancies and provides confidence scores
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MeasurementValidator:
    """
    Cross-validate measurements from multiple sources
    Ensures production-ready accuracy by comparing:
    - Pixel-based measurements (TF2DeepFloorplan, OpenCV)
    - OCR extracted dimensions (eDOCr)
    - LLM detected rooms (Claude API)
    """

    # Thresholds for validation
    PERFECT_MATCH_THRESHOLD = 0.02   # Within 2% = perfect match
    GOOD_MATCH_THRESHOLD = 0.05      # Within 5% = good match
    ACCEPTABLE_THRESHOLD = 0.10      # Within 10% = acceptable, flag for review
    POOR_MATCH_THRESHOLD = 0.15      # >15% = poor match, needs review

    def __init__(self):
        self.validation_results = []

    def validate_room_measurements(self,
                                   pixel_measurements: List[Dict],
                                   ocr_dimensions: List[Dict],
                                   llm_output: List[Dict]) -> Dict:
        """
        Compare room measurements from all three sources

        Args:
            pixel_measurements: From PreciseMeasurement
            ocr_dimensions: From DrawingOCR
            llm_output: From Claude API

        Returns:
            {
                'rooms': [
                    {
                        'name': 'Living Room',
                        'final_area_sqft': 245.3,
                        'confidence': 'high',  # or 'medium', 'low'
                        'needs_review': False,
                        'sources': {
                            'pixel': {'area': 245.3, 'perimeter': 64.5},
                            'ocr': {'area': 245.0, 'dimensions': "14' x 17.5'"},
                            'llm': {'area': 238.0}
                        },
                        'discrepancies': [],
                        'validation_score': 0.98
                    },
                    ...
                ],
                'summary': {
                    'total_rooms': 8,
                    'high_confidence': 6,
                    'needs_review': 2,
                    'average_confidence': 0.92
                }
            }
        """
        validated_rooms = []

        # Match rooms from different sources
        for pixel_room in pixel_measurements:
            room_name = pixel_room.get('name', 'Unknown')

            # Find matching OCR dimensions nearby
            ocr_match = self._find_matching_ocr_dimension(
                pixel_room,
                ocr_dimensions
            )

            # Find matching LLM room
            llm_match = self._find_matching_llm_room(
                pixel_room,
                llm_output
            )

            # Cross-validate all sources
            validated = self._cross_validate_room(
                pixel_room,
                ocr_match,
                llm_match
            )

            validated_rooms.append(validated)

        # Generate summary
        summary = self._generate_summary(validated_rooms)

        return {
            'rooms': validated_rooms,
            'summary': summary
        }

    def _cross_validate_room(self,
                            pixel_data: Dict,
                            ocr_data: Optional[Dict],
                            llm_data: Optional[Dict]) -> Dict:
        """
        Cross-validate a single room from multiple sources

        Returns validated room with confidence score
        """
        room_name = pixel_data.get('name', 'Unknown')

        # Extract areas from each source
        pixel_area = pixel_data.get('area_sqft', 0)

        ocr_area = 0
        if ocr_data:
            # OCR might have length × width
            if 'value_feet' in ocr_data and 'secondary_value_feet' in ocr_data:
                ocr_area = ocr_data['value_feet'] * ocr_data['secondary_value_feet']
            else:
                ocr_area = ocr_data.get('area_sqft', 0)

        llm_area = 0
        if llm_data:
            llm_area = llm_data.get('sqft', 0) or llm_data.get('area_sqft', 0)

        # Collect all area measurements
        measurements = []
        sources_info = {}

        if pixel_area > 0:
            measurements.append(pixel_area)
            sources_info['pixel'] = {
                'area': pixel_area,
                'perimeter': pixel_data.get('perimeter_feet'),
                'dimensions': pixel_data.get('dimensions', {})
            }

        if ocr_area > 0:
            measurements.append(ocr_area)
            sources_info['ocr'] = {
                'area': ocr_area,
                'text': ocr_data.get('text', ''),
                'dimensions': f"{ocr_data.get('value_feet', 0):.1f}' x {ocr_data.get('secondary_value_feet', 0):.1f}'"
            }

        if llm_area > 0:
            measurements.append(llm_area)
            sources_info['llm'] = {
                'area': llm_area,
                'name': llm_data.get('name', room_name)
            }

        # Calculate consensus
        if len(measurements) == 0:
            # No measurements available
            return {
                'name': room_name,
                'final_area_sqft': 0,
                'confidence': 'none',
                'needs_review': True,
                'sources': sources_info,
                'discrepancies': ['No measurements available'],
                'validation_score': 0.0
            }

        # Use median as final value (robust to outliers)
        final_area = float(np.median(measurements))

        # Calculate discrepancies
        discrepancies = []
        max_deviation = 0.0

        for area in measurements:
            deviation = abs(area - final_area) / final_area if final_area > 0 else 0
            max_deviation = max(max_deviation, deviation)

            if deviation > self.ACCEPTABLE_THRESHOLD:
                discrepancies.append(f"{area:.1f} sqft ({deviation*100:.1f}% difference)")

        # Determine confidence level
        confidence, validation_score = self._calculate_confidence(
            num_sources=len(measurements),
            max_deviation=max_deviation,
            measurements=measurements
        )

        # Flag for review if needed
        needs_review = (
            confidence in ['low', 'medium'] or
            max_deviation > self.ACCEPTABLE_THRESHOLD or
            len(measurements) < 2
        )

        return {
            'name': room_name,
            'final_area_sqft': round(final_area, 2),
            'confidence': confidence,
            'needs_review': needs_review,
            'sources': sources_info,
            'discrepancies': discrepancies,
            'validation_score': round(validation_score, 2),
            'max_deviation_percent': round(max_deviation * 100, 1),
            'num_sources': len(measurements),
            'measurement_range': {
                'min': round(min(measurements), 1),
                'max': round(max(measurements), 1),
                'median': round(final_area, 1)
            }
        }

    def _calculate_confidence(self,
                             num_sources: int,
                             max_deviation: float,
                             measurements: List[float]) -> Tuple[str, float]:
        """
        Calculate confidence level and validation score

        Returns:
            (confidence_level, validation_score)

        Confidence levels:
        - 'high': All sources agree within 5%, 3+ sources
        - 'medium': Sources agree within 10%, 2+ sources
        - 'low': Large discrepancies or single source
        """
        # Base score from number of sources
        if num_sources >= 3:
            base_score = 0.90
        elif num_sources == 2:
            base_score = 0.70
        else:
            base_score = 0.40

        # Adjust based on agreement
        if max_deviation <= self.PERFECT_MATCH_THRESHOLD:
            agreement_bonus = 0.10  # Perfect match
        elif max_deviation <= self.GOOD_MATCH_THRESHOLD:
            agreement_bonus = 0.05  # Good match
        elif max_deviation <= self.ACCEPTABLE_THRESHOLD:
            agreement_bonus = 0.0   # Acceptable
        else:
            agreement_bonus = -0.20  # Poor match

        validation_score = base_score + agreement_bonus
        validation_score = max(0.0, min(1.0, validation_score))  # Clamp to [0, 1]

        # Determine confidence level
        if validation_score >= 0.85:
            confidence = 'high'
        elif validation_score >= 0.60:
            confidence = 'medium'
        else:
            confidence = 'low'

        return confidence, validation_score

    def _find_matching_ocr_dimension(self,
                                    pixel_room: Dict,
                                    ocr_dimensions: List[Dict]) -> Optional[Dict]:
        """
        Find OCR dimension that matches pixel room location

        Looks for dimension text near room center
        """
        if not ocr_dimensions:
            return None

        room_center = self._get_room_center(pixel_room)
        if not room_center:
            return None

        # Find closest OCR dimension
        closest = None
        min_distance = float('inf')
        max_search_distance = 200  # pixels

        for ocr_dim in ocr_dimensions:
            if 'center' not in ocr_dim:
                continue

            ocr_center = ocr_dim['center']
            distance = np.sqrt(
                (ocr_center[0] - room_center[0])**2 +
                (ocr_center[1] - room_center[1])**2
            )

            if distance < min_distance and distance < max_search_distance:
                min_distance = distance
                closest = ocr_dim

        return closest

    def _find_matching_llm_room(self,
                               pixel_room: Dict,
                               llm_output: List[Dict]) -> Optional[Dict]:
        """
        Find LLM room that matches pixel room

        Matches by:
        1. Name similarity
        2. Area similarity
        """
        if not llm_output:
            return None

        pixel_name = pixel_room.get('name', '').lower()
        pixel_area = pixel_room.get('area_sqft', 0)

        best_match = None
        best_score = 0.0

        for llm_room in llm_output:
            llm_name = llm_room.get('name', '').lower()
            llm_area = llm_room.get('sqft', 0) or llm_room.get('area_sqft', 0)

            # Score based on name similarity
            name_score = 0.0
            if pixel_name in llm_name or llm_name in pixel_name:
                name_score = 0.5

            # Score based on area similarity
            area_score = 0.0
            if pixel_area > 0 and llm_area > 0:
                area_diff = abs(pixel_area - llm_area) / pixel_area
                if area_diff < 0.2:  # Within 20%
                    area_score = 0.5 * (1 - area_diff / 0.2)

            total_score = name_score + area_score

            if total_score > best_score:
                best_score = total_score
                best_match = llm_room

        return best_match if best_score > 0.3 else None

    def _get_room_center(self, room: Dict) -> Optional[Tuple[int, int]]:
        """Get center point of room from boundary points"""
        if 'boundary_points' not in room:
            return None

        points = room['boundary_points']
        if not points:
            return None

        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]

        center_x = int(np.mean(x_coords))
        center_y = int(np.mean(y_coords))

        return (center_x, center_y)

    def _generate_summary(self, validated_rooms: List[Dict]) -> Dict:
        """Generate summary statistics"""
        total_rooms = len(validated_rooms)

        if total_rooms == 0:
            return {
                'total_rooms': 0,
                'high_confidence': 0,
                'medium_confidence': 0,
                'low_confidence': 0,
                'needs_review': 0,
                'average_confidence': 0.0
            }

        high_confidence = sum(1 for r in validated_rooms if r['confidence'] == 'high')
        medium_confidence = sum(1 for r in validated_rooms if r['confidence'] == 'medium')
        low_confidence = sum(1 for r in validated_rooms if r['confidence'] == 'low')
        needs_review = sum(1 for r in validated_rooms if r['needs_review'])

        avg_score = np.mean([r['validation_score'] for r in validated_rooms])

        return {
            'total_rooms': total_rooms,
            'high_confidence': high_confidence,
            'medium_confidence': medium_confidence,
            'low_confidence': low_confidence,
            'needs_review': needs_review,
            'average_confidence': round(avg_score, 2),
            'percentage_high_confidence': round(high_confidence / total_rooms * 100, 1) if total_rooms > 0 else 0
        }


# Testing
if __name__ == '__main__':
    print("="*70)
    print("MEASUREMENT VALIDATOR TEST")
    print("="*70)

    validator = MeasurementValidator()

    # Test data: 3 rooms with measurements from different sources
    print("\n1. Perfect Match Example (All sources agree within 2%):")
    pixel_data = [
        {
            'name': 'Living Room',
            'area_sqft': 245.3,
            'perimeter_feet': 64.5,
            'dimensions': {'length_feet': 17.5, 'width_feet': 14.0}
        }
    ]

    ocr_data = [
        {
            'text': "14' x 17.5'",
            'value_feet': 14.0,
            'secondary_value_feet': 17.5,
            'area_sqft': 245.0,
            'center': (800, 600)
        }
    ]

    llm_data = [
        {
            'name': 'Living Room',
            'sqft': 243.0
        }
    ]

    result = validator.validate_room_measurements(pixel_data, ocr_data, llm_data)
    room = result['rooms'][0]

    print(f"   Final area: {room['final_area_sqft']} sqft")
    print(f"   Confidence: {room['confidence']} ({room['validation_score']})")
    print(f"   Needs review: {room['needs_review']}")
    print(f"   Max deviation: {room['max_deviation_percent']}%")
    print(f"   Sources: {room['num_sources']}")

    # Test 2: Discrepancy example
    print("\n2. Discrepancy Example (Sources disagree >10%):")
    pixel_data2 = [
        {
            'name': 'Kitchen',
            'area_sqft': 187.0,
            'perimeter_feet': 54.0
        }
    ]

    ocr_data2 = [
        {
            'text': "11'6\" x 15'",
            'value_feet': 11.5,
            'secondary_value_feet': 15.0,
            'area_sqft': 172.5,
            'center': (400, 300)
        }
    ]

    llm_data2 = [
        {
            'name': 'Kitchen',
            'sqft': 180.0
        }
    ]

    result2 = validator.validate_room_measurements(pixel_data2, ocr_data2, llm_data2)
    room2 = result2['rooms'][0]

    print(f"   Final area: {room2['final_area_sqft']} sqft")
    print(f"   Confidence: {room2['confidence']} ({room2['validation_score']})")
    print(f"   Needs review: {room2['needs_review']} ⚠️")
    print(f"   Max deviation: {room2['max_deviation_percent']}%")
    print(f"   Measurement range: {room2['measurement_range']['min']}-{room2['measurement_range']['max']} sqft")
    print(f"   Discrepancies: {room2['discrepancies']}")

    print("\n" + "="*70)
    print("✅ MEASUREMENT VALIDATOR TESTS COMPLETE")
    print("="*70 + "\n")
