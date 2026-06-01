"""
Quality Checker for Downloaded House Plans
Filters out low-quality, duplicate, or irrelevant images
Run: python quality_checker.py
"""

import os
import json
import shutil
from PIL import Image
import imagehash
from collections import defaultdict

class QualityChecker:
    def __init__(self, input_dirs, output_dir="verified_plans"):
        self.input_dirs = input_dirs if isinstance(input_dirs, list) else [input_dirs]
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "rejected"), exist_ok=True)

        self.stats = {
            "total": 0,
            "too_small": 0,
            "wrong_aspect": 0,
            "duplicate": 0,
            "low_quality": 0,
            "approved": 0
        }

        self.seen_hashes = set()

    def check_image_quality(self, image_path):
        """
        Check if image meets quality criteria

        Returns:
            (is_good, reason)
        """
        try:
            img = Image.open(image_path)

            # Check 1: Minimum resolution (800x600)
            width, height = img.size
            if width < 800 or height < 600:
                return False, "too_small"

            # Check 2: Aspect ratio (should be landscape or squarish for floor plans)
            aspect_ratio = width / height
            if aspect_ratio < 0.5 or aspect_ratio > 2.5:
                return False, "wrong_aspect"

            # Check 3: File size (too small = low quality)
            file_size = os.path.getsize(image_path)
            if file_size < 50000:  # 50KB
                return False, "low_quality"

            # Check 4: Duplicate detection (perceptual hash)
            img_hash = imagehash.average_hash(img)
            if img_hash in self.seen_hashes:
                return False, "duplicate"
            self.seen_hashes.add(img_hash)

            # Check 5: Color mode (should be RGB or grayscale)
            if img.mode not in ["RGB", "L", "RGBA"]:
                return False, "wrong_format"

            return True, "approved"

        except Exception as e:
            return False, f"error: {e}"

    def categorize_by_metadata(self, meta_path):
        """
        Try to categorize floor plan based on query/filename

        Returns:
            category (30x40, 40x60, duplex, etc.)
        """
        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
                query = meta.get('query', '').lower()

                # Detect plot size
                if "30x40" in query or "30*40" in query:
                    return "30x40"
                elif "40x60" in query or "40*60" in query:
                    return "40x60"
                elif "50x80" in query or "50*80" in query:
                    return "50x80"
                elif "20x50" in query or "25x50" in query:
                    return "20x50"
                elif "60x90" in query or "60*90" in query:
                    return "60x90"

                # Detect type
                if "duplex" in query or "g+1" in query:
                    return "duplex"
                elif "single" in query or "1 floor" in query:
                    return "single_story"

                # Detect BHK
                if "2bhk" in query or "2 bhk" in query:
                    return "2bhk"
                elif "3bhk" in query or "3 bhk" in query:
                    return "3bhk"
                elif "4bhk" in query or "4 bhk" in query:
                    return "4bhk"

                # Detect features
                if "vastu" in query:
                    return "vastu"

                return "uncategorized"

        except:
            return "uncategorized"

    def process_all(self):
        """Process all downloaded images"""

        print("\n" + "="*70)
        print("QUALITY CHECKER - Verifying Downloaded House Plans")
        print("="*70 + "\n")

        all_images = []

        # Collect all images from input directories
        for input_dir in self.input_dirs:
            if os.path.exists(input_dir):
                for filename in os.listdir(input_dir):
                    if filename.endswith(('.jpg', '.jpeg', '.png')):
                        image_path = os.path.join(input_dir, filename)
                        meta_path = image_path.replace('.jpg', '.json').replace('.jpeg', '.json').replace('.png', '.json')
                        all_images.append((image_path, meta_path))

        print(f"Found {len(all_images)} images to verify\n")

        # Process each image
        approved_by_category = defaultdict(list)

        for idx, (image_path, meta_path) in enumerate(all_images):
            self.stats["total"] += 1
            basename = os.path.basename(image_path)

            # Check quality
            is_good, reason = self.check_image_quality(image_path)

            if is_good:
                # Categorize
                category = self.categorize_by_metadata(meta_path) if os.path.exists(meta_path) else "uncategorized"

                # Create category folder
                category_dir = os.path.join(self.output_dir, category)
                os.makedirs(category_dir, exist_ok=True)

                # Copy to verified folder
                dest_path = os.path.join(category_dir, basename)
                shutil.copy2(image_path, dest_path)

                # Copy metadata
                if os.path.exists(meta_path):
                    dest_meta = os.path.join(category_dir, os.path.basename(meta_path))
                    shutil.copy2(meta_path, dest_meta)

                self.stats["approved"] += 1
                approved_by_category[category].append(basename)

                print(f"✅ [{idx+1}/{len(all_images)}] {basename} → {category}")

            else:
                # Move to rejected folder
                reject_reason = reason.replace(" ", "_")
                reject_dir = os.path.join(self.output_dir, "rejected", reject_reason)
                os.makedirs(reject_dir, exist_ok=True)

                dest_path = os.path.join(reject_dir, basename)
                shutil.copy2(image_path, dest_path)

                self.stats[reason] += 1
                print(f"❌ [{idx+1}/{len(all_images)}] {basename} → REJECTED ({reason})")

        # Print summary
        print("\n" + "="*70)
        print("QUALITY CHECK SUMMARY")
        print("="*70)
        print(f"\nTotal images: {self.stats['total']}")
        print(f"✅ Approved: {self.stats['approved']} ({self.stats['approved']/self.stats['total']*100:.1f}%)")
        print(f"\nRejection reasons:")
        print(f"  • Too small (<800x600): {self.stats['too_small']}")
        print(f"  • Wrong aspect ratio: {self.stats['wrong_aspect']}")
        print(f"  • Duplicate: {self.stats['duplicate']}")
        print(f"  • Low quality: {self.stats['low_quality']}")

        print(f"\nApproved images by category:")
        for category, images in sorted(approved_by_category.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  • {category}: {len(images)} images")

        print(f"\n📁 Verified plans saved to: {self.output_dir}/")
        print("="*70 + "\n")

        # Generate report
        report_path = os.path.join(self.output_dir, "quality_report.json")
        with open(report_path, 'w') as f:
            json.dump({
                "stats": self.stats,
                "categories": {cat: len(imgs) for cat, imgs in approved_by_category.items()}
            }, f, indent=2)

        print(f"📊 Report saved to: {report_path}\n")

if __name__ == "__main__":
    # Check all downloaded images
    checker = QualityChecker(
        input_dirs=[
            "pinterest_plans",
            "99acres_plans",
            "google_plans"
        ],
        output_dir="verified_plans"
    )
    checker.process_all()
