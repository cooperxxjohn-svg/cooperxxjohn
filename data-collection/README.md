# House Plan Data Collection

Automated scraping pipeline to collect 1,000+ Indian house plans for AI training.

---

## 📊 What This Does

Scrapes house plans from:
- **Pinterest**: 500+ plans (30x40, 40x60, duplex, Vastu, etc.)
- **99acres**: 200+ plans (from real estate project listings)
- **Google Images**: 300+ plans (targeted architectural searches)

Then filters for quality:
- ✅ Minimum 800x600 resolution
- ✅ Proper aspect ratio (floor plan shaped)
- ✅ No duplicates (perceptual hashing)
- ✅ File size > 50KB (quality check)

**Expected output**: 800-1,000 verified, high-quality floor plan images organized by category.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd data-collection

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Install Chrome WebDriver (auto-managed by selenium)
# No manual download needed!
```

### 2. Run Collection (Option A: All at Once)

```bash
# Run entire pipeline (takes 2-3 hours)
python collect_all.py
```

### 3. Run Collection (Option B: Step by Step)

```bash
# Step 1: Pinterest (30-45 min)
python pinterest_scraper.py

# Step 2: 99acres (20-30 min)
python 99acres_scraper.py

# Step 3: Google Images (30-45 min)
python google_images_scraper.py

# Step 4: Quality check (5-10 min)
python quality_checker.py
```

---

## 📁 Output Structure

After running, you'll have:

```
data-collection/
├── pinterest_plans/          # Raw Pinterest downloads
├── 99acres_plans/           # Raw 99acres downloads
├── google_plans/            # Raw Google downloads
└── verified_plans/          # ✅ FINAL VERIFIED IMAGES
    ├── 30x40/              # 30x40 plot plans
    ├── 40x60/              # 40x60 plot plans
    ├── 50x80/              # 50x80 plot plans
    ├── duplex/             # Multi-story plans
    ├── 2bhk/               # 2 bedroom plans
    ├── 3bhk/               # 3 bedroom plans
    ├── vastu/              # Vastu-compliant plans
    ├── uncategorized/      # Good quality, unclear category
    ├── rejected/           # Failed quality checks
    │   ├── too_small/
    │   ├── duplicate/
    │   └── low_quality/
    └── quality_report.json # Detailed stats
```

---

## 🔍 Manual Verification (Important!)

After automated collection, **manually review** the verified plans:

### What to Look For:

✅ **KEEP**:
- Clear floor plans with room labels
- Visible dimensions (12', 15', etc.)
- Indian styles (2BHK, 3BHK, duplex)
- Clean drawings (no watermarks blocking measurements)
- Complete plans (not cropped)

❌ **DELETE**:
- 3D renders (we need 2D floor plans)
- Exterior photos (not floor plans)
- Blurry or low resolution
- Plans without dimensions
- Non-Indian styles (US suburban, etc.)
- Plans with huge watermarks covering everything
- Incomplete/cropped plans

### Quick Manual Review:

```bash
# Open the verified_plans folder
cd verified_plans

# Review each category folder
# Delete bad images manually
# Move miscategorized images to correct folder
```

**Target after manual review**: 500-800 high-quality, training-ready images.

---

## 🛠️ Individual Scraper Details

### Pinterest Scraper

**Target**: 500+ images  
**Searches**: 30+ queries (30x40, 40x60, duplex, Vastu, BHK plans)  
**Time**: 30-45 minutes  
**Best for**: Variety and volume

**Customize searches**:
Edit `pinterest_scraper.py`, line 95+ (queries array):
```python
queries = [
    "30x40 house plans india",
    "your custom search here",
    # Add more...
]
```

---

### 99acres Scraper

**Target**: 200+ images  
**Searches**: 10 major Indian cities  
**Time**: 20-30 minutes  
**Best for**: Real project floor plans (authentic)

**Customize cities**:
Edit `99acres_scraper.py`, line 85+ (cities array):
```python
cities = [
    "bangalore",
    "your city here",
    # Add more...
]
```

---

### Google Images Scraper

**Target**: 300+ images  
**Searches**: 15 high-value queries  
**Time**: 30-45 minutes  
**Best for**: Professional architectural plans

**Customize searches**:
Edit `google_images_scraper.py`, line 82+ (queries array):
```python
queries = [
    "30x40 house floor plan with dimensions india",
    "your custom query here",
    # Add more...
]
```

---

## 🐛 Troubleshooting

### ChromeDriver Issues

If you see "chromedriver not found" error:

```bash
# Option 1: Let selenium auto-download (recommended)
pip install webdriver-manager
# Already included in requirements.txt

# Option 2: Manual install (if auto-download fails)
# Ubuntu/Debian:
sudo apt-get install chromium-chromedriver

# Mac:
brew install chromedriver

# Windows:
# Download from: https://chromedriver.chromium.org/
```

### Selenium Errors

If you see "element not found" or "timeout":
- **Slow internet**: Increase wait times in scrapers (line ~30: `time.sleep(3)` → `time.sleep(5)`)
- **Site changed**: Website HTML changed, needs scraper update (contact me)
- **Rate limiting**: Website blocking too many requests, add delays

### No Images Downloaded

If scrapers run but find 0 images:
1. **Disable headless mode**: Comment out `chrome_options.add_argument("--headless")` to see browser
2. **Check website**: Open site manually, verify it loads
3. **Pinterest login**: Pinterest may require login after many searches (add cookies)

---

## 📈 Expected Results

### Scraping Stats (Typical Run):

| Source | Raw Downloads | After Quality Check | Pass Rate |
|--------|--------------|---------------------|-----------|
| Pinterest | 600-800 | 400-500 | ~65% |
| 99acres | 150-250 | 100-150 | ~70% |
| Google | 300-400 | 200-250 | ~70% |
| **TOTAL** | **1,050-1,450** | **700-900** | **~68%** |

After manual review: **500-800 training-ready images**

---

## ⚙️ Configuration

### Adjust Number of Images

Each scraper has a `max_images` parameter:

```python
# pinterest_scraper.py, line 106
count = self.search_and_scrape(query, max_images=50)  # Change 50 → 100

# 99acres_scraper.py, line 78
count = self.scrape_city_projects(city, max_projects=20)  # Change 20 → 50

# google_images_scraper.py, line 87
count = self.search_and_scrape(query, max_images=50)  # Change 50 → 100
```

### Adjust Quality Thresholds

Edit `quality_checker.py`, line 39+:

```python
# Minimum resolution
if width < 800 or height < 600:  # Change to 1024x768 for higher quality

# Minimum file size
if file_size < 50000:  # Change to 100000 for 100KB minimum
```

---

## 🔄 Running Again (Additional Collection)

If you need more data later:

```bash
# Add new searches to scrapers (edit queries)
# Run again - duplicates will be caught by quality checker

python pinterest_scraper.py  # Gets new images only
python quality_checker.py    # Adds to verified_plans/
```

Duplicate detection prevents re-downloading same images.

---

## 📊 Monitoring Progress

Watch live as scrapers run:

```bash
# In another terminal, watch folder sizes grow
watch -n 5 'du -sh pinterest_plans/ 99acres_plans/ google_plans/'

# Count images in real-time
watch -n 5 'ls pinterest_plans/*.jpg | wc -l'
```

---

## 🚨 Legal & Ethical

- **Personal use only**: For training AI models for your own product
- **No redistribution**: Don't share scraped dataset publicly
- **Respect robots.txt**: Scrapers include delays to avoid overloading servers
- **Terms of service**: Verify you comply with each site's terms
- **Copyright**: Plans from architects are their IP, use for learning/training only

---

## ✅ Next Steps After Collection

Once you have 500-800 verified images:

1. **Manual review** (2-3 hours): Delete bad images, recategorize
2. **Annotation** (Week 2): Label rooms (bedroom, kitchen, etc.)
3. **Preprocessing** (Week 2): Resize, normalize, augment
4. **Training data prep** (Week 2): Create text prompts for each image
5. **Model training** (Weeks 3-5): Fine-tune Stable Diffusion + ControlNet

---

## 🆘 Need Help?

- **Scrapers not working**: Check terminal output for errors, disable headless mode
- **Quality too low**: Adjust thresholds in quality_checker.py
- **Need more data**: Add queries to scrapers, or run additional sources
- **Technical issues**: Contact @cooperxxjohn

---

## 📝 Collection Checklist

After running collection:

- [ ] All 3 scrapers completed successfully
- [ ] Quality checker ran (see quality_report.json)
- [ ] Verified 500+ images in verified_plans/
- [ ] Manually reviewed and deleted bad images
- [ ] Organized into categories (30x40, 40x60, duplex, etc.)
- [ ] Backed up to cloud storage (Google Drive/S3)
- [ ] Ready for annotation (Week 2)

**Estimated high-quality dataset after manual review**: 500-800 images ✅

---

**Ready to start? Run:** `python collect_all.py`
