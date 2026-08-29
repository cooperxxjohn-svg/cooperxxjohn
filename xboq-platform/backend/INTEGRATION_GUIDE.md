# Integration Guide: Open Source CV Tools for XBOQ

**Quick-start guide for integrating high-value open source computer vision tools**

---

## 🎯 Priority 1: eDOCr - Dimension Extraction from Drawings

### What It Does
Extracts dimension strings, annotations, and callouts from technical drawings using specialized OCR.

### Why Integrate
- **Accuracy:** Purpose-built for technical drawings (better than general OCR)
- **Validation:** Cross-check Claude's measurements
- **Data extraction:** Pull specifications directly from PDFs

### Installation

```bash
cd backend
source venv/bin/activate
pip install keras-ocr pillow
```

### Implementation

**File:** `backend/utils/drawing_ocr.py`

```python
"""
OCR for Technical Drawings - Extract Dimensions and Annotations
Uses keras-ocr (eDOCr approach) for construction drawing text extraction
"""

import keras_ocr
import numpy as np
from PIL import Image
import re
from typing import List, Dict, Tuple


class DrawingOCR:
    """Extract text from technical construction drawings"""
    
    def __init__(self):
        # Initialize keras-ocr pipeline
        # Downloads pretrained models on first run (~200MB)
        self.pipeline = keras_ocr.pipeline.Pipeline()
    
    def extract_text(self, image_path: str) -> List[Dict[str, any]]:
        """
        Extract all text from drawing with bounding boxes
        
        Args:
            image_path: Path to drawing image (PDF page converted to image)
        
        Returns:
            List of {text, box, confidence}
        """
        # Read image
        image = keras_ocr.tools.read(image_path)
        
        # Run OCR
        prediction_groups = self.pipeline.recognize([image])
        predictions = prediction_groups[0]
        
        # Format results
        results = []
        for text, box in predictions:
            results.append({
                'text': text,
                'box': box.tolist(),
                'confidence': 1.0  # keras-ocr doesn't provide confidence
            })
        
        return results
    
    def extract_dimensions(self, image_path: str) -> List[Dict[str, any]]:
        """
        Extract only dimension strings (e.g., "12'-6\"", "2440mm", "10'x12'")
        
        Returns:
            List of {dimension, value_feet, value_meters, original_text, box}
        """
        all_text = self.extract_text(image_path)
        
        dimensions = []
        
        # Regex patterns for common dimension formats
        patterns = [
            r"(\d+)'-(\d+)\"",           # 12'-6"
            r"(\d+)'",                    # 15'
            r"(\d+)\"",                   # 18"
            r"(\d+)mm",                   # 2440mm
            r"(\d+)cm",                   # 244cm
            r"(\d+)m",                    # 2.44m
            r"(\d+)x(\d+)",               # 10x12
            r"(\d+\.\d+)m",               # 12.5m
        ]
        
        for item in all_text:
            text = item['text']
            
            # Check all patterns
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    value_feet, value_meters = self._parse_dimension(text)
                    
                    dimensions.append({
                        'dimension': text,
                        'value_feet': value_feet,
                        'value_meters': value_meters,
                        'original_text': text,
                        'box': item['box']
                    })
                    break
        
        return dimensions
    
    def _parse_dimension(self, text: str) -> Tuple[float, float]:
        """Convert dimension string to numeric values in feet and meters"""
        
        # 12'-6" format
        feet_inches = re.search(r"(\d+)'-(\d+)\"", text)
        if feet_inches:
            feet = int(feet_inches.group(1))
            inches = int(feet_inches.group(2))
            total_feet = feet + (inches / 12)
            total_meters = total_feet * 0.3048
            return total_feet, total_meters
        
        # 15' format
        feet_only = re.search(r"(\d+)'", text)
        if feet_only:
            feet = int(feet_only.group(1))
            meters = feet * 0.3048
            return float(feet), meters
        
        # 18" format
        inches_only = re.search(r"(\d+)\"", text)
        if inches_only:
            inches = int(inches_only.group(1))
            feet = inches / 12
            meters = feet * 0.3048
            return feet, meters
        
        # 2440mm format
        mm = re.search(r"(\d+)mm", text)
        if mm:
            millimeters = int(mm.group(1))
            meters = millimeters / 1000
            feet = meters / 0.3048
            return feet, meters
        
        # 244cm format
        cm = re.search(r"(\d+)cm", text)
        if cm:
            centimeters = int(cm.group(1))
            meters = centimeters / 100
            feet = meters / 0.3048
            return feet, meters
        
        # 2.44m format
        meters_decimal = re.search(r"(\d+\.\d+)m", text)
        if meters_decimal:
            meters = float(meters_decimal.group(1))
            feet = meters / 0.3048
            return feet, meters
        
        # Default: return 0
        return 0.0, 0.0


# Usage example
if __name__ == '__main__':
    ocr = DrawingOCR()
    
    # Extract all text
    results = ocr.extract_text('path/to/drawing.png')
    print(f"Found {len(results)} text elements")
    
    # Extract only dimensions
    dimensions = ocr.extract_dimensions('path/to/drawing.png')
    print(f"Found {len(dimensions)} dimensions:")
    for dim in dimensions:
        print(f"  {dim['dimension']}: {dim['value_feet']:.2f}' = {dim['value_meters']:.2f}m")
```

### Integration with Existing Code

**Update:** `backend/modules/boq_generator.py`

```python
from utils.drawing_ocr import DrawingOCR

class BOQGenerator:
    def __init__(self):
        self.ocr = DrawingOCR()  # Add OCR engine
        # ... existing code
    
    def process_tender_document(self, file_path: str):
        # ... existing code to convert PDF to images
        
        # NEW: Extract dimensions via OCR
        dimensions = self.ocr.extract_dimensions(image_path)
        
        # Use OCR dimensions to validate Claude's output
        # Or use OCR as fallback if Claude fails
        
        # ... existing code
```

---

## 🎯 Priority 2: TF2DeepFloorplan - Floor Plan Room Detection

### What It Does
Deep learning model that detects room boundaries and room types from floor plans.

### Why Integrate
- **Cost:** Free vs. Claude API fees ($0.03-$0.15 per image)
- **Speed:** Local inference faster for batch processing
- **Offline:** Works without internet
- **Accuracy:** Trained on 1000s of floor plans

### Installation

**Option A: Docker (Recommended)**

```bash
# Pull pre-built image
docker pull zcemycl/deepfloorplan:latest

# Add to docker-compose.yml
services:
  deepfloorplan:
    image: zcemycl/deepfloorplan:latest
    ports:
      - "5001:5000"
    networks:
      - xboq-network

# Start service
docker-compose up -d deepfloorplan
```

**Option B: From Source**

```bash
git clone https://github.com/zcemycl/TF2DeepFloorplan
cd TF2DeepFloorplan
pip install -r requirements.txt
python app.py  # Starts Flask API on port 5000
```

### Implementation

**File:** `backend/utils/floor_plan_detector.py`

```python
"""
Floor Plan Detection using TF2DeepFloorplan
Alternative/backup to Claude API for room detection
"""

import requests
import numpy as np
from PIL import Image
import io
from typing import List, Dict


class FloorPlanDetector:
    """Detect rooms in floor plans using TF2DeepFloorplan"""
    
    def __init__(self, api_url: str = "http://localhost:5001"):
        self.api_url = api_url
    
    def detect_rooms(self, image_path: str) -> Dict:
        """
        Detect rooms from floor plan image
        
        Args:
            image_path: Path to floor plan image
        
        Returns:
            {
                'rooms': [
                    {
                        'type': 'bedroom',
                        'boundary': [[x1,y1], [x2,y2], ...],
                        'area_pixels': 12500,
                        'confidence': 0.95
                    },
                    ...
                ],
                'walls': [...],
                'doors': [...],
                'windows': [...]
            }
        """
        # Load image
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Send to TF2DeepFloorplan API
        files = {'image': image_bytes}
        response = requests.post(
            f"{self.api_url}/predict",
            files=files,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Floor plan detection failed: {response.text}")
        
        result = response.json()
        
        # Parse rooms
        rooms = self._parse_rooms(result)
        
        return {
            'rooms': rooms,
            'raw_output': result  # Full model output
        }
    
    def _parse_rooms(self, model_output: Dict) -> List[Dict]:
        """Parse model output into room objects"""
        rooms = []
        
        # TF2DeepFloorplan returns segmentation masks
        # Each pixel color = room type
        # Process segmentation → polygons
        
        # Simplified parsing (actual implementation depends on model output format)
        if 'room_masks' in model_output:
            for room_id, room_data in model_output['room_masks'].items():
                rooms.append({
                    'type': room_data.get('type', 'unknown'),
                    'boundary': room_data.get('boundary', []),
                    'area_pixels': room_data.get('area', 0),
                    'confidence': room_data.get('confidence', 0.0)
                })
        
        return rooms
    
    def is_available(self) -> bool:
        """Check if TF2DeepFloorplan service is running"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False


# Hybrid approach: TF2DeepFloorplan + Claude fallback
class HybridFloorPlanProcessor:
    """Use TF2DeepFloorplan for simple plans, Claude for complex"""
    
    def __init__(self):
        self.deepfloorplan = FloorPlanDetector()
        from utils.claude_client import get_claude_client
        self.claude = get_claude_client()
    
    def process(self, image_path: str) -> Dict:
        """
        Try TF2DeepFloorplan first, fallback to Claude if needed
        
        Strategy:
        1. Try TF2DeepFloorplan (fast, free)
        2. If confidence < 80%, use Claude API
        3. If TF2DeepFloorplan unavailable, use Claude
        """
        # Try TF2DeepFloorplan
        if self.deepfloorplan.is_available():
            try:
                result = self.deepfloorplan.detect_rooms(image_path)
                
                # Check confidence
                avg_confidence = np.mean([
                    room['confidence'] for room in result['rooms']
                ])
                
                if avg_confidence > 0.80:
                    print(f"✅ TF2DeepFloorplan succeeded (confidence: {avg_confidence:.2f})")
                    return result
                else:
                    print(f"⚠️ Low confidence ({avg_confidence:.2f}), falling back to Claude")
            
            except Exception as e:
                print(f"⚠️ TF2DeepFloorplan failed: {e}, falling back to Claude")
        
        # Fallback to Claude
        print("🤖 Using Claude API")
        return self._claude_detect_rooms(image_path)
    
    def _claude_detect_rooms(self, image_path: str) -> Dict:
        """Use Claude API for room detection"""
        # Existing Claude implementation
        # ... (current floor plan processing code)
        pass
```

### Integration with Existing Code

**Update:** `backend/modules/estimator.py`

```python
from utils.floor_plan_detector import HybridFloorPlanProcessor

class ConstructionEstimator:
    def __init__(self):
        self.floor_plan_processor = HybridFloorPlanProcessor()
        # ... existing code
    
    def process_floor_plan(self, file_path: str, trade: str = 'drywall'):
        # Use hybrid processor (TF2DeepFloorplan + Claude fallback)
        rooms_result = self.floor_plan_processor.process(file_path)
        
        # Continue with existing estimate generation
        # ... existing code
```

---

## 🎯 Priority 3: OpenConstructionEstimate Cost Database

### What It Does
Provides 55,000+ work items with real costs across 30 regions.

### Why Integrate
- **Replace hardcoded prices** with real regional data
- **Semantic matching:** "drywall 5/8 inch" → finds equivalent items
- **Multi-region support:** Expand internationally

### Installation

```bash
pip install qdrant-client
```

### Implementation

**File:** `backend/utils/cost_database.py`

```python
"""
Cost Database Integration - OpenConstructionEstimate
Regional pricing for 55K+ construction work items
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict
import numpy as np


class CostDatabase:
    """Access regional construction cost data"""
    
    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = "construction_costs"
    
    def search_item(self, description: str, region: str = "USA", limit: int = 5) -> List[Dict]:
        """
        Find work items matching description
        
        Args:
            description: "drywall 5/8 inch installation"
            region: "USA", "UK", "Canada", etc.
            limit: Number of results
        
        Returns:
            [
                {
                    'description': 'Drywall installation, 5/8" thickness',
                    'unit_cost': 2.50,
                    'unit': 'sqft',
                    'region': 'USA',
                    'material_cost': 1.20,
                    'labor_cost': 1.30,
                    'confidence': 0.95
                },
                ...
            ]
        """
        # Convert description to embedding
        # (Simplified - actual implementation needs embedding model)
        # vector = self._embed(description)
        
        # Search Qdrant
        # results = self.client.search(
        #     collection_name=self.collection_name,
        #     query_vector=vector,
        #     limit=limit,
        #     query_filter={"region": region}
        # )
        
        # For now, return mock data
        # TODO: Integrate actual OpenConstructionEstimate database
        return [
            {
                'description': 'Drywall installation, 5/8" thickness, taped and finished',
                'unit_cost': 2.50,
                'unit': 'sqft',
                'region': region,
                'material_cost': 1.20,
                'labor_cost': 1.30,
                'confidence': 0.95,
                'source': 'OpenConstructionEstimate'
            }
        ]
    
    def _embed(self, text: str) -> List[float]:
        """Convert text to vector embedding"""
        # Use sentence-transformers or OpenAI embeddings
        # from sentence_transformers import SentenceTransformer
        # model = SentenceTransformer('all-MiniLM-L6-v2')
        # return model.encode([text])[0].tolist()
        pass


# Usage in estimator
def get_material_cost(description: str, quantity: float, region: str = "USA") -> Dict:
    """Get cost for material/work item"""
    cost_db = CostDatabase()
    
    # Search database
    matches = cost_db.search_item(description, region=region, limit=1)
    
    if matches:
        item = matches[0]
        total_cost = item['unit_cost'] * quantity
        
        return {
            'description': description,
            'quantity': quantity,
            'unit': item['unit'],
            'unit_cost': item['unit_cost'],
            'total_cost': total_cost,
            'material_cost': item['material_cost'] * quantity,
            'labor_cost': item['labor_cost'] * quantity,
            'region': region,
            'confidence': item['confidence']
        }
    
    # Fallback to hardcoded prices
    return None
```

---

## 📦 Update Requirements

**File:** `backend/requirements.txt`

```txt
# Existing dependencies
Flask==2.3.3
flask-cors==4.0.0
# ... existing packages

# NEW: Computer Vision Integration
keras-ocr==0.9.3              # eDOCr dimension extraction
pillow==10.0.0                # Image processing (already exists)

# NEW: Cost Database (optional)
qdrant-client==1.7.0          # Vector search for cost matching

# NEW: Custom model deployment (optional)
# Uncomment if deploying custom YOLO models
# ultralytics==8.1.0          # YOLOv8/v11
# onnxruntime==1.17.0         # Fast inference
# torch==2.2.0                # PyTorch (training only)
```

---

## 🧪 Testing the Integrations

### Test OCR Dimension Extraction

```bash
cd backend
python -c "
from utils.drawing_ocr import DrawingOCR
ocr = DrawingOCR()
dims = ocr.extract_dimensions('test_drawing.png')
print(f'Found {len(dims)} dimensions')
for d in dims:
    print(f\"  {d['dimension']}: {d['value_feet']:.1f}' = {d['value_meters']:.2f}m\")
"
```

### Test TF2DeepFloorplan

```bash
# Start service
docker-compose up -d deepfloorplan

# Test
curl -X POST http://localhost:5001/predict \
  -F "image=@test_floor_plan.png" \
  | jq .
```

### Test Hybrid Processor

```python
from utils.floor_plan_detector import HybridFloorPlanProcessor

processor = HybridFloorPlanProcessor()
result = processor.process('test_floor_plan.png')
print(f"Detected {len(result['rooms'])} rooms")
```

---

## 📊 Expected Results

### Before Integration

- **Cost:** $0.10/floor plan (Claude API only)
- **Processing time:** 15-30 seconds
- **Dimension extraction:** Manual/Claude only
- **Offline mode:** ❌ No

### After Integration

- **Cost:** $0.03/floor plan (67% reduction)
- **Processing time:** 5-15 seconds (50% faster)
- **Dimension extraction:** ✅ Automated OCR
- **Offline mode:** ✅ Yes (TF2DeepFloorplan)
- **Accuracy:** +5-10% (OCR validation + better room detection)

---

## 🚀 Next Steps

1. **Week 1:** Implement eDOCr for dimension extraction
2. **Week 2:** Deploy TF2DeepFloorplan in Docker
3. **Week 3:** A/B test: Claude vs. Hybrid approach
4. **Week 4:** Integrate cost database (if needed)

---

**Last Updated:** May 24, 2026  
**Maintained by:** XBOQ Platform Team
