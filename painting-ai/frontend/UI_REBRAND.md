# UI Rebrand: Painting.ai → Drywall.ai

## Overview
This document outlines the complete rebrand of the frontend from Painting.ai to Drywall.ai, adapting the interface for drywall contractors instead of painting contractors.

## Changes Summary

### 1. Branding Updates
- **Name**: Painting.ai → Drywall.ai
- **Logo Icon**: PaintBucket → Hammer (lucide-react)
- **Color Scheme**: Maintained existing primary-600 colors (can be updated later for construction theme)
- **Industry**: Painting contractors → Drywall contractors

### 2. Terminology Changes

| Old (Painting) | New (Drywall) |
|----------------|---------------|
| Projects | Takeoffs |
| Rooms | Walls |
| Paint | Drywall/Materials |
| Gallons | Sheets |
| Coverage | Material quantities |
| Surface type | Finishing level |
| Estimate | Takeoff/Material list |
| Room detection | Wall detection |
| Assembly expansion | Material & labor breakdown |

### 3. Files Updated

#### Core Pages
- **src/pages/Landing.jsx**
  - Hero: "AI-Powered Drywall Takeoffs in 60 Seconds"
  - Tagline: "Upload floor plan → Get complete material list with studs, sheets, mud, tape, and labor hours"
  - Features updated to wall detection, framing calculations, material lists
  - Testimonials updated with drywall company names
  - All Painting.ai → Drywall.ai
  - All painting.ai → drywall.ai

- **src/pages/Pricing.jsx**
  - "50 projects" → "50 takeoffs"
  - "AI room detection" → "AI wall & opening detection"
  - "Assembly expansion" → "Material & labor breakdown"
  - Email references updated

- **src/pages/Dashboard.jsx**
  - "Projects" → "Takeoffs"
  - "Manage your painting takeoff projects" → "Manage your drywall takeoff projects"
  - "rooms" → "walls" in project listings
  - Empty state: "No takeoffs yet"

- **src/pages/Upload.jsx**
  - Title: "Upload Floor Plan for Drywall Takeoff"
  - Description: "We'll detect walls, calculate materials needed (studs, sheets, mud, tape)"

- **src/pages/ProjectView.jsx**
  - Summary cards: "Total Rooms" → "Total Walls", "Paintable Area" → "Total Area", "Paint Needed" → "Drywall Sheets"
  - Parameters: "Paint Price" → "Drywall Price", "Surface Type" → "Finishing Level"
  - Finishing levels: Level 1-5 (Fire Tape, Garage, Textured, Standard, Premium)
  - Buttons: "Generate Simple Estimate" → "Generate Quick Estimate", "Expand to Detailed Assembly" → "Generate Detailed Material List"
  - Imports WallEditor and MaterialsList components

- **src/pages/Help.jsx**
  - Updated all FAQs for drywall context
  - "rooms" → "walls"
  - Assembly expansion → Material breakdown
  - Updated descriptions for wall detection, linear footage, openings
  - All email references updated

- **src/pages/Settings.jsx**
  - API example URL: api.painting.ai → api.drywall.ai

- **src/pages/Login.jsx**
  - demo@painting.ai → demo@drywall.ai

- **src/pages/Privacy.jsx**
  - All email references updated

- **src/pages/Terms.jsx**
  - All email references updated

- **src/pages/Success.jsx**
  - Email references updated

#### Components
- **src/components/Layout.jsx**
  - Logo icon: PaintBucket → Hammer
  - Painting.ai → Drywall.ai
  - "Projects" nav → "Takeoffs"
  - "New Project" → "New Takeoff"
  - Footer updated
  - All email references updated

- **src/components/RoomEditor.jsx** → **REPLACED**
  - See WallEditor.jsx below

#### New Components Created

- **src/components/WallEditor.jsx**
  - Replaces RoomEditor component
  - Designed for wall-specific data:
    - Linear footage (instead of room dimensions)
    - Wall height
    - Wall type (interior/exterior)
    - Openings (doors/windows count)
    - Corners
  - UI updated: "Rooms" → "Walls", "Add Room" → "Add Wall"
  - Form fields adapted for wall measurements
  - Displays linear footage, area, and opening counts

- **src/components/MaterialsList.jsx**
  - **NEW COMPONENT** - Complete material breakdown display
  - Summary cards: Materials Cost, Labor Cost, Total Project Cost
  - Material categories:
    - **Framing Materials**: Studs (2x4), metal track
    - **Drywall Sheets**: 4x8 sheets (1/2", 5/8")
    - **Finishing Materials**: Joint compound, paper tape, mesh tape, corner bead
    - **Fasteners**: Drywall screws
  - Labor breakdown by phase:
    - Framing
    - Hanging Drywall
    - Taping & Mudding (1st coat)
    - Sanding & 2nd coat
    - Final coat & touch-ups
    - Cleanup
  - Each line item shows: name, quantity, unit, unit cost, total cost
  - Category totals displayed
  - Responsive design with gradient cards

#### Configuration
- **package.json**
  - name: "painting-ai-frontend" → "drywall-ai-frontend"
  - description: "AI-powered drywall takeoff system"

### 4. Feature Updates

#### Landing Page Features (Before → After)
1. Upload Floor Plans → Upload Floor Plans (same)
2. AI-Powered Detection → AI Wall Detection
   - "Automatically detect rooms..." → "Automatically detect walls, calculate linear footage, and identify openings"
3. Detailed Estimates → Complete Material Lists
   - "80-120 line items per room" → "Detailed breakdown of studs, sheets, mud, tape, and labor hours by phase"
4. Professional Exports → Professional Exports (same)

#### How It Works Steps
1. Upload Your Floor Plan (same)
2. Review AI Detections → "Our AI detects **walls** automatically..."
3. Generate Estimate → Generate Takeoff
   - "Expand into detailed line items" → "Get complete material list: framing, hanging, finishing with labor hours"
4. Export & Win (same)

### 5. Material List Structure

The new MaterialsList component displays:

```
Materials Breakdown:
├── Framing Materials
│   ├── 2x4 Studs (8ft)
│   ├── 2x4 Studs (10ft)
│   └── Metal Track (10ft)
├── Drywall Sheets
│   ├── 4x8 Drywall Sheets (1/2")
│   └── 4x8 Drywall Sheets (5/8")
├── Finishing Materials
│   ├── Joint Compound (5 gal)
│   ├── Paper Tape (500ft)
│   ├── Mesh Tape (300ft)
│   └── Corner Bead (10ft)
└── Fasteners & Hardware
    ├── Drywall Screws (1-1/4")
    └── Drywall Screws (1-5/8")

Labor Breakdown by Phase:
├── Framing (24 hrs @ $50/hr)
├── Hanging Drywall (16 hrs @ $50/hr)
├── Taping & Mudding (1st coat) (12 hrs @ $50/hr)
├── Sanding & 2nd coat (10 hrs @ $50/hr)
├── Final coat & touch-ups (8 hrs @ $50/hr)
└── Cleanup (4 hrs @ $40/hr)
```

### 6. Wall Data Model

The WallEditor component expects wall objects with:
```javascript
{
  id: string,
  name: string,
  dimensions: {
    length: number,      // Linear footage
    height: number,      // Wall height
    width: number        // Not used for walls, kept for compatibility
  },
  wall_type: 'interior' | 'exterior',
  openings: number,      // Count of doors/windows
  notes: string
}
```

### 7. Pricing Tiers

All three tiers updated:
- **Starter ($99/mo)**: 50 takeoffs/month, AI wall & opening detection
- **Pro ($299/mo)**: Unlimited takeoffs, Material & labor breakdown
- **Enterprise (Custom)**: Same features as before

### 8. Email Address Updates

All instances updated:
- support@painting.ai → support@drywall.ai
- sales@painting.ai → sales@drywall.ai
- privacy@painting.ai → privacy@drywall.ai
- dpo@painting.ai → dpo@drywall.ai
- legal@painting.ai → legal@drywall.ai
- demo@painting.ai → demo@drywall.ai

### 9. API References

Settings page API example:
```bash
curl -X POST https://api.drywall.ai/api/projects
```

### 10. Backward Compatibility Notes

**Important**: The WallEditor component still uses the `/projects/{id}/rooms` API endpoints for now. The backend API endpoints should be updated separately or aliased to maintain compatibility during migration.

### 11. Future Enhancements (Not Implemented)

These can be added later:
1. **Color scheme update**: Consider gray/construction-themed colors instead of current blue
2. **Wall-specific icons**: Use construction-related icons throughout
3. **Advanced features**:
   - Corner detection and automatic stud calculation
   - Opening deductions from material counts
   - Waste factor calculations
   - Multiple finish level pricing
4. **Backend integration**: Update API to return actual material calculations
5. **Export templates**: Update Excel/PDF exports for drywall-specific content

### 12. Testing Checklist

Before deploying, verify:
- [ ] Landing page displays correctly with drywall branding
- [ ] All "Painting.ai" references removed
- [ ] WallEditor shows wall-specific fields
- [ ] MaterialsList displays with mock data
- [ ] Navigation uses "Takeoffs" terminology
- [ ] Pricing page reflects drywall features
- [ ] Help/FAQ content is drywall-specific
- [ ] All email addresses use drywall.ai domain
- [ ] Settings API example shows drywall.ai URL
- [ ] Login demo email is demo@drywall.ai

## Files Modified
```
frontend/
├── package.json
├── src/
│   ├── pages/
│   │   ├── Landing.jsx
│   │   ├── Pricing.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Upload.jsx
│   │   ├── ProjectView.jsx
│   │   ├── Help.jsx
│   │   ├── Settings.jsx
│   │   ├── Login.jsx
│   │   ├── Privacy.jsx
│   │   ├── Terms.jsx
│   │   └── Success.jsx
│   └── components/
│       ├── Layout.jsx
│       ├── WallEditor.jsx (NEW - replaces RoomEditor)
│       └── MaterialsList.jsx (NEW)
```

## Migration Path

1. ✅ Update all branding (Painting.ai → Drywall.ai)
2. ✅ Update terminology (rooms → walls, projects → takeoffs)
3. ✅ Create WallEditor component
4. ✅ Create MaterialsList component
5. ✅ Update all page content for drywall context
6. ✅ Update email addresses
7. ⏳ Backend API updates (separate task)
8. ⏳ Update export templates (Excel/PDF)
9. ⏳ Integration testing with backend
10. ⏳ Deploy to staging environment

## Notes
- The rebrand maintains the same component structure and routing
- RoomEditor.jsx is kept in the codebase but no longer used (can be deleted)
- All API calls still use existing endpoints - backend changes are separate
- Material quantities in MaterialsList are currently mock data for demo purposes
