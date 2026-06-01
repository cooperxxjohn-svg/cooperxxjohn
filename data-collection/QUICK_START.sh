#!/bin/bash
# Quick Start - Training Setup Verification
# Run this to ensure everything is ready

echo "=================================="
echo "TRAINING SETUP VERIFICATION"
echo "=================================="
echo ""

# Check files exist
echo "1. Checking required files..."
if [ -f "training_data.zip" ]; then
    echo "   ✅ training_data.zip ($(du -h training_data.zip | cut -f1))"
else
    echo "   ❌ training_data.zip NOT FOUND"
    exit 1
fi

if [ -f "train_floor_plan_model.ipynb" ]; then
    echo "   ✅ train_floor_plan_model.ipynb"
else
    echo "   ❌ Notebook NOT FOUND"
    exit 1
fi

if [ -f "TRAINING_SETUP.md" ]; then
    echo "   ✅ TRAINING_SETUP.md"
else
    echo "   ❌ Setup guide NOT FOUND"
    exit 1
fi

echo ""
echo "2. Dataset verification..."
if [ -d "training_data/train" ]; then
    TRAIN_COUNT=$(ls training_data/train/images/*.png 2>/dev/null | wc -l)
    VAL_COUNT=$(ls training_data/val/images/*.png 2>/dev/null | wc -l)
    TEST_COUNT=$(ls training_data/test/images/*.png 2>/dev/null | wc -l)

    echo "   ✅ Train: $TRAIN_COUNT images"
    echo "   ✅ Val:   $VAL_COUNT images"
    echo "   ✅ Test:  $TEST_COUNT images"
else
    echo "   ❌ Training data directory NOT FOUND"
    exit 1
fi

echo ""
echo "=================================="
echo "✅ ALL CHECKS PASSED!"
echo "=================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Download these files to your computer:"
echo "   - training_data.zip (3.7GB)"
echo "   - train_floor_plan_model.ipynb"
echo "   - TRAINING_SETUP.md"
echo ""
echo "2. Upload to Google Drive:"
echo "   Create: My Drive/floor_plan_training/"
echo "   Upload: training_data.zip + notebook"
echo ""
echo "3. Open Google Colab:"
echo "   https://colab.research.google.com"
echo "   Upload notebook → Enable T4 GPU → Run all"
echo ""
echo "🚀 Training will start in ~30 minutes!"
echo "⏰ Results in 10-15 hours"
echo ""
