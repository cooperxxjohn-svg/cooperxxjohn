# Floor Plan Model Training - Quick Start Guide

## 🚀 Get Training in 30 Minutes

### Step 1: Prepare Data (5 minutes)

**Zip the training data:**
```bash
cd /home/user/cooperxxjohn/data-collection
zip -r training_data.zip training_data/
```

**Expected size:** ~2-3GB zipped

---

### Step 2: Upload to Google Drive (10 minutes)

1. **Download the zip file** from server to your computer
2. **Go to Google Drive** (drive.google.com)
3. **Create folder:** `floor_plan_training/`
4. **Upload files:**
   - `training_data.zip` (2-3GB)
   - `train_floor_plan_model.ipynb` (this notebook)

---

### Step 3: Open Google Colab (2 minutes)

1. **Go to:** https://colab.research.google.com
2. **File → Upload notebook**
3. **Select:** `train_floor_plan_model.ipynb` from Downloads
4. **Runtime → Change runtime type → T4 GPU** ✅

---

### Step 4: Start Training (1 click)

1. **Click:** Runtime → Run all
2. **Authenticate** when prompted (to mount Google Drive)
3. **Wait 30 minutes** for setup
4. **Training starts automatically** (10-15 hours)

You can close the tab - training continues in background!

---

## 📊 What Happens During Training

### Setup Phase (30 minutes):
- ✅ Mounts Google Drive
- ✅ Installs dependencies (diffusers, transformers, etc.)
- ✅ Downloads Stable Diffusion 1.5 (~4GB)
- ✅ Extracts training data
- ✅ Configures GPU

### Training Phase (10-15 hours):
- 🔄 Processes 4,000 floor plans
- 🔄 10 epochs × 1,000 steps/epoch = 10,000 steps
- 📸 Generates sample every 100 steps
- 💾 Saves checkpoint every 500 steps
- 🏆 Saves best model automatically

### Output:
- `floor_plan_model/best_model/` - Your trained AI ✅
- `floor_plan_model/samples/` - Generated samples during training
- `floor_plan_model/checkpoint-{step}/` - Intermediate checkpoints

---

## 💰 Cost Breakdown

**Google Colab Free Tier:**
- GPU hours: 15 hours/month (T4 GPU)
- Training time: 10-15 hours
- **Cost: $0** (fits in free quota) ✅

**Google Colab Pro ($10/mo):**
- GPU hours: 100+ hours/month
- Better GPU (V100 = 2x faster)
- Background execution
- **Recommended if training multiple models**

**Alternative: Vast.ai**
- RTX 3090: $0.20-0.30/hr
- 10 hours = $2-3 total
- Pay per use, no monthly fee

---

## 📈 Expected Results

**After 1,000 steps (1 hour):**
```
Loss: ~0.15
Quality: Blurry shapes, recognizable as floor plans
```

**After 5,000 steps (5 hours):**
```
Loss: ~0.08
Quality: Clear walls, rooms visible, correct counts
```

**After 10,000 steps (10 hours):**
```
Loss: ~0.05
Quality: Production-ready, accurate layouts
```

---

## 🔍 Monitoring Training

**Check progress:**
1. Open Colab notebook
2. Scroll to "Training Loop" cell
3. Watch loss decrease and samples improve

**Loss interpretati on:**
- Loss > 0.15: Early training, blurry
- Loss 0.08-0.15: Getting better, rooms visible
- Loss 0.05-0.08: Good quality
- Loss < 0.05: Excellent, production-ready

**Sample quality:**
- Step 100: Random noise
- Step 500: Blurry rectangles
- Step 1000: Recognizable floor plan shape
- Step 5000: Clear rooms and walls
- Step 10000: Professional quality ✅

---

## 🎯 After Training Completes

### Test Your Model:

Run the "Test Generation" cell in the notebook:

**Input prompt:**
```
"Floor plan with 3 bedrooms, 2 bathrooms, kitchen, living room"
```

**Output:**
- Generated floor plan image (512×512 pixels)
- Saved to `test_output_*.png`

### Download Your Model:

1. **In Colab:** Files panel (left sidebar)
2. **Navigate to:** `floor_plan_model/best_model/`
3. **Right-click → Download** (all files)
4. **Size:** ~4GB

### Use Your Model:

```python
from diffusers import StableDiffusionPipeline
import torch

pipe = StableDiffusionPipeline.from_pretrained(
    "floor_plan_model/best_model",
    torch_dtype=torch.float16
).to("cuda")

image = pipe(
    "Floor plan with 2 bedrooms, 1 bathroom, kitchen",
    num_inference_steps=50
).images[0]

image.save("my_floor_plan.png")
```

---

## 🐛 Troubleshooting

### "Out of memory" error:
```python
# Reduce batch size in Step 6
config['batch_size'] = 2  # Instead of 4
```

### "Runtime disconnected":
- **Free tier:** Colab disconnects after 12 hours
- **Solution:** Use Colab Pro or split into 2 sessions
- **Checkpoint saves:** Resume from last checkpoint

### "Can't find training_data.zip":
- **Check path:** Make sure uploaded to `My Drive/floor_plan_training/`
- **Re-run Step 1:** Mount Google Drive cell

### Slow training:
- **GPU not enabled:** Runtime → Change runtime type → GPU
- **T4 vs V100:** V100 is 2x faster (Colab Pro only)

---

## 📝 Next Steps After Training

### Week 2: Indian Localization

1. **Collect 200-500 Indian floor plans:**
   - 30×40, 40×60, 50×80 plot sizes
   - Vastu-compliant layouts
   - 2BHK, 3BHK, 4BHK configurations

2. **Fine-tune your model:**
   - Use same notebook, replace dataset
   - Train for 2,000-5,000 steps
   - Lower learning rate (1e-6)

3. **Add Vastu compliance:**
   - Post-processing rules
   - Main door facing East/North
   - Kitchen in South-East
   - Pooja room in North-East

### Week 3: Production Integration

1. **Build API:**
   - FastAPI server
   - Text prompt → Generated floor plan
   - CAD file export

2. **Frontend:**
   - Input form (bedrooms, bathrooms, plot size)
   - Generate button
   - Download floor plan

3. **Deploy:**
   - Model on GPU server
   - API on Railway/Render
   - Frontend on Vercel

---

## ✅ Checklist

Before starting training:

- [ ] Google account with Drive access
- [ ] Colab account (free or Pro)
- [ ] `training_data.zip` uploaded to Drive
- [ ] `train_floor_plan_model.ipynb` uploaded to Drive
- [ ] GPU runtime selected in Colab
- [ ] 12+ hours available (can run overnight)

---

**Ready to start?** Open the Colab notebook and click "Run all"!

Expected completion: Tomorrow morning if you start now ☕
