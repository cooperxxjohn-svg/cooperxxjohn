"""
Precise Measurement Module
Pixel-perfect room measurement using computer vision
Integrates with TF2DeepFloorplan for semantic segmentation
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from shapely.geometry import Polygon
from shapely.ops import unary_union
import logging

logger = logging.getLogger(__name__)


class PreciseMeasurement:
    """
    Accurate room and wall measurements from floor plans

    Methods:
    - Measure room area from boundary polygon
    - Calculate room perimeter
    - Measure individual wall lengths
    - Detect room shape (rectangular, L-shaped, irregular)
    - Calculate wall-to-wall distances
    """

    def __init__(self):
        self.scale_info = None

    def set_scale(self, scale_info: Dict):
        """
        Set scale calibration for measurements

        Args:
            scale_info: Output from ScaleDetector.detect_scale_auto()
        """
        self.scale_info = scale_info
        logger.info(f"Scale set: {scale_info['pixels_per_foot']:.2f} pixels/foot")

    def measure_room_from_polygon(self, boundary_points: List[Tuple[int, int]],
                                  room_name: str = "Room") -> Dict:
        """
        Measure room area and perimeter from boundary polygon

        Args:
            boundary_points: List of (x, y) pixel coordinates defining room boundary
            room_name: Name of room

        Returns:
            {
                'name': 'Living Room',
                'boundary_points': [(x1,y1), (x2,y2), ...],
                'area_pixels': 245000,
                'area_sqft': 245.3,
                'area_sqm': 22.8,
                'perimeter_pixels': 2400,
                'perimeter_feet': 64.5,
                'perimeter_meters': 19.7,
                'shape': 'rectangular',  # or 'L-shaped', 'irregular'
                'dimensions': {
                    'length_feet': 17.5,
                    'width_feet': 14.0
                }
            }
        """
        if not self.scale_info:
            logger.error("Scale not set! Call set_scale() first.")
            return {}

        # Convert to numpy array
        if isinstance(boundary_points[0], (list, tuple)):
            points = np.array(boundary_points, dtype=np.float32)
        else:
            points = boundary_points

        # Create shapely polygon for accurate measurements
        try:
            poly = Polygon(points)

            # Calculate area (pixels)
            area_pixels = poly.area

            # Calculate perimeter (pixels)
            perimeter_pixels = poly.length

            # Convert to real-world units
            pixels_per_foot = self.scale_info['pixels_per_foot']
            pixels_per_meter = self.scale_info['pixels_per_meter']

            area_sqft = area_pixels / (pixels_per_foot ** 2)
            area_sqm = area_pixels / (pixels_per_meter ** 2)

            perimeter_feet = perimeter_pixels / pixels_per_foot
            perimeter_meters = perimeter_pixels / pixels_per_meter

            # Detect shape and get dimensions
            shape_type, dimensions = self._analyze_room_shape(points, pixels_per_foot)

            result = {
                'name': room_name,
                'boundary_points': boundary_points,
                'area_pixels': float(area_pixels),
                'area_sqft': round(area_sqft, 2),
                'area_sqm': round(area_sqm, 2),
                'perimeter_pixels': float(perimeter_pixels),
                'perimeter_feet': round(perimeter_feet, 2),
                'perimeter_meters': round(perimeter_meters, 2),
                'shape': shape_type,
                'dimensions': dimensions,
                'scale_used': {
                    'pixels_per_foot': pixels_per_foot,
                    'scale_text': self.scale_info['scale_text']
                }
            }

            logger.info(f"Measured {room_name}: {area_sqft:.1f} sqft ({shape_type})")
            return result

        except Exception as e:
            logger.error(f"Failed to measure room: {e}")
            return {}

    def _analyze_room_shape(self, points: np.ndarray, pixels_per_foot: float) -> Tuple[str, Dict]:
        """
        Analyze room shape and extract dimensions

        Returns:
            (shape_type, dimensions)

        Shape types:
        - 'rectangular': 4 corners, 90-degree angles
        - 'L-shaped': 6 corners, forms L
        - 'irregular': Complex shape
        """
        num_points = len(points)

        # Simplify polygon to reduce noise
        epsilon = 0.02 * cv2.arcLength(points.astype(np.float32), True)
        approx = cv2.approxPolyDP(points.astype(np.float32), epsilon, True)
        num_corners = len(approx)

        dimensions = {}

        if num_corners == 4:
            # Rectangular room
            # Find length and width from bounding box
            x_coords = points[:, 0]
            y_coords = points[:, 1]

            width_pixels = np.max(x_coords) - np.min(x_coords)
            height_pixels = np.max(y_coords) - np.min(y_coords)

            width_feet = width_pixels / pixels_per_foot
            height_feet = height_pixels / pixels_per_foot

            # Longer dimension = length, shorter = width
            if width_feet > height_feet:
                length_feet = width_feet
                width_feet = height_feet
            else:
                length_feet = height_feet

            dimensions = {
                'length_feet': round(length_feet, 1),
                'width_feet': round(width_feet, 1),
                'is_square': abs(length_feet - width_feet) < 1.0  # Within 1 foot
            }

            return 'rectangular', dimensions

        elif num_corners == 6:
            # Possibly L-shaped
            return 'L-shaped', {}

        else:
            # Irregular shape
            return 'irregular', {}

    def measure_wall_length(self, point1: Tuple[int, int], point2: Tuple[int, int]) -> Dict:
        """
        Measure length of a single wall between two points

        Args:
            point1: (x1, y1) start point
            point2: (x2, y2) end point

        Returns:
            {
                'length_pixels': 1500.0,
                'length_feet': 20.0,
                'length_meters': 6.1,
                'angle_degrees': 90.0
            }
        """
        if not self.scale_info:
            logger.error("Scale not set!")
            return {}

        x1, y1 = point1
        x2, y2 = point2

        # Calculate pixel distance
        length_pixels = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

        # Calculate angle (0 = horizontal, 90 = vertical)
        angle_radians = np.arctan2(y2 - y1, x2 - x1)
        angle_degrees = np.degrees(angle_radians)

        # Convert to real-world units
        pixels_per_foot = self.scale_info['pixels_per_foot']
        pixels_per_meter = self.scale_info['pixels_per_meter']

        length_feet = length_pixels / pixels_per_foot
        length_meters = length_pixels / pixels_per_meter

        return {
            'length_pixels': float(length_pixels),
            'length_feet': round(length_feet, 2),
            'length_meters': round(length_meters, 2),
            'length_inches': round(length_feet * 12, 1),
            'angle_degrees': round(angle_degrees, 1),
            'start_point': point1,
            'end_point': point2
        }

    def calculate_perimeter_for_trim(self, boundary_points: List[Tuple[int, int]],
                                     door_openings: List[Dict] = None,
                                     window_openings: List[Dict] = None) -> Dict:
        """
        Calculate linear feet of trim needed (baseboard, crown molding)

        Subtracts door and window openings from perimeter

        Args:
            boundary_points: Room boundary polygon
            door_openings: List of {width_feet, location}
            window_openings: List of {width_feet, location}

        Returns:
            {
                'total_perimeter_feet': 64.5,
                'door_openings_feet': 6.0,  # 2 doors @ 3' each
                'window_openings_feet': 4.0,
                'trim_needed_feet': 54.5,
                'trim_needed_with_waste': 57.2  # +5% waste
            }
        """
        # Measure room perimeter
        room = self.measure_room_from_polygon(boundary_points)
        total_perimeter = room['perimeter_feet']

        # Sum door openings
        door_total = 0.0
        if door_openings:
            for door in door_openings:
                door_total += door.get('width_feet', 3.0)  # Default 3' door

        # Sum window openings
        window_total = 0.0
        if window_openings:
            for window in window_openings:
                window_total += window.get('width_feet', 4.0)  # Default 4' window

        # Calculate trim needed
        trim_needed = total_perimeter - door_total - window_total

        # Add waste factor (5%)
        trim_with_waste = trim_needed * 1.05

        return {
            'total_perimeter_feet': round(total_perimeter, 2),
            'door_openings_feet': round(door_total, 2),
            'window_openings_feet': round(window_total, 2),
            'trim_needed_feet': round(trim_needed, 2),
            'trim_needed_with_waste': round(trim_with_waste, 2),
            'waste_factor': 0.05
        }

    def measure_wall_segments(self, boundary_points: List[Tuple[int, int]]) -> List[Dict]:
        """
        Break room perimeter into individual wall segments

        Useful for:
        - Measuring each wall separately
        - Identifying exterior vs interior walls
        - Calculating materials per wall

        Returns:
            List of wall segments with lengths
        """
        walls = []

        for i in range(len(boundary_points)):
            # Get current point and next point (wrap around)
            p1 = boundary_points[i]
            p2 = boundary_points[(i + 1) % len(boundary_points)]

            # Measure wall
            wall = self.measure_wall_length(p1, p2)
            wall['wall_number'] = i + 1
            walls.append(wall)

        logger.info(f"Measured {len(walls)} wall segments")
        return walls

    def detect_room_boundaries_simple(self, image: np.ndarray, min_area: int = 1000) -> List[Dict]:
        """
        Simple room detection using contour detection
        (Fallback when TF2DeepFloorplan not available)

        Args:
            image: Floor plan image (numpy array)
            min_area: Minimum room area in pixels

        Returns:
            List of detected rooms with boundaries
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Threshold to get binary image
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        rooms = []
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)

            # Filter by minimum area
            if area < min_area:
                continue

            # Simplify contour
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Convert to list of points
            points = [(int(pt[0][0]), int(pt[0][1])) for pt in approx]

            # Measure room
            room = self.measure_room_from_polygon(points, f"Room {i+1}")
            room['contour_index'] = i
            rooms.append(room)

        logger.info(f"Detected {len(rooms)} rooms using simple contour detection")
        return rooms


# Testing
if __name__ == '__main__':
    print("="*70)
    print("PRECISE MEASUREMENT TEST")
    print("="*70)

    # Create measurement instance
    measurer = PreciseMeasurement()

    # Set scale (1/4" = 1'-0" at 300 DPI)
    scale_info = {
        'scale_text': '1/4" = 1\'-0"',
        'pixels_per_foot': 75.0,
        'pixels_per_meter': 246.06,
        'scale_type': 'architectural',
        'confidence': 0.85
    }
    measurer.set_scale(scale_info)

    # Test 1: Rectangular room
    print("\n1. Rectangular Room (20' x 15'):")
    # 20 feet = 1500 pixels, 15 feet = 1125 pixels
    boundary = [
        (100, 100),      # Top-left
        (1600, 100),     # Top-right (1500 pixels wide = 20 feet)
        (1600, 1225),    # Bottom-right (1125 pixels tall = 15 feet)
        (100, 1225)      # Bottom-left
    ]

    room = measurer.measure_room_from_polygon(boundary, "Living Room")
    print(f"   Area: {room['area_sqft']:.1f} sqft")
    print(f"   Perimeter: {room['perimeter_feet']:.1f} feet")
    print(f"   Shape: {room['shape']}")
    print(f"   Dimensions: {room['dimensions']['length_feet']:.1f}' x {room['dimensions']['width_feet']:.1f}'")

    # Test 2: Wall measurement
    print("\n2. Single Wall Measurement:")
    wall = measurer.measure_wall_length((100, 100), (1600, 100))
    print(f"   Length: {wall['length_feet']:.1f} feet ({wall['length_inches']:.0f} inches)")
    print(f"   Angle: {wall['angle_degrees']:.1f}°")

    # Test 3: Trim calculation
    print("\n3. Trim Calculation (with 2 doors, 1 window):")
    doors = [
        {'width_feet': 3.0},
        {'width_feet': 3.0}
    ]
    windows = [
        {'width_feet': 4.0}
    ]

    trim = measurer.calculate_perimeter_for_trim(boundary, doors, windows)
    print(f"   Total perimeter: {trim['total_perimeter_feet']:.1f} feet")
    print(f"   Door openings: -{trim['door_openings_feet']:.1f} feet")
    print(f"   Window openings: -{trim['window_openings_feet']:.1f} feet")
    print(f"   Trim needed: {trim['trim_needed_feet']:.1f} feet")
    print(f"   With 5% waste: {trim['trim_needed_with_waste']:.1f} feet")

    # Test 4: Wall segments
    print("\n4. Individual Wall Segments:")
    walls = measurer.measure_wall_segments(boundary)
    for wall in walls:
        print(f"   Wall {wall['wall_number']}: {wall['length_feet']:.1f} feet at {wall['angle_degrees']:.0f}°")

    print("\n" + "="*70)
    print("✅ PRECISE MEASUREMENT TESTS COMPLETE")
    print("="*70 + "\n")
