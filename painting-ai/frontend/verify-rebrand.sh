#!/bin/bash
# Verification script for Drywall.ai rebrand

echo "========================================="
echo "   Drywall.ai Rebrand Verification"
echo "========================================="
echo ""

# Check for remaining Painting.ai references
echo "1. Checking for 'Painting.ai' references (excluding tests)..."
PAINTING_COUNT=$(grep -r "Painting\.ai" src --include="*.jsx" --exclude-dir=__tests__ 2>/dev/null | wc -l)
if [ "$PAINTING_COUNT" -eq 0 ]; then
    echo "   ✅ No Painting.ai references found"
else
    echo "   ⚠️  Found $PAINTING_COUNT Painting.ai references:"
    grep -r "Painting\.ai" src --include="*.jsx" --exclude-dir=__tests__ 2>/dev/null
fi
echo ""

# Check for PaintBucket icon
echo "2. Checking for PaintBucket icon (excluding tests)..."
PAINT_ICON_COUNT=$(grep -r "PaintBucket" src --include="*.jsx" --exclude-dir=__tests__ 2>/dev/null | wc -l)
if [ "$PAINT_ICON_COUNT" -eq 0 ]; then
    echo "   ✅ No PaintBucket icons found"
else
    echo "   ⚠️  Found $PAINT_ICON_COUNT PaintBucket icon references:"
    grep -r "PaintBucket" src --include="*.jsx" --exclude-dir=__tests__ 2>/dev/null
fi
echo ""

# Check for new components
echo "3. Checking new components..."
if [ -f "src/components/WallEditor.jsx" ]; then
    echo "   ✅ WallEditor.jsx exists"
else
    echo "   ❌ WallEditor.jsx missing"
fi

if [ -f "src/components/MaterialsList.jsx" ]; then
    echo "   ✅ MaterialsList.jsx exists"
else
    echo "   ❌ MaterialsList.jsx missing"
fi
echo ""

# Check package.json
echo "4. Checking package.json..."
if grep -q "drywall-ai-frontend" package.json; then
    echo "   ✅ Package name updated to drywall-ai-frontend"
else
    echo "   ⚠️  Package name not updated"
fi
echo ""

# Summary
echo "========================================="
echo "   Summary"
echo "========================================="
echo "Branding: $([ "$PAINTING_COUNT" -eq 0 ] && echo "✅ Complete" || echo "⚠️  Incomplete")"
echo "Icons: $([ "$PAINT_ICON_COUNT" -eq 0 ] && echo "✅ Complete" || echo "⚠️  Incomplete")"
echo "Components: $([ -f "src/components/WallEditor.jsx" ] && [ -f "src/components/MaterialsList.jsx" ] && echo "✅ Complete" || echo "⚠️  Incomplete")"
echo ""

# Documentation
echo "Documentation files:"
[ -f "UI_REBRAND.md" ] && echo "  ✅ UI_REBRAND.md"
[ -f "REBRAND_SUMMARY.md" ] && echo "  ✅ REBRAND_SUMMARY.md"
echo ""

echo "========================================="
echo "For detailed information, see:"
echo "  - UI_REBRAND.md (complete technical documentation)"
echo "  - REBRAND_SUMMARY.md (quick summary)"
echo "========================================="
