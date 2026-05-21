# Drywall Detection System - README

AI-powered drywall takeoff from architectural drawings using Claude Sonnet 4 API.

---

## Overview

The Drywall Detection System analyzes floor plans, elevations, and sections to automatically extract:

- **Walls**: Linear footage, height, square footage, wall type (interior/exterior/partition)
- **Openings**: Doors and windows with dimensions
- **Corners**: Inside corners (finishing work) and outside corners (corner bead material)
- **Ceilings**: Square footage, type (flat/vaulted/tray/coffered), height
- **Materials**: Drywall sheets, joint compound, tape, screws, corner bead
- **Labor**: Installation hours based on industry production rates
- **Estimate**: Complete pricing with materials, labor, overhead, and profit

---

## Key Features

✓ **AI-Powered Detection**: Uses Claude Sonnet 4 vision API to analyze drawings  
✓ **Multiple Drawing Types**: Floor plans, elevations, sections, reflected ceiling plans  
✓ **Accurate Material Calculations**: Based on 2026 industry standards  
✓ **Labor Estimation**: Realistic production rates from actual contractor data  
✓ **Validation**: Automatic sanity checks and warnings for unusual dimensions  
✓ **Flexible**: Supports different sheet sizes, difficulty levels, and waste factors  
✓ **Well-Tested**: Comprehensive test suite with mock fixtures  

---

## Quick Start

### 1. Installation

```bash
cd /home/user/cooperxxjohn/painting-ai/backend

# Install dependencies (if not already installed)
pip install anthropic pillow pytest

# Set your API key
export ANTHROPIC_API_KEY='your-api-key-here'
```

### 2. Generate Test Fixtures

```bash
cd tests/fixtures
python generate_test_floorplans.py
```

This creates 5 sample floor plans for testing.

### 3. Run Basic Example

```python
from drywall_detector import DrywallDetector, DrywallCalculator
import os

# Initialize
detector = DrywallDetector(os.getenv("ANTHROPIC_API_KEY"))
calculator = DrywallCalculator(sheet_size="4x8")

# Analyze floor plan
detection = detector.analyze_drawing("tests/fixtures/simple_residential.png")

# Calculate estimate
estimate = calculator.calculate_estimate(detection, labor_rate=65.00)

# Print results
print(f"Total drywall: {detection.summary['total_drywall_sqft']} sqft")
print(f"Estimate: ${estimate['pricing']['total']:,.2f}")
print(f"Price/sqft: ${estimate['pricing']['price_per_sqft']:.2f}")
```

### 4. Run Example Script

```bash
python example_drywall_usage.py
```

This runs 4 complete examples showing different use cases.

---

## Usage Examples

### Example 1: Basic Detection

```python
from drywall_detector import DrywallDetector

detector = DrywallDetector(api_key="your-key")
detection = detector.analyze_drawing("floor_plan.png")

# View detected walls
for wall in detection.walls:
    print(f"{wall.wall_id}: {wall.length_ft}ft × {wall.height_ft}ft = {wall.square_footage} sqft")
    print(f"  Type: {wall.type}")
    print(f"  Corners: {wall.corners.inside_corners} inside, {wall.corners.outside_corners} outside")

# View detected ceilings
for ceiling in detection.ceilings:
    print(f"{ceiling.room}: {ceiling.type} ceiling, {ceiling.square_footage} sqft")

# View summary
print(detection.summary)
# {
#   'total_wall_sqft_gross': 800.0,
#   'total_wall_sqft_net': 736.0,
#   'total_ceiling_sqft': 600.0,
#   'total_drywall_sqft': 1336.0,
#   'total_linear_ft': 100.0,
#   'total_openings': 3,
#   'total_corners': 4,
#   'inside_corners': 0,
#   'outside_corners': 4
# }
```

### Example 2: Material Calculation

```python
from drywall_detector import DrywallCalculator

calc = DrywallCalculator(sheet_size="4x8")
materials = calc.calculate_materials(detection, waste_factor=1.10)

print(f"Drywall sheets: {materials['drywall_sheets']['quantity']}")
print(f"Joint compound: {materials['joint_compound']['buckets_5gal']} buckets")
print(f"Tape: {materials['tape']['rolls']} rolls")
print(f"Screws: {materials['screws']['pounds']} lbs")
print(f"Corner bead: {materials['corner_bead']['pieces_10ft']} pieces")
```

### Example 3: Labor Estimation

```python
labor = calc.calculate_labor(detection, difficulty="standard")

print(f"Hanging: {labor['hanging_hours']:.1f} hrs")
print(f"Taping: {labor['taping_hours']:.1f} hrs")
print(f"Finishing: {labor['finishing_hours']:.1f} hrs")
print(f"Sanding: {labor['sanding_hours']:.1f} hrs")
print(f"Total: {labor['total_hours']:.1f} hrs")
```

### Example 4: Complete Estimate

```python
estimate = calc.calculate_estimate(
    detection,
    sheet_price=15.00,      # $15 per 4×8 sheet
    labor_rate=65.00,       # $65/hr
    difficulty="standard",  # or "easy" or "difficult"
    waste_factor=1.10       # 10% waste
)

print("\nMATERIALS:")
print(f"  Total: ${estimate['materials']['total']:,.2f}")

print("\nLABOR:")
print(f"  Hours: {estimate['labor']['hours']:.1f}")
print(f"  Total: ${estimate['labor']['total']:,.2f}")

print("\nPRICING:")
print(f"  Subtotal: ${estimate['pricing']['subtotal']:,.2f}")
print(f"  Overhead (15%): ${estimate['pricing']['overhead']:,.2f}")
print(f"  Profit (20%): ${estimate['pricing']['profit']:,.2f}")
print(f"  TOTAL: ${estimate['pricing']['total']:,.2f}")
print(f"  Price/sqft: ${estimate['pricing']['price_per_sqft']:.2f}")
```

### Example 5: Different Sheet Sizes

```python
# Compare sheet sizes
for size in ["4x8", "4x10", "4x12"]:
    calc = DrywallCalculator(sheet_size=size)
    materials = calc.calculate_materials(detection)
    print(f"{size}: {materials['drywall_sheets']['quantity']} sheets")

# Output:
# 4x8: 46 sheets (32 sqft each)
# 4x10: 37 sheets (40 sqft each)
# 4x12: 31 sheets (48 sqft each)
```

### Example 6: Difficulty Levels

```python
# Compare difficulty levels
for difficulty in ["easy", "standard", "difficult"]:
    labor = calc.calculate_labor(detection, difficulty=difficulty)
    print(f"{difficulty}: {labor['total_hours']:.1f} hrs")

# Output:
# easy: 31.8 hrs (0.85× multiplier)
# standard: 37.4 hrs (1.00× multiplier)
# difficult: 48.6 hrs (1.30× multiplier)
```

---

## File Structure

```
painting-ai/backend/
│
├── drywall_detector.py              # Main AI detection engine
├── example_drywall_usage.py         # Usage examples
├── DRYWALL_DETECTOR_README.md       # This file
│
├── data/
│   └── AI_INTEGRATION_DRYWALL.md    # Detailed integration guide
│
└── tests/
    ├── test_drywall_detector.py     # Test suite
    │
    └── fixtures/
        ├── README.md                # Fixture documentation
        ├── generate_test_floorplans.py
        ├── simple_residential.png
        ├── commercial_office.png
        ├── multi_room.png
        ├── vaulted_ceiling.png
        └── complex_corners.png
```

---

## Testing

### Run All Tests

```bash
cd /home/user/cooperxxjohn/painting-ai/backend
pytest tests/test_drywall_detector.py -v
```

### Run Specific Test Classes

```bash
# Test only AI detection
pytest tests/test_drywall_detector.py::TestDrywallDetector -v

# Test only calculations
pytest tests/test_drywall_detector.py::TestDrywallCalculator -v

# Test only dataclasses
pytest tests/test_drywall_detector.py::TestDataClasses -v
```

### Test Coverage

```bash
pytest tests/test_drywall_detector.py --cov=drywall_detector --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

---

## API Reference

### DrywallDetector

```python
class DrywallDetector:
    def __init__(self, anthropic_api_key: str)
    def analyze_drawing(self, image_path: str) -> DrywallDetection
```

**Main Methods:**
- `analyze_drawing()`: Analyzes a floor plan and returns detection results

**Internal Methods:**
- `_classify_drawing()`: Determines drawing type (floor_plan, elevation, etc.)
- `_extract_from_floor_plan()`: Extracts walls/ceilings from floor plan
- `_extract_from_elevation()`: Extracts walls from elevation
- `_extract_from_section()`: Extracts info from section drawing
- `_calculate_summary()`: Calculates summary statistics
- `_validate_detection()`: Validates results and flags issues

---

### DrywallCalculator

```python
class DrywallCalculator:
    def __init__(self, sheet_size: str = "4x8")
    def calculate_materials(self, detection: DrywallDetection, waste_factor: float = 1.10) -> Dict
    def calculate_labor(self, detection: DrywallDetection, difficulty: str = "standard") -> Dict
    def calculate_estimate(self, detection: DrywallDetection, ...) -> Dict
```

**Sheet Sizes:**
- `"4x8"` - 32 sqft (standard residential)
- `"4x10"` - 40 sqft (9' ceilings)
- `"4x12"` - 48 sqft (commercial)
- `"4x14"` - 56 sqft (high ceilings)

**Difficulty Levels:**
- `"easy"` - 0.85× multiplier (new construction, simple)
- `"standard"` - 1.00× multiplier (normal conditions)
- `"difficult"` - 1.30× multiplier (remodel, high ceilings)

---

### Data Classes

```python
@dataclass
class Opening:
    type: str              # door, window, sliding_door
    width: float           # feet
    height: float          # feet
    square_footage: float
    quantity: int

@dataclass
class Corner:
    inside_corners: int    # For finishing work
    outside_corners: int   # Needs corner bead

@dataclass
class Wall:
    wall_id: str
    type: str             # interior, exterior, partition
    length_ft: float
    height_ft: float
    square_footage: float
    openings: List[Opening]
    corners: Corner
    special_features: List[str]

@dataclass
class Ceiling:
    room: str
    type: str             # flat, vaulted, tray, coffered
    square_footage: float
    height_ft: float
    special_notes: Optional[str]

@dataclass
class DrywallDetection:
    walls: List[Wall]
    ceilings: List[Ceiling]
    summary: Dict[str, float]
    drawing_type: str     # floor_plan, elevation, section
    scale: Optional[str]
    notes: List[str]
```

---

## Industry Standards (2026)

### Material Coverage Rates

- **Drywall sheets**: Various sizes (4×8, 4×10, 4×12, 4×14)
- **Joint compound**: 400 sqft per 5-gallon bucket (3 coats)
- **Tape**: 1.1 linear feet per sqft of drywall
- **Screws**: 32 per 4×8 sheet (16" OC studs)
- **Corner bead**: 8 linear feet per outside corner

### Labor Production Rates

- **Hanging**: 40 sqft/hour
- **Taping**: 150 sqft/hour (first coat)
- **Finishing**: 200 sqft/hour (second + third coats)
- **Sanding**: 300 sqft/hour

### Pricing

- **Drywall sheet (4×8)**: $15
- **Joint compound (5-gal)**: $25
- **Tape (500ft roll)**: $8
- **Screws (per lb)**: $12
- **Corner bead (10ft)**: $3.50
- **Labor rate**: $55-85/hr (varies by region and type)
- **Overhead**: 15% of subtotal
- **Profit**: 20% of subtotal

### Typical Price per Square Foot

- **Residential new construction**: $1.50 - $3.50/sqft
- **Residential remodel**: $2.00 - $5.00/sqft
- **Commercial office**: $2.50 - $6.00/sqft
- **High-end residential**: $4.00 - $10.00/sqft

---

## Validation & Quality Checks

The system automatically validates:

- **Wall height**: Flags if > 12ft or < 7ft
- **Wall length**: Warns if > 50ft (may need expansion joint)
- **Area calculation**: Verifies sqft ≈ length × height
- **Room size**: Flags very large rooms (> 2500 sqft)
- **Price range**: Warns if price/sqft outside $1.50-$8.00
- **Labor percentage**: Should be 70-80% of subtotal

---

## Troubleshooting

### "No walls detected"

**Causes:**
- Image quality too low
- Drawing is not a floor plan
- Wall lines too faint

**Solutions:**
- Increase image resolution (150+ DPI)
- Verify drawing type
- Adjust image contrast

### "Corner count seems wrong"

**Causes:**
- Complex geometry (angled walls)
- AI misinterpreting connections

**Solutions:**
- Manually verify and adjust
- Add notes about specific areas
- Use validation mode

### "Price seems too high/low"

**Causes:**
- Incorrect sqft calculation
- Wrong difficulty level
- Regional rates not applied

**Solutions:**
- Validate sqft manually
- Review difficulty setting
- Check labor rate for region

### API Errors

**Causes:**
- Invalid API key
- Rate limiting
- Network issues

**Solutions:**
- Verify ANTHROPIC_API_KEY is set
- Add retry logic with exponential backoff
- Check API quota

---

## Best Practices

### For Accurate Detection

1. Use high-quality images (150+ DPI)
2. Include scale indicator visible
3. Ensure dimensions are labeled
4. Use complete drawings (don't crop)
5. Follow standard architectural conventions

### For Reliable Estimates

1. Validate AI output before calculations
2. Set appropriate difficulty level
3. Apply regional labor multipliers
4. Include 5-10% contingency
5. Compare to industry benchmarks

### For Production Use

1. Cache results for identical drawings
2. Batch process multiple pages
3. Handle errors gracefully
4. Allow user review/correction
5. Track accuracy and improve prompts

---

## Integration with Painting.ai

The drywall detector complements the existing painting detector:

```python
from painting_detector import PaintingDetector, PaintCalculator
from drywall_detector import DrywallDetector, DrywallCalculator

# Detect both drywall and painting
drywall_detection = drywall_detector.analyze_drawing(image)
painting_detection = painting_detector.analyze_drawing(image)

# Calculate both estimates
drywall_estimate = drywall_calc.calculate_estimate(drywall_detection)
painting_estimate = paint_calc.calculate_room_estimate(painting_detection.rooms[0])

# Combined estimate
total_cost = drywall_estimate['pricing']['total'] + painting_estimate['totals']['total_cost']

print(f"Drywall: ${drywall_estimate['pricing']['total']:,.2f}")
print(f"Painting: ${painting_estimate['totals']['total_cost']:,.2f}")
print(f"Total: ${total_cost:,.2f}")
```

---

## API Costs

**Claude Sonnet 4 Pricing (2026):**
- Input: ~$3 per million tokens
- Output: ~$15 per million tokens

**Typical cost per floor plan:**
- Image: ~1,500 tokens
- Prompt: ~800 tokens
- Response: ~1,200 tokens
- **Cost**: ~$0.02-0.05 per drawing

**Monthly estimates:**
- 100 drawings: ~$3-5/month
- 500 drawings: ~$15-25/month
- 1,000 drawings: ~$30-50/month

Very cost-effective vs manual takeoff labor ($50-100/drawing)!

---

## Known Limitations

**What works well:**
✓ Rectangular and standard-shaped rooms  
✓ Standard doors and windows  
✓ Simple corner configurations  
✓ Clear architectural drawings  

**What needs improvement:**
✗ Curved walls (approximated)  
✗ Angled walls (not 90°)  
✗ Hand-drawn sketches  
✗ Very complex multi-level ceilings  
✗ Poor quality images  

---

## Contributing

To improve the system:

1. Add test cases for edge cases
2. Improve AI prompts for better accuracy
3. Update material prices quarterly
4. Add support for new drawing types
5. Enhance validation logic

---

## License

Part of the Painting.ai system.

---

## Support

For issues or questions:

1. Check this README
2. Review `data/AI_INTEGRATION_DRYWALL.md`
3. Run tests to verify setup
4. Check validation notes in detection results

---

**Last Updated:** 2026-05-21  
**Version:** 1.0  
**Claude Model:** claude-sonnet-4-20250514  
**Status:** Production Ready ✓
