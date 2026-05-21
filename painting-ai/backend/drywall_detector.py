"""
Drywall Detection Engine
Detects walls, corners, openings, and ceilings from architectural drawings
Uses Claude Sonnet 4 API for AI-powered takeoff extraction
"""

import anthropic
import base64
import json
import re
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from PIL import Image
import io


@dataclass
class Opening:
    """Represents a door or window opening"""
    type: str  # door, window, sliding_door, french_door
    width: float  # feet
    height: float  # feet
    square_footage: float
    quantity: int = 1


@dataclass
class Corner:
    """Represents corners in a wall section"""
    inside_corners: int = 0
    outside_corners: int = 0


@dataclass
class Wall:
    """Represents a wall with all drywall information"""
    wall_id: str
    type: str  # interior, exterior, partition
    length_ft: float
    height_ft: float
    square_footage: float
    openings: List[Opening]
    corners: Corner
    special_features: List[str]  # soffits, bulkheads, columns, etc.

    def __post_init__(self):
        if not isinstance(self.openings, list):
            self.openings = []
        if not isinstance(self.corners, Corner):
            self.corners = Corner()
        if not isinstance(self.special_features, list):
            self.special_features = []


@dataclass
class Ceiling:
    """Represents a ceiling section"""
    room: str
    type: str  # flat, vaulted, tray, coffered, cathedral, sloped
    square_footage: float
    height_ft: float
    special_notes: Optional[str] = None


@dataclass
class DrywallDetection:
    """Complete detection results for a drawing"""
    walls: List[Wall]
    ceilings: List[Ceiling]
    summary: Dict[str, float]
    drawing_type: str  # floor_plan, reflected_ceiling, elevation, section, detail
    scale: Optional[str] = None
    notes: List[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []


class DrywallDetector:
    """
    AI-powered drywall takeoff detector
    Analyzes architectural drawings and extracts wall dimensions, openings, corners, and ceilings
    """

    def __init__(self, anthropic_api_key: str):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"

    def analyze_drawing(self, image_path: str) -> DrywallDetection:
        """
        Main entry point: analyze a drawing and return all detected walls/ceilings
        """
        # Read and encode image
        image_data = self._encode_image(image_path)

        # Step 1: Classify drawing type
        drawing_info = self._classify_drawing(image_data)
        drawing_type = drawing_info.get("type", "unknown")

        # Step 2: Extract walls and ceilings based on drawing type
        if drawing_type == "floor_plan":
            walls, ceilings = self._extract_from_floor_plan(image_data)
        elif drawing_type == "reflected_ceiling":
            walls, ceilings = self._extract_from_rcp(image_data)
        elif drawing_type == "elevation":
            walls, ceilings = self._extract_from_elevation(image_data)
        elif drawing_type == "section":
            walls, ceilings = self._extract_from_section(image_data)
        else:
            walls, ceilings = [], []

        # Step 3: Calculate summary statistics
        summary = self._calculate_summary(walls, ceilings)

        # Step 4: Validate results
        validation_notes = self._validate_detection(walls, ceilings, summary)

        return DrywallDetection(
            walls=walls,
            ceilings=ceilings,
            summary=summary,
            drawing_type=drawing_type,
            scale=drawing_info.get("scale"),
            notes=validation_notes
        )

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        return base64.standard_b64encode(image_bytes).decode("utf-8")

    def _classify_drawing(self, image_data: str) -> Dict:
        """Classify what type of drawing this is"""
        prompt = """Analyze this architectural drawing and classify it for drywall takeoff.

Return a JSON object with:
{
  "type": "floor_plan" | "reflected_ceiling" | "elevation" | "section" | "detail" | "unknown",
  "scale": "1/4\\" = 1'-0\\"" or similar if visible,
  "building_type": "residential" | "commercial" | "industrial",
  "notes": "Any relevant observations"
}

Focus on:
- Floor plans: Show rooms from above (walls, doors, windows) - PRIMARY for drywall takeoff
- Reflected ceiling plans (RCP): Show ceiling layout from above
- Elevations: Show vertical wall views (exterior or interior)
- Sections: Show cut-through views with wall assemblies
- Details: Close-up construction details
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

        return json.loads(response.content[0].text)

    def _extract_from_floor_plan(self, image_data: str) -> Tuple[List[Wall], List[Ceiling]]:
        """Extract walls and ceilings from a floor plan - PRIMARY method"""
        prompt = """Analyze this floor plan for drywall takeoff. Extract ALL walls with precise measurements.

For EACH WALL, identify:
1. Wall ID (W1, W2, W3, etc.)
2. Wall type:
   - "exterior": Outer building perimeter (typically 2x6 or 2x4 + insulation)
   - "interior": Load-bearing or standard partition walls (typically 2x4)
   - "partition": Non-load bearing walls, room dividers
3. Wall dimensions:
   - Length in FEET (measure center-to-center or face-to-face as labeled)
   - Height in FEET (if shown; otherwise assume 8' residential, 9-10' commercial)
4. Openings (doors and windows):
   - Type: door, window, sliding_door, french_door, double_door
   - Width and height in FEET
   - Calculate square footage for each
5. Corners:
   - Inside corners: Where two walls meet at 90° inside
   - Outside corners: Where two walls meet at 90° outside (needs corner bead)
6. Special features:
   - Soffits, bulkheads, columns, chases, niches, etc.

For EACH CEILING/ROOM:
1. Room name
2. Ceiling type: flat, vaulted, tray, coffered, cathedral, sloped
3. Square footage (length × width)
4. Height in FEET (if indicated)

IMPORTANT - Drywall Takeoff Standards:
- All dimensions in FEET (decimal format, e.g., 12.5 not 12'-6")
- Count corners carefully (critical for corner bead material)
- Note wall thickness if visible (affects material calculations)
- Standard door = 3.0' × 6.67' (3' × 6'8") = 20 sqft
- Standard window = 3.0' × 4.0' = 12 sqft
- Deduct openings from wall square footage
- Perimeter walls = total linear feet for base trim

Return JSON in this EXACT format:
{
  "walls": [
    {
      "wall_id": "W1",
      "type": "exterior",
      "length_ft": 24.5,
      "height_ft": 8.0,
      "square_footage": 196,
      "openings": [
        {
          "type": "door",
          "width": 3.0,
          "height": 6.67,
          "square_footage": 20,
          "quantity": 1
        },
        {
          "type": "window",
          "width": 4.0,
          "height": 3.0,
          "square_footage": 12,
          "quantity": 2
        }
      ],
      "corners": {
        "inside_corners": 0,
        "outside_corners": 2
      },
      "special_features": []
    }
  ],
  "ceilings": [
    {
      "room": "Living Room",
      "type": "flat",
      "square_footage": 300,
      "height_ft": 8.0,
      "special_notes": null
    }
  ]
}

Be thorough - extract EVERY wall segment you can identify. If walls form a rectangle, you should have 4 wall entries.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
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

        # Convert to Wall and Ceiling objects
        walls = self._parse_walls(data.get("walls", []))
        ceilings = self._parse_ceilings(data.get("ceilings", []))

        return walls, ceilings

    def _extract_from_rcp(self, image_data: str) -> Tuple[List[Wall], List[Ceiling]]:
        """Extract ceiling information from reflected ceiling plan"""
        prompt = """Analyze this reflected ceiling plan (RCP) for drywall takeoff.

Extract ceiling information:
1. Each ceiling area/room
2. Ceiling type (flat, tray, coffered, etc.)
3. Square footage
4. Ceiling height if noted
5. Special features (drop ceilings, soffits, light coves)

Return JSON:
{
  "ceilings": [
    {
      "room": "Conference Room A",
      "type": "flat",
      "square_footage": 450,
      "height_ft": 9.0,
      "special_notes": "2x2 ACT grid, not drywall"
    }
  ],
  "walls": []
}

Note: RCPs typically don't show wall details, but may show soffits/bulkheads.
All dimensions in FEET.
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

        data = json.loads(response.content[0].text)
        walls = self._parse_walls(data.get("walls", []))
        ceilings = self._parse_ceilings(data.get("ceilings", []))

        return walls, ceilings

    def _extract_from_elevation(self, image_data: str) -> Tuple[List[Wall], List[Ceiling]]:
        """Extract wall information from elevation drawings"""
        prompt = """Analyze this elevation drawing for drywall takeoff.

Extract wall dimensions:
1. Wall length (horizontal dimension)
2. Wall height (vertical dimension)
3. All openings (doors, windows) with dimensions
4. Corner conditions (inside/outside)
5. Special features (wainscoting, chair rails, etc.)

Return JSON:
{
  "walls": [
    {
      "wall_id": "E1",
      "type": "interior",
      "length_ft": 40.0,
      "height_ft": 10.0,
      "square_footage": 400,
      "openings": [
        {
          "type": "window",
          "width": 4.0,
          "height": 6.0,
          "square_footage": 24,
          "quantity": 3
        }
      ],
      "corners": {
        "inside_corners": 0,
        "outside_corners": 0
      },
      "special_features": ["chair rail at 36\\""]
    }
  ],
  "ceilings": []
}

All dimensions in FEET. Calculate net wall area after deducting openings.
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

        data = json.loads(response.content[0].text)
        walls = self._parse_walls(data.get("walls", []))
        ceilings = []  # Elevations don't show ceilings

        return walls, ceilings

    def _extract_from_section(self, image_data: str) -> Tuple[List[Wall], List[Ceiling]]:
        """Extract information from section drawings"""
        prompt = """Analyze this section drawing for drywall takeoff.

Sections show cut-through views. Extract:
1. Wall heights at different levels
2. Ceiling configurations
3. Soffits, bulkheads, dropped ceilings
4. Special wall assemblies

Return JSON with walls and/or ceilings as applicable:
{
  "walls": [...],
  "ceilings": [...]
}

All dimensions in FEET. Focus on drywall-applicable areas.
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

        data = json.loads(response.content[0].text)
        walls = self._parse_walls(data.get("walls", []))
        ceilings = self._parse_ceilings(data.get("ceilings", []))

        return walls, ceilings

    def _parse_walls(self, walls_data: List[Dict]) -> List[Wall]:
        """Convert raw wall data to Wall objects"""
        walls = []
        for data in walls_data:
            # Parse openings
            openings = []
            for opening_data in data.get("openings", []):
                opening = Opening(
                    type=opening_data["type"],
                    width=opening_data["width"],
                    height=opening_data["height"],
                    square_footage=opening_data["square_footage"],
                    quantity=opening_data.get("quantity", 1)
                )
                openings.append(opening)

            # Parse corners
            corner_data = data.get("corners", {})
            corners = Corner(
                inside_corners=corner_data.get("inside_corners", 0),
                outside_corners=corner_data.get("outside_corners", 0)
            )

            # Create wall
            wall = Wall(
                wall_id=data["wall_id"],
                type=data["type"],
                length_ft=data["length_ft"],
                height_ft=data["height_ft"],
                square_footage=data["square_footage"],
                openings=openings,
                corners=corners,
                special_features=data.get("special_features", [])
            )
            walls.append(wall)

        return walls

    def _parse_ceilings(self, ceilings_data: List[Dict]) -> List[Ceiling]:
        """Convert raw ceiling data to Ceiling objects"""
        ceilings = []
        for data in ceilings_data:
            ceiling = Ceiling(
                room=data["room"],
                type=data["type"],
                square_footage=data["square_footage"],
                height_ft=data["height_ft"],
                special_notes=data.get("special_notes")
            )
            ceilings.append(ceiling)

        return ceilings

    def _calculate_summary(self, walls: List[Wall], ceilings: List[Ceiling]) -> Dict[str, float]:
        """Calculate summary statistics for the entire drawing"""
        # Wall totals
        total_wall_sqft = sum(wall.square_footage for wall in walls)
        total_linear_ft = sum(wall.length_ft for wall in walls)

        # Opening totals
        total_openings = 0
        total_opening_sqft = 0
        for wall in walls:
            for opening in wall.openings:
                total_openings += opening.quantity
                total_opening_sqft += opening.square_footage * opening.quantity

        # Calculate net wall area (gross - openings)
        net_wall_sqft = total_wall_sqft - total_opening_sqft

        # Corner totals
        total_inside_corners = sum(wall.corners.inside_corners for wall in walls)
        total_outside_corners = sum(wall.corners.outside_corners for wall in walls)
        total_corners = total_inside_corners + total_outside_corners

        # Ceiling totals
        total_ceiling_sqft = sum(ceiling.square_footage for ceiling in ceilings)

        # Combined totals
        total_drywall_sqft = net_wall_sqft + total_ceiling_sqft

        return {
            "total_wall_sqft_gross": round(total_wall_sqft, 2),
            "total_wall_sqft_net": round(net_wall_sqft, 2),
            "total_ceiling_sqft": round(total_ceiling_sqft, 2),
            "total_drywall_sqft": round(total_drywall_sqft, 2),
            "total_linear_ft": round(total_linear_ft, 2),
            "total_openings": total_openings,
            "total_opening_sqft": round(total_opening_sqft, 2),
            "total_corners": total_corners,
            "inside_corners": total_inside_corners,
            "outside_corners": total_outside_corners
        }

    def _validate_detection(self, walls: List[Wall], ceilings: List[Ceiling], summary: Dict) -> List[str]:
        """Validate detection results and flag potential issues"""
        notes = []

        # Check for reasonable wall heights
        for wall in walls:
            if wall.height_ft > 12:
                notes.append(f"WARNING: {wall.wall_id} has unusual height ({wall.height_ft}ft) - verify if correct")
            elif wall.height_ft < 7:
                notes.append(f"WARNING: {wall.wall_id} has low height ({wall.height_ft}ft) - verify if correct")

        # Check for very long walls (might need expansion joints)
        for wall in walls:
            if wall.length_ft > 50:
                notes.append(f"NOTE: {wall.wall_id} is {wall.length_ft}ft long - may need expansion joint")

        # Check if square footage roughly matches length × height
        for wall in walls:
            expected_sqft = wall.length_ft * wall.height_ft
            opening_sqft = sum(o.square_footage * o.quantity for o in wall.openings)
            actual_sqft = wall.square_footage + opening_sqft

            if abs(expected_sqft - actual_sqft) > (expected_sqft * 0.1):  # >10% difference
                notes.append(f"WARNING: {wall.wall_id} area calculation mismatch - verify dimensions")

        # Check for very large rooms (ceiling)
        for ceiling in ceilings:
            if ceiling.square_footage > 2500:
                side_length = math.sqrt(ceiling.square_footage)
                notes.append(f"NOTE: {ceiling.room} ceiling is {ceiling.square_footage}sqft "
                           f"(~{side_length:.0f}ft × {side_length:.0f}ft) - verify if single room")

        # Check if we have walls but no ceilings (might be incomplete)
        if len(walls) > 0 and len(ceilings) == 0:
            notes.append("NOTE: Walls detected but no ceilings - drawing may be elevation/section only")

        # Check if we have data at all
        if len(walls) == 0 and len(ceilings) == 0:
            notes.append("ERROR: No walls or ceilings detected - verify drawing type and quality")

        return notes


class DrywallCalculator:
    """Calculate drywall materials and labor from detected surfaces"""

    # Drywall sheet sizes (sqft)
    SHEET_SIZES = {
        "4x8": 32,      # Standard residential
        "4x10": 40,     # Reduces seams on 9ft walls
        "4x12": 48,     # Commercial, high ceilings
        "4x14": 56,     # Commercial
    }

    # Material coverage and usage rates
    JOINT_COMPOUND_COVERAGE = 400  # sqft per 5-gallon bucket (3 coats)
    TAPE_COVERAGE = 1.1  # linear feet per sqft of drywall
    SCREWS_PER_SHEET = 32  # for 4x8 sheet at 16" OC studs
    CORNER_BEAD_PER_CORNER = 8  # linear feet per standard corner

    # Labor production rates (sqft per hour) - 2026 industry standards
    PRODUCTION_RATES = {
        "hanging": 40,      # Hanging drywall sheets
        "taping": 150,      # First coat
        "finishing": 200,   # Second and third coats combined
        "sanding": 300,     # Final sanding
    }

    def __init__(self, sheet_size: str = "4x8"):
        """Initialize calculator with preferred sheet size"""
        self.sheet_size = sheet_size
        self.sheet_sqft = self.SHEET_SIZES.get(sheet_size, 32)

    def calculate_materials(self, detection: DrywallDetection,
                          waste_factor: float = 1.10) -> Dict:
        """
        Calculate all drywall materials needed

        Args:
            detection: DrywallDetection object with walls and ceilings
            waste_factor: Multiplier for waste (default 1.10 = 10% waste)

        Returns:
            Dict with material quantities
        """
        summary = detection.summary

        # Total drywall square footage (net, after deducting openings)
        total_sqft = summary["total_drywall_sqft"]

        # Drywall sheets
        sheets_needed_raw = (total_sqft * waste_factor) / self.sheet_sqft
        sheets_needed = math.ceil(sheets_needed_raw)

        # Joint compound (5-gallon buckets)
        buckets_compound = math.ceil(total_sqft / self.JOINT_COMPOUND_COVERAGE)

        # Tape (linear feet)
        tape_linear_ft = math.ceil(total_sqft * self.TAPE_COVERAGE)
        tape_rolls = math.ceil(tape_linear_ft / 500)  # 500ft per roll

        # Screws (pounds - approximately 1 lb per 150 screws)
        total_screws = sheets_needed * self.SCREWS_PER_SHEET
        screws_lbs = math.ceil(total_screws / 150)

        # Corner bead (linear feet)
        corner_bead_ft = summary["outside_corners"] * self.CORNER_BEAD_PER_CORNER
        corner_bead_pieces = math.ceil(corner_bead_ft / 10)  # 10ft pieces

        return {
            "drywall_sheets": {
                "quantity": sheets_needed,
                "size": self.sheet_size,
                "total_sqft": sheets_needed * self.sheet_sqft,
                "coverage_sqft": total_sqft,
                "waste_factor": waste_factor
            },
            "joint_compound": {
                "buckets_5gal": buckets_compound,
                "coverage_sqft_per_bucket": self.JOINT_COMPOUND_COVERAGE
            },
            "tape": {
                "rolls": tape_rolls,
                "linear_ft": tape_linear_ft,
                "ft_per_roll": 500
            },
            "screws": {
                "pounds": screws_lbs,
                "count_approx": total_screws
            },
            "corner_bead": {
                "pieces_10ft": corner_bead_pieces,
                "linear_ft": corner_bead_ft,
                "corners": summary["outside_corners"]
            }
        }

    def calculate_labor(self, detection: DrywallDetection,
                       difficulty: str = "standard") -> Dict:
        """
        Calculate labor hours for drywall installation

        Args:
            detection: DrywallDetection object
            difficulty: "easy", "standard", or "difficult"

        Returns:
            Dict with labor breakdown
        """
        summary = detection.summary
        total_sqft = summary["total_drywall_sqft"]

        # Base hours for each phase
        hanging_hours = total_sqft / self.PRODUCTION_RATES["hanging"]
        taping_hours = total_sqft / self.PRODUCTION_RATES["taping"]
        finishing_hours = total_sqft / self.PRODUCTION_RATES["finishing"]
        sanding_hours = total_sqft / self.PRODUCTION_RATES["sanding"]

        base_hours = hanging_hours + taping_hours + finishing_hours + sanding_hours

        # Difficulty adjustments
        difficulty_multipliers = {
            "easy": 0.85,      # New construction, simple rooms, good access
            "standard": 1.00,  # Normal conditions
            "difficult": 1.30  # Remodel, high ceilings, tight spaces, complex geometry
        }
        multiplier = difficulty_multipliers.get(difficulty, 1.00)

        # High ceiling adjustment (>10ft)
        avg_wall_height = (summary["total_wall_sqft_net"] / summary["total_linear_ft"]) if summary["total_linear_ft"] > 0 else 8
        if avg_wall_height > 10:
            height_multiplier = 1.15  # 15% more time for high ceilings
        else:
            height_multiplier = 1.00

        # Corner complexity adjustment
        corner_hours = (summary["total_corners"] * 0.25)  # 15 minutes per corner

        total_hours = (base_hours * multiplier * height_multiplier) + corner_hours

        return {
            "base_hours": round(base_hours, 2),
            "hanging_hours": round(hanging_hours, 2),
            "taping_hours": round(taping_hours, 2),
            "finishing_hours": round(finishing_hours, 2),
            "sanding_hours": round(sanding_hours, 2),
            "corner_hours": round(corner_hours, 2),
            "difficulty": difficulty,
            "difficulty_multiplier": multiplier,
            "height_multiplier": height_multiplier,
            "total_hours": round(total_hours, 2)
        }

    def calculate_estimate(self, detection: DrywallDetection,
                          sheet_price: float = 15.00,
                          labor_rate: float = 65.00,
                          difficulty: str = "standard",
                          waste_factor: float = 1.10) -> Dict:
        """
        Calculate complete drywall estimate with materials and labor

        Args:
            detection: DrywallDetection object
            sheet_price: Price per drywall sheet
            labor_rate: Labor rate per hour
            difficulty: Installation difficulty level
            waste_factor: Material waste factor

        Returns:
            Complete estimate with pricing breakdown
        """
        materials = self.calculate_materials(detection, waste_factor)
        labor = self.calculate_labor(detection, difficulty)

        # Material costs (2026 industry pricing)
        drywall_cost = materials["drywall_sheets"]["quantity"] * sheet_price
        compound_cost = materials["joint_compound"]["buckets_5gal"] * 25.00  # $25 per bucket
        tape_cost = materials["tape"]["rolls"] * 8.00  # $8 per roll
        screws_cost = materials["screws"]["pounds"] * 12.00  # $12 per lb
        corner_bead_cost = materials["corner_bead"]["pieces_10ft"] * 3.50  # $3.50 per piece

        # Sundries (sandpaper, primers, misc)
        sundries = detection.summary["total_drywall_sqft"] * 0.15  # $0.15 per sqft

        total_materials = (drywall_cost + compound_cost + tape_cost +
                          screws_cost + corner_bead_cost + sundries)

        # Labor cost
        total_labor = labor["total_hours"] * labor_rate

        # Subtotal
        subtotal = total_materials + total_labor

        # Overhead and profit (industry standard)
        overhead = subtotal * 0.15  # 15%
        profit = subtotal * 0.20    # 20% for drywall (lower than painting)

        total_cost = subtotal + overhead + profit

        price_per_sqft = total_cost / detection.summary["total_drywall_sqft"] if detection.summary["total_drywall_sqft"] > 0 else 0

        return {
            "materials": {
                "drywall_sheets": drywall_cost,
                "joint_compound": compound_cost,
                "tape": tape_cost,
                "screws": screws_cost,
                "corner_bead": corner_bead_cost,
                "sundries": sundries,
                "total": total_materials
            },
            "material_details": materials,
            "labor": {
                "hours": labor["total_hours"],
                "rate": labor_rate,
                "total": total_labor,
                "breakdown": labor
            },
            "pricing": {
                "subtotal": round(subtotal, 2),
                "overhead": round(overhead, 2),
                "profit": round(profit, 2),
                "total": round(total_cost, 2),
                "price_per_sqft": round(price_per_sqft, 2)
            },
            "summary": detection.summary
        }


if __name__ == "__main__":
    # Test the detector
    import os

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        exit(1)

    detector = DrywallDetector(api_key)
    calculator = DrywallCalculator(sheet_size="4x8")

    # Test with a sample drawing (user will provide)
    print("Drywall.ai Detection Engine Ready")
    print("Usage: detector.analyze_drawing('path/to/floorplan.png')")
    print("\nExample:")
    print("  detection = detector.analyze_drawing('floorplan.png')")
    print("  estimate = calculator.calculate_estimate(detection)")
    print("  print(f'Total: ${estimate[\"pricing\"][\"total\"]:,.2f}')")
