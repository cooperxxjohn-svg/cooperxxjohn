#!/usr/bin/env python3
"""
Sample Drywall Estimates
Demonstrates calculator output for common project types
"""

import json
from backend.drywall_calculator import (
    DrywallCalculator,
    FinishLevel,
    ProjectType,
    StudSpacing
)


def print_estimate(estimate, title):
    """Pretty print an estimate"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)
    print(f"\nRoom: {estimate.room_name}")
    print(f"Dimensions: {estimate.geometry.length}' × {estimate.geometry.width}' × {estimate.geometry.height}'")

    total_sqft = estimate.geometry.wall_sqft + estimate.geometry.ceiling_sqft
    print(f"\nAREA BREAKDOWN:")
    print(f"  Wall area:        {estimate.geometry.wall_sqft:>8.0f} sqft")
    print(f"  Ceiling area:     {estimate.geometry.ceiling_sqft:>8.0f} sqft")
    print(f"  Opening area:     {estimate.geometry.opening_sqft:>8.0f} sqft")
    print(f"  Total gross:      {total_sqft:>8.0f} sqft")

    print(f"\nMATERIALS:")
    print(f"  Drywall sheets:   {estimate.materials.total_sheets:>8} sheets")
    print(f"  Waste factor:     {estimate.materials.sheets_waste:>7.1%}")
    if estimate.materials.studs > 0:
        print(f"  Studs:            {estimate.materials.studs:>8} pieces")
        print(f"  Top track:        {estimate.materials.top_track:>8.0f} LF")
        print(f"  Bottom track:     {estimate.materials.bottom_track:>8.0f} LF")
    print(f"  Joint compound:   {estimate.materials.joint_compound:>8.0f} lbs")
    print(f"  Paper tape:       {estimate.materials.paper_tape:>8.0f} LF")
    print(f"  Corner bead (in): {estimate.materials.corner_bead_inside:>8.0f} LF")
    print(f"  Corner bead (out):{estimate.materials.corner_bead_outside:>8.0f} LF")
    print(f"  Screws:           {estimate.materials.screws:>8} pieces")

    print(f"\nLABOR BREAKDOWN (hours):")
    if estimate.labor.framing > 0:
        print(f"  Framing:          {estimate.labor.framing:>8.1f}")
    print(f"  Hanging:          {estimate.labor.hanging:>8.1f}")
    if estimate.labor.taping_first_coat > 0:
        print(f"  First coat:       {estimate.labor.taping_first_coat:>8.1f}")
    if estimate.labor.taping_second_coat > 0:
        print(f"  Second coat:      {estimate.labor.taping_second_coat:>8.1f}")
    if estimate.labor.taping_third_coat > 0:
        print(f"  Third coat:       {estimate.labor.taping_third_coat:>8.1f}")
    if estimate.labor.skim_coat > 0:
        print(f"  Skim coat:        {estimate.labor.skim_coat:>8.1f}")
    if estimate.labor.corner_bead > 0:
        print(f"  Corner bead:      {estimate.labor.corner_bead:>8.1f}")
    if estimate.labor.sanding > 0:
        print(f"  Sanding:          {estimate.labor.sanding:>8.1f}")
    print(f"  Cleanup:          {estimate.labor.cleanup:>8.1f}")
    print(f"  TOTAL:            {estimate.labor.total:>8.1f} hours")

    print(f"\nCOST BREAKDOWN:")
    print(f"  Drywall sheets:   ${estimate.costs.drywall_sheets:>9.2f}")
    if estimate.costs.framing_materials > 0:
        print(f"  Framing:          ${estimate.costs.framing_materials:>9.2f}")
    print(f"  Joint compound:   ${estimate.costs.joint_compound:>9.2f}")
    print(f"  Tape & bead:      ${estimate.costs.tape_and_bead:>9.2f}")
    print(f"  Fasteners:        ${estimate.costs.fasteners:>9.2f}")
    if estimate.costs.specialty_materials > 0:
        print(f"  Specialty items:  ${estimate.costs.specialty_materials:>9.2f}")
    print(f"  ----------------  -----------")
    print(f"  Total materials:  ${estimate.costs.total_materials:>9.2f}")
    print(f"  Labor cost:       ${estimate.costs.labor_cost:>9.2f}")
    print(f"  ----------------  -----------")
    print(f"  Subtotal:         ${estimate.costs.subtotal:>9.2f}")
    print(f"  Overhead (15%):   ${estimate.costs.overhead:>9.2f}")
    print(f"  Profit (25%):     ${estimate.costs.profit:>9.2f}")
    print(f"  ================  ===========")
    print(f"  TOTAL:            ${estimate.costs.total:>9.2f}")
    print(f"\n  Price per sqft:   ${estimate.price_per_sqft:>9.2f}/sqft")


def sample_1_small_bedroom():
    """Sample 1: Small bedroom - typical residential"""
    calc = DrywallCalculator(labor_rate=65.0)

    room_data = {
        "name": "Small Bedroom",
        "length": 12.0,
        "width": 10.0,
        "height": 8.0,
        "openings": [
            {"width": 3.0, "height": 7.0, "type": "door"},
            {"width": 3.0, "height": 4.0, "type": "window"}
        ],
        "inside_corners": 4,
        "outside_corners": 0,
        "has_ceiling": True
    }

    estimate = calc.estimate_project(room_data)
    print_estimate(estimate, "SAMPLE 1: Small Bedroom (12' × 10' × 8') - Level 3 Finish")


def sample_2_master_suite():
    """Sample 2: Master bedroom suite with vaulted ceiling"""
    calc = DrywallCalculator(labor_rate=70.0)

    room_data = {
        "name": "Master Bedroom Suite",
        "length": 18.0,
        "width": 16.0,
        "height": 9.0,
        "openings": [
            {"width": 3.0, "height": 7.0, "type": "door"},
            {"width": 6.0, "height": 5.0, "type": "window"},
            {"width": 6.0, "height": 5.0, "type": "window"}
        ],
        "inside_corners": 4,
        "outside_corners": 0,
        "has_ceiling": True
    }

    specs = {
        "finish_level": FinishLevel.LEVEL_4,
        "sheet_length": 12.0
    }

    estimate = calc.estimate_project(room_data, specs)
    print_estimate(estimate, "SAMPLE 2: Master Suite (18' × 16' × 9') - Level 4 Finish")


def sample_3_commercial_office():
    """Sample 3: Commercial office space"""
    calc = DrywallCalculator(labor_rate=75.0, overhead_percent=0.18, profit_percent=0.22)

    room_data = {
        "name": "Executive Office",
        "length": 25.0,
        "width": 20.0,
        "height": 10.0,
        "openings": [
            {"width": 3.0, "height": 7.0, "type": "door"},
            {"width": 6.0, "height": 6.0, "type": "window"},
            {"width": 6.0, "height": 6.0, "type": "window"}
        ],
        "inside_corners": 4,
        "outside_corners": 0,
        "has_ceiling": True
    }

    specs = {
        "finish_level": FinishLevel.LEVEL_4,
        "project_type": ProjectType.COMMERCIAL,
        "sheet_thickness": "5/8"
    }

    estimate = calc.estimate_project(room_data, specs)
    print_estimate(estimate, "SAMPLE 3: Commercial Office (25' × 20' × 10') - Level 4 Finish")


def sample_4_high_end():
    """Sample 4: High-end residence with Level 5 finish"""
    calc = DrywallCalculator(labor_rate=85.0, overhead_percent=0.15, profit_percent=0.30)

    room_data = {
        "name": "Luxury Living Room",
        "length": 30.0,
        "width": 22.0,
        "height": 12.0,
        "openings": [
            {"width": 8.0, "height": 8.0, "type": "door"},
            {"width": 10.0, "height": 8.0, "type": "window"},
            {"width": 10.0, "height": 8.0, "type": "window"}
        ],
        "inside_corners": 4,
        "outside_corners": 2,
        "has_ceiling": True,
        "soffits": 2
    }

    specs = {
        "finish_level": FinishLevel.LEVEL_5,
        "sheet_thickness": "5/8",
        "sheet_length": 12.0
    }

    estimate = calc.estimate_project(room_data, specs)
    print_estimate(estimate, "SAMPLE 4: Luxury Living Room (30' × 22' × 12') - Level 5 Finish")


def sample_5_garage():
    """Sample 5: Garage with fire-rated Type X drywall"""
    calc = DrywallCalculator(labor_rate=65.0)

    room_data = {
        "name": "2-Car Garage",
        "length": 24.0,
        "width": 22.0,
        "height": 9.0,
        "openings": [
            {"width": 3.0, "height": 7.0, "type": "door"},
            {"width": 16.0, "height": 7.0, "type": "garage_door"}
        ],
        "inside_corners": 4,
        "outside_corners": 0,
        "has_ceiling": True
    }

    specs = {
        "finish_level": FinishLevel.LEVEL_2,
        "fire_rated": True,
        "sheet_thickness": "5/8"
    }

    estimate = calc.estimate_project(room_data, specs)
    print_estimate(estimate, "SAMPLE 5: Garage (24' × 22' × 9') - Type X Fire-Rated, Level 2")


def sample_6_basement():
    """Sample 6: Basement finishing"""
    calc = DrywallCalculator(labor_rate=65.0)

    room_data = {
        "name": "Basement Recreation Room",
        "length": 28.0,
        "width": 20.0,
        "height": 8.0,
        "openings": [
            {"width": 3.0, "height": 7.0, "type": "door"},
            {"width": 4.0, "height": 3.0, "type": "window"},
            {"width": 4.0, "height": 3.0, "type": "window"}
        ],
        "inside_corners": 4,
        "outside_corners": 0,
        "has_ceiling": True,
        "soffits": 3
    }

    specs = {
        "finish_level": FinishLevel.LEVEL_3,
        "moisture_resistant": True
    }

    estimate = calc.estimate_project(room_data, specs)
    print_estimate(estimate, "SAMPLE 6: Basement Rec Room (28' × 20' × 8') - Moisture-Resistant")


def sample_7_complete_house():
    """Sample 7: Complete 2,000 sqft house estimate"""
    calc = DrywallCalculator(labor_rate=65.0)

    rooms = [
        {
            "name": "Living Room",
            "length": 20.0,
            "width": 16.0,
            "height": 9.0,
            "openings": [
                {"width": 3.0, "height": 7.0, "type": "door"},
                {"width": 6.0, "height": 5.0, "type": "window"},
                {"width": 6.0, "height": 5.0, "type": "window"}
            ],
            "inside_corners": 4,
            "has_ceiling": True
        },
        {
            "name": "Kitchen",
            "length": 16.0,
            "width": 12.0,
            "height": 9.0,
            "openings": [
                {"width": 3.0, "height": 7.0, "type": "door"},
                {"width": 3.0, "height": 5.0, "type": "window"}
            ],
            "inside_corners": 4,
            "has_ceiling": True
        },
        {
            "name": "Dining Room",
            "length": 14.0,
            "width": 12.0,
            "height": 9.0,
            "openings": [
                {"width": 6.0, "height": 5.0, "type": "window"}
            ],
            "inside_corners": 4,
            "has_ceiling": True
        },
        {
            "name": "Master Bedroom",
            "length": 16.0,
            "width": 14.0,
            "height": 8.0,
            "openings": [
                {"width": 3.0, "height": 7.0, "type": "door"},
                {"width": 5.0, "height": 5.0, "type": "window"}
            ],
            "inside_corners": 4,
            "has_ceiling": True
        },
        {
            "name": "Bedroom 2",
            "length": 12.0,
            "width": 11.0,
            "height": 8.0,
            "openings": [
                {"width": 3.0, "height": 7.0, "type": "door"},
                {"width": 3.0, "height": 5.0, "type": "window"}
            ],
            "inside_corners": 4,
            "has_ceiling": True
        },
        {
            "name": "Bedroom 3",
            "length": 12.0,
            "width": 10.0,
            "height": 8.0,
            "openings": [
                {"width": 3.0, "height": 7.0, "type": "door"},
                {"width": 3.0, "height": 5.0, "type": "window"}
            ],
            "inside_corners": 4,
            "has_ceiling": True
        }
    ]

    result = calc.estimate_multi_room_project(rooms)

    print("\n" + "=" * 70)
    print(" SAMPLE 7: Complete 2,000 sqft House - 6 Rooms")
    print("=" * 70)

    print(f"\nPROJECT SUMMARY:")
    print(f"  Total rooms:      {result['totals']['total_rooms']:>8}")
    print(f"  Total sqft:       {result['totals']['total_sqft']:>8.0f} sqft")

    print(f"\nMATERIALS TOTAL:")
    print(f"  Drywall sheets:   {result['totals']['materials']['total_sheets']:>8} sheets")
    print(f"  Joint compound:   {result['totals']['materials']['joint_compound']:>8.0f} lbs")
    print(f"  Paper tape:       {result['totals']['materials']['paper_tape']:>8.0f} LF")
    print(f"  Corner bead (in): {result['totals']['materials']['corner_bead_inside']:>8.0f} LF")
    print(f"  Corner bead (out):{result['totals']['materials']['corner_bead_outside']:>8.0f} LF")
    print(f"  Screws:           {result['totals']['materials']['screws']:>8} pieces")

    print(f"\nLABOR TOTAL:")
    print(f"  Hanging:          {result['totals']['labor']['hanging']:>8.1f} hours")
    print(f"  Finishing:        {result['totals']['labor']['taping_first_coat'] + result['totals']['labor']['taping_second_coat'] + result['totals']['labor']['taping_third_coat']:>8.1f} hours")
    print(f"  Other:            {result['totals']['labor']['corner_bead'] + result['totals']['labor']['sanding'] + result['totals']['labor']['cleanup']:>8.1f} hours")
    print(f"  TOTAL:            {result['totals']['labor']['total']:>8.1f} hours")

    print(f"\nCOST BREAKDOWN:")
    print(f"  Materials:        ${result['totals']['costs']['total_materials']:>9.2f}")
    print(f"  Labor:            ${result['totals']['costs']['labor_cost']:>9.2f}")
    print(f"  ----------------  -----------")
    print(f"  Subtotal:         ${result['totals']['costs']['subtotal']:>9.2f}")
    print(f"  Overhead (15%):   ${result['totals']['costs']['overhead']:>9.2f}")
    print(f"  Profit (25%):     ${result['totals']['costs']['profit']:>9.2f}")
    print(f"  ================  ===========")
    print(f"  TOTAL:            ${result['totals']['costs']['total']:>9.2f}")
    print(f"\n  Price per sqft:   ${result['totals']['price_per_sqft']:>9.2f}/sqft")

    print("\n  INDIVIDUAL ROOMS:")
    for est in result['room_estimates']:
        sqft = est['geometry']['wall_sqft'] + est['geometry']['ceiling_sqft']
        print(f"    {est['room_name']:<20} {sqft:>6.0f} sqft  ${est['costs']['total']:>8.2f}")


def main():
    """Generate all sample estimates"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  DRYWALL CALCULATOR - SAMPLE ESTIMATES".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")

    sample_1_small_bedroom()
    sample_2_master_suite()
    sample_3_commercial_office()
    sample_4_high_end()
    sample_5_garage()
    sample_6_basement()
    sample_7_complete_house()

    print("\n" + "=" * 70)
    print("End of sample estimates")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
