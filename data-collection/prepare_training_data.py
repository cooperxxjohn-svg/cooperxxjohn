"""
Prepare CubiCasa5K for floor plan generation training
Converts dataset to format suitable for Stable Diffusion + ControlNet

Output:
- PNG images of floor plans
- Text prompts describing each floor plan
- Train/validation/test splits
"""

import os
import json
import shutil
from pathlib import Path
from PIL import Image
import xml.etree.ElementTree as ET

class CubiCasaPreprocessor:
    def __init__(self, data_dir="cubicasa5k/data/cubicasa5k"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path("training_data")
        self.output_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.output_dir / "images").mkdir(exist_ok=True)
        (self.output_dir / "prompts").mkdir(exist_ok=True)

        self.stats = {
            "total": 0,
            "processed": 0,
            "failed": 0,
            "by_category": {}
        }

    def parse_svg_annotations(self, svg_path):
        """
        Parse SVG file to extract room information

        Returns:
            {
                'rooms': ['bedroom', 'kitchen', 'bathroom'],
                'num_bedrooms': 2,
                'num_bathrooms': 1,
                'has_kitchen': True,
                'total_rooms': 5
            }
        """
        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()

            # Extract room types from SVG
            rooms = []

            # Look for text elements or class attributes with room names
            for elem in root.iter():
                # Common room keywords
                text = elem.text if elem.text else ""
                class_attr = elem.get('class', '')

                if any(keyword in text.lower() + class_attr.lower()
                       for keyword in ['bedroom', 'bath', 'kitchen', 'living']):
                    rooms.append(text.lower() if text else class_attr.lower())

            # Count room types
            room_counts = {
                'bedrooms': sum(1 for r in rooms if 'bedroom' in r),
                'bathrooms': sum(1 for r in rooms if 'bath' in r),
                'kitchen': any('kitchen' in r for r in rooms),
                'living': any('living' in r for r in rooms)
            }

            return {
                'rooms': list(set(rooms)),
                'num_bedrooms': room_counts['bedrooms'],
                'num_bathrooms': room_counts['bathrooms'],
                'has_kitchen': room_counts['kitchen'],
                'has_living': room_counts['living'],
                'total_rooms': len(rooms)
            }
        except Exception as e:
            print(f"Error parsing SVG {svg_path}: {e}")
            return None

    def generate_prompt(self, plan_info):
        """
        Generate text prompt for floor plan

        Example: "Floor plan with 2 bedrooms, 1 bathroom, kitchen, and living room"
        """
        parts = []

        if plan_info['num_bedrooms'] > 0:
            parts.append(f"{plan_info['num_bedrooms']} bedroom{'s' if plan_info['num_bedrooms'] > 1 else ''}")

        if plan_info['num_bathrooms'] > 0:
            parts.append(f"{plan_info['num_bathrooms']} bathroom{'s' if plan_info['num_bathrooms'] > 1 else ''}")

        if plan_info['has_kitchen']:
            parts.append("kitchen")

        if plan_info['has_living']:
            parts.append("living room")

        if not parts:
            # Generic prompt if we couldn't parse details
            return f"Residential floor plan with {plan_info['total_rooms']} rooms"

        return f"Floor plan with {', '.join(parts)}"

    def process_floor_plan(self, plan_folder):
        """
        Process a single floor plan:
        1. Copy image
        2. Parse SVG annotations
        3. Generate text prompt
        4. Save metadata
        """
        plan_name = plan_folder.name

        # Find the floor plan image
        image_path = plan_folder / "F1_scaled.png"
        if not image_path.exists():
            # Try alternative names
            image_path = plan_folder / "F1_original.png"

        if not image_path.exists():
            return False

        # Find SVG annotations
        svg_path = plan_folder / "model.svg"

        # Parse room information
        plan_info = None
        if svg_path.exists():
            plan_info = self.parse_svg_annotations(svg_path)

        if not plan_info:
            # Use default info
            plan_info = {
                'rooms': [],
                'num_bedrooms': 0,
                'num_bathrooms': 0,
                'has_kitchen': False,
                'has_living': False,
                'total_rooms': 0
            }

        # Generate prompt
        prompt = self.generate_prompt(plan_info)

        # Copy image to output
        output_image = self.output_dir / "images" / f"{plan_name}.png"
        shutil.copy(image_path, output_image)

        # Save prompt
        prompt_file = self.output_dir / "prompts" / f"{plan_name}.txt"
        with open(prompt_file, 'w') as f:
            f.write(prompt)

        # Save metadata
        metadata = {
            'plan_id': plan_name,
            'prompt': prompt,
            'plan_info': plan_info
        }

        metadata_file = self.output_dir / "prompts" / f"{plan_name}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        return True

    def process_all(self):
        """Process entire dataset"""
        print("\n" + "="*70)
        print("CUBICASA5K PREPROCESSING")
        print("="*70 + "\n")

        # Find all floor plan folders
        categories = ['high_quality', 'high_quality_architectural', 'colorful']

        for category in categories:
            category_path = self.data_dir / category

            if not category_path.exists():
                print(f"⚠️  Category not found: {category}")
                continue

            print(f"\n📁 Processing {category}...")

            # Get all plan folders in this category
            plan_folders = [f for f in category_path.iterdir() if f.is_dir()]

            count = 0
            for plan_folder in plan_folders:
                self.stats['total'] += 1

                if self.process_floor_plan(plan_folder):
                    self.stats['processed'] += 1
                    count += 1

                    if count % 100 == 0:
                        print(f"   Processed {count}/{len(plan_folders)}...")
                else:
                    self.stats['failed'] += 1

            print(f"   ✅ {category}: {count} plans processed")

            self.stats['by_category'][category] = count

        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate processing summary"""
        print("\n" + "="*70)
        print("PREPROCESSING SUMMARY")
        print("="*70)
        print(f"\nTotal floor plans: {self.stats['total']}")
        print(f"✅ Successfully processed: {self.stats['processed']}")
        print(f"❌ Failed: {self.stats['failed']}")

        print("\nBy category:")
        for category, count in self.stats['by_category'].items():
            print(f"  • {category}: {count}")

        print(f"\n📁 Output saved to: {self.output_dir}/")
        print(f"   - Images: {self.output_dir}/images/")
        print(f"   - Prompts: {self.output_dir}/prompts/")
        print("="*70 + "\n")

        # Save stats
        stats_file = self.output_dir / "preprocessing_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)


if __name__ == "__main__":
    preprocessor = CubiCasaPreprocessor()
    preprocessor.process_all()
