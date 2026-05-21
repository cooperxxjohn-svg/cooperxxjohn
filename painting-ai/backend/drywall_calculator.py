"""
Drywall Takeoff Calculator
Production-ready drywall estimation engine for residential and commercial projects
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math


class FinishLevel(Enum):
    """ASTM C840 Drywall Finishing Levels"""
    LEVEL_0 = 0  # No taping, finishing, or accessories
    LEVEL_1 = 1  # Tape embedded in compound (fire-rated assemblies)
    LEVEL_2 = 2  # Tape + one coat compound (behind tile, industrial)
    LEVEL_3 = 3  # Tape + two coats compound (typical residential)
    LEVEL_4 = 4  # Tape + three coats compound (commercial, flat paint)
    LEVEL_5 = 5  # Tape + three coats + skim coat (critical lighting)


class ProjectType(Enum):
    """Project classifications affecting labor rates and specifications"""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    TENANT_IMPROVEMENT = "tenant_improvement"
    REMODEL = "remodel"


class StudSpacing(Enum):
    """On-center stud spacing options"""
    SPACING_12_OC = 12
    SPACING_16_OC = 16
    SPACING_24_OC = 24


@dataclass
class Opening:
    """Represents a door, window, or other opening"""
    width: float  # feet
    height: float  # feet
    type: str = "door"  # door, window, pass-through, etc.

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass
class RoomGeometry:
    """Complete geometric data for a room"""
    length: float  # feet
    width: float  # feet
    height: float  # feet (ceiling height)
    perimeter: Optional[float] = None  # override calculated perimeter for irregular rooms
    openings: List[Opening] = field(default_factory=list)

    # Room characteristics
    has_ceiling: bool = True
    ceiling_type: str = "flat"  # flat, vaulted, tray, cathedral

    # Complexity factors
    inside_corners: int = 4  # typical rectangular room
    outside_corners: int = 0
    soffits: int = 0
    archways: int = 0

    def __post_init__(self):
        if self.perimeter is None:
            self.perimeter = 2 * (self.length + self.width)

    @property
    def wall_sqft(self) -> float:
        """Gross wall square footage before deductions"""
        return self.perimeter * self.height

    @property
    def ceiling_sqft(self) -> float:
        """Ceiling square footage"""
        if not self.has_ceiling:
            return 0.0

        base_sqft = self.length * self.width

        # Adjust for ceiling types
        if self.ceiling_type == "vaulted":
            return base_sqft * 1.3  # ~30% more surface area
        elif self.ceiling_type == "cathedral":
            return base_sqft * 1.4
        elif self.ceiling_type == "tray":
            return base_sqft * 1.15

        return base_sqft

    @property
    def opening_sqft(self) -> float:
        """Total opening square footage"""
        return sum(opening.area for opening in self.openings)


@dataclass
class DrywallSpecifications:
    """Project specifications for drywall installation"""
    sheet_width: float = 4.0  # feet
    sheet_length: float = 12.0  # feet (can be 8, 10, 12)
    sheet_thickness: str = "1/2"  # 1/4, 3/8, 1/2, 5/8
    finish_level: FinishLevel = FinishLevel.LEVEL_3
    project_type: ProjectType = ProjectType.RESIDENTIAL

    # Special requirements
    fire_rated: bool = False  # Type X drywall
    moisture_resistant: bool = False  # Green board or purple board
    mold_resistant: bool = False  # Mold-resistant drywall
    soundproofing: bool = False  # Double layer or special board

    # Material preferences
    stud_type: str = "metal"  # metal or wood
    stud_spacing: StudSpacing = StudSpacing.SPACING_16_OC
    corner_bead_type: str = "metal"  # metal, vinyl, paper-faced
    tape_type: str = "paper"  # paper or fiberglass mesh

    @property
    def sheet_sqft(self) -> float:
        """Square footage per sheet"""
        return self.sheet_width * self.sheet_length


@dataclass
class MaterialQuantities:
    """Complete material takeoff quantities"""
    # Drywall sheets
    sheets_needed: int = 0
    sheets_waste: float = 0.0
    total_sheets: int = 0

    # Framing materials
    studs: int = 0
    top_track: float = 0.0  # linear feet
    bottom_track: float = 0.0  # linear feet
    headers: int = 0

    # Joint materials
    paper_tape: float = 0.0  # linear feet
    corner_bead_inside: float = 0.0  # linear feet
    corner_bead_outside: float = 0.0  # linear feet
    joint_compound: float = 0.0  # pounds

    # Fasteners
    screws: int = 0

    # Specialty items
    fire_caulk: int = 0  # tubes
    construction_adhesive: int = 0  # tubes


@dataclass
class LaborHours:
    """Labor breakdown by task"""
    framing: float = 0.0
    hanging: float = 0.0
    taping_first_coat: float = 0.0
    taping_second_coat: float = 0.0
    taping_third_coat: float = 0.0
    skim_coat: float = 0.0
    sanding: float = 0.0
    corner_bead: float = 0.0
    cleanup: float = 0.0

    @property
    def total(self) -> float:
        return (self.framing + self.hanging + self.taping_first_coat +
                self.taping_second_coat + self.taping_third_coat +
                self.skim_coat + self.sanding + self.corner_bead + self.cleanup)


@dataclass
class CostBreakdown:
    """Complete cost breakdown"""
    # Material costs
    drywall_sheets: float = 0.0
    framing_materials: float = 0.0
    joint_compound: float = 0.0
    tape_and_bead: float = 0.0
    fasteners: float = 0.0
    specialty_materials: float = 0.0

    # Labor costs
    labor_cost: float = 0.0

    # Markup
    overhead: float = 0.0
    profit: float = 0.0

    @property
    def total_materials(self) -> float:
        return (self.drywall_sheets + self.framing_materials +
                self.joint_compound + self.tape_and_bead +
                self.fasteners + self.specialty_materials)

    @property
    def subtotal(self) -> float:
        return self.total_materials + self.labor_cost

    @property
    def total(self) -> float:
        return self.subtotal + self.overhead + self.profit


@dataclass
class DrywallEstimate:
    """Complete estimate for a drywall project"""
    room_name: str
    geometry: RoomGeometry
    specifications: DrywallSpecifications
    materials: MaterialQuantities
    labor: LaborHours
    costs: CostBreakdown

    @property
    def price_per_sqft(self) -> float:
        """Total price per square foot"""
        total_sqft = self.geometry.wall_sqft + self.geometry.ceiling_sqft
        if total_sqft == 0:
            return 0.0
        return self.costs.total / total_sqft


class DrywallCalculator:
    """
    Production-ready drywall takeoff calculator
    Based on industry standards and real contractor data
    """

    # Material pricing (2026 national averages - adjust by region)
    MATERIAL_PRICES = {
        # Drywall sheets (per sheet)
        "drywall_1/2_standard": 12.50,
        "drywall_1/2_lightweight": 14.00,
        "drywall_5/8_standard": 15.00,
        "drywall_5/8_type_x": 18.00,
        "drywall_moisture_resistant": 20.00,
        "drywall_mold_resistant": 22.00,

        # Framing (per linear foot or piece)
        "metal_stud_25ga": 1.80,  # per piece (8' or 10')
        "metal_track": 0.95,  # per linear foot
        "wood_stud_2x4": 4.50,  # per piece (8')

        # Joint materials
        "joint_compound_bucket_4.5gal": 18.00,  # ~54 lbs
        "paper_tape_500ft": 8.50,
        "mesh_tape_300ft": 12.00,
        "corner_bead_metal_8ft": 3.50,
        "corner_bead_vinyl_8ft": 4.00,

        # Fasteners
        "drywall_screws_1lb": 8.00,
        "construction_adhesive_tube": 6.50,
    }

    # Labor rates (hours per unit) - based on industry standards
    LABOR_RATES = {
        # Framing (hours per linear foot of wall)
        "framing_metal": 0.010,
        "framing_wood": 0.012,
        "framing_complex": 0.015,  # soffits, archways

        # Hanging (hours per square foot)
        "hanging_walls": 0.012,
        "hanging_ceiling": 0.018,
        "hanging_ceiling_high": 0.025,  # >10' ceiling

        # Taping by level (hours per square foot)
        "taping_level_1": 0.008,
        "taping_level_2": 0.012,
        "taping_level_3": 0.018,
        "taping_level_4": 0.022,
        "taping_level_5": 0.030,

        # Other tasks
        "corner_bead_install": 0.08,  # per linear foot
        "sanding": 0.006,  # per square foot
        "cleanup": 0.002,  # per square foot
    }

    # Waste factors
    WASTE_FACTORS = {
        "base": 0.15,  # 15% base waste
        "complex_layout": 0.05,  # add 5% for many corners/openings
        "high_ceiling": 0.05,  # add 5% for >10' ceilings
        "ceiling_work": 0.10,  # add 10% for ceiling installation
        "inexperienced": 0.10,  # add 10% for less experienced crews
    }

    # Joint compound coverage (pounds per square foot by level)
    COMPOUND_COVERAGE = {
        FinishLevel.LEVEL_1: 0.020,
        FinishLevel.LEVEL_2: 0.035,
        FinishLevel.LEVEL_3: 0.053,
        FinishLevel.LEVEL_4: 0.075,
        FinishLevel.LEVEL_5: 0.095,
    }

    def __init__(self, labor_rate: float = 65.0, overhead_percent: float = 0.15,
                 profit_percent: float = 0.25, region: str = "national"):
        """
        Initialize calculator

        Args:
            labor_rate: Hourly labor rate ($/hour)
            overhead_percent: Overhead percentage (0.15 = 15%)
            profit_percent: Profit margin (0.25 = 25%)
            region: Geographic region for pricing adjustments
        """
        self.labor_rate = labor_rate
        self.overhead_percent = overhead_percent
        self.profit_percent = profit_percent
        self.region = region

    def calculate_framing(self, geometry: RoomGeometry,
                         specs: DrywallSpecifications) -> Tuple[MaterialQuantities, float]:
        """
        Calculate framing materials and labor

        Returns:
            (materials, labor_hours)
        """
        materials = MaterialQuantities()

        # Calculate studs needed
        spacing_inches = specs.stud_spacing.value
        studs_per_wall = math.ceil((geometry.perimeter * 12) / spacing_inches)

        # Add corner studs (2 per inside corner, 3 per outside corner)
        corner_studs = (geometry.inside_corners * 2) + (geometry.outside_corners * 3)

        # Add studs for openings (king studs, jack studs, cripples)
        opening_studs = len(geometry.openings) * 4  # conservative estimate

        materials.studs = studs_per_wall + corner_studs + opening_studs

        # Track (top and bottom)
        materials.top_track = geometry.perimeter
        materials.bottom_track = geometry.perimeter

        # Headers for openings
        materials.headers = len(geometry.openings)

        # Labor calculation
        base_labor = geometry.perimeter * self.LABOR_RATES.get(
            f"framing_{specs.stud_type}", 0.010
        )

        # Add complexity labor
        complexity_labor = (
            geometry.soffits * 2.0 +  # 2 hours per soffit
            geometry.archways * 3.0    # 3 hours per archway
        )

        labor_hours = base_labor + complexity_labor

        return materials, labor_hours

    def calculate_sheets(self, geometry: RoomGeometry,
                        specs: DrywallSpecifications,
                        include_ceiling: bool = True) -> Tuple[int, float]:
        """
        Calculate drywall sheets needed

        Returns:
            (total_sheets, waste_percentage)
        """
        # Calculate total square footage
        wall_sqft = geometry.wall_sqft
        ceiling_sqft = geometry.ceiling_sqft if include_ceiling else 0.0
        total_sqft = wall_sqft + ceiling_sqft

        # Apply opening deductions (only if opening > 10 sqft)
        deductible_openings = sum(
            opening.area for opening in geometry.openings
            if opening.area >= 10.0
        )
        net_sqft = total_sqft - deductible_openings

        # Calculate base sheets needed
        sheet_sqft = specs.sheet_sqft
        base_sheets = net_sqft / sheet_sqft

        # Calculate waste factor
        waste_factor = self.WASTE_FACTORS["base"]

        # Add complexity waste
        if geometry.inside_corners + geometry.outside_corners > 6:
            waste_factor += self.WASTE_FACTORS["complex_layout"]

        # Add high ceiling waste
        if geometry.height > 10.0:
            waste_factor += self.WASTE_FACTORS["high_ceiling"]

        # Add ceiling work waste
        if include_ceiling and geometry.has_ceiling:
            waste_factor += self.WASTE_FACTORS["ceiling_work"]

        # Calculate total sheets
        total_sheets = math.ceil(base_sheets * (1 + waste_factor))

        return total_sheets, waste_factor

    def calculate_opening_reduction(self, geometry: RoomGeometry) -> Tuple[float, float]:
        """
        Calculate area reduction for openings and additional labor for cuts

        Returns:
            (deductible_sqft, additional_labor_hours)
        """
        deductible_sqft = 0.0
        cutting_labor = 0.0

        for opening in geometry.openings:
            # Only deduct if opening > 10 sqft (smaller openings covered by waste)
            if opening.area >= 10.0:
                deductible_sqft += opening.area

            # Add cutting/fitting labor for each opening
            cutting_labor += 0.25  # 15 minutes per opening

        return deductible_sqft, cutting_labor

    def calculate_corners(self, geometry: RoomGeometry) -> Tuple[float, float]:
        """
        Calculate corner bead needed

        Returns:
            (inside_corner_lf, outside_corner_lf)
        """
        # Inside corners use paper tape, outside corners use bead
        inside_lf = geometry.inside_corners * geometry.height
        outside_lf = geometry.outside_corners * geometry.height

        # Add ceiling perimeter corners if applicable
        if geometry.has_ceiling:
            inside_lf += geometry.perimeter

        return inside_lf, outside_lf

    def calculate_joint_compound(self, total_sqft: float,
                                specs: DrywallSpecifications) -> float:
        """
        Calculate joint compound needed in pounds
        """
        coverage_rate = self.COMPOUND_COVERAGE.get(
            specs.finish_level, 0.053
        )

        pounds_needed = total_sqft * coverage_rate

        # Add 10% waste for compound
        pounds_with_waste = pounds_needed * 1.10

        return pounds_with_waste

    def calculate_tape(self, geometry: RoomGeometry) -> float:
        """
        Calculate tape needed in linear feet

        All seams plus inside corners
        Estimate: 1.1 LF of tape per 1 LF of wall (includes waste)
        """
        # Perimeter seams
        perimeter_tape = geometry.perimeter * geometry.height

        # Horizontal seams (assuming 8' or 12' sheets)
        horizontal_seams = geometry.perimeter * (geometry.height / 8.0)

        # Inside corners
        inside_lf, _ = self.calculate_corners(geometry)

        # Total with waste factor
        total_tape = (perimeter_tape + horizontal_seams + inside_lf) * 1.1

        return total_tape

    def calculate_screws(self, num_sheets: int, specs: DrywallSpecifications) -> int:
        """
        Calculate screws needed

        Typical: 32-40 screws per sheet (we'll use 36 as standard)
        """
        screws_per_sheet = 36

        # Ceiling requires more screws
        if specs.sheet_length == 12.0:
            screws_per_sheet = 40

        total_screws = num_sheets * screws_per_sheet

        # Add 10% for waste/drops
        return int(total_screws * 1.10)

    def calculate_labor_hours(self, geometry: RoomGeometry,
                             specs: DrywallSpecifications,
                             total_sheets: int) -> LaborHours:
        """
        Calculate complete labor breakdown by phase
        """
        labor = LaborHours()

        total_sqft = geometry.wall_sqft + geometry.ceiling_sqft

        # Framing labor
        if specs.project_type != ProjectType.REMODEL:
            _, labor.framing = self.calculate_framing(geometry, specs)

        # Hanging labor
        wall_sqft = geometry.wall_sqft
        ceiling_sqft = geometry.ceiling_sqft

        hanging_rate = self.LABOR_RATES["hanging_walls"]
        if geometry.height > 10.0:
            hanging_rate = self.LABOR_RATES["hanging_ceiling_high"]

        labor.hanging = (wall_sqft * hanging_rate)

        if geometry.has_ceiling:
            ceiling_rate = self.LABOR_RATES["hanging_ceiling"]
            if geometry.height > 10.0:
                ceiling_rate = self.LABOR_RATES["hanging_ceiling_high"]
            labor.hanging += ceiling_sqft * ceiling_rate

        # Add labor for cutting around openings
        _, cutting_labor = self.calculate_opening_reduction(geometry)
        labor.hanging += cutting_labor

        # Taping labor by finish level
        level_key = f"taping_level_{specs.finish_level.value}"
        taping_rate = self.LABOR_RATES.get(level_key, 0.018)

        if specs.finish_level.value >= 1:
            labor.taping_first_coat = total_sqft * (taping_rate / 3)

        if specs.finish_level.value >= 2:
            labor.taping_second_coat = total_sqft * (taping_rate / 3)

        if specs.finish_level.value >= 3:
            labor.taping_third_coat = total_sqft * (taping_rate / 3)

        # Level 5 requires skim coat
        if specs.finish_level == FinishLevel.LEVEL_5:
            labor.skim_coat = total_sqft * 0.012

        # Corner bead installation
        _, outside_lf = self.calculate_corners(geometry)
        labor.corner_bead = outside_lf * self.LABOR_RATES["corner_bead_install"]

        # Sanding
        if specs.finish_level.value >= 3:
            labor.sanding = total_sqft * self.LABOR_RATES["sanding"]

        # Cleanup
        labor.cleanup = total_sqft * self.LABOR_RATES["cleanup"]

        return labor

    def calculate_pricing(self, materials: MaterialQuantities,
                         labor: LaborHours,
                         specs: DrywallSpecifications) -> CostBreakdown:
        """
        Calculate complete pricing breakdown
        """
        costs = CostBreakdown()

        # Drywall sheets
        sheet_price_key = f"drywall_{specs.sheet_thickness}_standard"
        if specs.fire_rated:
            sheet_price_key = "drywall_5/8_type_x"
        elif specs.moisture_resistant:
            sheet_price_key = "drywall_moisture_resistant"
        elif specs.mold_resistant:
            sheet_price_key = "drywall_mold_resistant"

        sheet_price = self.MATERIAL_PRICES.get(sheet_price_key, 12.50)
        costs.drywall_sheets = materials.total_sheets * sheet_price

        # Framing materials
        if materials.studs > 0:
            stud_price = self.MATERIAL_PRICES.get(
                f"{specs.stud_type}_stud_25ga" if specs.stud_type == "metal" else "wood_stud_2x4",
                1.80
            )
            track_price = self.MATERIAL_PRICES.get("metal_track", 0.95)

            costs.framing_materials = (
                materials.studs * stud_price +
                (materials.top_track + materials.bottom_track) * track_price
            )

        # Joint compound (convert pounds to buckets)
        buckets_needed = math.ceil(materials.joint_compound / 54)  # 54 lbs per bucket
        costs.joint_compound = buckets_needed * self.MATERIAL_PRICES["joint_compound_bucket_4.5gal"]

        # Tape and corner bead
        tape_rolls = math.ceil(materials.paper_tape / 500)  # 500 ft per roll
        corner_bead_pieces = math.ceil(materials.corner_bead_outside / 8)  # 8 ft pieces

        tape_price = self.MATERIAL_PRICES.get(
            f"{specs.tape_type}_tape_500ft" if specs.tape_type == "paper" else "mesh_tape_300ft",
            8.50
        )
        bead_price = self.MATERIAL_PRICES.get(
            f"corner_bead_{specs.corner_bead_type}_8ft",
            3.50
        )

        costs.tape_and_bead = (tape_rolls * tape_price) + (corner_bead_pieces * bead_price)

        # Fasteners (screws sold by pound, ~150 screws per lb)
        screw_pounds = math.ceil(materials.screws / 150)
        costs.fasteners = screw_pounds * self.MATERIAL_PRICES["drywall_screws_1lb"]

        # Specialty materials
        if specs.fire_rated:
            costs.specialty_materials = materials.fire_caulk * 8.00

        # Labor cost
        costs.labor_cost = labor.total * self.labor_rate

        # Overhead and profit
        costs.overhead = costs.subtotal * self.overhead_percent
        costs.profit = costs.subtotal * self.profit_percent

        return costs

    def estimate_project(self, room_data: Dict,
                        specifications: Optional[Dict] = None) -> DrywallEstimate:
        """
        Complete estimate from room data

        Args:
            room_data: {
                "name": "Living Room",
                "length": 20.0,
                "width": 15.0,
                "height": 9.0,
                "openings": [
                    {"width": 3.0, "height": 7.0, "type": "door"},
                    {"width": 4.0, "height": 5.0, "type": "window"}
                ],
                "inside_corners": 4,
                "outside_corners": 0,
                "has_ceiling": true
            }
            specifications: Optional override for DrywallSpecifications

        Returns:
            Complete DrywallEstimate
        """
        # Build geometry
        openings = [
            Opening(**opening_data)
            for opening_data in room_data.get("openings", [])
        ]

        geometry = RoomGeometry(
            length=room_data["length"],
            width=room_data["width"],
            height=room_data["height"],
            openings=openings,
            has_ceiling=room_data.get("has_ceiling", True),
            inside_corners=room_data.get("inside_corners", 4),
            outside_corners=room_data.get("outside_corners", 0),
            soffits=room_data.get("soffits", 0),
            archways=room_data.get("archways", 0)
        )

        # Build specifications
        if specifications:
            specs = DrywallSpecifications(**specifications)
        else:
            specs = DrywallSpecifications()

        # Calculate materials
        materials = MaterialQuantities()

        # Framing (if new construction)
        if specs.project_type != ProjectType.REMODEL:
            framing_materials, _ = self.calculate_framing(geometry, specs)
            materials.studs = framing_materials.studs
            materials.top_track = framing_materials.top_track
            materials.bottom_track = framing_materials.bottom_track
            materials.headers = framing_materials.headers

        # Drywall sheets
        materials.total_sheets, waste_factor = self.calculate_sheets(
            geometry, specs, include_ceiling=geometry.has_ceiling
        )
        materials.sheets_waste = waste_factor

        # Joint materials
        total_sqft = geometry.wall_sqft + geometry.ceiling_sqft
        materials.joint_compound = self.calculate_joint_compound(total_sqft, specs)
        materials.paper_tape = self.calculate_tape(geometry)

        inside_lf, outside_lf = self.calculate_corners(geometry)
        materials.corner_bead_inside = inside_lf
        materials.corner_bead_outside = outside_lf

        # Fasteners
        materials.screws = self.calculate_screws(materials.total_sheets, specs)

        # Calculate labor
        labor = self.calculate_labor_hours(geometry, specs, materials.total_sheets)

        # Calculate costs
        costs = self.calculate_pricing(materials, labor, specs)

        # Build estimate
        estimate = DrywallEstimate(
            room_name=room_data.get("name", "Unnamed Room"),
            geometry=geometry,
            specifications=specs,
            materials=materials,
            labor=labor,
            costs=costs
        )

        return estimate

    def estimate_multi_room_project(self, rooms: List[Dict],
                                   specifications: Optional[Dict] = None) -> Dict:
        """
        Estimate a complete project with multiple rooms

        Returns summary with totals across all rooms
        """
        estimates = []

        for room_data in rooms:
            estimate = self.estimate_project(room_data, specifications)
            estimates.append(estimate)

        # Calculate totals
        total_materials = MaterialQuantities()
        total_labor = LaborHours()
        total_costs = CostBreakdown()

        for estimate in estimates:
            # Sum materials
            total_materials.total_sheets += estimate.materials.total_sheets
            total_materials.studs += estimate.materials.studs
            total_materials.top_track += estimate.materials.top_track
            total_materials.bottom_track += estimate.materials.bottom_track
            total_materials.joint_compound += estimate.materials.joint_compound
            total_materials.paper_tape += estimate.materials.paper_tape
            total_materials.corner_bead_inside += estimate.materials.corner_bead_inside
            total_materials.corner_bead_outside += estimate.materials.corner_bead_outside
            total_materials.screws += estimate.materials.screws

            # Sum labor
            total_labor.framing += estimate.labor.framing
            total_labor.hanging += estimate.labor.hanging
            total_labor.taping_first_coat += estimate.labor.taping_first_coat
            total_labor.taping_second_coat += estimate.labor.taping_second_coat
            total_labor.taping_third_coat += estimate.labor.taping_third_coat
            total_labor.skim_coat += estimate.labor.skim_coat
            total_labor.sanding += estimate.labor.sanding
            total_labor.corner_bead += estimate.labor.corner_bead
            total_labor.cleanup += estimate.labor.cleanup

            # Sum costs
            total_costs.drywall_sheets += estimate.costs.drywall_sheets
            total_costs.framing_materials += estimate.costs.framing_materials
            total_costs.joint_compound += estimate.costs.joint_compound
            total_costs.tape_and_bead += estimate.costs.tape_and_bead
            total_costs.fasteners += estimate.costs.fasteners
            total_costs.specialty_materials += estimate.costs.specialty_materials
            total_costs.labor_cost += estimate.costs.labor_cost

        # Recalculate overhead and profit on totals
        total_costs.overhead = total_costs.subtotal * self.overhead_percent
        total_costs.profit = total_costs.subtotal * self.profit_percent

        return {
            "room_estimates": [asdict(est) for est in estimates],
            "totals": {
                "materials": asdict(total_materials),
                "labor": asdict(total_labor),
                "costs": asdict(total_costs),
                "total_rooms": len(estimates),
                "total_sqft": sum(
                    est.geometry.wall_sqft + est.geometry.ceiling_sqft
                    for est in estimates
                ),
                "price_per_sqft": total_costs.total / sum(
                    est.geometry.wall_sqft + est.geometry.ceiling_sqft
                    for est in estimates
                ) if estimates else 0.0
            }
        }


if __name__ == "__main__":
    # Example usage
    calculator = DrywallCalculator(labor_rate=65.0, overhead_percent=0.15, profit_percent=0.25)

    # Sample room
    room_data = {
        "name": "Living Room",
        "length": 20.0,
        "width": 15.0,
        "height": 9.0,
        "openings": [
            {"width": 3.0, "height": 7.0, "type": "door"},
            {"width": 4.0, "height": 5.0, "type": "window"},
            {"width": 4.0, "height": 5.0, "type": "window"}
        ],
        "inside_corners": 4,
        "outside_corners": 0,
        "has_ceiling": True
    }

    estimate = calculator.estimate_project(room_data)

    print(f"\n=== Drywall Estimate: {estimate.room_name} ===")
    print(f"\nTotal Square Footage: {estimate.geometry.wall_sqft + estimate.geometry.ceiling_sqft:.0f} sqft")
    print(f"Drywall Sheets: {estimate.materials.total_sheets}")
    print(f"Joint Compound: {estimate.materials.joint_compound:.0f} lbs")
    print(f"Total Labor Hours: {estimate.labor.total:.1f}")
    print(f"\nTotal Cost: ${estimate.costs.total:,.2f}")
    print(f"Price per sqft: ${estimate.price_per_sqft:.2f}")
