"""
Pinterest House Plan Scraper
Scrapes Indian house plans from Pinterest searches
Run: python pinterest_scraper.py
"""

import os
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs
import hashlib

class PinterestScraper:
    def __init__(self, output_dir="pinterest_plans"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Set up Chrome in headless mode
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Comment out to see browser
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.downloaded = set()

    def search_and_scrape(self, query, max_images=100):
        """Search Pinterest and download images"""
        print(f"\n🔍 Searching: {query}")

        # Pinterest search URL
        search_url = f"https://www.pinterest.com/search/pins/?q={query.replace(' ', '%20')}"
        self.driver.get(search_url)

        # Wait for images to load
        time.sleep(3)

        # Scroll to load more images
        image_urls = set()
        scroll_pause = 2
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while len(image_urls) < max_images:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)

            # Find all image elements
            images = self.driver.find_elements(By.TAG_NAME, "img")

            for img in images:
                src = img.get_attribute("src")
                if src and "pinimg.com" in src and src not in self.downloaded:
                    # Get high-res version (replace size suffix)
                    high_res = src.replace("/236x/", "/originals/").replace("/474x/", "/originals/")
                    image_urls.add(high_res)

            print(f"   Found {len(image_urls)} images so far...")

            # Check if reached bottom
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Download images
        print(f"📥 Downloading {len(image_urls)} images...")
        count = 0
        for url in image_urls:
            if count >= max_images:
                break
            try:
                # Download image
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    # Create filename from hash
                    filename = hashlib.md5(url.encode()).hexdigest() + ".jpg"
                    filepath = os.path.join(self.output_dir, filename)

                    with open(filepath, 'wb') as f:
                        f.write(response.content)

                    # Save metadata
                    meta_file = filepath.replace(".jpg", ".json")
                    with open(meta_file, 'w') as f:
                        json.dump({
                            "url": url,
                            "query": query,
                            "source": "pinterest"
                        }, f)

                    self.downloaded.add(url)
                    count += 1
                    print(f"   ✓ Downloaded {count}/{max_images}")
            except Exception as e:
                print(f"   ✗ Failed: {e}")
                continue

        return count

    def run(self):
        """Run scraper with multiple search queries"""

        # Indian house plan search queries (high-value keywords)
        queries = [
            # By plot size (most searched)
            "30x40 house plans india",
            "30x40 duplex house plans",
            "40x60 house plans india",
            "40x60 duplex house plans",
            "50x80 house plans",
            "60x90 house plans india",
            "20x50 house plans",
            "25x50 house plans india",

            # By BHK
            "2bhk house plans 1000 sqft",
            "3bhk house plans 1500 sqft",
            "4bhk house plans 2000 sqft",
            "1bhk house plans 600 sqft",

            # Duplex specific
            "duplex house plans india",
            "duplex floor plans 30x40",
            "duplex floor plans 40x60",
            "2 floor house plans india",

            # Vastu
            "vastu house plans 30x40",
            "vastu compliant house plans",
            "vastu duplex house plans",
            "east facing house plans vastu",
            "north facing house plans",

            # Styles
            "modern house plans india",
            "contemporary house plans india",
            "traditional indian house plans",
            "kerala house plans",
            "small house plans india",

            # Specific features
            "house plans with pooja room",
            "house plans with car parking",
            "3 bedroom house plans with dimensions",
            "house floor plans with measurements"
        ]

        total = 0
        for query in queries:
            try:
                count = self.search_and_scrape(query, max_images=50)
                total += count
                print(f"✅ Query '{query}': {count} images")
                time.sleep(5)  # Be nice to Pinterest
            except Exception as e:
                print(f"❌ Query '{query}' failed: {e}")
                continue

        print(f"\n🎉 DONE! Total downloaded: {total} images")
        print(f"📁 Saved to: {self.output_dir}/")

        self.driver.quit()

if __name__ == "__main__":
    scraper = PinterestScraper()
    scraper.run()
