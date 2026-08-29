"""
Google Images House Plan Scraper
Scrapes Indian house plans from Google Images
Run: python google_images_scraper.py
"""

import os
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import hashlib

class GoogleImagesScraper:
    def __init__(self, output_dir="google_plans"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.downloaded = set()

    def search_and_scrape(self, query, max_images=50):
        """Search Google Images and download results"""
        print(f"\n🔍 Searching: {query}")

        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=isch"
        self.driver.get(search_url)
        time.sleep(2)

        # Scroll to load more images
        image_urls = set()
        scroll_pause = 1.5

        for _ in range(5):  # Scroll 5 times
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)

            # Click "Show more results" button if it appears
            try:
                show_more = self.driver.find_element(By.CSS_SELECTOR, ".mye4qd")
                show_more.click()
                time.sleep(2)
            except:
                pass

        # Find all thumbnail images
        thumbnails = self.driver.find_elements(By.CSS_SELECTOR, "img.rg_i")
        print(f"   Found {len(thumbnails)} thumbnail images")

        # Click each thumbnail to get high-res image
        for idx, thumb in enumerate(thumbnails[:max_images]):
            try:
                # Click thumbnail
                thumb.click()
                time.sleep(1)

                # Find high-res image
                high_res_images = self.driver.find_elements(By.CSS_SELECTOR, "img.n3VNCb")
                for img in high_res_images:
                    src = img.get_attribute("src")
                    if src and src.startswith("http") and src not in self.downloaded:
                        image_urls.add(src)
                        break

            except Exception as e:
                continue

            if len(image_urls) >= max_images:
                break

        # Download images
        print(f"📥 Downloading {len(image_urls)} images...")
        count = 0
        for url in image_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200 and len(response.content) > 10000:  # Skip tiny images
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
                            "source": "google"
                        }, f)

                    self.downloaded.add(url)
                    count += 1
                    print(f"   ✓ Downloaded {count}/{len(image_urls)}")
            except Exception as e:
                print(f"   ✗ Failed: {e}")
                continue

        return count

    def run(self):
        """Run scraper with targeted queries"""

        queries = [
            # High-quality architectural queries
            "30x40 house floor plan with dimensions india",
            "40x60 duplex floor plan with measurements",
            "2bhk house plan 1000 sqft with dimensions",
            "3bhk house plan 1500 sqft floor plan",
            "vastu house plan 30x40 with room sizes",
            "indian house floor plan with measurements",
            "duplex house ground floor plan india",
            "single floor house plan 1200 sqft",
            "modern house floor plan india 2000 sqft",
            "small house floor plan 800 sqft india",
            "g+1 house plan 30x40 site",
            "40x60 house plan 3d elevation",
            "kerala house plan with nadumuttam",
            "row house floor plan india",
            "villa floor plan 3000 sqft india"
        ]

        total = 0
        for query in queries:
            try:
                count = self.search_and_scrape(query, max_images=40)
                total += count
                print(f"✅ Query '{query}': {count} images")
                time.sleep(3)
            except Exception as e:
                print(f"❌ Query '{query}' failed: {e}")
                continue

        print(f"\n🎉 DONE! Total downloaded: {total} images")
        print(f"📁 Saved to: {self.output_dir}/")

        self.driver.quit()

if __name__ == "__main__":
    scraper = GoogleImagesScraper()
    scraper.run()
