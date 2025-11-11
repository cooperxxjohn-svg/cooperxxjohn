"""
BOQ Mapper - Converts Extracted Drawing Data to BOQ Items
Maps extracted dimensions and materials to structured BOQ line items

This module bridges the gap between raw drawing extraction and
formatted BOQ items ready for estimation.
"""

from typing import List, Dict, Optional
from decimal import Decimal
import logging

from boq_schema import (
    BOQLineItem, BOQSection, WorkCategory, UnitType, MaterialGrade
)
from boq_calculator import (
    get_calculator, EarthworkCalculator, ConcreteCalculator,
    FormworkCalculator, ReinforcementCalculator, MasonryCalculator
)
from drawing_extractor import (
    DrawingExtractionResult, ExtractedDimension, ExtractedMaterial
)

logger = logging.getLogger(__name__)


class BOQMapper:
    """
    Maps extracted drawing data to BOQ line items
    Uses calculators to generate complete BOQ items with rates
    """

    # Mapping of element types to work categories
    ELEMENT_TO_CATEGORY = {
        'foundation': WorkCategory.CONCRETE_WORK,
        'footing': WorkCategory.CONCRETE_WORK,
        'column': WorkCategory.CONCRETE_WORK,
        'beam': WorkCategory.CONCRETE_WORK,
        'slab': WorkCategory.CONCRETE_WORK,
        'wall': WorkCategory.MASONRY,
        'brick wall': WorkCategory.MASONRY,
        'retaining wall': WorkCategory.CONCRETE_WORK,
        'excavation': WorkCategory.EARTHWORK,
        'earthwork': WorkCategory.EARTHWORK,
        'filling': WorkCategory.EARTHWORK,
        'steel': WorkCategory.REINFORCEMENT,
        'reinforcement': WorkCategory.REINFORCEMENT,
        'rebar': WorkCategory.REINFORCEMENT,
    }

    # Default material grades if not specified
    DEFAULT_GRADES = {
        'foundation': MaterialGrade.M20,
        'column': MaterialGrade.M25,
        'beam': MaterialGrade.M25,
        'slab': MaterialGrade.M25,
        'pcc': MaterialGrade.M15,
    }

    def __init__(self, dsr_rates: Optional[Dict] = None):
        """
        Initialize mapper

        Args:
            dsr_rates: Dictionary of standard rates (DSR)
        """
        self.dsr_rates = dsr_rates or {}
        self.item_counter = 1

    def map_extraction_to_boq(
        self,
        extraction_results: List[DrawingExtractionResult],
        project_name: str = "Project"
    ) -> List[BOQSection]:
        """
        Convert extraction results to BOQ sections

        Args:
            extraction_results: List of drawing extraction results
            project_name: Project name for reference

        Returns:
            List of BOQ sections with items
        """
        # Group items by category
        items_by_category: Dict[WorkCategory, List[BOQLineItem]] = {}

        for result in extraction_results:
            logger.info(f"Processing drawing: {result.drawing_name}")

            # Process dimensions
            for dimension in result.dimensions:
                try:
                    items = self._convert_dimension_to_items(dimension, result)
                    for item in items:
                        if item.category not in items_by_category:
                            items_by_category[item.category] = []
                        items_by_category[item.category].append(item)
                except Exception as e:
                    logger.error(f"Failed to convert dimension {dimension.element_type}: {e}")

        # Create sections from categorized items
        sections = []
        section_number = 1

        for category, items in sorted(items_by_category.items(), key=lambda x: x[0].value):
            section = BOQSection(
                section_no=str(section_number),
                title=category.value.replace('_', ' ').title(),
                description=f"{category.value} items from drawings",
                items=items
            )
            sections.append(section)
            section_number += 1

        return sections

    def _convert_dimension_to_items(
        self,
        dimension: ExtractedDimension,
        drawing_result: DrawingExtractionResult
    ) -> List[BOQLineItem]:
        """
        Convert a single extracted dimension to BOQ items

        May generate multiple items (e.g., concrete + formwork + reinforcement for a beam)

        Args:
            dimension: Extracted dimension
            drawing_result: Parent drawing result for context

        Returns:
            List of BOQ items
        """
        items = []
        element_type = dimension.element_type.lower()

        # Determine category
        category = self._get_category(element_type)

        if category == WorkCategory.CONCRETE_WORK:
            # Generate concrete, formwork, and possibly reinforcement items
            items.extend(self._create_concrete_items(dimension, drawing_result))

        elif category == WorkCategory.EARTHWORK:
            items.append(self._create_earthwork_item(dimension, drawing_result))

        elif category == WorkCategory.MASONRY:
            items.append(self._create_masonry_item(dimension, drawing_result))

        elif category == WorkCategory.REINFORCEMENT:
            items.append(self._create_reinforcement_item(dimension, drawing_result))

        else:
            # Generic item
            items.append(self._create_generic_item(dimension, drawing_result, category))

        return items

    def _get_category(self, element_type: str) -> WorkCategory:
        """Determine work category from element type"""
        for key, category in self.ELEMENT_TO_CATEGORY.items():
            if key in element_type:
                return category
        return WorkCategory.MISCELLANEOUS

    def _create_concrete_items(
        self,
        dimension: ExtractedDimension,
        drawing_result: DrawingExtractionResult
    ) -> List[BOQLineItem]:
        """
        Create concrete work items (concrete + formwork)

        Returns list of items for concrete and formwork
        """
        items = []
        element_type = dimension.element_type.lower()

        # Get concrete grade from materials or use default
        grade = self._get_concrete_grade(drawing_result.materials, element_type)

        # Concrete item
        try:
            calc = ConcreteCalculator(self.dsr_rates)
            concrete_item = calc.calculate(
                item_no=self._get_next_item_no(),
                concrete_type=element_type,
                grade=grade,
                length=Decimal(str(dimension.length or 0)),
                width=Decimal(str(dimension.width or 0)),
                thickness=Decimal(str(dimension.thickness or dimension.height or 0)),
                count=dimension.count,
                location=dimension.location,
                drawing_ref=dimension.drawing_reference
            )
            items.append(concrete_item)
        except Exception as e:
            logger.error(f"Failed to create concrete item: {e}")

        # Formwork item
        try:
            formwork_calc = FormworkCalculator(self.dsr_rates)
            formwork_item = formwork_calc.calculate(
                item_no=self._get_next_item_no(),
                element_type=element_type,
                length=Decimal(str(dimension.length or 0)),
                width=Decimal(str(dimension.width or 0)),
                height=Decimal(str(dimension.thickness or dimension.height or 0)),
                count=dimension.count,
                location=dimension.location,
                drawing_ref=dimension.drawing_reference
            )
            items.append(formwork_item)
        except Exception as e:
            logger.error(f"Failed to create formwork item: {e}")

        return items

    def _create_earthwork_item(
        self,
        dimension: ExtractedDimension,
        drawing_result: DrawingExtractionResult
    ) -> BOQLineItem:
        """Create earthwork item"""
        calc = EarthworkCalculator(self.dsr_rates)

        # Determine earthwork type from element description
        work_type = 'excavation_ordinary_soil'
        if 'hard' in dimension.element_type.lower():
            work_type = 'excavation_hard_soil'
        elif 'fill' in dimension.element_type.lower():
            work_type = 'filling'

        return calc.calculate(
            item_no=self._get_next_item_no(),
            work_type=work_type,
            length=Decimal(str(dimension.length or 0)),
            width=Decimal(str(dimension.width or 0)),
            depth=Decimal(str(dimension.height or dimension.thickness or 0)),
            location=dimension.location,
            drawing_ref=dimension.drawing_reference
        )

    def _create_masonry_item(
        self,
        dimension: ExtractedDimension,
        drawing_result: DrawingExtractionResult
    ) -> BOQLineItem:
        """Create masonry item"""
        calc = MasonryCalculator(self.dsr_rates)

        # Determine wall thickness
        thickness_mm = int((dimension.thickness or 0.230) * 1000)
        wall_thickness = f"{thickness_mm}mm"
        if wall_thickness not in ['115mm', '230mm', '345mm']:
            wall_thickness = '230mm'  # Default

        return calc.calculate(
            item_no=self._get_next_item_no(),
            wall_thickness=wall_thickness,
            mortar_ratio='1:6',
            length=Decimal(str(dimension.length or 0)),
            height=Decimal(str(dimension.height or 0)),
            location=dimension.location,
            drawing_ref=dimension.drawing_reference
        )

    def _create_reinforcement_item(
        self,
        dimension: ExtractedDimension,
        drawing_result: DrawingExtractionResult
    ) -> BOQLineItem:
        """Create reinforcement item"""
        calc = ReinforcementCalculator(self.dsr_rates)

        # Extract bar diameter (default 12mm if not specified)
        bar_diameter = int(dimension.diameter * 1000) if dimension.diameter else 12

        # Ensure valid bar diameter
        if bar_diameter not in [8, 10, 12, 16, 20, 25, 32]:
            bar_diameter = 12

        return calc.calculate(
            item_no=self._get_next_item_no(),
            bar_diameter=bar_diameter,
            length_per_bar=Decimal(str(dimension.length or 0)),
            number_of_bars=dimension.count,
            location=dimension.location,
            drawing_ref=dimension.drawing_reference
        )

    def _create_generic_item(
        self,
        dimension: ExtractedDimension,
        drawing_result: DrawingExtractionResult,
        category: WorkCategory
    ) -> BOQLineItem:
        """Create generic item when no specific calculator available"""

        # Calculate quantity based on available dimensions
        if dimension.length and dimension.width and dimension.height:
            quantity = Decimal(str(dimension.length * dimension.width * dimension.height * dimension.count))
            unit = UnitType.CUBIC_METER
        elif dimension.length and dimension.width:
            quantity = Decimal(str(dimension.length * dimension.width * dimension.count))
            unit = UnitType.SQUARE_METER
        elif dimension.length:
            quantity = Decimal(str(dimension.length * dimension.count))
            unit = UnitType.METER
        else:
            quantity = Decimal(str(dimension.count))
            unit = UnitType.NUMBER

        return BOQLineItem(
            item_no=self._get_next_item_no(),
            description=f"{dimension.element_type}",
            category=category,
            specification=dimension.remarks or f"{dimension.element_type} as per drawing",
            unit=unit,
            quantity=quantity,
            unit_rate=Decimal("100"),  # Placeholder rate
            total_amount=quantity * Decimal("100"),
            location=dimension.location,
            drawing_reference=dimension.drawing_reference,
            remarks=dimension.remarks
        )

    def _get_concrete_grade(
        self,
        materials: List[ExtractedMaterial],
        element_type: str
    ) -> MaterialGrade:
        """
        Get concrete grade from extracted materials or use default

        Args:
            materials: List of extracted materials
            element_type: Type of element

        Returns:
            MaterialGrade
        """
        # Look for concrete grade in materials
        for material in materials:
            if material.material_type.lower() == 'concrete' and material.grade:
                grade_str = material.grade.upper()
                try:
                    return MaterialGrade[grade_str]
                except KeyError:
                    pass

        # Use default grade based on element type
        for key, grade in self.DEFAULT_GRADES.items():
            if key in element_type:
                return grade

        # Default fallback
        return MaterialGrade.M20

    def _get_next_item_no(self) -> str:
        """Get next sequential item number"""
        item_no = f"{self.item_counter}"
        self.item_counter += 1
        return item_no

    def reset_item_counter(self):
        """Reset item counter to 1"""
        self.item_counter = 1


class BOQAutoNumberer:
    """
    Renumbers BOQ items in a structured format (1.1, 1.2, 2.1, etc.)
    """

    @staticmethod
    def renumber_sections(sections: List[BOQSection]) -> List[BOQSection]:
        """
        Renumber all sections and items in hierarchical format

        Args:
            sections: List of BOQ sections

        Returns:
            Renumbered sections
        """
        for section_idx, section in enumerate(sections, start=1):
            section.section_no = str(section_idx)

            for item_idx, item in enumerate(section.items, start=1):
                item.item_no = f"{section_idx}.{item_idx}"

        return sections


def merge_similar_items(items: List[BOQLineItem], tolerance: Decimal = Decimal("0.01")) -> List[BOQLineItem]:
    """
    Merge similar BOQ items to reduce duplication

    Args:
        items: List of BOQ items
        tolerance: Tolerance for considering items similar (rate difference)

    Returns:
        Merged list of items
    """
    merged = []
    processed = set()

    for i, item1 in enumerate(items):
        if i in processed:
            continue

        # Start with current item
        merged_item = item1
        merged_qty = item1.quantity

        # Look for similar items
        for j, item2 in enumerate(items[i+1:], start=i+1):
            if j in processed:
                continue

            # Check if items are similar
            if (item1.category == item2.category and
                item1.unit == item2.unit and
                item1.description == item2.description and
                abs(item1.unit_rate - item2.unit_rate) <= tolerance):

                # Merge quantities
                merged_qty += item2.quantity
                processed.add(j)

        # Update merged item
        merged_item.quantity = merged_qty
        merged_item.total_amount = merged_qty * merged_item.unit_rate

        if len(processed) > 0:
            merged_item.remarks = f"{merged_item.remarks} (merged {len(processed)} similar items)" if merged_item.remarks else f"Merged {len(processed)} similar items"

        merged.append(merged_item)
        processed.add(i)

    logger.info(f"Merged {len(items)} items into {len(merged)} items")
    return merged
