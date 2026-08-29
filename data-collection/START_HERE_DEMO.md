# 🚀 Quick Start - Demo Training (2-3 hours)

## Everything is ready! Just follow these steps:

### Step 1: Open Google Colab
Go to: https://colab.research.google.com

### Step 2: Open the notebook from Google Drive
1. Click **File → Open notebook**
2. Click **Google Drive** tab
3. Navigate to **floor_plan_training/**
4. Open **train_floor_plan_model.ipynb**

### Step 3: Enable GPU
1. Click **Runtime → Change runtime type**
2. Select **T4 GPU**
3. Click **Save**

### Step 4: Modify ONE line for demo
In **Step 1** (the upload cell), change the filename check to use the demo:

**Find this line:**
```python
if not os.path.exists('training_data.zip'):
```

**Change it to:**
```python
if not os.path.exists('training_data_demo.zip'):
```

Then add before the upload section:
```python
# Download from Google Drive instead
from google.colab import drive
drive.mount('/content/drive')
!cp /content/drive/MyDrive/floor_plan_training/training_data_demo.zip /content/
!mv /content/training_data_demo.zip /content/training_data.zip
```

### Step 5: Run all cells
1. Click **Runtime → Run all**
2. Authorize Google Drive when prompted
3. Training starts automatically!

---

## What happens:
- ✅ Downloads 196MB demo dataset from your Drive
- ✅ Installs all dependencies (~5 minutes)
- ✅ Trains on 500 floor plans (~2-3 hours)
- ✅ Generates test images
- ✅ You have a working floor plan AI!

## Monitor progress:
- Loss should decrease from ~0.15 → ~0.05
- Sample images improve every 100 steps
- Can close tab - training continues

## After training:
- Download the trained model
- Test with different prompts
- If it works, train on full 5,000 dataset later!

---

**Everything is uploaded to your Google Drive:**
- ✅ training_data_demo.zip (196MB)
- ✅ train_floor_plan_model.ipynb
- ✅ TRAINING_SETUP.md

**Ready to start? Open Colab now!** 🎉
