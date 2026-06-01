"""
Quick start script - simplified Pinterest scraper
Run: python quick_start.py
"""
import os
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import hashlib

print("\n" + "="*70)
print("QUICK START DATA COLLECTION")
print("="*70 + "\n")

output_dir = "collected_plans"
os.makedirs(output_dir, exist_ok=True)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service('/usr/local/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

# Test searches for Indian house plans
queries = [
    "30x40 house plans india site:pinterest.com",
    "40x60 duplex house plans site:pinterest.com",
    "2bhk house plan 1000 sqft site:pinterest.com"
]

total_downloaded = 0

for query in queries[:1]:  # Start with just 1 query as test
    print(f"\n🔍 Searching: {query}")
    
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=isch"
    driver.get(search_url)
    time.sleep(3)
    
    # Get images
    images = driver.find_elements(By.TAG_NAME, "img")
    print(f"   Found {len(images)} images")
    
    # Download first 10 as test
    count = 0
    for img in images[:20]:
        try:
            src = img.get_attribute("src")
            if src and src.startswith("http") and len(src) > 100:
                response = requests.get(src, timeout=10)
                if response.status_code == 200 and len(response.content) > 10000:
                    filename = hashlib.md5(src.encode()).hexdigest() + ".jpg"
                    filepath = os.path.join(output_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    count += 1
                    total_downloaded += 1
                    print(f"   ✓ Downloaded {count}/10")
                    
                    if count >= 10:
                        break
        except:
            continue
    
    print(f"✅ Query complete: {count} images")

driver.quit()

print(f"\n🎉 DONE! Downloaded {total_downloaded} test images")
print(f"📁 Saved to: {output_dir}/\n")
