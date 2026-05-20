# Painting.ai MVP Product Specification

## Vision
AI-powered takeoff and estimating software for painting contractors in the USA.

## Target Market
- **Primary:** Commercial painting contractors ($5M-50M annual revenue)
- **Secondary:** Residential painting contractors ($1M-5M annual revenue)
- **Market Size:** 300,000+ painting contractors in USA, $50-60B annual market

## Core Value Proposition
"Generate accurate painting takeoffs in 5 minutes instead of 4 hours"

## MVP Features (Week 1)

### 1. Project Upload
- Accept PDF architectural drawings (floor plans, elevations)
- Support multi-page drawing sets
- Auto-classify sheet types (floor plans, elevations, sections)

### 2. AI Detection & Extraction
- **Room Detection:** Identify rooms from floor plans
- **Wall Detection:** Measure wall lengths and heights
- **Ceiling Detection:** Calculate ceiling areas
- **Surface Detection:** Detect paintable surfaces (walls, ceilings, trim, doors)
- **Dimension Extraction:** Parse measurements from drawings

### 3. Paint Calculation Engine
- **Surface Area Calculation:**
  - Walls: Length × Height
  - Ceilings: Room area
  - Trim: Linear footage × height
  - Deductions: Windows, doors
  
- **Paint Volume Calculation:**
  - Coverage rates: 400 sqft/gallon (smooth drywall), 350 sqft/gallon (textured)
  - Coats: Primer (1 coat) + Finish (2 coats)
  - Waste factor: 10-15%

- **Labor Estimation:**
  - Production rates: 300 sqft/hr (walls), 350 sqft/hr (ceilings), 200 sqft/hr (trim)
  - Prep time: 15% of total time
  - Touch-up time: 5% of total time

### 4. Assembly Expansion
Transform detected rooms into detailed line items:
- Room → 5-15 line items:
  - Walls (primer, 2 coats finish)
  - Ceiling (primer, 2 coats finish)
  - Trim/baseboard (1-2 coats)
  - Doors/frames (1-2 coats)
  - Labor (prep, application, cleanup)

### 5. Pricing Integration
- **Phase 1 (MVP):** Manual pricing (contractor inputs $/gallon, $/hour)
- **Phase 2:** RS Means database integration
- **Phase 3:** Local market pricing API

### 6. Review & Edit
- View all detected rooms/surfaces
- Manual adjustments (add/remove/edit quantities)
- Override calculations
- Add notes/specifications

### 7. Export
- **Excel:** Detailed takeoff spreadsheet
- **PDF:** Formatted bid proposal
- **CSV:** For import to other systems

## Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL 15
- **Cache:** Redis
- **CV/AI:** 
  - YOLOv8 (object detection)
  - Claude Sonnet 4 (vision analysis)
  - Tesseract OCR (dimension extraction)
- **File Processing:** PyMuPDF, Pillow

### Frontend
- **Framework:** React 18 + Vite
- **Styling:** Tailwind CSS
- **State:** React Query + Zustand
- **Components:** shadcn/ui
- **Charts:** Recharts

### Infrastructure
- **Hosting:** AWS (EC2 + RDS + S3)
- **CDN:** CloudFront
- **Email:** SendGrid
- **Payments:** Stripe

## Data Models

### Project
```python
{
  "id": "uuid",
  "name": "Office Building Painting",
  "customer": "ABC Construction",
  "created_at": "timestamp",
  "status": "processing|complete|failed",
  "drawing_files": ["file1.pdf", "file2.pdf"],
  "total_rooms": 24,
  "total_sqft": 12500,
  "total_gallons": 85,
  "total_labor_hours": 240,
  "estimated_cost": 18500
}
```

### Room
```python
{
  "id": "uuid",
  "project_id": "uuid",
  "name": "Conference Room A",
  "floor": 2,
  "room_number": "201",
  "dimensions": {
    "length": 20,
    "width": 15,
    "height": 9
  },
  "surfaces": {
    "walls": {"area": 630, "deductions": 50},
    "ceiling": {"area": 300},
    "trim": {"linear_ft": 70}
  },
  "paint_requirements": {
    "primer": {"gallons": 2.5, "cost": 75},
    "finish": {"gallons": 5.0, "cost": 200}
  },
  "labor": {"hours": 12, "cost": 480}
}
```

### Line Item
```python
{
  "id": "uuid",
  "room_id": "uuid",
  "description": "Paint walls - primer coat",
  "quantity": 580,
  "unit": "sqft",
  "material_cost": 75,
  "labor_hours": 4,
  "labor_cost": 160,
  "total_cost": 235
}
```

## Pricing Model
- **Free Trial:** 3 projects, no credit card
- **Starter:** $299/month - 50 projects/month
- **Pro:** $699/month - Unlimited projects + API access
- **Enterprise:** $1,499/month - Custom integrations + priority support

## Success Metrics (Week 1)
- ✅ Process 1 sample drawing successfully
- ✅ Generate accurate takeoff (±10% of manual estimate)
- ✅ Export to Excel
- ✅ 1 beta user actively using
- 🎯 1 paying customer at $299/month

## Competitive Positioning
**Painting.ai vs Alternatives:**

| Feature | Painting.ai | Manual (Excel) | PlanSwift | STACK |
|---------|-------------|----------------|-----------|-------|
| **Setup Time** | 2 min upload | 4 hours | 1 hour | 2 hours |
| **Accuracy** | 95%+ (AI) | 90% (human error) | 95% | 93% |
| **Learning Curve** | None | N/A | 2 weeks | 1 week |
| **Cost** | $299/month | $0 | $1,500 one-time | $600/month |
| **Auto-detection** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Mobile Access** | ✅ Yes | ❌ No | ❌ No | ✅ Yes |

## Go-to-Market Strategy

### Week 1: Beta Launch
- Build MVP
- Test with 3-5 painting contractors
- Iterate based on feedback

### Month 1: Private Beta (50 users)
- LinkedIn outreach to painting estimators
- Offer free lifetime access to first 50 users
- Collect testimonials

### Month 2-3: Public Launch
- Landing page + SEO
- Content marketing (blog posts, videos)
- Reddit (r/construction, r/smallbusiness)
- Trade show presence (Painting & Decorating Contractors Association)

### Month 4-6: Scale to 100 Paying Customers
- Paid ads (Google, Facebook)
- Partnerships with paint suppliers
- Integration with Sherwin-Williams, Benjamin Moore
- Target: $30K MRR

## Development Timeline

### Day 1-2: Research & Architecture
- ✅ Contractor interviews
- ✅ Sample drawings collection
- ✅ Database schema
- ✅ API design

### Day 3-4: Backend Core
- ✅ Painting detection engine
- ✅ Calculation logic
- ✅ API endpoints

### Day 5: Frontend
- ✅ Upload UI
- ✅ Project dashboard
- ✅ Review interface

### Day 6: Polish
- ✅ Bug fixes
- ✅ Landing page
- ✅ Demo video

### Day 7: Launch
- ✅ First beta user
- ✅ Payment integration
- ✅ First paying customer

## Risk Mitigation

### Technical Risks
- **AI accuracy < 90%:** Manual review interface, allow corrections
- **Drawing quality issues:** Image enhancement preprocessing
- **Scale issues:** Start with PostgreSQL, plan MongoDB migration

### Market Risks
- **Low adoption:** Free tier with generous limits, money-back guarantee
- **Competitor copies:** First-mover advantage (12-18 months), build moat with data
- **Pricing resistance:** Start high ($299), can always decrease

### Operational Risks
- **Customer support:** In-app chat, comprehensive docs, video tutorials
- **Integration needs:** Start simple (Excel export), add integrations based on demand
- **Churn:** Weekly check-ins with early customers, rapid iteration

## Future Roadmap (Post-MVP)

### Month 2-3
- Mobile app (iOS/Android)
- Integrations (QuickBooks, Sage, HCSS)
- Team collaboration features
- Historical pricing data

### Month 4-6
- Multi-trade support (drywall, flooring)
- Advanced scheduling
- Crew management
- Material ordering integration

### Month 7-12
- AI-powered bid optimization
- Win rate analytics
- Market pricing intelligence
- Predictive labor hours

## Exit Strategy
- **Acquisition targets:** PlanSwift, STACK, Procore, Autodesk
- **Valuation goal:** 10-15x revenue multiple (industry standard)
- **Timeline:** 3-5 years to $20-50M revenue = $200-750M exit
