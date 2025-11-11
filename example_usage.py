"""
Example Usage of BOQ Estimation System
Demonstrates different use cases and workflows
"""

import os
from decimal import Decimal
from pathlib import Path

from boq_estimator import BOQEstimator, quick_estimate
from boq_schema import (
    ContractDetails, BOQDocument, WorkCategory,
    UnitType, MaterialGrade
)
from boq_calculator import (
    ConcreteCalculator, EarthworkCalculator,
    FormworkCalculator, MasonryCalculator
)
from boq_validator import CPWDValidator


def example_1_complete_workflow():
    """
    Example 1: Complete workflow from drawings to BOQ
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Complete Workflow - Drawings to BOQ")
    print("=" * 80)

    # Get API key from environment
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("⚠ Set ANTHROPIC_API_KEY environment variable")
        print("Example: export ANTHROPIC_API_KEY='your-key-here'")
        return

    # Define contract details
    contract = ContractDetails(
        contract_name="Government Office Building - Phase 1",
        contract_no="CPWD/2024/001",
        location="Connaught Place, New Delhi",
        client="Ministry of Public Works",
        department="CPWD",
        completion_period_days=365
    )

    # Initialize estimator
    estimator = BOQEstimator(
        anthropic_api_key=api_key,
        enable_logging=True
    )

    # Process drawings (replace with actual paths)
    drawing_files = [
        "path/to/foundation_plan.pdf",
        "path/to/floor_plan.pdf",
        "path/to/sections.pdf"
    ]

    # Check if files exist
    existing_files = [f for f in drawing_files if Path(f).exists()]

    if not existing_files:
        print("⚠ No drawing files found. Using simulated workflow...")
        example_2_manual_boq_creation()
        return

    # Generate BOQ
    boq = estimator.estimate_from_drawings(
        drawing_paths=existing_files,
        contract_details=contract,
        output_dir="./boq_output",
        merge_duplicates=True,
        validate=True
    )

    # Export to Excel
    estimator.export_to_excel(boq, "./boq_output/boq_final.xlsx")

    print(f"\n✓ BOQ Generated: {boq.boq_id}")
    print(f"  Total Amount: ₹{boq.total_amount:,.2f}")
    print(f"  Total Sections: {len(boq.sections)}")
    print(f"  Total Items: {sum(len(s.items) for s in boq.sections)}")


def example_2_manual_boq_creation():
    """
    Example 2: Manual BOQ creation using calculators
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Manual BOQ Creation Using Calculators")
    print("=" * 80)

    # Sample DSR rates
    dsr_rates = {
        'CEMENT_OPC43': Decimal("7.50"),
        'SAND': Decimal("1200"),
        'AGGREGATE_20MM': Decimal("1400"),
        'WATER': Decimal("0.05"),
        'LABOUR_MASON': Decimal("850"),
        'LABOUR_HELPER': Decimal("600"),
    }

    # 1. Create earthwork item
    print("\n1. Creating Earthwork Item...")
    earthwork_calc = EarthworkCalculator(dsr_rates)
    excavation_item = earthwork_calc.calculate(
        item_no="1.1",
        work_type='excavation_ordinary_soil',
        length=Decimal("20.0"),
        width=Decimal("15.0"),
        depth=Decimal("2.5"),
        location="Foundation - Grid A1 to A4",
        drawing_ref="DWG-F-001"
    )
    print(f"   ✓ {excavation_item.description}")
    print(f"     Quantity: {excavation_item.quantity} {excavation_item.unit.value}")
    print(f"     Amount: ₹{excavation_item.total_amount:,.2f}")

    # 2. Create concrete item
    print("\n2. Creating Concrete Item...")
    concrete_calc = ConcreteCalculator(dsr_rates)
    foundation_item = concrete_calc.calculate(
        item_no="2.1",
        concrete_type="foundation",
        grade=MaterialGrade.M20,
        length=Decimal("20.0"),
        width=Decimal("15.0"),
        thickness=Decimal("0.3"),
        location="Foundation - Grid A1 to A4",
        drawing_ref="DWG-F-001"
    )
    print(f"   ✓ {foundation_item.description}")
    print(f"     Quantity: {foundation_item.quantity} {foundation_item.unit.value}")
    print(f"     Amount: ₹{foundation_item.total_amount:,.2f}")
    print(f"     Material Cost: ₹{foundation_item.material_cost:,.2f}")
    print(f"     Labour Cost: ₹{foundation_item.labour_cost:,.2f}")

    # 3. Create formwork item
    print("\n3. Creating Formwork Item...")
    formwork_calc = FormworkCalculator(dsr_rates)
    formwork_item = formwork_calc.calculate(
        item_no="2.2",
        element_type="foundation",
        length=Decimal("20.0"),
        width=Decimal("15.0"),
        height=Decimal("0.3"),
        location="Foundation - Grid A1 to A4",
        drawing_ref="DWG-F-001"
    )
    print(f"   ✓ {formwork_item.description}")
    print(f"     Quantity: {formwork_item.quantity} {formwork_item.unit.value}")
    print(f"     Amount: ₹{formwork_item.total_amount:,.2f}")

    # 4. Create masonry item
    print("\n4. Creating Masonry Item...")
    masonry_calc = MasonryCalculator(dsr_rates)
    wall_item = masonry_calc.calculate(
        item_no="3.1",
        wall_thickness="230mm",
        mortar_ratio="1:6",
        length=Decimal("50.0"),
        height=Decimal("3.5"),
        deductions=Decimal("5.0"),  # Openings
        location="External Wall - North Elevation",
        drawing_ref="DWG-A-002"
    )
    print(f"   ✓ {wall_item.description}")
    print(f"     Quantity: {wall_item.quantity} {wall_item.unit.value}")
    print(f"     Amount: ₹{wall_item.total_amount:,.2f}")

    print("\n" + "-" * 80)
    total = (excavation_item.total_amount + foundation_item.total_amount +
             formwork_item.total_amount + wall_item.total_amount)
    print(f"Total Estimated Cost: ₹{total:,.2f}")
    print("=" * 80)


def example_3_validation():
    """
    Example 3: BOQ Validation
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: BOQ Validation Against CPWD Standards")
    print("=" * 80)

    from boq_schema import BOQLineItem, BOQSection, Material, Labour

    # Create a sample BOQ item with potential issues
    test_item = BOQLineItem(
        item_no="1.1",
        description="Test concrete work",
        category=WorkCategory.CONCRETE_WORK,
        specification="M20 concrete",
        reference_standard="IS 456:2000",
        unit=UnitType.CUBIC_METER,
        quantity=Decimal("100.0"),
        unit_rate=Decimal("5000.0"),
        total_amount=Decimal("500000.0"),
        overhead_percentage=Decimal("25.0"),  # Too high!
        profit_percentage=Decimal("15.0"),  # Too high!
        materials=[
            Material(
                name="Cement",
                specification="OPC 43",
                unit=UnitType.KILOGRAM,
                quantity=Decimal("30000"),
                rate=Decimal("7.5"),
                wastage_percentage=Decimal("25.0")  # Too high!
            )
        ],
        labour=[
            Labour(
                category="Mason",
                unit=UnitType.NUMBER,
                quantity=Decimal("100"),
                rate=Decimal("850")
            )
        ]
    )

    section = BOQSection(
        section_no="1",
        title="Concrete Work",
        items=[test_item]
    )

    contract = ContractDetails(
        contract_name="Test Project",
        location="Delhi",
        client="Test Client",
        department="CPWD"
    )

    boq = BOQDocument(
        boq_id="TEST-001",
        contract=contract,
        sections=[section],
        gst_percentage=Decimal("18.0")
    )

    # Validate
    print("\nValidating BOQ...")
    validator = CPWDValidator()
    is_valid, results = validator.validate_document(boq)

    validator.print_validation_report()

    if is_valid:
        print("\n✓ BOQ is valid and compliant!")
    else:
        print("\n⚠ BOQ has validation issues that need attention")


def example_4_quick_estimate():
    """
    Example 4: Quick estimate using convenience function
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Quick Estimate")
    print("=" * 80)

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("⚠ Set ANTHROPIC_API_KEY environment variable")
        return

    # Quick estimate with minimal setup
    boq = quick_estimate(
        drawing_paths=["drawing1.pdf", "drawing2.pdf"],
        project_name="Quick Project Estimate",
        location="Mumbai",
        anthropic_api_key=api_key,
        output_dir="./quick_estimate_output"
    )

    print(f"\n✓ Quick estimate completed!")
    print(f"  BOQ ID: {boq.boq_id}")
    print(f"  Total: ₹{boq.total_amount:,.2f}")


def example_5_custom_rates():
    """
    Example 5: Using custom DSR rates
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Custom DSR Rates")
    print("=" * 80)

    # Define custom rates (e.g., for a specific location or year)
    custom_rates = {
        # Labour rates for Delhi region 2024
        'LABOUR_UNSKILLED': Decimal("650"),
        'LABOUR_SKILLED': Decimal("850"),
        'LABOUR_MASON': Decimal("900"),
        'LABOUR_HELPER': Decimal("650"),
        'LABOUR_CARPENTER': Decimal("950"),
        'LABOUR_BARBENDER': Decimal("900"),

        # Material rates - Delhi 2024
        'CEMENT_OPC43': Decimal("8.00"),  # Increased
        'SAND': Decimal("1350"),
        'AGGREGATE_20MM': Decimal("1500"),
        'BRICK_FIRST_CLASS': Decimal("6.50"),
        'STEEL_FE500': Decimal("70"),  # Increased
        'PLYWOOD_12MM': Decimal("2000"),
    }

    # Use custom rates with calculator
    concrete_calc = ConcreteCalculator(custom_rates)

    column_item = concrete_calc.calculate(
        item_no="1.1",
        concrete_type="column",
        grade=MaterialGrade.M25,
        length=Decimal("0.3"),
        width=Decimal("0.45"),
        thickness=Decimal("3.5"),
        count=4,
        location="Columns C1-C4",
        drawing_ref="DWG-S-001"
    )

    print(f"\n✓ {column_item.description}")
    print(f"  Quantity: {column_item.quantity} {column_item.unit.value}")
    print(f"  Unit Rate: ₹{column_item.unit_rate:,.2f}")
    print(f"  Total: ₹{column_item.total_amount:,.2f}")
    print(f"\n  Material Breakdown:")
    for material in column_item.materials:
        print(f"    - {material.name}: {material.quantity} {material.unit.value} @ ₹{material.rate} = ₹{material.amount:,.2f}")


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("BOQ ESTIMATION SYSTEM - EXAMPLES")
    print("=" * 80)
    print("\nThese examples demonstrate various features of the BOQ estimation system.")
    print("Modify the examples to match your specific requirements.")

    # Run examples
    example_2_manual_boq_creation()
    example_3_validation()
    example_5_custom_rates()

    # These require actual files or API key
    # example_1_complete_workflow()
    # example_4_quick_estimate()

    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
