"""
Material pricing database and supplier integration
Real-time pricing from suppliers like Sherwin-Williams, Benjamin Moore
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path


class MaterialDatabase:
    """Database of paint materials with pricing"""

    def __init__(self, data_file: str = "data/materials.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(exist_ok=True)

        if not self.data_file.exists():
            self._init_database()

        self.materials = self._load_materials()

    def _init_database(self):
        """Initialize with common paint materials"""
        initial_data = {
            "paint": {
                "primer": [
                    {
                        "id": "sw_prep_primer",
                        "name": "Sherwin-Williams PrepRite ProBlock Interior Primer",
                        "manufacturer": "Sherwin-Williams",
                        "category": "primer",
                        "coverage": 400,  # sqft per gallon
                        "price": 42.99,
                        "unit": "gallon",
                        "product_code": "B28W00750",
                        "sheen": "flat"
                    },
                    {
                        "id": "bm_fresh_start",
                        "name": "Benjamin Moore Fresh Start Multi-Purpose Primer",
                        "manufacturer": "Benjamin Moore",
                        "category": "primer",
                        "coverage": 400,
                        "price": 45.99,
                        "unit": "gallon",
                        "product_code": "N023",
                        "sheen": "flat"
                    }
                ],
                "interior_paint": [
                    {
                        "id": "sw_promar_200",
                        "name": "Sherwin-Williams ProMar 200 Zero VOC Interior Latex",
                        "manufacturer": "Sherwin-Williams",
                        "category": "interior_paint",
                        "coverage": 400,
                        "price": 52.99,
                        "unit": "gallon",
                        "product_code": "B20W00751",
                        "sheen": "eggshell",
                        "voc": "zero"
                    },
                    {
                        "id": "sw_promar_400",
                        "name": "Sherwin-Williams ProMar 400 Interior Latex",
                        "manufacturer": "Sherwin-Williams",
                        "category": "interior_paint",
                        "coverage": 400,
                        "price": 65.99,
                        "unit": "gallon",
                        "product_code": "B30W00750",
                        "sheen": "eggshell"
                    },
                    {
                        "id": "bm_regal_select",
                        "name": "Benjamin Moore Regal Select Interior Paint",
                        "manufacturer": "Benjamin Moore",
                        "category": "interior_paint",
                        "coverage": 400,
                        "price": 74.99,
                        "unit": "gallon",
                        "product_code": "N548",
                        "sheen": "eggshell",
                        "premium": True
                    },
                    {
                        "id": "behr_premium_plus",
                        "name": "BEHR Premium Plus Interior Paint",
                        "manufacturer": "BEHR",
                        "category": "interior_paint",
                        "coverage": 400,
                        "price": 38.98,
                        "unit": "gallon",
                        "product_code": "PR17",
                        "sheen": "eggshell",
                        "economy": True
                    }
                ]
            },
            "supplies": [
                {
                    "id": "roller_cover_9in",
                    "name": "9\" Roller Cover (3/8\" nap)",
                    "category": "roller",
                    "price": 3.99,
                    "unit": "each",
                    "coverage": 1000  # sqft per roller
                },
                {
                    "id": "roller_frame",
                    "name": "9\" Roller Frame",
                    "category": "roller",
                    "price": 8.99,
                    "unit": "each"
                },
                {
                    "id": "brush_2in",
                    "name": "2\" Angled Brush",
                    "category": "brush",
                    "price": 12.99,
                    "unit": "each"
                },
                {
                    "id": "painters_tape",
                    "name": "Painter's Tape 2\" x 60yd",
                    "category": "masking",
                    "price": 8.99,
                    "unit": "roll",
                    "coverage": 180  # linear feet
                },
                {
                    "id": "drop_cloth_9x12",
                    "name": "Canvas Drop Cloth 9' x 12'",
                    "category": "protection",
                    "price": 18.99,
                    "unit": "each"
                },
                {
                    "id": "paint_tray",
                    "name": "Paint Tray with Liner",
                    "category": "supplies",
                    "price": 4.99,
                    "unit": "each"
                },
                {
                    "id": "caulk_tube",
                    "name": "Acrylic Latex Caulk",
                    "category": "prep",
                    "price": 3.99,
                    "unit": "tube",
                    "coverage": 56  # linear feet
                },
                {
                    "id": "sandpaper_120",
                    "name": "120-Grit Sandpaper (5-pack)",
                    "category": "prep",
                    "price": 6.99,
                    "unit": "pack"
                }
            ]
        }

        with open(self.data_file, "w") as f:
            json.dump(initial_data, f, indent=2)

    def _load_materials(self) -> dict:
        """Load materials from JSON"""
        with open(self.data_file, "r") as f:
            return json.load(f)

    def search_materials(self, query: str, category: Optional[str] = None) -> List[dict]:
        """Search for materials"""
        results = []

        for cat, items in self.materials.items():
            if isinstance(items, dict):
                for subcat, subitems in items.items():
                    if category and subcat != category:
                        continue
                    for item in subitems:
                        if query.lower() in item["name"].lower():
                            results.append(item)
            elif isinstance(items, list):
                if category and cat != category:
                    continue
                for item in items:
                    if query.lower() in item["name"].lower():
                        results.append(item)

        return results

    def get_material_by_id(self, material_id: str) -> Optional[dict]:
        """Get material by ID"""
        for cat, items in self.materials.items():
            if isinstance(items, dict):
                for subitems in items.values():
                    for item in subitems:
                        if item["id"] == material_id:
                            return item
            elif isinstance(items, list):
                for item in items:
                    if item["id"] == material_id:
                        return item
        return None

    def get_recommended_materials(self, project_type: str = "commercial") -> dict:
        """Get recommended materials for a project"""
        if project_type == "commercial":
            return {
                "primer": self.get_material_by_id("sw_prep_primer"),
                "paint": self.get_material_by_id("sw_promar_400"),
                "quality": "mid-range"
            }
        elif project_type == "premium":
            return {
                "primer": self.get_material_by_id("bm_fresh_start"),
                "paint": self.get_material_by_id("bm_regal_select"),
                "quality": "premium"
            }
        else:  # economy
            return {
                "primer": self.get_material_by_id("sw_prep_primer"),
                "paint": self.get_material_by_id("behr_premium_plus"),
                "quality": "economy"
            }

    def calculate_supplies_needed(self, total_sqft: float) -> List[dict]:
        """Calculate supplies needed for a project"""
        supplies = []

        # Roller covers (1 per 1000 sqft)
        roller_covers = max(1, round(total_sqft / 1000))
        supplies.append({
            **self.get_material_by_id("roller_cover_9in"),
            "quantity": roller_covers,
            "total_price": roller_covers * 3.99
        })

        # Roller frame (1 per crew member, assume 1)
        supplies.append({
            **self.get_material_by_id("roller_frame"),
            "quantity": 1,
            "total_price": 8.99
        })

        # Brushes (2 per project)
        supplies.append({
            **self.get_material_by_id("brush_2in"),
            "quantity": 2,
            "total_price": 2 * 12.99
        })

        # Painter's tape (1 roll per 180 linear feet, assume perimeter = sqft / 10)
        perimeter = total_sqft / 10
        tape_rolls = max(1, round(perimeter / 180))
        supplies.append({
            **self.get_material_by_id("painters_tape"),
            "quantity": tape_rolls,
            "total_price": tape_rolls * 8.99
        })

        # Drop cloths (1 per 100 sqft)
        drop_cloths = max(1, round(total_sqft / 100))
        supplies.append({
            **self.get_material_by_id("drop_cloth_9x12"),
            "quantity": drop_cloths,
            "total_price": drop_cloths * 18.99
        })

        # Paint trays (1 per crew member)
        supplies.append({
            **self.get_material_by_id("paint_tray"),
            "quantity": 1,
            "total_price": 4.99
        })

        # Caulk (1 tube per 50 linear feet)
        caulk_tubes = max(1, round(perimeter / 56))
        supplies.append({
            **self.get_material_by_id("caulk_tube"),
            "quantity": caulk_tubes,
            "total_price": caulk_tubes * 3.99
        })

        # Sandpaper (1 pack)
        supplies.append({
            **self.get_material_by_id("sandpaper_120"),
            "quantity": 1,
            "total_price": 6.99
        })

        return supplies


class SupplierAPI:
    """Integration with supplier APIs for real-time pricing"""

    def __init__(self):
        self.sherwin_williams_api_key = os.getenv("SHERWIN_WILLIAMS_API_KEY")
        self.benjamin_moore_api_key = os.getenv("BENJAMIN_MOORE_API_KEY")
        self.cache_duration = timedelta(hours=24)
        self.cache = {}

    def get_sherwin_williams_price(self, product_code: str, zip_code: str) -> Optional[dict]:
        """Get real-time price from Sherwin-Williams API"""
        cache_key = f"sw_{product_code}_{zip_code}"

        # Check cache
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_data

        # In production, call real API
        # For now, return None (would integrate when API keys are available)
        return None

    def get_benjamin_moore_price(self, product_code: str, zip_code: str) -> Optional[dict]:
        """Get real-time price from Benjamin Moore API"""
        cache_key = f"bm_{product_code}_{zip_code}"

        # Check cache
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_data

        # In production, call real API
        return None

    def get_best_price(self, material_name: str, zip_code: str) -> dict:
        """Get best price from all suppliers"""
        # This would query multiple suppliers and return the best price
        # For now, return default pricing
        material_db = MaterialDatabase()
        materials = material_db.search_materials(material_name)

        if materials:
            return {
                "material": materials[0],
                "supplier": "Local Store",
                "price": materials[0]["price"],
                "availability": "in_stock"
            }

        return None


# Global instances
material_db = MaterialDatabase()
supplier_api = SupplierAPI()


if __name__ == "__main__":
    # Test material database
    print("🎨 Testing Material Database")

    # Search for paint
    results = material_db.search_materials("ProMar")
    print(f"\nFound {len(results)} ProMar products:")
    for r in results:
        print(f"  - {r['name']}: ${r['price']}/gallon")

    # Get recommended materials
    recommended = material_db.get_recommended_materials("commercial")
    print(f"\nRecommended for commercial:")
    print(f"  Primer: {recommended['primer']['name']} - ${recommended['primer']['price']}")
    print(f"  Paint: {recommended['paint']['name']} - ${recommended['paint']['price']}")

    # Calculate supplies
    supplies = material_db.calculate_supplies_needed(2000)
    print(f"\nSupplies needed for 2000 sqft:")
    total_cost = 0
    for s in supplies:
        print(f"  - {s['name']} × {s['quantity']} = ${s['total_price']:.2f}")
        total_cost += s['total_price']
    print(f"  Total supplies cost: ${total_cost:.2f}")
