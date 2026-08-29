"""
99acres House Plan Scraper
Scrapes floor plans from real estate listings
Run: python 99acres_scraper.py
"""

import os
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import hashlib

class NinetyNineAcresScraper:
    def __init__(self, output_dir="99acres_plans"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.downloaded = set()

    def scrape_city_projects(self, city, max_projects=20):
        """Scrape floor plans from new projects in a city"""
        print(f"\n🏙️ Scraping {city}...")

        # Search for new residential projects
        search_url = f"https://www.99acres.com/new-projects-in-{city.lower()}"
        self.driver.get(search_url)
        time.sleep(3)

        # Get project links
        project_links = []
        try:
            projects = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/new-project/']")
            for project in projects[:max_projects]:
                link = project.get_attribute("href")
                if link and link not in project_links:
                    project_links.append(link)
        except Exception as e:
            print(f"   ✗ Failed to get project links: {e}")
            return 0

        print(f"   Found {len(project_links)} projects")

        # Visit each project and download floor plans
        count = 0
        for idx, link in enumerate(project_links):
            try:
                print(f"   Project {idx+1}/{len(project_links)}: {link}")
                self.driver.get(link)
                time.sleep(2)

                # Look for floor plan images
                # 99acres shows floor plans in galleries
                images = self.driver.find_elements(By.TAG_NAME, "img")

                for img in images:
                    src = img.get_attribute("src")
                    alt = img.get_attribute("alt") or ""

                    # Filter for floor plan images
                    if src and ("floor" in alt.lower() or "plan" in alt.lower() or "layout" in src.lower()):
                        if src not in self.downloaded:
                            try:
                                response = requests.get(src, timeout=10)
                                if response.status_code == 200:
                                    filename = hashlib.md5(src.encode()).hexdigest() + ".jpg"
                                    filepath = os.path.join(self.output_dir, filename)

                                    with open(filepath, 'wb') as f:
                                        f.write(response.content)

                                    # Save metadata
                                    meta_file = filepath.replace(".jpg", ".json")
                                    with open(meta_file, 'w') as f:
                                        json.dump({
                                            "url": src,
                                            "project_url": link,
                                            "city": city,
                                            "source": "99acres"
                                        }, f)

                                    self.downloaded.add(src)
                                    count += 1
                                    print(f"      ✓ Downloaded floor plan {count}")
                            except Exception as e:
                                print(f"      ✗ Download failed: {e}")
                                continue

            except Exception as e:
                print(f"   ✗ Project failed: {e}")
                continue

        return count

    def run(self):
        """Run scraper for multiple cities"""
        cities = [
            "bangalore",
            "hyderabad",
            "chennai",
            "mumbai",
            "pune",
            "delhi",
            "gurgaon",
            "noida",
            "kolkata",
            "ahmedabad"
        ]

        total = 0
        for city in cities:
            try:
                count = self.scrape_city_projects(city, max_projects=20)
                total += count
                print(f"✅ {city}: {count} floor plans")
                time.sleep(5)
            except Exception as e:
                print(f"❌ {city} failed: {e}")
                continue

        print(f"\n🎉 DONE! Total downloaded: {total} images")
        print(f"📁 Saved to: {self.output_dir}/")

        self.driver.quit()

if __name__ == "__main__":
    scraper = NinetyNineAcresScraper()
    scraper.run()
