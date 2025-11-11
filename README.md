# BOQ Estimation System for Indian Government Contractors

A production-ready AI-powered Bill of Quantities (BOQ) estimation system compliant with CPWD (Central Public Works Department) standards. This system automatically extracts quantities from construction drawings and generates standardized BOQ documents.

## 🎯 Features

- **AI-Powered Drawing Extraction**: Uses Claude Vision API to extract dimensions, materials, and specifications from PDF drawings
- **CPWD-Compliant BOQ Generation**: Automatic generation of BOQ following CPWD format and standards
- **Comprehensive Calculators**: Pre-built calculators for:
  - Earthwork
  - Concrete Work
  - Formwork/Shuttering
  - Steel Reinforcement
  - Masonry
  - And more...
- **Automatic Validation**: Validates BOQ against CPWD standards and best practices
- **Material & Labour Breakdown**: Detailed breakdown with wastage calculations
- **DSR Rate Integration**: Support for Delhi Schedule of Rates (DSR) or custom rates
- **Multiple Export Formats**: JSON and Excel output

## 📋 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Construction Drawings                      │
│                    (PDF/Image Files)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Drawing Extractor (Claude Vision)               │
│  • Extracts dimensions, materials, specifications           │
│  • Identifies element types (beams, columns, slabs, etc.)   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    BOQ Mapper                                │
│  • Maps extracted data to BOQ structure                     │
│  • Groups by work categories                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   BOQ Calculators                            │
│  • Applies CPWD calculation rules                           │
│  • Calculates material & labour requirements                │
│  • Computes rates and amounts                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   CPWD Validator                             │
│  • Validates against CPWD standards                         │
│  • Checks specifications, rates, quantities                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Final BOQ Document (JSON/Excel)                 │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd cooperxxjohn

# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies (for pdf2image)
# Ubuntu/Debian:
sudo apt-get install poppler-utils

# macOS:
brew install poppler

# Windows:
# Download from https://github.com/oschwartz10612/poppler-windows/releases/
```

### Basic Usage

```python
from boq_estimator import BOQEstimator
from boq_schema import ContractDetails

# Set up your Anthropic API key
api_key = "your-anthropic-api-key"

# Define contract details
contract = ContractDetails(
    contract_name="Government Office Building",
    location="New Delhi",
    client="Ministry of Public Works",
    department="CPWD",
    completion_period_days=365
)

# Initialize estimator
estimator = BOQEstimator(anthropic_api_key=api_key)

# Generate BOQ from drawings
boq = estimator.estimate_from_drawings(
    drawing_paths=[
        "foundation_plan.pdf",
        "floor_plan.pdf",
        "sections.pdf"
    ],
    contract_details=contract,
    output_dir="./boq_output"
)

# Export to Excel
estimator.export_to_excel(boq, "boq_final.xlsx")

print(f"Total Estimate: ₹{boq.total_amount:,.2f}")
```

## 📦 Modules

### 1. `boq_schema.py`
Defines the core data structures and Pydantic models for BOQ.

**Key Classes:**
- `BOQDocument`: Root document structure
- `BOQSection`: Section/group of items
- `BOQLineItem`: Individual work item
- `Material`: Material specification
- `Labour`: Labour requirement
- `ContractDetails`: Contract metadata

### 2. `boq_calculator.py`
Calculation engines for different work categories.

**Calculators:**
- `EarthworkCalculator`: Excavation, filling
- `ConcreteCalculator`: RCC work with material composition
- `FormworkCalculator`: Shuttering/formwork
- `ReinforcementCalculator`: Steel reinforcement
- `MasonryCalculator`: Brick/block masonry

**Example:**
```python
from boq_calculator import ConcreteCalculator
from boq_schema import MaterialGrade
from decimal import Decimal

calc = ConcreteCalculator(dsr_rates={...})
item = calc.calculate(
    item_no="1.1",
    concrete_type="foundation",
    grade=MaterialGrade.M20,
    length=Decimal("10.0"),
    width=Decimal("5.0"),
    thickness=Decimal("0.3")
)
```

### 3. `boq_validator.py`
CPWD compliance validation engine.

**Validates:**
- Quantity reasonableness
- Rate limits (overhead, profit)
- Material specifications
- Unit correctness
- Standard references

**Example:**
```python
from boq_validator import CPWDValidator

validator = CPWDValidator()
is_valid, results = validator.validate_document(boq_doc)
validator.print_validation_report()
```

### 4. `drawing_extractor.py`
AI-powered drawing analysis using Claude Vision API.

**Features:**
- PDF to image conversion
- Dimension extraction
- Material identification
- Scale detection
- Batch processing

**Example:**
```python
from drawing_extractor import DrawingExtractor

extractor = DrawingExtractor(api_key="...")
results = extractor.extract_from_pdf("foundation_plan.pdf")

for result in results:
    print(f"Found {len(result.dimensions)} dimensions")
    for dim in result.dimensions:
        print(f"  {dim.element_type}: {dim.length}m × {dim.width}m")
```

### 5. `boq_mapper.py`
Maps extracted data to BOQ structure.

**Features:**
- Element type to category mapping
- Material grade inference
- Item consolidation
- Automatic numbering

**Example:**
```python
from boq_mapper import BOQMapper

mapper = BOQMapper(dsr_rates={...})
sections = mapper.map_extraction_to_boq(extraction_results)
```

### 6. `boq_estimator.py`
Main orchestration module - complete workflow.

**Features:**
- End-to-end workflow
- Intermediate output saving
- Excel export
- Validation integration

## 🔧 Configuration

### DSR Rates

You can provide custom rates for your region/year:

```python
custom_rates = {
    # Labour rates (per day)
    'LABOUR_MASON': Decimal("900"),
    'LABOUR_HELPER': Decimal("650"),

    # Material rates
    'CEMENT_OPC43': Decimal("8.00"),  # per kg
    'SAND': Decimal("1350"),  # per cum
    'STEEL_FE500': Decimal("70"),  # per kg
}

estimator = BOQEstimator(
    anthropic_api_key=api_key,
    dsr_rates=custom_rates
)
```

### Environment Variables

```bash
# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Or use .env file
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

## 📊 Output Format

### JSON Output
```json
{
  "boq_id": "BOQ-20240101-120000",
  "contract": {
    "contract_name": "Office Building",
    "location": "New Delhi",
    "department": "CPWD"
  },
  "sections": [
    {
      "section_no": "1",
      "title": "Earthwork",
      "items": [
        {
          "item_no": "1.1",
          "description": "Excavation in ordinary soil",
          "unit": "cum",
          "quantity": 750.0,
          "unit_rate": 250.50,
          "total_amount": 187875.0
        }
      ]
    }
  ],
  "total_amount": 5750000.0
}
```

### Excel Output
Formatted spreadsheet with:
- Title and metadata
- Sectioned items
- Material/labour breakdown
- Section subtotals
- Grand total

## 🎓 Examples

See `example_usage.py` for comprehensive examples:

1. **Complete Workflow**: Drawing to BOQ
2. **Manual BOQ Creation**: Using calculators directly
3. **Validation**: CPWD compliance checking
4. **Quick Estimate**: Minimal configuration
5. **Custom Rates**: Region-specific rates

Run examples:
```bash
python example_usage.py
```

## 🏗️ CPWD Standards Implemented

- IS 456:2000 - Code of Practice for Plain and Reinforced Concrete
- IS 1077 - Common Burnt Clay Building Bricks
- IS 1786 - High Strength Deformed Steel Bars
- IS 383 - Specification for Coarse and Fine Aggregates
- IS 1200 - Method of Measurement of Building and Civil Engineering Works
- CPWD Specifications
- CPWD DSR (Delhi Schedule of Rates)

## 🔍 Validation Rules

The system validates:

### Quantities
- ✓ Positive values
- ✓ Reasonable magnitude
- ✓ Unit appropriateness

### Rates
- ✓ Overhead ≤ 20%
- ✓ Profit ≤ 12%
- ✓ Wastage ≤ 20%
- ✓ Amount calculations

### Specifications
- ✓ Material grades
- ✓ IS code references
- ✓ Drawing references
- ✓ Complete descriptions

### Category-Specific
- ✓ Concrete: Cement in materials, cum unit
- ✓ Steel: kg/MT unit, Fe grade
- ✓ Earthwork: cum/sqm unit
- ✓ And more...

## 🤝 Integration with Backend API

### FastAPI Example

```python
from fastapi import FastAPI, UploadFile, File
from boq_estimator import BOQEstimator
from boq_schema import ContractDetails
import tempfile

app = FastAPI()
estimator = BOQEstimator(anthropic_api_key=API_KEY)

@app.post("/estimate")
async def create_estimate(
    drawings: List[UploadFile] = File(...),
    project_name: str,
    location: str
):
    # Save uploaded files
    temp_files = []
    for drawing in drawings:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_file.write(await drawing.read())
        temp_files.append(temp_file.name)

    # Generate BOQ
    contract = ContractDetails(
        contract_name=project_name,
        location=location,
        client="API Client",
        department="CPWD"
    )

    boq = estimator.estimate_from_drawings(
        drawing_paths=temp_files,
        contract_details=contract
    )

    # Return JSON
    return boq.dict()
```

## 📈 Performance

- **Drawing Extraction**: ~10-30 seconds per page (depends on complexity)
- **BOQ Generation**: ~1-2 seconds for 100 items
- **Validation**: <1 second for typical BOQ

## 🐛 Error Handling

The system includes comprehensive error handling:

```python
try:
    boq = estimator.estimate_from_drawings(...)
except FileNotFoundError:
    print("Drawing file not found")
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    logger.error(f"Estimation failed: {e}")
```

## 📝 Logging

Enable detailed logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('boq_estimator.log'),
        logging.StreamHandler()
    ]
)
```

## 🔐 Security Considerations

- API keys stored in environment variables (not in code)
- Input validation on all user inputs
- File type verification for uploads
- Rate limiting recommended for API endpoints

## 🚦 Testing

Create unit tests:

```python
import unittest
from boq_calculator import ConcreteCalculator
from decimal import Decimal

class TestConcreteCalculator(unittest.TestCase):
    def test_foundation_calculation(self):
        calc = ConcreteCalculator()
        item = calc.calculate(
            item_no="1.1",
            concrete_type="foundation",
            grade=MaterialGrade.M20,
            length=Decimal("10"),
            width=Decimal("5"),
            thickness=Decimal("0.3")
        )
        self.assertEqual(item.quantity, Decimal("15.0"))
```

## 📞 Support

For issues or questions:
1. Check the `example_usage.py` file
2. Review validation messages for guidance
3. Consult CPWD specifications
4. Review module docstrings

## 📄 License

This system is designed for Indian government contracting and follows CPWD standards. Ensure compliance with local regulations and standards.

## 🎯 Roadmap

- [ ] Support for more work categories (plumbing, electrical, HVAC)
- [ ] Integration with BIM models
- [ ] Multi-language support (Hindi, regional languages)
- [ ] Mobile app for field verification
- [ ] Real-time rate updates from CPWD
- [ ] Machine learning for rate prediction
- [ ] Template library for common building types

---

**Built with ❤️ for Indian construction industry**

*Version: 1.0.0*
