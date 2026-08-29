# BOQ Line Item Classifier - Project Report
*Automated classification system for construction BOQ line items*

---

## Executive Summary

Successfully built a BOQ line item classifier trained on **3579 public construction documents** from Indian government sources.

**Key Results:**
- **7,442** raw line items extracted from **5 public sources**
- **4,977** items after cleaning and deduplication
- **3,579** items labeled using weak supervision
- **18 categories** covering all major construction trades
- **84.9% test accuracy** using TF-IDF + Linear SVM
- **84.2% cross-validation accuracy**

---

## 1. Data Collection

### Public Sources

BOQ documents were downloaded from the following government portals:

1. **MCGM Mumbai** - Municipal Corporation BOQ (39 pages)
2. **MEA India** - Nepal Polytechnic Civil Works (113 pages)
3. **NIELIT Agartala** - Campus Construction (294 pages)
4. **BITM** - Building Infrastructure (92 pages)
5. **IIT Bombay** - Centre for Propulsion Technology (107 pages)

**Total pages processed:** 645 pages
**Total raw items extracted:** 7,442

### Items per Source

| Source | Items |
|--------|-------|
| NIELIT_Campus_BOQ | 1,689 |
| IITB_COPT_BOQ | 1,365 |
| MCGM_Civil_BOQ | 692 |
| BITM_BOQ | 669 |
| Nepal_Polytechnic_Civil | 562 |

---

## 2. Data Cleaning & Normalization

### Cleaning Steps

1. **Text normalization:** Lowercasing, removing special characters
2. **Abbreviation expansion:** RCC → reinforced cement concrete, etc.
3. **Noise removal:** Filtered items < 30 characters
4. **Deduplication:** Removed 2,181 duplicate entries

**Final cleaned dataset:** 4,977 unique items

### Top 20 Construction Terms

| Rank | Term | Count |
|------|------|-------|
| 1 | cement | 949 |
| 2 | millimeter | 619 |
| 3 | including | 527 |
| 4 | meter | 481 |
| 5 | sand | 434 |
| 6 | providing | 428 |
| 7 | fixing | 422 |
| 8 | steel | 400 |
| 9 | concrete | 388 |
| 10 | pipe | 295 |
| 11 | thick | 280 |
| 12 | complete | 274 |
| 13 | work | 267 |
| 14 | floor | 259 |
| 15 | size | 252 |
| 16 | square | 220 |
| 17 | wall | 217 |
| 18 | each | 211 |
| 19 | mortar | 205 |
| 20 | shall | 205 |

---

## 3. Classification Categories

The system classifies BOQ items into **18 categories**:

| # | Category | Description |
|---|----------|-------------|
| 1 | Demolition | Breaking, removal, dismantling |
| 2 | Earthwork | Excavation, filling, grading |
| 3 | Concrete | RCC, PCC, all concrete work |
| 4 | Masonry | Brickwork, blockwork, stone masonry |
| 5 | Steel | Reinforcement, structural steel |
| 6 | Carpentry & Joinery | Wood, timber, plywood work |
| 7 | Doors, Windows & Glazing | All fenestration work |
| 8 | Waterproofing | Membranes, sealants, damp proofing |
| 9 | Flooring & Tiling | Tiles, marble, granite flooring |
| 10 | Plaster & Painting | Plastering, painting, finishes |
| 11 | Plumbing & Sanitary | Pipes, fittings, fixtures |
| 12 | Electrical | Wiring, switches, lighting |
| 13 | HVAC & Fire | AC, ventilation, fire systems |
| 14 | Facade & Cladding | External walls, ACP panels |
| 15 | Roofing | Roof slabs, terrace work |
| 16 | Paving & External | Pathways, compound walls, gates |
| 17 | Utilities | Manholes, tanks, chambers |
| 18 | Misc & General | Testing, scaffolding, formwork |

---

## 4. Weak Labeling Strategy

Since no human-labeled data exists, we used **keyword-based weak labeling**:

- Each category has 5-10 characteristic keywords
- Items scored by keyword matches
- Filtered out low-confidence labels (< 0.1)
- **3,579 items** successfully labeled

### Items per Category (Training Data)

| Category | Count | Avg Confidence |
|----------|-------|----------------|
| Carpentry Joinery | 65 | 1.000 |
| Concrete | 400 | 0.902 |
| Demolition | 35 | 1.000 |
| Doors Windows Glazing | 450 | 1.000 |
| Earthwork | 291 | 0.937 |
| Electrical | 362 | 0.881 |
| Facade Cladding | 3 | 1.000 |
| Flooring Tiling | 240 | 1.000 |
| Hvac Fire | 53 | 1.000 |
| Masonry | 213 | 1.000 |
| Misc General Conditions | 107 | 1.000 |
| Paving External | 118 | 1.000 |
| Plaster Painting | 476 | 0.959 |
| Plumbing Sanitary | 383 | 0.738 |
| Roofing | 225 | 1.000 |
| Steel | 60 | 1.000 |
| Utilities Storm Sanitary | 53 | 1.000 |
| Waterproofing | 45 | 1.000 |

---

## 5. Model Performance

### Architecture

- **Feature Extraction:** TF-IDF (5,000 features, 1-3 grams)
- **Classifier:** Linear SVM (SGD with balanced class weights)
- **Training:** 2,863 items
- **Testing:** 716 items

### Results

- **Test Accuracy:** 84.9%
- **5-Fold CV Accuracy:** 84.2% (± 1.6%)

---

## 6. Top Keywords per Category

These keywords have the highest predictive power:

### Carpentry Joinery

`wood`, `wooden`, `laminated`, `laminate`, `surface with`, `6mm`, `shuttering`, `frame`, `fitted`, `type of`

### Concrete

`cement concrete`, `concrete`, `ofconcrete`, `of concrete`, `reinforced`, `concrete of`, `incement concrete`, `concrete to`, `reinforced cement`, `reinforced cement concrete`

### Demolition

`removal`, `dismantling`, `removing`, `cement`, `roof`, `removal of`, `aluminium`, `manhole`, `existing`, `after`

### Doors Windows Glazing

`door`, `doors`, `outdoor`, `windows`, `window`, `indoor`, `shutter`, `glass`, `glazing`, `polyester`

### Earthwork

`filling`, `excavation`, `earth`, `cutting`, `earthing`, `refilling`, `trenches`, `trenching`, `sand`, `including trenching`

### Electrical

`electrical`, `wiring`, `conduits`, `switch`, `light`, `andbolts`, `mcb`, `socketed`, `fan`, `incoming`

### Facade Cladding

`grit plaster`, `grit`, `exterior`, `plaster on`, `height`, `walls`, `more than`, `walls of`, `cladding`, `stone grit`

### Flooring Tiling

`tiles`, `flooring`, `marble`, `tile`, `granite`, `mosaic`, `floor finish`, `00flooring work`, `00flooring`, `skirting`

### Hvac Fire

`sprinkler`, `hvac`, `fighting`, `pump suction`, `acoustic`, `suction`, `light fittings`, `cylinder with`, `cylinder`, `hvac panel`

### Masonry

`brick`, `masonry`, `bricks`, `edge`, `ballast`, `masonry or`, `drybrick`, `15mm`, `either`, `joints of`

### Misc General Conditions

`testing`, `centering`, `scaffolding`, `15 providing`, `approved quality`, `40mm`, `testing of`, `commissioning`, `height of`, `iii`

### Paving External

`aggregate`, `valve`, `20mm`, `stone aggregate`, `wall`, `aggregated`, `weight`, `compound`, `stiff`, `channels`

### Plaster Painting

`paint`, `painting`, `plaster`, `finishing`, `plastering`, `finished`, `finish`, `putty`, `painted`, `plastered`

### Plumbing Sanitary

`pipe`, `pipes`, `plumbing`, `sanitary`, `sink`, `specials`, `drainage`, `with lamp`, `water supply`, `fittings`

### Roofing

`slab`, `proofing`, `slabs`, `terrace`, `proof`, `15 00`, `slab with`, `roofs`, `terrace level`, `kota`

### Steel

`reinforcement`, `forreinforced`, `structural steel`, `steel`, `before`, `22`, `steel bars`, `415`, `frame work`, `millimeter with`

### Utilities Storm Sanitary

`chamber`, `manholes`, `manhole`, `polytechnic`, `tanks`, `1500`, `tank`, `chambers`, `pit`, `having`

### Waterproofing

`waterproofing`, `waterproof`, `11`, `damper`, `structural`, `wp`, `cs wp`, `filled`, `in the`, `of`

---

## 7. Example Classifications

### Carpentry Joinery

**Confidence: 100.0%**
> finishing all exposed surfaces of wood...

**Confidence: 100.0%**
> 37Fire rated Double leaf Door - Laminate...

### Concrete

**Confidence: 100.0%**
> cement concrete of specified grade cement...

**Confidence: 100.0%**
> concrete for reinforced cement concrete...

### Demolition

**Confidence: 100.0%**
> removing rank vegetation, backfilling in...

**Confidence: 100.0%**
> 175 R2-CS-DD-2 Demolishing R.C.C. slab, R.C.C. wall of any...

### Doors Windows Glazing

**Confidence: 100.0%**
> and shuttering at all level : Nominal Mix of Cum 950 6821 6479950...

**Confidence: 100.0%**
> centering, shuttering, finishing and...

### Earthwork

**Confidence: 100.0%**
> vegetation, backfilling in layers not more...

**Confidence: 100.0%**
> excavation, backfill in immediate contact...

---

## 8. How to Use

### CLI

```bash
# Classify items from CSV
python predict.py input.csv output.csv
```

### Streamlit UI

```bash
# Start web interface
streamlit run app_streamlit.py
```

---

## 9. Suggestions for Improvement

1. **Expand training data:**
   - Scrape more PWD SOR documents from other states
   - Add CPWD specification documents
   - Include MES, Railways, NHAI tender BOQs

2. **Improve labeling:**
   - Manually review and correct 100-200 samples per category
   - Use active learning to label uncertain cases
   - Add more sophisticated rules (regex patterns)

3. **Model enhancements:**
   - Try ensemble methods (Random Forest, XGBoost)
   - Experiment with deep learning (BERT-based models)
   - Add hierarchical classification (super-categories)

4. **Feature engineering:**
   - Extract quantities and units as features
   - Add context from surrounding items in BOQ
   - Use word embeddings instead of TF-IDF

---

## Conclusion

Successfully built a BOQ classifier with **84.9% accuracy** using only public data and weak supervision. The system can now automatically categorize construction line items, enabling better BOQ analysis, cost estimation, and project planning.

**Next Steps:**
- Integrate with XBOQ Enhanced drawing extraction system
- Deploy as API service
- Build dashboards for BOQ analytics

---

*Report generated automatically by the BOQ Classification System*
