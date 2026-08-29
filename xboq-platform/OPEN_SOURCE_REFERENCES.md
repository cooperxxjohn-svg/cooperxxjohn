# Open Source References for XBOQ Platform

**Computer Vision & AI Tools for Construction Takeoff and Estimating**

This document catalogs open source projects, datasets, and research tools that can enhance the XBOQ platform's capabilities in automated construction takeoff, floor plan analysis, and cost estimation.

---

## 🎯 Integration Priority

### High Priority (Immediate Value)

| Project | Use Case | Integration Path |
|---------|----------|------------------|
| **TF2DeepFloorplan** | Floor plan room detection | Add as alternative to Claude API for room detection |
| **CubiCasa5K** | Training dataset | Fine-tune custom models for floor plan segmentation |
| **eDOCr** | Dimension extraction | Extract measurements from PDF technical drawings |
| **OpenConstructionEstimate** | Cost database | Integrate 55K+ work items for cost estimation |

### Medium Priority (Strategic Enhancements)

| Project | Use Case | Integration Path |
|---------|----------|------------------|
| **OpenConstructionERP** | Full pipeline reference | Learn from complete takeoff workflow implementation |
| **QTO Buccaneer** | BIM/IFC support | Add IFC file processing for BIM-based projects |
| **Blueprint Symbol Detection** | Symbol recognition | Pre-trained YOLO model for detecting blueprint symbols |

### Research/Future (Long-term Roadmap)

| Project | Use Case | Integration Path |
|---------|----------|------------------|
| **CV4AEC Challenge** | Scan-to-BIM | 3D point cloud processing for site verification |
| **Graph2Plan** | Plan generation | Reverse engineering: generate plans from descriptions |
| **SODA Dataset** | Site monitoring | Construction site object detection for progress tracking |

---

## 📦 Full Takeoff & Estimating Pipelines

### OpenConstructionERP
- **Repository:** https://github.com/datadrivenconstruction/OpenConstructionERP
- **License:** AGPL-3.0
- **Stack:** Python
- **Capabilities:**
  - PDF, CAD (DWG), and BIM takeoff
  - AI cost matching
  - Complete BOQ generation from photos, text, or drawings
  - DWG polyline measurement
  - PDF measurement for construction drawings
- **Features:**
  - 42 regional cost catalogues
  - 21 languages
  - 71 modules
  - Full construction ERP suite

**Integration Potential:**
- Use as reference implementation for complete takeoff workflow
- Adopt cost catalogue structure for international expansion
- Learn from their PDF/DWG processing pipeline

**XBOQ Platform Benefits:**
- See how they handle multi-format input (PDF, DWG, photos)
- Study their cost matching algorithms
- Reference their BOQ output format standards

---

### ProTakeoff
- **Repository:** https://github.com/Halo7726/protakeoff
- **Stack:** Python
- **Capabilities:**
  - AI estimating tool for contractors
  - Digital takeoffs with marked-up drawings
  - Area and linear measurements on blueprints
  - Estimate generation

**Integration Potential:**
- Integrate their takeoff canvas for interactive measurement UI
- Adopt their contractor-focused workflow patterns

**XBOQ Platform Benefits:**
- Frontend UI patterns for interactive drawing markup
- Measurement tools (area, linear, count)
- Export formats contractors actually use

---

### OpenConstructionEstimate-DDC-CWICR
- **Repository:** https://github.com/datadrivenconstruction/OpenConstructionEstimate-DDC-CWICR
- **Stack:** Python, Qdrant vector DB
- **Capabilities:**
  - Multilingual cost database (55K+ work items, 27K+ resources, 30 regions)
  - PDF takeoff module with auto-quantity extraction
  - Semantic search via Qdrant

**Integration Potential:** ⭐ **HIGH PRIORITY**
- Replace hardcoded material prices with their cost database
- Use Qdrant for semantic matching of extracted items to cost catalogue
- Add multi-region pricing support

**XBOQ Platform Benefits:**
- **Immediate:** 55,000 pre-built work items with real costs
- **Strategic:** Multi-region support (30 countries)
- **Technical:** Semantic search for "drywall 5/8 inch" → matches equivalent items

**Integration Steps:**
```bash
# 1. Add Qdrant to requirements
pip install qdrant-client

# 2. Import their cost database
# 3. Build semantic embeddings for our extracted BOQ items
# 4. Match extracted items → cost database items
# 5. Return accurate regional pricing
```

---

## 🏗️ Floor Plan / Drawing Segmentation & Recognition

### TF2DeepFloorplan ⭐ **RECOMMENDED**
- **Repository:** https://github.com/zcemycl/TF2DeepFloorplan
- **Stack:** TensorFlow 2, Docker, TFLite, Flask API
- **Capabilities:**
  - Multi-task deep neural network
  - Detects room boundaries AND room types simultaneously
  - Room-boundary-Guided Attention mechanism
  - TFLite export for mobile deployment
  - REST API included

**Integration Potential:** ⭐ **HIGH PRIORITY**
- Deploy as alternative/backup to Claude API for floor plan room detection
- Use for batch processing (cheaper than API calls)
- Offline mode support

**XBOQ Platform Benefits:**
- **Cost:** Free processing vs. Claude API costs
- **Speed:** Local inference faster for batch jobs
- **Accuracy:** Trained on 1000s of floor plans
- **Deployment:** Docker container ready to deploy

**Integration Steps:**
```bash
# 1. Clone and set up
git clone https://github.com/zcemycl/TF2DeepFloorplan
cd TF2DeepFloorplan
docker build -t deepfloorplan .

# 2. Add to docker-compose.yml
services:
  deepfloorplan:
    image: deepfloorplan
    ports:
      - "5001:5000"

# 3. Create backend/modules/floor_plan_vision.py
# 4. Call API: POST /predict with floor plan image
# 5. Parse room boundaries and types
# 6. Hybrid: use for basic detection, Claude for measurements
```

---

### DeepFloorplan (ICCV 2019)
- **Repository:** https://github.com/zlzeng/DeepFloorplan
- **Paper:** ICCV 2019
- **Stack:** TensorFlow
- **Capabilities:**
  - Multi-task network for floor plan element recognition
  - Models spatial relationships between room-boundary and room-type

**Integration Potential:**
- Research reference for understanding floor plan semantics
- Foundational work that TF2DeepFloorplan builds on

---

### AFPlan — Architectural Floor Plan Analysis
- **Repository:** https://github.com/cansik/architectural-floor-plan
- **Stack:** Python, OpenCV
- **Capabilities:**
  - Fast room detection on non-standardized floor plans
  - Morphological cleaning (noise removal)
  - Machine learning classifier
  - Convex hull gap-closing
  - Connected component analysis

**Integration Potential:**
- Preprocessing step before Claude API or TF2DeepFloorplan
- Handle "messy" real-world plans with noise, coffee stains, etc.

**XBOQ Platform Benefits:**
- Clean up scanned PDFs before processing
- Improve detection accuracy on low-quality uploads

---

### Floor Plan Room Segmentation (U-Net + ResNet)
- **Repository:** https://github.com/ozturkoktay/floor-plan-room-segmentation
- **Stack:** PyTorch (U-Net, EfficientNet, ResNet, PSPNet, DeepLabV3+)
- **Capabilities:**
  - Semantic segmentation: rooms, walls, doors, windows
  - Modular encoder design (swap backbones easily)

**Integration Potential:**
- Use for pixel-level segmentation → accurate area calculations
- Train custom model on construction-specific plans

---

### Graph2Plan
- **Repository:** https://github.com/HanHan55/Graph2plan
- **Stack:** Python
- **Capabilities:**
  - Converts layout graph + building boundary → full floor plan
  - Deep neural network–based plan generation

**Integration Potential:**
- Future feature: "Generate floor plan from text description"
- Reverse engineering: understand plan structure semantically

---

## 📝 OCR & Text Extraction from Technical Drawings

### eDOCr ⭐ **RECOMMENDED**
- **Repository:** https://github.com/javvi51/eDOCr
- **Stack:** Python (keras-ocr)
- **Capabilities:**
  - End-to-end OCR for mechanical engineering drawings
  - Extracts dimensions, tolerances, annotations (GD&T data)
  - Packaged system based on keras-ocr

**Integration Potential:** ⭐ **HIGH PRIORITY**
- Extract dimension strings from construction drawings
- Read callouts, notes, and specifications
- Complement Claude's vision with specialized OCR

**XBOQ Platform Benefits:**
- **Accuracy:** Purpose-built for technical drawings
- **Data:** Extract measurements directly (e.g., "12'-6\"", "2440mm")
- **Automation:** Reduce manual dimension entry

**Integration Steps:**
```bash
# 1. Install keras-ocr
pip install keras-ocr

# 2. Create backend/utils/drawing_ocr.py
# 3. Process PDF → image → OCR → extract dimensions
# 4. Parse dimension strings: "12'-6\"" → 12.5 feet
# 5. Use for BOQ quantity validation
```

---

## 🏢 AEC-Specific Computer Vision

### AECVision
- **Repository:** https://github.com/PawelKinczyk/AECVision
- **Stack:** Python, YOLOv5
- **Capabilities:**
  - Computer vision for construction documentation
  - Element detection and classification in drawings and images

**Integration Potential:**
- Train YOLOv5 on construction-specific elements
- Detect doors, windows, fixtures in drawings

---

### Awesome-AECO ⭐ **REFERENCE**
- **Repository:** https://github.com/osama-ata/Awesome-AECO
- **Type:** Curated resource list
- **Contents:**
  - BIM workflows
  - CAD modeling
  - Simulation tools
  - Smart buildings
  - Digital twins
  - Robotics in construction

**Integration Potential:**
- Research repository for discovering new tools
- Stay updated on AEC open source ecosystem

---

### AEC Open Source Directory
- **Repository:** https://github.com/opensource-construction/osc-directory
- **Type:** Community-maintained directory
- **Contents:** Open source projects specifically for AEC industry

---

### QTO Buccaneer
- **Repository:** https://github.com/simondilhas/qto_buccaneer
- **Stack:** Python
- **Capabilities:**
  - Extract and calculate quantities from IFC (Industry Foundation Classes) BIM models
  - Explore IFC structure
  - Quantity takeoff from BIM

**Integration Potential:**
- Add IFC/BIM file support to XBOQ platform
- When drawings are paired with BIM files, extract quantities directly

**XBOQ Platform Benefits:**
- **Format support:** IFC files (Revit, ArchiCAD exports)
- **Accuracy:** BIM models have embedded quantity data
- **Workflow:** Many architects provide both PDF plans + IFC models

---

## 📊 Datasets (Essential for Training Custom Models)

### CubiCasa5K ⭐ **ESSENTIAL**
- **Repository:** https://github.com/CubiCasa/CubiCasa5k
- **Paper:** SCIA 2019
- **Contents:**
  - 5,000 annotated floor plan images
  - 80+ categories (rooms, walls, doors, windows, stairs, etc.)
  - Dense polygon annotations
  - Multi-task CNN implementation included

**Compatible Formats:**
- YOLOv5, YOLOv7, YOLOv8, YOLOv11 (via Roboflow export)

**Integration Potential:** ⭐ **HIGH PRIORITY**
- Train custom YOLO model for XBOQ-specific floor plan detection
- Fine-tune on construction drawings (vs. residential plans)
- Benchmark accuracy against Claude API

**XBOQ Platform Benefits:**
- **Custom model:** Train on YOUR data (government tenders, commercial drawings)
- **Accuracy:** Specialized for construction vs. general floor plans
- **Cost:** One-time training cost vs. ongoing API fees

**Training Steps:**
```bash
# 1. Download CubiCasa5K dataset
# 2. Add 100-500 of your own annotated BOQ drawings
# 3. Fine-tune YOLOv8 or YOLOv11
# 4. Export to ONNX for fast inference
# 5. Deploy in backend/models/
# 6. A/B test: Claude API vs. custom model
```

---

### Blueprint Symbol Detection-BR (Roboflow)
- **Dataset:** https://universe.roboflow.com/conti-z14wj/blueprint-symbol-detection-br
- **Contents:**
  - Annotated construction blueprint symbols
  - Pre-trained model included
  - Hosted API available
  - 30+ light-source image classes

**Integration Potential:**
- Drop-in YOLO model for symbol detection
- Detect doors, windows, electrical symbols, plumbing fixtures

**XBOQ Platform Benefits:**
- **Ready-to-use:** No training required
- **API:** Hosted inference available
- **Accuracy:** Pre-trained on real blueprints

**Integration Steps:**
```bash
# 1. Sign up for Roboflow API key (free tier available)
# 2. POST image to API: /blueprint-symbol-detection-br/1
# 3. Receive bounding boxes + symbol classes
# 4. Count symbols: "10 doors, 15 windows, 20 electrical outlets"
# 5. Add to BOQ automatically
```

---

### SODA — Site Object Detection Dataset
- **Paper:** https://arxiv.org/pdf/2202.09554
- **Contents:**
  - 19,000+ annotated construction site images
  - Object detection: safety equipment, workers, machinery
  - Not drawing-based, but site photo–based

**Integration Potential:**
- Future feature: "Upload site photos to verify progress"
- Safety compliance checking
- Progress monitoring vs. BOQ

---

### CV4AEC Challenge Dataset (Stanford/CVPR 2024)
- **Repository:** https://github.com/GradientSpaces/cv4aec-challenge
- **Workshop:** https://cv4aec.github.io/
- **Contents:**
  - Scan-to-BIM challenge dataset
  - 3D scan data paired with BIM models
  - Tasks: floor detection, room segmentation, structural element recognition

**Integration Potential:**
- Research frontier for 3D point cloud processing
- Future: "Upload 3D scan → generate BOQ"

---

## 📚 Research Papers with Released Code

| Paper | Conference | Task | Method | Code | mAP/Accuracy |
|-------|-----------|------|--------|------|--------------|
| DeepFloorplan | ICCV 2019 | Room + boundary segmentation | Multi-task CNN | [Link](https://github.com/zlzeng/DeepFloorplan) | - |
| CubiCasa5K | SCIA 2019 | 80+ category floor plan parsing | Multi-task CNN | [Link](https://github.com/CubiCasa/CubiCasa5k) | - |
| Symbol Detection in Construction Drawings | IJDAR 2024 | Symbol detection | YOLOv7 + Keypoint R-CNN | Paper only | 83% mAP |
| Explainable AI for Symbol Detection | 2024 | Symbol classification + explainability | CNN + GradCAM | ResearchGate | - |
| Text Detection on Floor Plans | 2023 | OCR of dimension labels | DL + synthetic data | ScienceDirect | - |

---

## 🚀 Recommended Integration Roadmap

### Phase 1: Quick Wins (Week 1-2)

**1. Add eDOCr for Dimension Extraction**
```bash
pip install keras-ocr
# Integrate into backend/utils/drawing_ocr.py
# Extract dimensions from PDFs → validate Claude's measurements
```

**2. Deploy TF2DeepFloorplan as Backup**
```bash
docker run -p 5001:5000 deepfloorplan
# Use for batch processing or when Claude API is down
# Cost savings: $0 vs. $0.03/image with Claude
```

**3. Integrate Blueprint Symbol Detection API**
```bash
# Roboflow API integration
# Count doors, windows, fixtures automatically
# Add to BOQ line items
```

**Expected Impact:**
- 30% cost reduction (TF2DeepFloorplan for simple plans)
- 50% faster dimension extraction (eDOCr)
- 90% automation for symbol counting

---

### Phase 2: Custom Model Training (Week 3-6)

**4. Fine-tune YOLOv11 on CubiCasa5K + Your Data**
```bash
# 1. Download CubiCasa5K (5,000 plans)
# 2. Annotate 100-500 of your BOQ drawings
# 3. Fine-tune YOLOv11
# 4. Deploy custom model
# 5. A/B test vs. Claude API
```

**5. Integrate OpenConstructionEstimate Cost Database**
```bash
pip install qdrant-client
# Import 55,000 work items
# Semantic matching: extracted items → cost database
# Multi-region pricing support
```

**Expected Impact:**
- 95%+ accuracy on construction-specific plans
- Regional cost databases (30 countries)
- Custom model = no ongoing API costs

---

### Phase 3: Advanced Features (Month 2-3)

**6. Add IFC/BIM Support (QTO Buccaneer)**
```bash
# Accept .ifc uploads alongside PDFs
# Extract quantities directly from BIM models
# Cross-validate: PDF vs. BIM quantities
```

**7. Preprocessing Pipeline (AFPlan)**
```bash
# Clean noisy/scanned PDFs before processing
# Morphological noise removal
# Improve accuracy on low-quality uploads
```

**8. Research Integration (CV4AEC, Graph2Plan)**
```bash
# Explore 3D scan processing
# "Generate plan from description" feature
# Point cloud → BOQ
```

**Expected Impact:**
- BIM file support = 40% of commercial projects
- Noise cleaning = 20% accuracy improvement on scans
- Future-proof with cutting-edge research

---

## 💰 Cost-Benefit Analysis

### Current: Claude API Only

| Metric | Value |
|--------|-------|
| Cost per floor plan | $0.03 - $0.15 |
| Processing time | 10-30 seconds |
| Accuracy | 85-95% (varies by quality) |
| Offline mode | ❌ No |
| Custom training | ❌ No |

### With Integrations: Hybrid Approach

| Metric | Value | Change |
|--------|-------|--------|
| Cost per floor plan | $0.01 - $0.05 | 🟢 67% reduction |
| Processing time | 5-15 seconds | 🟢 50% faster |
| Accuracy | 90-98% | 🟢 +5% improvement |
| Offline mode | ✅ Yes (TF2DeepFloorplan) | 🟢 New capability |
| Custom training | ✅ Yes (CubiCasa5K) | 🟢 New capability |
| Symbol detection | ✅ Automated | 🟢 New capability |
| Dimension OCR | ✅ Automated | 🟢 New capability |
| BIM/IFC support | ✅ Yes | 🟢 New capability |
| Regional pricing | ✅ 30 countries | 🟢 New capability |

**ROI Calculation:**
- Current: 1,000 plans/month × $0.10 = $100/month
- With integrations: 1,000 plans/month × $0.03 = $30/month
- **Savings: $70/month = $840/year**
- **Break-even: ~2 weeks of development**

---

## 🛠️ Technical Stack Additions

### New Dependencies

```txt
# Computer Vision
keras-ocr==0.9.3          # eDOCr dimension extraction
qdrant-client==1.7.0      # Vector search for cost matching

# Optional (if deploying custom models)
ultralytics==8.1.0        # YOLOv8/v11
onnxruntime==1.17.0       # Fast inference
torch==2.2.0              # PyTorch for model training
torchvision==0.17.0       # Vision utilities
```

### New Docker Services

```yaml
# docker-compose.yml additions

services:
  # Existing: postgres, redis, backend, frontend

  deepfloorplan:
    image: zcemycl/deepfloorplan:latest
    ports:
      - "5001:5000"
    networks:
      - xboq-network

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
    networks:
      - xboq-network

volumes:
  qdrant_storage:
```

---

## 📖 Additional Resources

### Research Papers
- **DeepFloorplan (ICCV 2019):** https://arxiv.org/abs/1908.11025
- **CubiCasa5K (SCIA 2019):** https://arxiv.org/abs/1904.01920
- **Symbol Detection in Construction Drawings (IJDAR 2024):** https://link.springer.com/article/10.1007/s10032-024-00492-9
- **SODA Dataset (2022):** https://arxiv.org/pdf/2202.09554

### Workshops & Challenges
- **CV4AEC @ CVPR 2024:** https://cv4aec.github.io/
- **Computer Vision in the Built Environment Workshop**

### Community Resources
- **Awesome-AECO:** https://github.com/osama-ata/Awesome-AECO
- **AEC Open Source Directory:** https://github.com/opensource-construction/osc-directory

---

## 🎯 Next Steps

1. **Review this document** with the team
2. **Prioritize integrations** based on immediate business needs
3. **Proof of concept:** Deploy TF2DeepFloorplan + eDOCr in 1 week
4. **A/B test:** Compare Claude API vs. hybrid approach
5. **Iterate:** Based on accuracy and cost metrics, adjust strategy

---

**Document Version:** 1.0  
**Last Updated:** May 24, 2026  
**Maintained by:** XBOQ Platform Team  
**Related Docs:** `backend/README.md`, `DEPLOYMENT.md`, `DAY_4_PLAN.md`
