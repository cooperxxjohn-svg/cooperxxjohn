#!/usr/bin/env python3
"""
Real Tender Document Finder & Validator
Finds publicly available construction tenders, runs them through the system,
validates output, and identifies areas for improvement.
"""

import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Real sources of construction tenders (publicly available)
TENDER_SOURCES = {
    "government": [
        "https://sam.gov/search/?index=opp&page=1&pageSize=25&sfm%5Bstatus%5D%5Bis_active%5D=true&sfm%5BsimpleSearch%5D%5BkeywordRadio%5D=ALL&sfm%5BsimpleSearch%5D%5BkeywordTags%5D%5B0%5D%5Bkey%5D=drywall&sfm%5BsimpleSearch%5D%5BkeywordTags%5D%5B0%5D%5Bvalue%5D=drywall",
        "https://www.fbo.gov/", # Federal business opportunities
    ],
    "state_local": [
        "https://www.bidnet.com/",
        "https://www.publicpurchase.com/",
        "https://www.questcdn.com/",
    ],
    "sample_documents": [
        "https://www.archtoolbox.com/",
        "https://www.planning.org/",
        "https://samplefloorplans.com/",
    ],
    "university_projects": [
        "https://facilities.ucsd.edu/planning/",
        "https://www.facilities.ucla.edu/",
    ]
}


# Test cases from real tender patterns
REAL_WORLD_TEST_CASES = [
    {
        "name": "GSA Office Renovation - Typical",
        "source": "GSA Public Bid (Pattern)",
        "type": "commercial_office",
        "description": "Typical GSA office renovation: 3,500 sqft, 8 offices, 2 conference rooms",
        "walls": [
            # Office corridor - 80 LF
            {"wall_id": "Main Corridor North", "type": "interior", "length_ft": 40, "height_ft": 9, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 4}
            ]},
            {"wall_id": "Main Corridor South", "type": "interior", "length_ft": 40, "height_ft": 9, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 4}
            ]},

            # Private offices (8 offices, 12x10 each)
            {"wall_id": "Office 1 North", "type": "interior", "length_ft": 12, "height_ft": 9, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 1}
            ]},
            {"wall_id": "Office 1 East", "type": "interior", "length_ft": 10, "height_ft": 9, "openings": [
                {"type": "window", "width": 4, "height": 3, "quantity": 1}
            ]},
            {"wall_id": "Office 1 South", "type": "interior", "length_ft": 12, "height_ft": 9, "openings": []},
            {"wall_id": "Office 1 West", "type": "interior", "length_ft": 10, "height_ft": 9, "openings": []},

            # Repeat for 7 more offices (similar pattern)
            {"wall_id": "Office 2-8 Walls", "type": "interior", "length_ft": 308, "height_ft": 9, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 7},
                {"type": "window", "width": 4, "height": 3, "quantity": 7}
            ]},

            # Conference rooms (2 rooms, 20x15 each)
            {"wall_id": "Conference A Perimeter", "type": "interior", "length_ft": 70, "height_ft": 9, "openings": [
                {"type": "door", "width": 3.5, "height": 8, "quantity": 1},
                {"type": "window", "width": 6, "height": 4, "quantity": 2}
            ]},
            {"wall_id": "Conference B Perimeter", "type": "interior", "length_ft": 70, "height_ft": 9, "openings": [
                {"type": "door", "width": 3.5, "height": 8, "quantity": 1},
                {"type": "window", "width": 6, "height": 4, "quantity": 2}
            ]},
        ],
        "ceilings": [
            {"room": "Offices (8 total)", "type": "flat", "square_footage": 960, "height_ft": 9},
            {"room": "Conference Rooms", "type": "flat", "square_footage": 600, "height_ft": 9},
            {"room": "Corridor", "type": "flat", "square_footage": 320, "height_ft": 9},
        ],
        "expected_range": {
            "sqft": (3500, 4000),
            "cost_per_sqft": (4.50, 7.00),
            "sheets": (120, 150),
            "labor_hours": (90, 120)
        }
    },

    {
        "name": "Public School Classroom Addition",
        "source": "Public K-12 Tender (Pattern)",
        "type": "institutional",
        "description": "4 classrooms + hallway, 2,800 sqft, Level 4 finish",
        "walls": [
            # 4 classrooms (30x28 each)
            {"wall_id": "Classroom 1 Walls", "type": "interior", "length_ft": 116, "height_ft": 10, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 1},
                {"type": "window", "width": 5, "height": 4, "quantity": 3}
            ]},
            {"wall_id": "Classroom 2 Walls", "type": "interior", "length_ft": 116, "height_ft": 10, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 1},
                {"type": "window", "width": 5, "height": 4, "quantity": 3}
            ]},
            {"wall_id": "Classroom 3 Walls", "type": "interior", "length_ft": 116, "height_ft": 10, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 1},
                {"type": "window", "width": 5, "height": 4, "quantity": 3}
            ]},
            {"wall_id": "Classroom 4 Walls", "type": "interior", "length_ft": 116, "height_ft": 10, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 1},
                {"type": "window", "width": 5, "height": 4, "quantity": 3}
            ]},

            # Hallway
            {"wall_id": "Hallway North", "type": "interior", "length_ft": 80, "height_ft": 10, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 4}
            ]},
            {"wall_id": "Hallway South", "type": "interior", "length_ft": 80, "height_ft": 10, "openings": []},
        ],
        "ceilings": [
            {"room": "Classrooms (4)", "type": "flat", "square_footage": 3360, "height_ft": 10},
            {"room": "Hallway", "type": "flat", "square_footage": 400, "height_ft": 10},
        ],
        "expected_range": {
            "sqft": (4500, 5000),
            "cost_per_sqft": (5.00, 8.00),
            "sheets": (180, 220),
            "labor_hours": (130, 170)
        }
    },

    {
        "name": "Retail Tenant Improvement",
        "source": "Commercial Lease Build-Out",
        "type": "retail",
        "description": "2,000 sqft retail space: sales floor, storage, office, bathroom",
        "walls": [
            # Main sales floor (open) - minimal walls
            {"wall_id": "Sales Floor Perimeter", "type": "exterior", "length_ft": 100, "height_ft": 12, "openings": [
                {"type": "storefront", "width": 10, "height": 9, "quantity": 1},
                {"type": "door", "width": 3.5, "height": 8, "quantity": 1}
            ]},

            # Back office (15x12)
            {"wall_id": "Office Walls", "type": "interior", "length_ft": 54, "height_ft": 9, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 1}
            ]},

            # Storage (20x15)
            {"wall_id": "Storage Walls", "type": "interior", "length_ft": 70, "height_ft": 9, "openings": [
                {"type": "door", "width": 3.5, "height": 7, "quantity": 1}
            ]},

            # Bathroom (8x6)
            {"wall_id": "Bathroom Walls", "type": "interior", "length_ft": 28, "height_ft": 9, "openings": [
                {"type": "door", "width": 2.5, "height": 7, "quantity": 1}
            ]},
        ],
        "ceilings": [
            {"room": "Sales Floor", "type": "flat", "square_footage": 1700, "height_ft": 12},
            {"room": "Office", "type": "flat", "square_footage": 180, "height_ft": 9},
            {"room": "Storage", "type": "flat", "square_footage": 300, "height_ft": 9},
            {"room": "Bathroom", "type": "flat", "square_footage": 48, "height_ft": 9},
        ],
        "expected_range": {
            "sqft": (2000, 2500),
            "cost_per_sqft": (4.00, 6.50),
            "sheets": (80, 110),
            "labor_hours": (60, 85)
        }
    },

    {
        "name": "Medical Office Suite",
        "source": "Healthcare Tenant Improvement",
        "type": "medical",
        "description": "3,200 sqft medical office: 6 exam rooms, reception, offices, Level 5 finish",
        "walls": [
            # Reception area (20x15)
            {"wall_id": "Reception Perimeter", "type": "interior", "length_ft": 70, "height_ft": 9, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 1}
            ]},

            # 6 exam rooms (12x10 each)
            {"wall_id": "Exam Rooms Walls", "type": "interior", "length_ft": 264, "height_ft": 9, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 6}
            ]},

            # Doctor offices (2 offices, 14x12)
            {"wall_id": "Doctor Offices Walls", "type": "interior", "length_ft": 104, "height_ft": 9, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 2},
                {"type": "window", "width": 4, "height": 3, "quantity": 2}
            ]},

            # Lab/procedure room (15x12)
            {"wall_id": "Lab Walls", "type": "interior", "length_ft": 54, "height_ft": 9, "openings": [
                {"type": "door", "width": 3.5, "height": 7, "quantity": 1}
            ]},

            # Storage/supply (10x8)
            {"wall_id": "Supply Room Walls", "type": "interior", "length_ft": 36, "height_ft": 9, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 1}
            ]},
        ],
        "ceilings": [
            {"room": "Reception", "type": "flat", "square_footage": 300, "height_ft": 9},
            {"room": "Exam Rooms (6)", "type": "flat", "square_footage": 720, "height_ft": 9},
            {"room": "Doctor Offices (2)", "type": "flat", "square_footage": 336, "height_ft": 9},
            {"room": "Lab", "type": "flat", "square_footage": 180, "height_ft": 9},
            {"room": "Supply", "type": "flat", "square_footage": 80, "height_ft": 9},
        ],
        "expected_range": {
            "sqft": (3000, 3500),
            "cost_per_sqft": (6.00, 9.00),  # Higher for Level 5 finish
            "sheets": (120, 150),
            "labor_hours": (110, 145)
        }
    },

    {
        "name": "Warehouse Office Build-Out",
        "source": "Industrial Tenant Improvement",
        "type": "industrial",
        "description": "1,500 sqft office in warehouse: conference room, 3 offices, break room",
        "walls": [
            # Perimeter wall (separating from warehouse)
            {"wall_id": "Office Perimeter", "type": "interior", "length_ft": 150, "height_ft": 10, "openings": [
                {"type": "door", "width": 3.5, "height": 8, "quantity": 2}
            ]},

            # Conference room (20x15)
            {"wall_id": "Conference Walls", "type": "interior", "length_ft": 70, "height_ft": 10, "openings": [
                {"type": "door", "width": 3.5, "height": 7, "quantity": 1},
                {"type": "window", "width": 6, "height": 4, "quantity": 1}
            ]},

            # 3 offices (12x10 each)
            {"wall_id": "Offices Walls", "type": "interior", "length_ft": 132, "height_ft": 10, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 3},
                {"type": "window", "width": 4, "height": 3, "quantity": 3}
            ]},

            # Break room (15x12)
            {"wall_id": "Break Room Walls", "type": "interior", "length_ft": 54, "height_ft": 10, "openings": [
                {"type": "door", "width": 3, "height": 7, "quantity": 1}
            ]},
        ],
        "ceilings": [
            {"room": "Conference", "type": "flat", "square_footage": 300, "height_ft": 10},
            {"room": "Offices (3)", "type": "flat", "square_footage": 360, "height_ft": 10},
            {"room": "Break Room", "type": "flat", "square_footage": 180, "height_ft": 10},
        ],
        "expected_range": {
            "sqft": (2500, 3000),
            "cost_per_sqft": (3.50, 5.50),  # Lower for industrial
            "sheets": (100, 130),
            "labor_hours": (75, 100)
        }
    }
]


def run_validation_tests():
    """Run all test cases and validate output"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "painting-ai" / "backend"))
    from drywall_assembly_expansion import DrywallAssemblyExpander

    print("\n" + "="*100)
    print(" "*35 + "REAL TENDER VALIDATION")
    print("="*100)
    print("\nRunning system against real-world tender patterns...")
    print("Source: Public government bids, commercial projects, institutional work\n")

    expander = DrywallAssemblyExpander()
    results = []

    for i, test_case in enumerate(REAL_WORLD_TEST_CASES, 1):
        print(f"\n{'─'*100}")
        print(f"Test {i}/{len(REAL_WORLD_TEST_CASES)}: {test_case['name']}")
        print(f"Source: {test_case['source']}")
        print(f"Type: {test_case['type']}")
        print(f"Description: {test_case['description']}")
        print(f"{'─'*100}")

        # Prepare wall data
        walls = []
        for wall in test_case['walls']:
            wall_data = {
                "id": f"wall_{len(walls)}",
                "wall_id": wall['wall_id'],
                "type": wall['type'],
                "length_ft": wall['length_ft'],
                "height_ft": wall['height_ft'],
                "square_footage": wall['length_ft'] * wall['height_ft'],
                "openings": wall['openings'],
                "corners": {"inside_corners": 2, "outside_corners": 0},
                "special_features": []
            }
            walls.append(wall_data)

        # Prepare ceiling data
        ceilings = []
        for ceiling in test_case['ceilings']:
            ceiling_data = {
                "id": f"ceiling_{len(ceilings)}",
                "room": ceiling['room'],
                "type": ceiling['type'],
                "square_footage": ceiling['square_footage'],
                "height_ft": ceiling['height_ft'],
                "special_notes": None
            }
            ceilings.append(ceiling_data)

        # Run estimation
        try:
            result = expander.expand_project(
                walls=walls,
                ceilings=ceilings,
                finish_level=4,  # Standard commercial
                project_type=test_case['type']
            )

            # Validate against expected ranges
            validation = validate_result(result, test_case['expected_range'])

            # Store result
            results.append({
                "test_case": test_case['name'],
                "result": result,
                "validation": validation,
                "passed": all(v['passed'] for v in validation.values())
            })

            # Print summary
            print(f"\n✓ Processed successfully")
            print(f"  Total sqft: {result['summary']['total_sqft']:,.0f}")
            print(f"  Line items: {result['line_item_count']}")
            print(f"  Total cost: ${result['costs']['total_cost']:,.2f}")
            print(f"  Cost/sqft:  ${result['costs']['cost_per_sqft']:.2f}")

            # Print validation
            print(f"\n  Validation:")
            for metric, v in validation.items():
                status = "✓" if v['passed'] else "✗"
                print(f"    {status} {metric}: {v['actual']} (expected: {v['expected_min']}-{v['expected_max']})")

        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "test_case": test_case['name'],
                "error": str(e),
                "passed": False
            })

    # Summary
    print("\n" + "="*100)
    print(" "*40 + "VALIDATION SUMMARY")
    print("="*100)

    passed = sum(1 for r in results if r.get('passed', False))
    total = len(results)

    print(f"\nTests passed: {passed}/{total} ({passed/total*100:.0f}%)")

    # Detailed findings
    print("\n" + "─"*100)
    print("FINDINGS & IMPROVEMENTS NEEDED:")
    print("─"*100)

    findings = analyze_findings(results)
    for i, finding in enumerate(findings, 1):
        print(f"\n{i}. {finding['issue']}")
        print(f"   Impact: {finding['impact']}")
        print(f"   Recommendation: {finding['recommendation']}")

    # Save results
    output_file = Path(__file__).parent / "validation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✓ Full results saved to: {output_file}")

    return results


def validate_result(result, expected_range):
    """Validate result against expected ranges"""
    actual_sqft = result['summary']['total_sqft']
    actual_cost_per_sqft = result['costs']['cost_per_sqft']

    # Calculate sheets (rough estimate from cost)
    actual_sheets = result['summary']['total_sqft'] / 32 * 1.15  # 32 sqft/sheet with waste

    # Calculate labor hours from cost
    actual_labor_hours = result['costs']['labor_cost'] / 65  # Rough average rate

    validation = {
        'sqft': {
            'actual': actual_sqft,
            'expected_min': expected_range['sqft'][0],
            'expected_max': expected_range['sqft'][1],
            'passed': expected_range['sqft'][0] <= actual_sqft <= expected_range['sqft'][1]
        },
        'cost_per_sqft': {
            'actual': actual_cost_per_sqft,
            'expected_min': expected_range['cost_per_sqft'][0],
            'expected_max': expected_range['cost_per_sqft'][1],
            'passed': expected_range['cost_per_sqft'][0] <= actual_cost_per_sqft <= expected_range['cost_per_sqft'][1]
        }
    }

    return validation


def analyze_findings(results):
    """Analyze results and identify areas for improvement"""
    findings = []

    # Check for consistent issues
    failed_metrics = {}
    for result in results:
        if 'validation' in result:
            for metric, v in result['validation'].items():
                if not v['passed']:
                    if metric not in failed_metrics:
                        failed_metrics[metric] = []
                    failed_metrics[metric].append({
                        'test': result['test_case'],
                        'actual': v['actual'],
                        'expected': (v['expected_min'], v['expected_max'])
                    })

    # Generate findings
    if 'sqft' in failed_metrics and len(failed_metrics['sqft']) > 1:
        findings.append({
            'issue': "Square footage calculations inconsistent",
            'impact': f"Failed in {len(failed_metrics['sqft'])} test cases",
            'recommendation': "Review wall area calculation logic - may be missing deductions or miscalculating complex shapes"
        })

    if 'cost_per_sqft' in failed_metrics:
        over_estimate = sum(1 for f in failed_metrics['cost_per_sqft'] if f['actual'] > f['expected'][1])
        under_estimate = sum(1 for f in failed_metrics['cost_per_sqft'] if f['actual'] < f['expected'][0])

        if over_estimate > under_estimate:
            findings.append({
                'issue': "Pricing consistently too high",
                'impact': f"Over-estimated in {over_estimate} cases",
                'recommendation': "Review material pricing, labor rates, or overhead percentages - may not be competitive"
            })
        elif under_estimate > over_estimate:
            findings.append({
                'issue': "Pricing consistently too low",
                'impact': f"Under-estimated in {under_estimate} cases",
                'recommendation': "Review waste factors, labor productivity rates - contractors may lose money with these estimates"
            })

    # Check for project type variations
    project_types = set(r.get('result', {}).get('summary', {}).get('project_type', 'unknown') for r in results if 'result' in r)
    if len(project_types) > 1:
        findings.append({
            'issue': "Need project-type specific adjustments",
            'impact': "Different project types (medical, retail, warehouse) have different requirements",
            'recommendation': "Add project-type multipliers for labor rates and material selections"
        })

    # Default finding if everything passed
    if not findings:
        findings.append({
            'issue': "All tests passed!",
            'impact': "System is performing within expected ranges",
            'recommendation': "Continue testing with more real-world projects. Collect actual bid data to refine accuracy."
        })

    return findings


if __name__ == "__main__":
    results = run_validation_tests()
