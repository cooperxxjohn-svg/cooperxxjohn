# Quick Start Guide - BOQ Estimation System

Get started with the BOQ estimation system in 5 minutes!

## 🚀 Installation

### Option 1: Local Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd cooperxxjohn

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install system dependencies
# Ubuntu/Debian:
sudo apt-get install poppler-utils

# macOS:
brew install poppler

# 5. Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Option 2: Docker

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 2. Run with Docker Compose
docker-compose up -d

# API will be available at http://localhost:8000
```

## 📝 Basic Usage

### Example 1: Quick Estimate

```python
from boq_estimator import quick_estimate
import os

# Set API key
os.environ['ANTHROPIC_API_KEY'] = 'your-key-here'

# Generate BOQ from drawings
boq = quick_estimate(
    drawing_paths=["foundation_plan.pdf", "floor_plan.pdf"],
    project_name="Office Building Construction",
    location="New Delhi",
    anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
    output_dir="./my_boq_output"
)

print(f"Total Estimate: ₹{boq.total_amount:,.2f}")
```

### Example 2: Manual BOQ Creation

```python
from boq_calculator import ConcreteCalculator
from boq_schema import MaterialGrade
from decimal import Decimal

# Create calculator
calc = ConcreteCalculator()

# Calculate foundation concrete
foundation = calc.calculate(
    item_no="1.1",
    concrete_type="foundation",
    grade=MaterialGrade.M20,
    length=Decimal("20.0"),  # meters
    width=Decimal("15.0"),
    thickness=Decimal("0.3"),
    location="Grid A1-A4"
)

print(f"Item: {foundation.description}")
print(f"Quantity: {foundation.quantity} cum")
print(f"Amount: ₹{foundation.total_amount:,.2f}")
```

### Example 3: Using the API

```bash
# Start the API server
python api_server.py

# Or with uvicorn
uvicorn api_server:app --reload
```

Then use curl or Postman:

```bash
# Upload drawings and create estimation
curl -X POST "http://localhost:8000/estimate" \
  -F "drawings=@foundation_plan.pdf" \
  -F "drawings=@floor_plan.pdf" \
  -F "contract_name=Office Building" \
  -F "location=Delhi"

# Check job status
curl "http://localhost:8000/status/{job_id}"

# Download BOQ
curl "http://localhost:8000/download/{job_id}/excel" -o boq.xlsx
```

## 🧪 Run Examples

```bash
# Run all examples
python example_usage.py

# Or run specific examples
python -c "from example_usage import example_2_manual_boq_creation; example_2_manual_boq_creation()"
```

## 📊 Understanding the Output

After running estimation, you'll get:

```
boq_output/
├── boq_document.json       # Complete BOQ in JSON format
├── boq_summary.json        # Summary with totals by category
├── validation_report.json  # CPWD compliance validation
├── boq.xlsx               # Excel spreadsheet (if requested)
└── extractions/           # Raw extraction data from drawings
    ├── drawing1_page1_extraction.json
    └── drawing2_page1_extraction.json
```

## 🔧 Custom Configuration

### Using Custom Rates

```python
from boq_estimator import BOQEstimator
from config import BOQConfig

# Create custom config
config = BOQConfig()
config.update_rates({
    'CEMENT_OPC43': 8.50,  # Updated rate
    'LABOUR_MASON': 950.0,
})

# Use with estimator
estimator = BOQEstimator(
    anthropic_api_key='your-key',
    dsr_rates=config.get_all_rates()
)
```

### Regional Configuration

```python
from config import create_custom_config

# Mumbai rates (15% higher than Delhi)
mumbai_config = create_custom_config("Mumbai", "2024")
mumbai_config.apply_regional_multiplier(1.15)

# Save for future use
mumbai_config.save_to_file("mumbai_rates_2024.json")
```

## 🎯 Common Workflows

### Workflow 1: Complete Estimation from Drawings

```python
from boq_estimator import BOQEstimator
from boq_schema import ContractDetails

contract = ContractDetails(
    contract_name="Hospital Building - Phase 1",
    contract_no="CPWD/2024/H001",
    location="Delhi",
    client="Ministry of Health",
    completion_period_days=730
)

estimator = BOQEstimator(anthropic_api_key='your-key')

boq = estimator.estimate_from_drawings(
    drawing_paths=["drawings/foundation.pdf", "drawings/floor1.pdf"],
    contract_details=contract,
    output_dir="./hospital_boq",
    merge_duplicates=True,
    validate=True
)

# Export to Excel
estimator.export_to_excel(boq, "./hospital_boq.xlsx")
```

### Workflow 2: Validation Only

```python
from boq_validator import CPWDValidator
import json

# Load existing BOQ
with open('boq_document.json') as f:
    boq_data = json.load(f)

from boq_schema import BOQDocument
boq = BOQDocument(**boq_data)

# Validate
validator = CPWDValidator()
is_valid, results = validator.validate_document(boq)

# Print report
validator.print_validation_report()
```

### Workflow 3: Calculate Specific Items

```python
from boq_calculator import (
    EarthworkCalculator, ConcreteCalculator, MasonryCalculator
)
from decimal import Decimal

# Excavation
earthwork = EarthworkCalculator()
excavation = earthwork.calculate(
    item_no="1.1",
    work_type='excavation_ordinary_soil',
    length=Decimal("50"),
    width=Decimal("30"),
    depth=Decimal("2.5")
)

# Brick wall
masonry = MasonryCalculator()
wall = masonry.calculate(
    item_no="2.1",
    wall_thickness="230mm",
    mortar_ratio="1:6",
    length=Decimal("100"),
    height=Decimal("3.5")
)

total = excavation.total_amount + wall.total_amount
print(f"Total: ₹{total:,.2f}")
```

## 🐛 Troubleshooting

### Issue: API Key Error
```
Solution: Ensure ANTHROPIC_API_KEY is set in environment or .env file
export ANTHROPIC_API_KEY='your-key-here'
```

### Issue: PDF Processing Error
```
Solution: Install poppler-utils
Ubuntu: sudo apt-get install poppler-utils
macOS: brew install poppler
```

### Issue: Import Errors
```
Solution: Ensure all dependencies are installed
pip install -r requirements.txt
```

### Issue: Validation Errors
```
Solution: Check validation report for specific issues
The validator provides suggestions for fixing each issue
```

## 📚 Next Steps

1. **Read the full README.md** for comprehensive documentation
2. **Study example_usage.py** for detailed examples
3. **Review boq_schema.py** to understand data structures
4. **Explore calculators** in boq_calculator.py
5. **Customize rates** in config.py for your region

## 🆘 Getting Help

- Check validation reports for guidance on fixing BOQ issues
- Review example_usage.py for common patterns
- Check module docstrings for detailed API documentation
- Ensure all file paths are correct and files exist

## 🎉 You're Ready!

You now have a production-ready BOQ estimation system. Start by running the examples, then adapt them to your specific needs.

```bash
# Try it now!
python example_usage.py
```

Happy estimating! 🏗️
