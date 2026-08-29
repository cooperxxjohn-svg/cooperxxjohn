# XBOQ Platform - Frontend

React frontend for XBOQ Platform with dual products: BOQ Generator + Construction Estimator.

---

## Quick Start

```bash
npm install
npm run dev
```

Frontend runs on: **http://localhost:3000**

---

## Features Built (Day 1)

### ✅ Homepage
- Product selector cards (BOQ + Estimator)
- Hero section with branding
- Use cases section
- Responsive design
- Gradient background

### ✅ Routing
- React Router v6
- `/` - Homepage
- `/boq` - BOQ Generator tool
- `/estimator` - Construction Estimator tool

### ✅ BOQ Page
- File upload interface
- Connection to backend API
- Result display
- Error handling

### ✅ Estimator Page
- Trade selector (drywall/painting/concrete)
- Mode toggle (manual/upload)
- Placeholder for Day 2 implementation

---

## Project Structure

```
frontend/
├── src/
│   ├── App.jsx         # Main router + all pages
│   ├── App.css         # All styling
│   ├── main.jsx        # React entry point
│   └── index.css       # Global styles
├── public/
├── index.html          # HTML template
├── vite.config.js      # Vite configuration
├── package.json        # Dependencies
└── README.md           # This file
```

---

## Pages

### 1. Homepage (`/`)

**Components:**
- Hero section with XBOQ.AI branding
- Product cards (BOQ + Estimator)
- Features list
- Use cases grid
- Footer

**Features:**
- Gradient background
- Hover animations on cards
- Click to navigate to tools

### 2. BOQ Generator (`/boq`)

**Features:**
- Upload tender PDF
- Process with backend API (`POST /api/boq/upload`)
- Display extracted BOQ
- Error handling

**Status:** Working (needs API key in backend)

### 3. Construction Estimator (`/estimator`)

**Features:**
- Trade selector
- Mode toggle (manual/upload)
- Placeholder interface

**Status:** Placeholder (full implementation in Day 2)

---

## API Integration

Backend URL: `http://localhost:5000`

**Endpoints Used:**
- `POST /api/boq/upload` - BOQ extraction
- `POST /api/estimate/manual` - Manual estimates (Day 2)
- `POST /api/estimate/upload` - Floor plan estimates (Day 2)

---

## Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.0.8"
  }
}
```

---

## Development

### Start Dev Server

```bash
npm run dev
```

Opens on: http://localhost:3000

### Build for Production

```bash
npm run build
```

Output: `dist/`

### Preview Production Build

```bash
npm run preview
```

---

## Day 2 TODO

### Estimator Page Enhancement
- [ ] Build manual input form
  - Room dimensions (length, width, height)
  - Doors and windows count
  - Add/remove rooms dynamically
- [ ] Floor plan upload interface
- [ ] Connect to backend API
- [ ] Display estimate results
  - Summary section
  - Materials breakdown
  - Labor hours
  - Cost breakdown
- [ ] Export functionality

### Global Enhancements
- [ ] Add loading states
- [ ] Improve error messages
- [ ] Add success notifications
- [ ] Mobile responsiveness improvements

---

## Styling

**Design System:**
- Primary color: #667eea (purple-blue)
- Secondary color: #764ba2 (purple)
- Background: Linear gradient
- Cards: White with shadows
- Typography: System fonts

**Animations:**
- Card hover: translateY + shadow
- Button hover: opacity + scale
- Smooth transitions (0.3s)

---

## Deployment

### Vercel

```bash
npm run build
vercel --prod
```

### Netlify

```bash
npm run build
netlify deploy --prod --dir=dist
```

### Environment Variables

```bash
# Production backend URL
VITE_API_URL=https://api.xboq.ai
```

Update fetch URLs:
```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'
```

---

## Status

**Day 1 Complete:**
- [x] Project structure
- [x] React + Vite setup
- [x] React Router configured
- [x] Homepage with product cards
- [x] BOQ page with upload
- [x] Estimator page placeholder
- [x] Responsive styling
- [x] API integration ready

**Ready for Day 2:**
- Full estimator implementation
- Enhanced UI/UX
- Production deployment

---

## Screenshots

### Homepage
- Hero with XBOQ.AI branding
- Two product cards side-by-side
- Use cases section
- Gradient background

### BOQ Page
- Upload interface
- Back to home link
- Clean, professional layout

### Estimator Page
- Trade selector dropdown
- Manual/Upload toggle
- Placeholder message

---

**Time Spent:** 4 hours  
**Status:** Complete! ✅
