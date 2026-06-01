"""Quick test to see if Chrome/Selenium works"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

print("Setting up ChromeDriver...")

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

try:
    # Use manually installed ChromeDriver
    service = Service('/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get("https://www.google.com")
    print(f"✅ Chrome working! Page title: {driver.title}")
    driver.quit()
    print("✅ All systems GO - ready to collect data!")
except Exception as e:
    print(f"❌ Chrome failed: {e}")
