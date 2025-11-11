"""
BOQ Calculator - Calculation Rules Engine
Implements CPWD-compliant calculation methods for different work categories

This module provides calculation classes for each major work category
with standard formulas and material/labour requirements.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
import logging

from boq_schema import (
    BOQLineItem, Material, Labour, UnitType, WorkCategory,
    MaterialGrade
)

logger = logging.getLogger(__name__)


class BaseCalculator(ABC):
    """Base class for all BOQ calculators"""

    def __init__(self, dsr_rates: Optional[Dict] = None):
        """
        Args:
            dsr_rates: Dictionary of DSR (Delhi Schedule of Rates) or local rates
        """
        self.dsr_rates = dsr_rates or {}

    @abstractmethod
    def calculate(self, **kwargs) -> BOQLineItem:
        """Calculate BOQ line item from input parameters"""
        pass

    def apply_wastage(self, quantity: Decimal, wastage_pct: Decimal = Decimal("5.0")) -> Decimal:
        """Apply wastage percentage to quantity"""
        return quantity * (1 + wastage_pct / 100)

    def get_rate(self, item_code: str, default: Decimal = Decimal("0")) -> Decimal:
        """Get rate from DSR or return default"""
        return Decimal(str(self.dsr_rates.get(item_code, default)))


class EarthworkCalculator(BaseCalculator):
    """Calculator for earthwork items"""

    EARTHWORK_TYPES = {
        'excavation_ordinary_soil': {
            'code': 'EW001',
            'spec': 'Excavation for all types and sizes of foundations in ordinary soil',
            'labour_per_cum': Decimal("0.50"),  # Labour days per cum
            'equipment_required': False
        },
        'excavation_hard_soil': {
            'code': 'EW002',
            'spec': 'Excavation in hard soil/murrum',
            'labour_per_cum': Decimal("0.75"),
            'equipment_required': False
        },
        'excavation_soft_rock': {
            'code': 'EW003',
            'spec': 'Excavation in soft rock',
            'labour_per_cum': Decimal("1.50"),
            'equipment_required': True
        },
        'filling': {
            'code': 'EW010',
            'spec': 'Filling in plinth/floor with excavated earth',
            'labour_per_cum': Decimal("0.30"),
            'equipment_required': False
        }
    }

    def calculate(
        self,
        item_no: str,
        work_type: str,
        length: Decimal,
        width: Decimal,
        depth: Decimal,
        deductions: Decimal = Decimal("0"),
        location: str = "",
        drawing_ref: str = ""
    ) -> BOQLineItem:
        """
        Calculate earthwork item

        Args:
            item_no: BOQ item number
            work_type: Type from EARTHWORK_TYPES keys
            length, width, depth: Dimensions in meters
            deductions: Volume to deduct in cum
            location: Location description
            drawing_ref: Drawing reference

        Returns:
            BOQLineItem with calculated quantities and rates
        """
        if work_type not in self.EARTHWORK_TYPES:
            raise ValueError(f"Unknown earthwork type: {work_type}")

        work_spec = self.EARTHWORK_TYPES[work_type]

        # Calculate volume
        gross_volume = length * width * depth
        net_volume = gross_volume - deductions

        # Labour calculation
        labour_days = net_volume * work_spec['labour_per_cum']
        unskilled_rate = self.get_rate('LABOUR_UNSKILLED', Decimal("600"))
        skilled_rate = self.get_rate('LABOUR_SKILLED', Decimal("800"))

        labour = [
            Labour(
                category="Unskilled Labour",
                unit=UnitType.NUMBER,
                quantity=labour_days * Decimal("2"),  # 2 unskilled per day
                rate=unskilled_rate,
            ),
            Labour(
                category="Skilled Labour (Mason)",
                unit=UnitType.NUMBER,
                quantity=labour_days * Decimal("0.5"),  # 0.5 skilled per day
                rate=skilled_rate,
            )
        ]

        # Calculate costs
        labour_cost = sum(l.amount for l in labour if l.amount)
        equipment_cost = Decimal("0")
        if work_spec['equipment_required']:
            equipment_cost = net_volume * Decimal("50")  # Equipment charge per cum

        unit_rate = (labour_cost + equipment_cost) / net_volume if net_volume > 0 else Decimal("0")

        return BOQLineItem(
            item_no=item_no,
            description=work_spec['spec'],
            category=WorkCategory.EARTHWORK,
            specification=f"{work_spec['spec']} as per CPWD specification",
            reference_standard="IS 1200 Part 1, CPWD Specifications",
            unit=UnitType.CUBIC_METER,
            quantity=net_volume,
            unit_rate=unit_rate,
            labour_cost=labour_cost,
            equipment_cost=equipment_cost,
            total_amount=net_volume * unit_rate,
            labour=labour,
            materials=[],
            location=location,
            drawing_reference=drawing_ref,
            remarks=f"L={length}m × W={width}m × D={depth}m"
        )


class ConcreteCalculator(BaseCalculator):
    """Calculator for concrete work items"""

    # Standard material composition per cum of concrete
    CONCRETE_MIX = {
        MaterialGrade.M10: {
            'cement': Decimal("210"),  # kg
            'sand': Decimal("0.70"),   # cum
            'aggregate_20mm': Decimal("1.40"),  # cum
            'water': Decimal("200"),   # litres
        },
        MaterialGrade.M15: {
            'cement': Decimal("250"),
            'sand': Decimal("0.65"),
            'aggregate_20mm': Decimal("1.30"),
            'water': Decimal("200"),
        },
        MaterialGrade.M20: {
            'cement': Decimal("300"),
            'sand': Decimal("0.60"),
            'aggregate_20mm': Decimal("1.20"),
            'water': Decimal("200"),
        },
        MaterialGrade.M25: {
            'cement': Decimal("350"),
            'sand': Decimal("0.55"),
            'aggregate_20mm': Decimal("1.10"),
            'water': Decimal("200"),
        },
        MaterialGrade.M30: {
            'cement': Decimal("380"),
            'sand': Decimal("0.52"),
            'aggregate_20mm': Decimal("1.04"),
            'water': Decimal("200"),
        },
    }

    def calculate(
        self,
        item_no: str,
        concrete_type: str,  # e.g., "foundation", "column", "beam", "slab"
        grade: MaterialGrade,
        length: Decimal,
        width: Decimal,
        thickness: Decimal,
        count: int = 1,
        deductions: Decimal = Decimal("0"),
        location: str = "",
        drawing_ref: str = ""
    ) -> BOQLineItem:
        """
        Calculate concrete work item

        Args:
            item_no: BOQ item number
            concrete_type: Type of concrete work
            grade: Concrete grade (M10, M15, M20, etc.)
            length, width, thickness: Dimensions in meters
            count: Number of similar elements
            deductions: Volume to deduct
            location: Location description
            drawing_ref: Drawing reference
        """
        if grade not in self.CONCRETE_MIX:
            raise ValueError(f"Unknown concrete grade: {grade}")

        mix = self.CONCRETE_MIX[grade]

        # Calculate volume
        single_volume = length * width * thickness
        gross_volume = single_volume * count
        net_volume = gross_volume - deductions

        # Calculate materials with wastage
        materials = [
            Material(
                name="Cement (OPC 43 Grade)",
                specification="Conforming to IS 8112",
                unit=UnitType.KILOGRAM,
                quantity=net_volume * mix['cement'],
                rate=self.get_rate('CEMENT_OPC43', Decimal("7.5")),
                wastage_percentage=Decimal("2.0")
            ),
            Material(
                name="Fine Aggregate (Sand)",
                specification="Confirming to IS 383, Zone II",
                unit=UnitType.CUBIC_METER,
                quantity=net_volume * mix['sand'],
                rate=self.get_rate('SAND', Decimal("1200")),
                wastage_percentage=Decimal("5.0")
            ),
            Material(
                name="Coarse Aggregate 20mm",
                specification="Confirming to IS 383",
                unit=UnitType.CUBIC_METER,
                quantity=net_volume * mix['aggregate_20mm'],
                rate=self.get_rate('AGGREGATE_20MM', Decimal("1400")),
                wastage_percentage=Decimal("5.0")
            ),
            Material(
                name="Water",
                specification="Potable water",
                unit=UnitType.LITRE,
                quantity=net_volume * mix['water'],
                rate=self.get_rate('WATER', Decimal("0.05")),
                wastage_percentage=Decimal("10.0")
            ),
        ]

        # Labour calculation - varies by concrete type
        labour_per_cum = {
            'foundation': Decimal("0.80"),
            'column': Decimal("1.20"),
            'beam': Decimal("1.00"),
            'slab': Decimal("1.00"),
            'floor': Decimal("0.90"),
        }.get(concrete_type.lower(), Decimal("1.00"))

        mason_rate = self.get_rate('LABOUR_MASON', Decimal("800"))
        helper_rate = self.get_rate('LABOUR_HELPER', Decimal("600"))

        labour = [
            Labour(
                category="Mason",
                unit=UnitType.NUMBER,
                quantity=net_volume * labour_per_cum,
                rate=mason_rate
            ),
            Labour(
                category="Helper",
                unit=UnitType.NUMBER,
                quantity=net_volume * labour_per_cum * Decimal("2"),  # 2 helpers per mason
                rate=helper_rate
            ),
        ]

        # Calculate costs
        material_cost = sum(m.amount for m in materials if m.amount)
        labour_cost = sum(l.amount for l in labour if l.amount)
        equipment_cost = net_volume * Decimal("150")  # Concrete mixer, vibrator etc.

        unit_rate = (material_cost + labour_cost + equipment_cost) / net_volume if net_volume > 0 else Decimal("0")

        description = f"Providing and laying {grade.value} grade concrete in {concrete_type}"

        return BOQLineItem(
            item_no=item_no,
            description=description,
            category=WorkCategory.CONCRETE_WORK,
            specification=f"{grade.value} concrete as per IS 456:2000",
            reference_standard="IS 456:2000, IS 383",
            unit=UnitType.CUBIC_METER,
            quantity=net_volume,
            unit_rate=unit_rate,
            material_cost=material_cost,
            labour_cost=labour_cost,
            equipment_cost=equipment_cost,
            total_amount=net_volume * unit_rate,
            materials=materials,
            labour=labour,
            location=location,
            drawing_reference=drawing_ref,
            remarks=f"L={length}m × W={width}m × T={thickness}m × {count} nos"
        )


class FormworkCalculator(BaseCalculator):
    """Calculator for formwork/shuttering items"""

    def calculate(
        self,
        item_no: str,
        element_type: str,  # foundation, column, beam, slab
        area: Decimal = None,
        length: Decimal = None,
        width: Decimal = None,
        height: Decimal = None,
        count: int = 1,
        location: str = "",
        drawing_ref: str = ""
    ) -> BOQLineItem:
        """
        Calculate formwork area and item

        Can accept either direct area or calculate from dimensions
        """
        # Calculate area if not provided
        if area is None:
            if element_type.lower() == 'column':
                # Perimeter × height for column
                if length and width and height:
                    area = 2 * (length + width) * height * count
                else:
                    raise ValueError("For column formwork, provide length, width, and height")

            elif element_type.lower() in ['beam', 'foundation']:
                # Two sides + bottom
                if length and width and height:
                    area = (2 * height + width) * length * count
                else:
                    raise ValueError(f"For {element_type} formwork, provide length, width, and height")

            elif element_type.lower() == 'slab':
                # Bottom area only
                if length and width:
                    area = length * width * count
                else:
                    raise ValueError("For slab formwork, provide length and width")
            else:
                raise ValueError("Provide area or valid element_type with dimensions")

        # Material - Plywood shuttering
        plywood_area = area * Decimal("1.05")  # 5% wastage
        plywood_rate = self.get_rate('PLYWOOD_12MM', Decimal("1800"))

        materials = [
            Material(
                name="Plywood 12mm thick",
                specification="BWP grade plywood",
                unit=UnitType.SQUARE_METER,
                quantity=plywood_area / Decimal("10"),  # Reusable 10 times
                rate=plywood_rate,
                wastage_percentage=Decimal("5.0")
            ),
            Material(
                name="Wooden battens",
                specification="Seasoned timber",
                unit=UnitType.RUNNING_METER,
                quantity=area * Decimal("3"),  # 3 rmt per sqm
                rate=self.get_rate('TIMBER_BATTEN', Decimal("60")),
                wastage_percentage=Decimal("10.0")
            ),
        ]

        # Labour
        carpenter_rate = self.get_rate('LABOUR_CARPENTER', Decimal("900"))
        helper_rate = self.get_rate('LABOUR_HELPER', Decimal("600"))

        labour = [
            Labour(
                category="Carpenter",
                unit=UnitType.NUMBER,
                quantity=area * Decimal("0.15"),  # 0.15 days per sqm
                rate=carpenter_rate
            ),
            Labour(
                category="Helper",
                unit=UnitType.NUMBER,
                quantity=area * Decimal("0.15"),
                rate=helper_rate
            ),
        ]

        material_cost = sum(m.amount for m in materials if m.amount)
        labour_cost = sum(l.amount for l in labour if l.amount)
        unit_rate = (material_cost + labour_cost) / area if area > 0 else Decimal("0")

        return BOQLineItem(
            item_no=item_no,
            description=f"Providing and fixing formwork for {element_type}",
            category=WorkCategory.FORMWORK,
            specification="Plywood formwork as per CPWD specifications",
            reference_standard="CPWD Specifications",
            unit=UnitType.SQUARE_METER,
            quantity=area,
            unit_rate=unit_rate,
            material_cost=material_cost,
            labour_cost=labour_cost,
            total_amount=area * unit_rate,
            materials=materials,
            labour=labour,
            location=location,
            drawing_reference=drawing_ref
        )


class ReinforcementCalculator(BaseCalculator):
    """Calculator for steel reinforcement"""

    # Weight per meter for different bar diameters (kg/m)
    BAR_WEIGHT = {
        8: Decimal("0.395"),
        10: Decimal("0.617"),
        12: Decimal("0.888"),
        16: Decimal("1.578"),
        20: Decimal("2.466"),
        25: Decimal("3.854"),
        32: Decimal("6.313"),
    }

    def calculate(
        self,
        item_no: str,
        bar_diameter: int,  # mm
        length_per_bar: Decimal,
        number_of_bars: int,
        overlap_length: Decimal = Decimal("0"),  # Additional length for lapping
        location: str = "",
        drawing_ref: str = ""
    ) -> BOQLineItem:
        """
        Calculate steel reinforcement item

        Args:
            bar_diameter: Diameter in mm (8, 10, 12, 16, 20, 25, 32)
            length_per_bar: Length of each bar in meters
            number_of_bars: Total number of bars
            overlap_length: Additional length for overlaps/laps
        """
        if bar_diameter not in self.BAR_WEIGHT:
            raise ValueError(f"Invalid bar diameter: {bar_diameter}mm")

        weight_per_meter = self.BAR_WEIGHT[bar_diameter]

        # Calculate total length
        total_length = (length_per_bar + overlap_length) * number_of_bars

        # Calculate weight with wastage
        total_weight = total_length * weight_per_meter
        weight_with_wastage = total_weight * Decimal("1.05")  # 5% wastage

        # Materials
        steel_rate = self.get_rate('STEEL_FE500', Decimal("65"))  # per kg
        binding_wire_rate = self.get_rate('BINDING_WIRE', Decimal("80"))

        materials = [
            Material(
                name=f"TMT Steel Fe500 - {bar_diameter}mm dia",
                specification="High strength deformed steel bars conforming to IS 1786",
                unit=UnitType.KILOGRAM,
                quantity=total_weight,
                rate=steel_rate,
                wastage_percentage=Decimal("5.0")
            ),
            Material(
                name="Binding Wire",
                specification="GI binding wire",
                unit=UnitType.KILOGRAM,
                quantity=total_weight * Decimal("0.01"),  # 1% of steel weight
                rate=binding_wire_rate,
                wastage_percentage=Decimal("10.0")
            ),
        ]

        # Labour - Bar bending and fixing
        barbender_rate = self.get_rate('LABOUR_BARBENDER', Decimal("850"))
        helper_rate = self.get_rate('LABOUR_HELPER', Decimal("600"))

        labour = [
            Labour(
                category="Bar Bender",
                unit=UnitType.NUMBER,
                quantity=weight_with_wastage * Decimal("0.008"),  # 0.008 days per kg
                rate=barbender_rate
            ),
            Labour(
                category="Helper",
                unit=UnitType.NUMBER,
                quantity=weight_with_wastage * Decimal("0.008"),
                rate=helper_rate
            ),
        ]

        material_cost = sum(m.amount for m in materials if m.amount)
        labour_cost = sum(l.amount for l in labour if l.amount)
        unit_rate = (material_cost + labour_cost) / weight_with_wastage if weight_with_wastage > 0 else Decimal("0")

        return BOQLineItem(
            item_no=item_no,
            description=f"Providing and fixing TMT steel reinforcement {bar_diameter}mm dia",
            category=WorkCategory.REINFORCEMENT,
            specification=f"TMT Fe500 grade steel bars of {bar_diameter}mm diameter",
            reference_standard="IS 1786, IS 2502",
            unit=UnitType.KILOGRAM,
            quantity=weight_with_wastage,
            unit_rate=unit_rate,
            material_cost=material_cost,
            labour_cost=labour_cost,
            total_amount=weight_with_wastage * unit_rate,
            materials=materials,
            labour=labour,
            location=location,
            drawing_reference=drawing_ref,
            remarks=f"{number_of_bars} bars × {length_per_bar}m each"
        )


class MasonryCalculator(BaseCalculator):
    """Calculator for brickwork/masonry items"""

    # Bricks required per cum for different wall thicknesses
    BRICK_REQUIREMENTS = {
        '230mm': {  # 1 brick thick
            'bricks_per_cum': 500,
            'mortar_per_cum': Decimal("0.30"),  # cum
        },
        '115mm': {  # Half brick thick
            'bricks_per_cum': 500,
            'mortar_per_cum': Decimal("0.25"),
        },
        '345mm': {  # 1.5 brick thick
            'bricks_per_cum': 500,
            'mortar_per_cum': Decimal("0.33"),
        },
    }

    # Mortar mix ratios (cement:sand by volume)
    MORTAR_MIX = {
        '1:4': {'cement': Decimal("8.5"), 'sand': Decimal("0.27")},  # per cum of masonry
        '1:5': {'cement': Decimal("7.0"), 'sand': Decimal("0.28")},
        '1:6': {'cement': Decimal("6.0"), 'sand': Decimal("0.29")},
    }

    def calculate(
        self,
        item_no: str,
        wall_thickness: str,  # '115mm', '230mm', '345mm'
        mortar_ratio: str,  # '1:4', '1:5', '1:6'
        length: Decimal,
        height: Decimal,
        deductions: Decimal = Decimal("0"),  # For openings
        brick_class: str = "First Class",
        location: str = "",
        drawing_ref: str = ""
    ) -> BOQLineItem:
        """
        Calculate brick masonry item
        """
        if wall_thickness not in self.BRICK_REQUIREMENTS:
            raise ValueError(f"Invalid wall thickness: {wall_thickness}")
        if mortar_ratio not in self.MORTAR_MIX:
            raise ValueError(f"Invalid mortar ratio: {mortar_ratio}")

        brick_spec = self.BRICK_REQUIREMENTS[wall_thickness]
        mortar_spec = self.MORTAR_MIX[mortar_ratio]

        # Calculate volume
        thickness_m = Decimal(wall_thickness.replace('mm', '')) / Decimal("1000")
        gross_volume = length * height * thickness_m
        net_volume = gross_volume - deductions

        # Calculate materials
        num_bricks = net_volume * brick_spec['bricks_per_cum']

        materials = [
            Material(
                name=f"{brick_class} Bricks",
                specification=f"{brick_class} modular bricks conforming to IS 1077",
                unit=UnitType.NUMBER,
                quantity=num_bricks,
                rate=self.get_rate('BRICK_FIRST_CLASS', Decimal("6")),
                wastage_percentage=Decimal("8.0")
            ),
            Material(
                name="Cement",
                specification="OPC 43 grade",
                unit=UnitType.KILOGRAM,
                quantity=net_volume * mortar_spec['cement'] * Decimal("50"),  # Convert bags to kg
                rate=self.get_rate('CEMENT_OPC43', Decimal("7.5")),
                wastage_percentage=Decimal("3.0")
            ),
            Material(
                name="Sand",
                specification="Fine sand for mortar",
                unit=UnitType.CUBIC_METER,
                quantity=net_volume * mortar_spec['sand'],
                rate=self.get_rate('SAND', Decimal("1200")),
                wastage_percentage=Decimal("5.0")
            ),
        ]

        # Labour
        mason_rate = self.get_rate('LABOUR_MASON', Decimal("800"))
        helper_rate = self.get_rate('LABOUR_HELPER', Decimal("600"))

        labour = [
            Labour(
                category="Mason",
                unit=UnitType.NUMBER,
                quantity=net_volume * Decimal("1.2"),  # 1.2 days per cum
                rate=mason_rate
            ),
            Labour(
                category="Helper",
                unit=UnitType.NUMBER,
                quantity=net_volume * Decimal("2.4"),  # 2.4 helpers per cum
                rate=helper_rate
            ),
        ]

        material_cost = sum(m.amount for m in materials if m.amount)
        labour_cost = sum(l.amount for l in labour if l.amount)
        unit_rate = (material_cost + labour_cost) / net_volume if net_volume > 0 else Decimal("0")

        return BOQLineItem(
            item_no=item_no,
            description=f"{brick_class} brick masonry {wall_thickness} thick in {mortar_ratio} cement mortar",
            category=WorkCategory.MASONRY,
            specification=f"Brick masonry in {mortar_ratio} cement sand mortar",
            reference_standard="IS 1077, IS 2250, CPWD Specifications",
            unit=UnitType.CUBIC_METER,
            quantity=net_volume,
            unit_rate=unit_rate,
            material_cost=material_cost,
            labour_cost=labour_cost,
            total_amount=net_volume * unit_rate,
            materials=materials,
            labour=labour,
            location=location,
            drawing_reference=drawing_ref,
            remarks=f"L={length}m × H={height}m × T={thickness_m}m"
        )


# Factory function to get appropriate calculator
def get_calculator(category: WorkCategory, dsr_rates: Optional[Dict] = None) -> BaseCalculator:
    """
    Factory function to get calculator for a work category

    Args:
        category: WorkCategory enum
        dsr_rates: Optional DSR rate dictionary

    Returns:
        Appropriate calculator instance
    """
    calculators = {
        WorkCategory.EARTHWORK: EarthworkCalculator,
        WorkCategory.CONCRETE_WORK: ConcreteCalculator,
        WorkCategory.FORMWORK: FormworkCalculator,
        WorkCategory.REINFORCEMENT: ReinforcementCalculator,
        WorkCategory.MASONRY: MasonryCalculator,
    }

    calculator_class = calculators.get(category)
    if calculator_class is None:
        logger.warning(f"No calculator found for {category}, using BaseCalculator")
        return BaseCalculator(dsr_rates)

    return calculator_class(dsr_rates)
