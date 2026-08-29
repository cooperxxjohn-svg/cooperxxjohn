"""
Manual Review Helper
Shows images one-by-one for quick approve/reject
Run: python manual_review.py

Controls:
- SPACE / ENTER: Keep image (approved)
- D: Delete image (rejected)
- LEFT/RIGHT arrows: Navigate
- R: Recategorize (choose new category)
- Q: Quit
"""

import os
import sys
import json
import shutil
from pathlib import Path
try:
    from PIL import Image
    import tkinter as tk
    from tkinter import simpledialog
except ImportError:
    print("Installing required packages...")
    os.system("pip install Pillow")
    from PIL import Image
    import tkinter as tk
    from tkinter import simpledialog

class ManualReviewer:
    def __init__(self, input_dir="verified_plans"):
        self.input_dir = input_dir
        self.current_idx = 0
        self.images = []
        self.stats = {
            "total": 0,
            "reviewed": 0,
            "approved": 0,
            "deleted": 0,
            "recategorized": 0
        }

        # Available categories
        self.categories = [
            "30x40", "40x60", "50x80", "60x90", "20x50",
            "duplex", "triplex", "single_story",
            "2bhk", "3bhk", "4bhk",
            "vastu", "modern", "traditional",
            "uncategorized"
        ]

        # Load all images
        self._load_images()

    def _load_images(self):
        """Load all images from verified_plans folder"""
        print("Loading images...")

        for root, dirs, files in os.walk(self.input_dir):
            # Skip rejected folder
            if "rejected" in root:
                continue

            for file in files:
                if file.endswith(('.jpg', '.jpeg', '.png')):
                    image_path = os.path.join(root, file)
                    category = os.path.basename(root)
                    self.images.append({
                        "path": image_path,
                        "category": category,
                        "reviewed": False
                    })

        self.stats["total"] = len(self.images)
        print(f"Found {len(self.images)} images to review\n")

    def show_image(self):
        """Display current image with info"""
        if self.current_idx >= len(self.images):
            print("\n✅ Review complete!")
            self.show_stats()
            return False

        img_data = self.images[self.current_idx]
        img_path = img_data["path"]
        category = img_data["category"]

        # Clear screen
        os.system('clear' if os.name != 'nt' else 'cls')

        # Show progress
        print("="*70)
        print(f"MANUAL REVIEW - Image {self.current_idx + 1} / {len(self.images)}")
        print("="*70)
        print(f"\nCategory: {category}")
        print(f"File: {os.path.basename(img_path)}\n")

        # Show image (in terminal if possible, otherwise open externally)
        try:
            img = Image.open(img_path)
            width, height = img.size
            print(f"Resolution: {width}x{height}px")
            print(f"File size: {os.path.getsize(img_path)/1024:.1f} KB\n")

            # Open in default image viewer
            if sys.platform == "darwin":  # macOS
                os.system(f"open '{img_path}'")
            elif sys.platform == "linux":
                os.system(f"xdg-open '{img_path}' 2>/dev/null &")
            elif sys.platform == "win32":
                os.system(f"start '{img_path}'")

        except Exception as e:
            print(f"Error loading image: {e}\n")

        # Show controls
        print("─"*70)
        print("Controls:")
        print("  SPACE/ENTER : Keep (approved)")
        print("  D           : Delete (rejected)")
        print("  R           : Recategorize")
        print("  S           : Skip (come back later)")
        print("  Q           : Quit and save progress")
        print("─"*70)

        return True

    def approve(self):
        """Mark image as approved"""
        self.images[self.current_idx]["reviewed"] = True
        self.stats["reviewed"] += 1
        self.stats["approved"] += 1
        print("\n✅ APPROVED\n")
        self.current_idx += 1

    def delete(self):
        """Move image to rejected folder"""
        img_data = self.images[self.current_idx]
        img_path = img_data["path"]

        # Move to rejected folder
        rejected_dir = os.path.join(self.input_dir, "rejected", "manual_review")
        os.makedirs(rejected_dir, exist_ok=True)

        dest_path = os.path.join(rejected_dir, os.path.basename(img_path))
        shutil.move(img_path, dest_path)

        # Move metadata too
        meta_path = img_path.replace('.jpg', '.json').replace('.jpeg', '.json').replace('.png', '.json')
        if os.path.exists(meta_path):
            dest_meta = os.path.join(rejected_dir, os.path.basename(meta_path))
            shutil.move(meta_path, dest_meta)

        self.images[self.current_idx]["reviewed"] = True
        self.stats["reviewed"] += 1
        self.stats["deleted"] += 1
        print("\n❌ DELETED\n")
        self.current_idx += 1

    def recategorize(self):
        """Move image to different category"""
        img_data = self.images[self.current_idx]
        img_path = img_data["path"]
        old_category = img_data["category"]

        # Show category options
        print("\nAvailable categories:")
        for i, cat in enumerate(self.categories):
            print(f"  {i+1}. {cat}")

        choice = input("\nEnter category number (or name): ").strip()

        # Parse choice
        try:
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(self.categories):
                    new_category = self.categories[idx]
                else:
                    print("Invalid number")
                    return
            else:
                new_category = choice
        except:
            print("Invalid input")
            return

        # Move to new category folder
        new_category_dir = os.path.join(self.input_dir, new_category)
        os.makedirs(new_category_dir, exist_ok=True)

        dest_path = os.path.join(new_category_dir, os.path.basename(img_path))
        shutil.move(img_path, dest_path)

        # Move metadata
        meta_path = img_path.replace('.jpg', '.json').replace('.jpeg', '.json').replace('.png', '.json')
        if os.path.exists(meta_path):
            dest_meta = os.path.join(new_category_dir, os.path.basename(meta_path))
            shutil.move(meta_path, dest_meta)

        # Update in memory
        self.images[self.current_idx]["path"] = dest_path
        self.images[self.current_idx]["category"] = new_category
        self.images[self.current_idx]["reviewed"] = True

        self.stats["reviewed"] += 1
        self.stats["recategorized"] += 1
        print(f"\n📁 Moved: {old_category} → {new_category}\n")
        self.current_idx += 1

    def skip(self):
        """Skip to next image"""
        print("\n⏭️  SKIPPED\n")
        self.current_idx += 1

    def show_stats(self):
        """Show review statistics"""
        print("\n" + "="*70)
        print("REVIEW STATISTICS")
        print("="*70)
        print(f"\nTotal images: {self.stats['total']}")
        print(f"Reviewed: {self.stats['reviewed']} ({self.stats['reviewed']/self.stats['total']*100:.1f}%)")
        print(f"\nBreakdown:")
        print(f"  ✅ Approved: {self.stats['approved']}")
        print(f"  ❌ Deleted: {self.stats['deleted']}")
        print(f"  📁 Recategorized: {self.stats['recategorized']}")
        print(f"  ⏭️  Skipped: {self.stats['total'] - self.stats['reviewed']}")
        print("\n" + "="*70 + "\n")

    def run(self):
        """Run interactive review session"""
        print("\n" + "="*70)
        print("MANUAL REVIEW HELPER")
        print("="*70)
        print("\nReview images and keep only high-quality floor plans\n")
        input("Press Enter to start...")

        while self.current_idx < len(self.images):
            if not self.show_image():
                break

            # Get user input
            choice = input("\nAction: ").strip().lower()

            if choice in ['', ' ']:  # Space or Enter
                self.approve()
            elif choice == 'd':
                self.delete()
            elif choice == 'r':
                self.recategorize()
            elif choice == 's':
                self.skip()
            elif choice == 'q':
                print("\n💾 Saving progress and quitting...")
                self.show_stats()
                break
            else:
                print("Invalid choice. Use SPACE/D/R/S/Q")
                input("Press Enter to continue...")

        # Save review log
        log_file = "review_log.json"
        with open(log_file, 'w') as f:
            json.dump({
                "stats": self.stats,
                "progress": {
                    "reviewed_count": self.current_idx,
                    "total_count": len(self.images)
                }
            }, f, indent=2)

        print(f"📄 Review log saved to: {log_file}")

if __name__ == "__main__":
    reviewer = ManualReviewer(input_dir="verified_plans")
    reviewer.run()
