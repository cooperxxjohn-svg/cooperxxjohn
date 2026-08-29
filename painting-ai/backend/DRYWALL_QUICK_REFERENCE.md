# Drywall Detector - Quick Reference Card

**One-page reference for developers integrating the drywall detection system**

---

## Installation & Setup

```bash
# Install dependencies
pip install anthropic pillow pytest

# Set API key
export ANTHROPIC_API_KEY='your-key-here'

# Generate test fixtures
cd tests/fixtures && python generate_test_floorplans.py
```

---

## Basic Usage (3 Steps)

```python
from drywall_detector import DrywallDetector, DrywallCalculator
import os

# 1. Initialize
detector = DrywallDetector(os.getenv("ANTHROPIC_API_KEY"))
calc = DrywallCalculator(sheet_size="4x8")

# 2. Detect
detection = detector.analyze_drawing("floor_plan.png")

# 3. Estimate
estimate = calc.calculate_estimate(detection, labor_rate=65.00)
print(f"Total: ${estimate['pricing']['total']:,.2f}")
```

---

## Detection Output Structure

```python
detection = DrywallDetection(
    walls=[
        Wall(
            wall_id="W1",
            type="interior",           # interior | exterior | partition
            length_ft=24.5,
            height_ft=8.0,
            square_footage=196.0,
            openings=[
                Opening("door", 3.0, 6.67, 20.0, quantity=1)
            ],
            corners=Corner(inside_corners=2, outside_corners=0),
            special_features=["soffit"]
        )
    ],
    ceilings=[
        Ceiling("Living Room", "flat", 600.0, 8.0)
    ],
    summary={
        "total_wall_sqft_gross": 800.0,
        "total_wall_sqft_net": 736.0,    # After deducting openings
        "total_ceiling_sqft": 600.0,
        "total_drywall_sqft": 1336.0,
        "total_linear_ft": 100.0,
        "total_openings": 3,
        "total_corners": 4,
        "inside_corners": 0,
        "outside_corners": 4
    },
    drawing_type="floor_plan",
    scale="1/4\" = 1'-0\"",
    notes=[]
)
```

---

## Estimate Output Structure

```python
estimate = {
    "materials": {
        "drywall_sheets": 550.00,
        "joint_compound": 75.00,
        "tape": 24.00,
        "screws": 96.00,
        "corner_bead": 7.00,
        "sundries": 140.00,
        "total": 892.00
    },
    "material_details": {
        "drywall_sheets": {"quantity": 42, "size": "4x8"},
        "joint_compound": {"buckets_5gal": 3},
        "tape": {"rolls": 3, "linear_ft": 1469},
        "screws": {"pounds": 9},
        "corner_bead": {"pieces_10ft": 2, "linear_ft": 16}
    },
    "labor": {
        "hours": 42.0,
        "rate": 65.00,
        "total": 2730.00,
        "breakdown": {
            "hanging_hours": 23.4,
            "taping_hours": 6.2,
            "finishing_hours": 4.7,
            "sanding_hours": 3.1
        }
    },
    "pricing": {
        "subtotal": 3622.00,
        "overhead": 543.30,      # 15%
        "profit": 724.40,        # 20%
        "total": 4889.70,
        "price_per_sqft": 5.14
    }
}
```

---

## Key Parameters

### Sheet Sizes
```python
"4x8"   → 32 sqft (standard residential)
"4x10"  → 40 sqft (9' walls)
"4x12"  → 48 sqft (commercial)
"4x14"  → 56 sqft (high ceilings)
```

### Difficulty Levels
```python
"easy"      → 0.85× multiplier (new construction)
"standard"  → 1.00× multiplier (normal)
"difficult" → 1.30× multiplier (remodel, high ceilings)
```

### Waste Factors
```python
1.08  → 8% (simple rectangular rooms)
1.10  → 10% (standard, recommended)
1.15  → 15% (complex geometry)
1.20  → 20% (very complex, curves)
```

---

## Common Operations

### Compare Sheet Sizes
```python
for size in ["4x8", "4x10", "4x12"]:
    calc = DrywallCalculator(sheet_size=size)
    materials = calc.calculate_materials(detection)
    print(f"{size}: {materials['drywall_sheets']['quantity']} sheets")
```

### Adjust for Difficulty
```python
for diff in ["easy", "standard", "difficult"]:
    labor = calc.calculate_labor(detection, difficulty=diff)
    print(f"{diff}: {labor['total_hours']:.1f} hrs")
```

### Regional Labor Rates
```python
REGIONAL_RATES = {
    "San Francisco": 85.00,
    "New York": 80.00,
    "Chicago": 70.00,
    "Dallas": 65.00,
    "Rural": 55.00
}
```

---

## Industry Standards (2026)

### Material Coverage
- **Joint compound**: 400 sqft per 5-gal bucket (3 coats)
- **Tape**: 1.1 linear feet per sqft drywall
- **Screws**: 32 per 4×8 sheet
- **Corner bead**: 8 linear feet per outside corner

### Labor Production Rates
- **Hanging**: 40 sqft/hour
- **Taping**: 150 sqft/hour
- **Finishing**: 200 sqft/hour
- **Sanding**: 300 sqft/hour

### Pricing
- **Drywall (4×8)**: $15/sheet
- **Joint compound**: $25/bucket
- **Labor**: $55-85/hr (regional)
- **Overhead**: 15%
- **Profit**: 20%

### Price per Sqft Ranges
- **Residential new**: $1.50 - $3.50/sqft
- **Residential remodel**: $2.00 - $5.00/sqft
- **Commercial**: $2.50 - $6.00/sqft
- **High-end**: $4.00 - $10.00/sqft

---

## Validation Checks

```python
# Automatic warnings for:
wall.height_ft > 12          # "Unusual height"
wall.length_ft > 50          # "May need expansion joint"
price_per_sqft < 1.50        # "Price too low"
price_per_sqft > 8.00        # "Price too high"
labor_pct < 60 or > 80       # "Labor % outside normal range"
```

---

## Error Handling

```python
try:
    detection = detector.analyze_drawing(image_path)
    
    if len(detection.walls) == 0:
        print("ERROR: No walls detected")
        # Fallback to manual input
    
    if detection.notes:
        for note in detection.notes:
            print(f"WARNING: {note}")
    
    estimate = calc.calculate_estimate(detection)
    
except FileNotFoundError:
    print("ERROR: Image file not found")
except json.JSONDecodeError:
    print("ERROR: Invalid API response")
except Exception as e:
    print(f"ERROR: {e}")
```

---

## Testing

### Run All Tests
```bash
pytest tests/test_drywall_detector.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_drywall_detector.py::TestDrywallCalculator -v
```

### Quick Smoke Test
```python
python -c "
from drywall_detector import DrywallCalculator, Wall, Ceiling, Corner, DrywallDetection

wall = Wall('W1', 'interior', 24.0, 8.0, 192.0, [], Corner(0, 2), [])
ceiling = Ceiling('Room', 'flat', 300.0, 8.0)
summary = {'total_drywall_sqft': 492.0, 'total_linear_ft': 24.0, 
           'total_corners': 2, 'outside_corners': 2}
detection = DrywallDetection([wall], [ceiling], summary, 'floor_plan', None, [])

calc = DrywallCalculator()
estimate = calc.calculate_estimate(detection)
print(f'✅ Test passed: \${estimate[\"pricing\"][\"total\"]:,.2f}')
"
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `drywall_detector.py` | Main detection engine |
| `example_drywall_usage.py` | Usage examples |
| `tests/test_drywall_detector.py` | Test suite |
| `tests/fixtures/*.png` | Sample floor plans |
| `data/AI_INTEGRATION_DRYWALL.md` | Detailed guide |
| `DRYWALL_DETECTOR_README.md` | Full documentation |
| `DRYWALL_QUICK_REFERENCE.md` | This file |

---

## API Costs

**Claude Sonnet 4 (2026):**
- ~$0.02-0.05 per floor plan
- 100 drawings/month: ~$3-5
- 1,000 drawings/month: ~$30-50

**vs Manual Takeoff:**
- $100-200 per drawing
- **ROI: 2,000-10,000×**

---

## Integration with Painting.ai

```python
from painting_detector import PaintingDetector
from drywall_detector import DrywallDetector

# Detect both
painting = painting_detector.analyze_drawing(image)
drywall = drywall_detector.analyze_drawing(image)

# Combined estimate
total = (
    painting_calc.calculate_room_estimate(painting.rooms[0])['totals']['total_cost'] +
    drywall_calc.calculate_estimate(drywall)['pricing']['total']
)

print(f"Combined estimate: ${total:,.2f}")
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No walls detected" | Check image quality, verify drawing type |
| "Corner count wrong" | Manual review, complex geometry |
| "Price too high" | Check difficulty level, labor rate |
| "API error" | Verify ANTHROPIC_API_KEY is set |
| "Import error" | Ensure in correct directory, dependencies installed |

---

## Quick Tips

💡 **Always validate AI output** - Review wall counts and dimensions  
💡 **Use appropriate difficulty** - Remodel ≠ new construction  
💡 **Apply regional rates** - SF ≠ Dallas labor costs  
💡 **Include contingency** - Add 5-10% for unknowns  
💡 **Compare to benchmarks** - Typical price: $2-5/sqft residential  

---

**Need more details?** See `DRYWALL_DETECTOR_README.md` or `data/AI_INTEGRATION_DRYWALL.md`

**Ready to use?** Run `python example_drywall_usage.py`
