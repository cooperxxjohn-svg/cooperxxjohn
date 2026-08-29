"""
Master Data Collection Script
Runs all scrapers and quality checker
Run: python collect_all.py
"""

import os
import sys
import time
from datetime import datetime

def print_header(text):
    print("\n" + "="*70)
    print(text.center(70))
    print("="*70 + "\n")

def run_scraper(script_name, description):
    """Run a scraper script"""
    print_header(f"STEP: {description}")
    print(f"Running: {script_name}\n")

    start_time = time.time()

    try:
        # Import and run the scraper
        if script_name == "pinterest_scraper.py":
            from pinterest_scraper import PinterestScraper
            scraper = PinterestScraper()
            scraper.run()
        elif script_name == "99acres_scraper.py":
            from 99acres_scraper import NinetyNineAcresScraper
            scraper = NinetyNineAcresScraper()
            scraper.run()
        elif script_name == "google_images_scraper.py":
            from google_images_scraper import GoogleImagesScraper
            scraper = GoogleImagesScraper()
            scraper.run()
        elif script_name == "quality_checker.py":
            from quality_checker import QualityChecker
            checker = QualityChecker(
                input_dirs=["pinterest_plans", "99acres_plans", "google_plans"],
                output_dir="verified_plans"
            )
            checker.process_all()

        elapsed = time.time() - start_time
        print(f"\n✅ {description} completed in {elapsed/60:.1f} minutes\n")
        return True

    except Exception as e:
        print(f"\n❌ {description} failed: {e}\n")
        return False

def main():
    print_header("HOUSE PLAN DATA COLLECTION PIPELINE")
    print("This will take ~2-3 hours to complete")
    print("Press Ctrl+C to stop at any time\n")

    input("Press Enter to start...")

    start_time = time.time()
    results = {}

    # Step 1: Pinterest (largest source)
    results['pinterest'] = run_scraper(
        "pinterest_scraper.py",
        "Pinterest Scraper (Target: 500+ images)"
    )

    # Step 2: 99acres
    results['99acres'] = run_scraper(
        "99acres_scraper.py",
        "99acres Scraper (Target: 200+ images)"
    )

    # Step 3: Google Images
    results['google'] = run_scraper(
        "google_images_scraper.py",
        "Google Images Scraper (Target: 300+ images)"
    )

    # Step 4: Quality Check
    results['quality_check'] = run_scraper(
        "quality_checker.py",
        "Quality Verification"
    )

    # Final summary
    total_time = time.time() - start_time

    print_header("COLLECTION COMPLETE")

    print("Results:")
    for step, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {step.ljust(20)}: {status}")

    print(f"\nTotal time: {total_time/60:.1f} minutes")
    print(f"\nVerified plans are in: verified_plans/")
    print("Next step: Review images manually, then start preprocessing\n")

    # Save collection log
    log_file = f"collection_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(log_file, 'w') as f:
        f.write(f"Collection completed at: {datetime.now()}\n")
        f.write(f"Total time: {total_time/60:.1f} minutes\n\n")
        for step, success in results.items():
            f.write(f"{step}: {'SUCCESS' if success else 'FAILED'}\n")

    print(f"📄 Log saved to: {log_file}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted by user")
        sys.exit(0)
