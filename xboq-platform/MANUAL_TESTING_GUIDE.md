# Manual Testing Guide - XBOQ Platform

**Purpose**: Complete browser-based testing checklist for all features  
**Time Required**: 15-20 minutes  
**Environment**: Local development (TEST_MODE enabled)

---

## Prerequisites

### 1. Start Services

```bash
# Terminal 1: Backend
cd /home/user/cooperxxjohn/xboq-platform/backend
source venv/bin/activate
python app.py

# Terminal 2: Frontend
cd /home/user/cooperxxjohn/xboq-platform/frontend
npm run dev
```

**Verify Services Running:**
- Backend: http://localhost:5000/health
- Frontend: http://localhost:3000

---

## Test 1: Homepage & Navigation (2 minutes)

### Actions
1. Open http://localhost:3000 in browser
2. Verify homepage loads
3. Check both product cards visible:
   - 📋 BOQ Generator
   - 🏗️ Construction Estimator
4. Click "Get Started" on BOQ Generator → should route to /boq
5. Click back/home
6. Click "Get Started" on Construction Estimator → should route to /estimator

### Expected Results
- ✅ Homepage loads without errors
- ✅ Both product cards display correctly
- ✅ Navigation works smoothly
- ✅ URLs update correctly (/boq, /estimator)
- ✅ No console errors (F12 → Console)

### Issues to Check
- [ ] Cards aligned properly
- [ ] Icons display correctly
- [ ] Text readable and formatted
- [ ] Responsive on mobile (resize browser)

---

## Test 2: BOQ Generator (3 minutes)

### Actions
1. Navigate to http://localhost:3000/boq
2. Verify page loads with upload interface
3. **Test Error Handling:**
   - Click "Extract BOQ" without selecting file
   - Should show error: "Please select a file"
4. **Test File Upload:**
   - Select any PDF file (or use test_tender.pdf from backend/)
   - Click "Extract BOQ"
   - Watch loading state
   - Wait for results

### Expected Results (Test Mode)
- ✅ Error message for no file
- ✅ Loading indicator shows
- ✅ Results display after ~1 second
- ✅ Mock BOQ data shows:
  - Project: "Test Construction Project"
  - 2 sections: Earthwork, Concrete Work
  - 4 items with quantities and units
- ✅ Results formatted nicely

### Issues to Check
- [ ] File input works
- [ ] Error messages clear
- [ ] Loading spinner displays
- [ ] Results readable
- [ ] Can upload again (reset works)

---

## Test 3: Construction Estimator - Manual Input (5 minutes)

### Actions
1. Navigate to http://localhost:3000/estimator
2. Verify manual input mode is default
3. **Test Drywall Estimate:**
   - Trade: Drywall (default)
   - Keep default room (Room 1)
   - Modify dimensions: Length=20, Width=15, Height=9
   - Click "Generate Estimate"
   - Verify results display

4. **Test Multiple Rooms:**
   - Click "Add Room"
   - Should add Room 2
   - Modify Room 2: Length=12, Width=12, Height=8
   - Change Room 2 name to "Bedroom"
   - Click "Generate Estimate"
   - Verify both rooms in results

5. **Test Remove Room:**
   - Click "Remove" on Room 2
   - Should remove successfully
   - Try removing last room
   - Should show error: "You must have at least one room"

6. **Test Painting Estimate:**
   - Switch trade to "Painting"
   - Click "Generate Estimate"
   - Verify painting results (different from drywall)

### Expected Results (Test Mode)
- ✅ Default room loads
- ✅ Can add unlimited rooms
- ✅ Can remove rooms (minimum 1)
- ✅ Can modify all fields (name, L, W, H, doors, windows)
- ✅ Estimates generate quickly (~1 second)
- ✅ Results show 4 cards:
  - Summary (total cost, sqft, labor hours)
  - Materials breakdown
  - Labor details
  - Cost breakdown
- ✅ Different results for drywall vs painting

### Issues to Check
- [ ] Room inputs work smoothly
- [ ] Add/Remove buttons functional
- [ ] Number inputs accept only numbers
- [ ] Generate button clear
- [ ] Results cards formatted well
- [ ] Can switch trades and re-estimate

---

## Test 4: Construction Estimator - Upload Mode (3 minutes)

### Actions
1. Stay on /estimator page
2. Click "Upload Floor Plan" tab/button
3. **Test Error Handling:**
   - Click "Generate Estimate" without file
   - Should show error: "Please select a file"

4. **Test Drywall Upload:**
   - Select trade: Drywall
   - Choose any PDF/image file
   - Click "Generate Estimate"
   - Wait for results

5. **Test Painting Upload:**
   - Select trade: Painting
   - Choose same file
   - Click "Generate Estimate"
   - Verify painting results

### Expected Results (Test Mode)
- ✅ Can switch between Manual/Upload modes
- ✅ Error handling works
- ✅ File selection works
- ✅ Loading indicator shows
- ✅ Mock results display:
  - 1 room detected
  - Materials and labor calculated
  - Costs shown
- ✅ Different results per trade

### Issues to Check
- [ ] Mode switching clear
- [ ] File input works
- [ ] Trade selector visible
- [ ] Results match trade selected

---

## Test 5: Error Handling & Edge Cases (3 minutes)

### Actions
1. **Backend Offline Test:**
   - Stop backend (Ctrl+C in backend terminal)
   - Try generating estimate
   - Should show error: "Failed to connect" or similar
   - Restart backend

2. **Large File Test (if not in test mode):**
   - Try uploading very large file (>100MB)
   - Should show error or reject

3. **Invalid Input Test:**
   - Manual mode: Set room dimensions to 0 or negative
   - Should either prevent or show error

4. **Rapid Clicking:**
   - Click "Generate Estimate" multiple times rapidly
   - Should handle gracefully (disable button or queue)

### Expected Results
- ✅ Graceful error messages
- ✅ No app crashes
- ✅ User can recover from errors
- ✅ No console errors pile up

---

## Test 6: Visual & Responsive (2 minutes)

### Actions
1. **Desktop View:**
   - Full screen browser
   - Check layout is clean
   - Verify spacing, alignment

2. **Tablet View:**
   - Resize to ~768px width
   - Cards should stack nicely
   - All features accessible

3. **Mobile View:**
   - Resize to ~375px width
   - Single column layout
   - Buttons still clickable
   - Text readable

4. **Dark Mode (if supported):**
   - Check if system dark mode works
   - Colors readable

### Expected Results
- ✅ Responsive at all sizes
- ✅ No horizontal scroll
- ✅ Buttons accessible
- ✅ Text legible
- ✅ Professional appearance

---

## Test 7: Browser Compatibility (3 minutes)

Test in multiple browsers (if available):

### Chrome/Chromium
- [ ] All features work
- [ ] No console errors
- [ ] Performance good

### Firefox
- [ ] All features work
- [ ] File uploads work
- [ ] Styling correct

### Safari (Mac)
- [ ] All features work
- [ ] No WebKit issues

---

## Console Checks (Throughout Testing)

Open DevTools (F12) and monitor:

### Console Tab
- ❌ No errors (red)
- ⚠️ Warnings acceptable (yellow, if minor)
- ℹ️ Info/logs okay

### Network Tab
- ✅ API calls to localhost:5000
- ✅ 200 status codes
- ✅ Response times <2 seconds
- ❌ No 404s or 500s

### Common Issues to Watch For:
- CORS errors → backend CORS config issue
- 404 errors → API endpoint mismatch
- Timeout errors → backend not running
- React errors → frontend code bugs

---

## Test Results Checklist

### Critical (Must Pass)
- [ ] Homepage loads
- [ ] Can navigate to both products
- [ ] BOQ upload works
- [ ] Manual estimate works (both trades)
- [ ] Upload estimate works (both trades)
- [ ] Error handling works
- [ ] No console errors

### Important (Should Pass)
- [ ] Multiple rooms work
- [ ] Add/remove rooms work
- [ ] Responsive design works
- [ ] Loading states show
- [ ] Results formatted well

### Nice-to-Have
- [ ] Animations smooth
- [ ] Dark mode works
- [ ] Mobile fully usable
- [ ] All browsers work

---

## Bug Reporting Template

If you find issues, document:

```markdown
### Bug: [Brief Description]

**Page**: /boq | /estimator | /

**Steps to Reproduce**:
1. 
2. 
3. 

**Expected**: 
**Actual**: 

**Console Errors**: 
[Paste any errors from F12 Console]

**Screenshot**: 
[If helpful]

**Browser**: Chrome 120 / Firefox 122 / Safari 17
**Device**: Desktop / Tablet / Mobile
```

---

## Post-Testing

### If All Tests Pass ✅
- Document completion in DAY_2_HOUR_7_COMPLETE.md
- Commit changes
- Ready for deployment testing

### If Issues Found ❌
- Fix critical bugs first
- Re-test after fixes
- Document known issues
- Plan fixes for next session

---

## Quick Start Command

```bash
# One-line test check
curl http://localhost:5000/health && \
curl http://localhost:3000 && \
echo "✅ Services ready for testing!"
```

---

**Testing Time**: ~15-20 minutes  
**Last Updated**: Day 2, Hour 7  
**Test Mode**: Enabled (mock data)  
**Status**: Ready for manual testing 🧪
