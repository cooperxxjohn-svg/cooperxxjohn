# Drywall Detector Test Fixtures

This directory contains sample floor plan images for testing the drywall detection AI engine.

## Test Floor Plans

### 1. simple_residential.png
**Description:** Basic residential floor plan  
**Dimensions:** 30' × 20' single room  
**Features:**
- 1 door (3' wide)
- 2 windows (3' wide each)
- 4 exterior walls
- 600 SF total

**Expected Detection:**
- Total wall linear feet: ~100 LF (perimeter)
- Wall square footage: ~800 SF (100 LF × 8' height)
- Ceiling square footage: 600 SF
- Openings: 3 total (1 door + 2 windows)
- Corners: 4 outside corners

---

### 2. commercial_office.png
**Description:** Commercial office with partition wall  
**Dimensions:** 40' × 30' divided into 2 offices  
**Features:**
- Interior partition wall with door
- Multiple windows on exterior
- Commercial ceiling height (9-10')

**Expected Detection:**
- Total wall linear feet: ~140 LF + partition
- 2 separate rooms/offices
- Interior partition wall
- Multiple windows
- Both interior and exterior wall types

---

### 3. multi_room.png
**Description:** Multi-room residential layout  
**Dimensions:** Living Room (20' × 15') + Bedroom (12' × 14')  
**Features:**
- 2 connected rooms
- Shared wall with door opening
- Multiple windows
- Different ceiling areas

**Expected Detection:**
- Total ceiling SF: ~468 SF (300 + 168)
- Shared interior wall
- Door opening between rooms
- Multiple exterior walls with windows

---

### 4. vaulted_ceiling.png
**Description:** Great room with vaulted ceiling  
**Dimensions:** 24' × 20' single room  
**Features:**
- Vaulted ceiling (14' peak height)
- Higher than standard 8' walls
- Larger square footage due to sloped ceiling

**Expected Detection:**
- Room name: "Great Room"
- Ceiling type: "vaulted" or "cathedral"
- Peak height: 14'
- Higher wall square footage due to ceiling slope
- Special note about vaulted ceiling

---

### 5. complex_corners.png
**Description:** L-shaped room with multiple corners  
**Dimensions:** Horizontal (30' × 12') + Vertical (12' × 18')  
**Features:**
- L-shaped configuration
- 1 inside corner (critical for corner bead)
- 4 outside corners
- Tests corner detection algorithm

**Expected Detection:**
- Inside corners: 1
- Outside corners: 4
- Total corners: 5
- Complex wall geometry
- Multiple wall segments

---

## Using These Fixtures

### In Python Tests

```python
import os
from drywall_detector import DrywallDetector

# Path to fixtures
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

# Load and test
detector = DrywallDetector(api_key="your-key")
detection = detector.analyze_drawing(
    os.path.join(FIXTURES_DIR, 'simple_residential.png')
)

# Verify results
assert detection.summary['total_corners'] == 4
assert detection.summary['total_openings'] == 3
```

### Manual Testing

```bash
cd /home/user/cooperxxjohn/painting-ai/backend
python -c "
from drywall_detector import DrywallDetector, DrywallCalculator
import os

detector = DrywallDetector(os.getenv('ANTHROPIC_API_KEY'))
calc = DrywallCalculator()

# Test simple residential
detection = detector.analyze_drawing('tests/fixtures/simple_residential.png')
print(f'Detected: {len(detection.walls)} walls, {len(detection.ceilings)} ceilings')
print(f'Total SF: {detection.summary[\"total_drywall_sqft\"]} sqft')

# Calculate estimate
estimate = calc.calculate_estimate(detection)
print(f'Estimate: ${estimate[\"pricing\"][\"total\"]:,.2f}')
print(f'Price/sqft: ${estimate[\"pricing\"][\"price_per_sqft\"]:.2f}')
"
```

## Regenerating Fixtures

If you need to regenerate the test images:

```bash
cd /home/user/cooperxxjohn/painting-ai/backend/tests/fixtures
python generate_test_floorplans.py
```

This will create fresh PNG images with the same specifications.

---

## AI Detection Testing Checklist

When testing AI detection on these fixtures, verify:

- [ ] **Wall Detection**
  - Correct number of wall segments identified
  - Accurate wall lengths (±2 feet acceptable)
  - Correct wall heights (8' residential, 9-10' commercial)
  - Proper wall type classification (interior vs exterior)

- [ ] **Opening Detection**
  - All doors detected
  - All windows detected
  - Correct dimensions (standard 3' × 6'8" doors)
  - Opening square footage calculated correctly

- [ ] **Corner Detection**
  - Inside corners counted (for drywall finishing)
  - Outside corners counted (for corner bead material)
  - Total corner count matches floor plan

- [ ] **Ceiling Detection**
  - Room names extracted
  - Ceiling type identified (flat, vaulted, etc.)
  - Square footage calculated correctly
  - Special features noted (vaulted, tray, etc.)

- [ ] **Summary Calculations**
  - Total wall SF = Σ(wall lengths × heights)
  - Net wall SF = Gross wall SF - opening SF
  - Total drywall SF = Net wall SF + Ceiling SF
  - Linear feet = Σ(wall lengths)

- [ ] **Validation**
  - No ERROR flags for valid floor plans
  - Warnings for unusual dimensions (>12' height, >50' length)
  - Notes for special features

---

## Expected Detection Results

### Simple Residential
```json
{
  "walls": 4,
  "total_wall_sqft_gross": 800,
  "total_wall_sqft_net": ~736,
  "total_ceiling_sqft": 600,
  "total_drywall_sqft": ~1336,
  "total_linear_ft": 100,
  "total_openings": 3,
  "total_corners": 4,
  "outside_corners": 4,
  "inside_corners": 0
}
```

### Complex Corners
```json
{
  "total_corners": 5,
  "inside_corners": 1,
  "outside_corners": 4
}
```

---

**Note:** Actual AI detection results may vary slightly depending on image quality and AI interpretation. Acceptable variance: ±10% for dimensions, ±1 for corner counts.
