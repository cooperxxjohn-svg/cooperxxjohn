"""
Painting Detection Engine
Detects rooms, walls, ceilings, and paintable surfaces from architectural drawings
"""

import anthropic
import base64
import json
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from PIL import Image
import io


@dataclass
class Surface:
    """Represents a paintable surface"""
    type: str  # wall, ceiling, trim, door, window
    area: float  # square feet
    linear_feet: Optional[float] = None  # for trim
    height: Optional[float] = None
    deductions: float = 0.0  # sqft to subtract (windows, doors)


@dataclass
class Room:
    """Represents a room with all paintable surfaces"""
    id: str
    name: str
    number: Optional[str] = None
    floor: Optional[int] = None
    dimensions: Dict[str, float] = None  # length, width, height
    surfaces: Dict[str, Surface] = None
    total_area: float = 0.0

    def __post_init__(self):
        if self.dimensions is None:
            self.dimensions = {}
        if self.surfaces is None:
            self.surfaces = {}


@dataclass
class PaintingDetection:
    """Complete detection results for a drawing"""
    rooms: List[Room]
    total_rooms: int
    total_paintable_area: float
    drawing_type: str  # floor_plan, elevation, section
    scale: Optional[str] = None


class PaintingDetector:
    """
    AI-powered painting takeoff detector
    Analyzes architectural drawings and extracts room dimensions and paintable surfaces
    """

    def __init__(self, anthropic_api_key: str):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"

    def analyze_drawing(self, image_path: str) -> PaintingDetection:
        """
        Main entry point: analyze a drawing and return all detected rooms/surfaces
        """
        # Read and encode image
        image_data = self._encode_image(image_path)

        # Step 1: Classify drawing type
        drawing_type = self._classify_drawing(image_data)

        # Step 2: Extract rooms and dimensions
        if drawing_type == "floor_plan":
            rooms = self._extract_rooms_from_floor_plan(image_data)
        elif drawing_type == "elevation":
            rooms = self._extract_from_elevation(image_data)
        else:
            rooms = []

        # Step 3: Calculate paintable surfaces for each room
        for room in rooms:
            self._calculate_surfaces(room)

        # Calculate totals
        total_area = sum(room.total_area for room in rooms)

        return PaintingDetection(
            rooms=rooms,
            total_rooms=len(rooms),
            total_paintable_area=total_area,
            drawing_type=drawing_type
        )

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        return base64.standard_b64encode(image_bytes).decode("utf-8")

    def _classify_drawing(self, image_data: str) -> str:
        """Classify what type of drawing this is"""
        prompt = """Analyze this architectural drawing and classify it:

Return a JSON object with:
{
  "type": "floor_plan" | "elevation" | "section" | "detail" | "site_plan" | "unknown",
  "scale": "1/4\" = 1'-0\"" or similar if visible,
  "contains_rooms": true/false
}

Focus on:
- Floor plans show rooms from above (walls, doors, windows)
- Elevations show vertical views (exterior or interior walls)
- Sections show cut-through views
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            }]
        )

        result = json.loads(response.content[0].text)
        return result.get("type", "unknown")

    def _extract_rooms_from_floor_plan(self, image_data: str) -> List[Room]:
        """Extract all rooms from a floor plan"""
        prompt = """Analyze this floor plan and extract ALL rooms with their dimensions.

For EACH room, identify:
1. Room name/label (e.g., "Living Room", "Bedroom 1", "Office")
2. Room number if labeled (e.g., "101", "205")
3. Dimensions: length, width, ceiling height (if noted)
4. Number of doors (for deductions)
5. Number of windows with approximate sizes (for deductions)
6. Any special features (vaulted ceilings, built-ins, etc.)

Return a JSON array of rooms:
[
  {
    "id": "room_1",
    "name": "Living Room",
    "number": "101",
    "dimensions": {
      "length": 20.0,
      "width": 15.0,
      "height": 9.0
    },
    "doors": [
      {"width": 3.0, "height": 7.0}
    ],
    "windows": [
      {"width": 3.0, "height": 5.0},
      {"width": 3.0, "height": 5.0}
    ],
    "notes": "Cathedral ceiling"
  }
]

IMPORTANT:
- All dimensions in FEET (convert if needed)
- If ceiling height not shown, assume 9.0 feet for residential, 10.0 for commercial
- Standard door = 3' × 7'
- Standard window = 3' × 5'
- Be thorough - extract EVERY room you can identify
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            }]
        )

        # Parse response
        rooms_data = json.loads(response.content[0].text)

        # Convert to Room objects
        rooms = []
        for data in rooms_data:
            room = Room(
                id=data["id"],
                name=data["name"],
                number=data.get("number"),
                dimensions=data.get("dimensions", {}),
                surfaces={}
            )

            # Store door/window info for deductions
            room.doors = data.get("doors", [])
            room.windows = data.get("windows", [])
            room.notes = data.get("notes", "")

            rooms.append(room)

        return rooms

    def _extract_from_elevation(self, image_data: str) -> List[Room]:
        """Extract wall information from elevation drawings"""
        prompt = """Analyze this elevation drawing and extract wall dimensions.

Return JSON:
{
  "walls": [
    {
      "id": "wall_1",
      "length": 40.0,
      "height": 10.0,
      "windows": [{"width": 4.0, "height": 6.0}],
      "doors": [{"width": 3.0, "height": 7.0}]
    }
  ]
}

All dimensions in FEET.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            }]
        )

        data = json.loads(response.content[0].text)

        # Convert walls to "rooms" (each wall is a room for elevation)
        rooms = []
        for i, wall in enumerate(data.get("walls", [])):
            room = Room(
                id=f"wall_{i+1}",
                name=f"Wall {i+1}",
                dimensions={
                    "length": wall["length"],
                    "height": wall["height"]
                },
                surfaces={}
            )
            room.windows = wall.get("windows", [])
            room.doors = wall.get("doors", [])
            rooms.append(room)

        return rooms

    def _calculate_surfaces(self, room: Room):
        """Calculate all paintable surfaces for a room"""
        dims = room.dimensions

        if not dims:
            return

        # Get dimensions
        length = dims.get("length", 0)
        width = dims.get("width", 0)
        height = dims.get("height", 9.0)  # Default ceiling height

        # Calculate perimeter for walls
        if length and width:
            perimeter = 2 * (length + width)
        else:
            # If only length/height (elevation view)
            perimeter = length if length else 0
            width = 0

        # WALLS
        wall_area = perimeter * height

        # Deductions for doors and windows
        door_deductions = sum(
            d.get("width", 3) * d.get("height", 7)
            for d in getattr(room, "doors", [])
        )
        window_deductions = sum(
            w.get("width", 3) * w.get("height", 5)
            for w in getattr(room, "windows", [])
        )

        total_deductions = door_deductions + window_deductions
        net_wall_area = max(0, wall_area - total_deductions)

        room.surfaces["walls"] = Surface(
            type="wall",
            area=net_wall_area,
            height=height,
            deductions=total_deductions
        )

        # CEILING (only if we have length and width)
        if length and width:
            ceiling_area = length * width
            room.surfaces["ceiling"] = Surface(
                type="ceiling",
                area=ceiling_area
            )

        # TRIM/BASEBOARD
        if perimeter:
            # Subtract door widths from trim length
            door_widths = sum(d.get("width", 3) for d in getattr(room, "doors", []))
            trim_linear = max(0, perimeter - door_widths)
            trim_height = 0.5  # 6 inches standard baseboard
            trim_area = trim_linear * trim_height

            room.surfaces["trim"] = Surface(
                type="trim",
                area=trim_area,
                linear_feet=trim_linear,
                height=trim_height
            )

        # DOORS (paint both sides)
        door_area = sum(
            d.get("width", 3) * d.get("height", 7) * 2  # Both sides
            for d in getattr(room, "doors", [])
        )
        if door_area > 0:
            room.surfaces["doors"] = Surface(
                type="door",
                area=door_area
            )

        # Calculate total paintable area for room
        room.total_area = sum(s.area for s in room.surfaces.values())


class PaintCalculator:
    """Calculate paint requirements from detected surfaces"""

    # Coverage rates (sqft per gallon)
    COVERAGE_RATES = {
        "smooth_drywall": 400,
        "textured_drywall": 350,
        "smooth_plaster": 400,
        "rough_plaster": 325,
        "wood": 350,
        "metal": 500,
        "concrete": 300,
        "default": 400
    }

    # Production rates (sqft per hour)
    PRODUCTION_RATES = {
        "wall": 300,
        "ceiling": 350,
        "trim": 200,
        "door": 30
    }

    def __init__(self, surface_type: str = "smooth_drywall"):
        self.surface_type = surface_type
        self.coverage_rate = self.COVERAGE_RATES.get(surface_type, 400)

    def calculate_paint(self, surface: Surface, num_coats: int = 2,
                       waste_factor: float = 1.10) -> Dict:
        """Calculate paint needed for a surface"""
        total_area = surface.area * num_coats
        gallons_needed = (total_area / self.coverage_rate) * waste_factor
        gallons_rounded = max(1, round(gallons_needed))

        return {
            "surface_area": surface.area,
            "num_coats": num_coats,
            "gallons_calculated": gallons_needed,
            "gallons_to_buy": gallons_rounded,
            "coverage_rate": self.coverage_rate
        }

    def calculate_labor(self, surface: Surface, num_coats: int = 2) -> Dict:
        """Calculate labor hours for a surface"""
        production_rate = self.PRODUCTION_RATES.get(surface.type, 300)

        base_hours = (surface.area / production_rate) * num_coats
        prep_hours = base_hours * 0.15  # 15% prep time
        touch_up_hours = base_hours * 0.05  # 5% touch-up time

        total_hours = base_hours + prep_hours + touch_up_hours

        return {
            "base_hours": base_hours,
            "prep_hours": prep_hours,
            "touch_up_hours": touch_up_hours,
            "total_hours": total_hours,
            "production_rate": production_rate
        }

    def calculate_room_estimate(self, room: Room, paint_price: float = 55.0,
                               labor_rate: float = 50.0) -> Dict:
        """Calculate complete estimate for a room"""
        estimate = {
            "room_id": room.id,
            "room_name": room.name,
            "surfaces": {},
            "totals": {
                "paint_gallons": 0,
                "labor_hours": 0,
                "material_cost": 0,
                "labor_cost": 0,
                "total_cost": 0
            }
        }

        for surface_name, surface in room.surfaces.items():
            # Determine coats based on surface type
            if surface.type == "trim" or surface.type == "door":
                finish_coats = 2
                primer_coats = 1
            elif surface.type == "ceiling":
                finish_coats = 2
                primer_coats = 1
            else:  # walls
                finish_coats = 2
                primer_coats = 1

            # Calculate primer
            primer = self.calculate_paint(surface, num_coats=primer_coats)
            primer_labor = self.calculate_labor(surface, num_coats=primer_coats)

            # Calculate finish paint
            finish = self.calculate_paint(surface, num_coats=finish_coats)
            finish_labor = self.calculate_labor(surface, num_coats=finish_coats)

            # Material costs
            primer_cost = primer["gallons_to_buy"] * (paint_price * 0.75)  # Primer cheaper
            finish_cost = finish["gallons_to_buy"] * paint_price

            # Labor costs
            labor_hours = primer_labor["total_hours"] + finish_labor["total_hours"]
            labor_cost = labor_hours * labor_rate

            surface_estimate = {
                "primer": primer,
                "finish": finish,
                "labor": {
                    "hours": labor_hours,
                    "cost": labor_cost
                },
                "costs": {
                    "primer": primer_cost,
                    "finish": finish_cost,
                    "labor": labor_cost,
                    "total": primer_cost + finish_cost + labor_cost
                }
            }

            estimate["surfaces"][surface_name] = surface_estimate

            # Add to totals
            estimate["totals"]["paint_gallons"] += (
                primer["gallons_to_buy"] + finish["gallons_to_buy"]
            )
            estimate["totals"]["labor_hours"] += labor_hours
            estimate["totals"]["material_cost"] += primer_cost + finish_cost
            estimate["totals"]["labor_cost"] += labor_cost

        # Add sundries (5% of material cost or $0.095/sqft)
        sundries = max(
            estimate["totals"]["material_cost"] * 0.05,
            room.total_area * 0.095
        )
        estimate["totals"]["material_cost"] += sundries

        # Calculate total
        estimate["totals"]["total_cost"] = (
            estimate["totals"]["material_cost"] +
            estimate["totals"]["labor_cost"]
        )

        return estimate


if __name__ == "__main__":
    # Test the detector
    import os

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        exit(1)

    detector = PaintingDetector(api_key)
    calculator = PaintCalculator()

    # Test with a sample drawing (user will provide)
    print("Painting.ai Detection Engine Ready")
    print("Usage: detector.analyze_drawing('path/to/drawing.pdf')")
