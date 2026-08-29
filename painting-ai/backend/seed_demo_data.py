#!/usr/bin/env python3
"""
Demo Data Seeder for Painting.ai
Creates realistic sample projects for contractor demonstrations
"""

import sys
import uuid
from datetime import datetime, timedelta
from database import Database
from painting_detector import Room, Surface

def seed_demo_projects():
    """Seed 3 comprehensive demo projects"""

    db = Database()
    print("🌱 Seeding Demo Data for Painting.ai")
    print("=" * 60)

    # Project 1: Office Building Renovation (Commercial)
    print("\n📁 Creating Project 1: Office Building Renovation")

    project1_id = str(uuid.uuid4())
    project1 = {
        "id": project1_id,
        "name": "Downtown Office Renovation",
        "customer": "ABC Commercial Properties",
        "address": "123 Business Ave, Suite 500",
        "project_type": "commercial",
        "status": "complete",
        "created_at": (datetime.utcnow() - timedelta(days=5)).isoformat(),
        "total_rooms": 10,
        "total_sqft": 4200.0,
        "total_gallons": 42.0,
        "total_labor_hours": 84.0,
        "estimated_cost": 8500.0
    }

    db.save_project(project1)
    print(f"   ✓ Created project: {project1['name']}")

    # Add rooms for Project 1
    office_rooms = [
        {"name": "Lobby", "length": 30, "width": 25, "height": 12, "doors": 2, "windows": 4},
        {"name": "Conference Room A", "length": 25, "width": 20, "height": 10, "doors": 2, "windows": 3},
        {"name": "Conference Room B", "length": 20, "width": 18, "height": 10, "doors": 2, "windows": 2},
        {"name": "Executive Office", "length": 18, "width": 15, "height": 10, "doors": 1, "windows": 2},
        {"name": "Open Work Area", "length": 40, "width": 30, "height": 10, "doors": 2, "windows": 6},
        {"name": "Break Room", "length": 20, "width": 15, "height": 9, "doors": 1, "windows": 2},
        {"name": "IT Room", "length": 15, "width": 12, "height": 9, "doors": 1, "windows": 0},
        {"name": "Storage Closet", "length": 10, "width": 8, "height": 9, "doors": 1, "windows": 0},
        {"name": "Restroom", "length": 12, "width": 10, "height": 9, "doors": 1, "windows": 1},
        {"name": "Hallway", "length": 60, "width": 6, "height": 9, "doors": 0, "windows": 0}
    ]

    for room_info in office_rooms:
        room_id = str(uuid.uuid4())

        # Calculate surfaces
        length = room_info["length"]
        width = room_info["width"]
        height = room_info["height"]

        # Wall area
        perimeter = 2 * (length + width)
        wall_area = perimeter * height

        # Deductions
        door_area = room_info["doors"] * 21  # 3' x 7'
        window_area = room_info["windows"] * 15  # 3' x 5'
        wall_area_net = wall_area - door_area - window_area

        # Ceiling area
        ceiling_area = length * width

        # Total
        total_area = wall_area_net + ceiling_area

        room_data = {
            "id": room_id,
            "project_id": project1_id,
            "name": room_info["name"],
            "dimensions": {
                "length": length,
                "width": width,
                "height": height
            },
            "surfaces": {
                "walls": {
                    "type": "wall",
                    "area": wall_area_net,
                    "height": height,
                    "deductions": door_area + window_area
                },
                "ceiling": {
                    "type": "ceiling",
                    "area": ceiling_area
                }
            },
            "total_area": total_area
        }

        db.save_room(room_data)
        print(f"   ✓ Added room: {room_info['name']} ({total_area:.0f} sqft)")

    # Project 2: Retail Space (Premium)
    print("\n📁 Creating Project 2: Retail Space")

    project2_id = str(uuid.uuid4())
    project2 = {
        "id": project2_id,
        "name": "Luxury Retail Boutique",
        "customer": "Fashion Forward LLC",
        "address": "456 Shopping Mall, Store #12",
        "project_type": "retail",
        "status": "complete",
        "created_at": (datetime.utcnow() - timedelta(days=3)).isoformat(),
        "total_rooms": 5,
        "total_sqft": 2400.0,
        "total_gallons": 30.0,
        "total_labor_hours": 60.0,
        "estimated_cost": 6800.0
    }

    db.save_project(project2)
    print(f"   ✓ Created project: {project2['name']}")

    # Add rooms for Project 2
    retail_rooms = [
        {"name": "Main Sales Floor", "length": 40, "width": 30, "height": 12, "doors": 2, "windows": 6},
        {"name": "Fitting Rooms (4)", "length": 15, "width": 12, "height": 9, "doors": 4, "windows": 0},
        {"name": "Stock Room", "length": 20, "width": 15, "height": 9, "doors": 1, "windows": 0},
        {"name": "Office", "length": 12, "width": 10, "height": 9, "doors": 1, "windows": 1},
        {"name": "Employee Break Area", "length": 12, "width": 10, "height": 9, "doors": 1, "windows": 1}
    ]

    for room_info in retail_rooms:
        room_id = str(uuid.uuid4())

        length = room_info["length"]
        width = room_info["width"]
        height = room_info["height"]

        perimeter = 2 * (length + width)
        wall_area = perimeter * height
        door_area = room_info["doors"] * 21
        window_area = room_info["windows"] * 15
        wall_area_net = wall_area - door_area - window_area
        ceiling_area = length * width
        total_area = wall_area_net + ceiling_area

        room_data = {
            "id": room_id,
            "project_id": project2_id,
            "name": room_info["name"],
            "dimensions": {
                "length": length,
                "width": width,
                "height": height
            },
            "surfaces": {
                "walls": {
                    "type": "wall",
                    "area": wall_area_net,
                    "height": height,
                    "deductions": door_area + window_area
                },
                "ceiling": {
                    "type": "ceiling",
                    "area": ceiling_area
                }
            },
            "total_area": total_area
        }

        db.save_room(room_data)
        print(f"   ✓ Added room: {room_info['name']} ({total_area:.0f} sqft)")

    # Project 3: Warehouse Interior (Economy)
    print("\n📁 Creating Project 3: Warehouse Interior")

    project3_id = str(uuid.uuid4())
    project3 = {
        "id": project3_id,
        "name": "Industrial Warehouse Refresh",
        "customer": "Logistics Plus Inc",
        "address": "789 Industrial Parkway",
        "project_type": "industrial",
        "status": "complete",
        "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "total_rooms": 3,
        "total_sqft": 3200.0,
        "total_gallons": 38.0,
        "total_labor_hours": 64.0,
        "estimated_cost": 5200.0
    }

    db.save_project(project3)
    print(f"   ✓ Created project: {project3['name']}")

    # Add rooms for Project 3
    warehouse_rooms = [
        {"name": "Main Warehouse Floor", "length": 60, "width": 40, "height": 16, "doors": 3, "windows": 8},
        {"name": "Office Area", "length": 25, "width": 20, "height": 10, "doors": 2, "windows": 3},
        {"name": "Loading Dock", "length": 30, "width": 15, "height": 12, "doors": 2, "windows": 2}
    ]

    for room_info in warehouse_rooms:
        room_id = str(uuid.uuid4())

        length = room_info["length"]
        width = room_info["width"]
        height = room_info["height"]

        perimeter = 2 * (length + width)
        wall_area = perimeter * height
        door_area = room_info["doors"] * 21
        window_area = room_info["windows"] * 15
        wall_area_net = wall_area - door_area - window_area
        ceiling_area = length * width
        total_area = wall_area_net + ceiling_area

        room_data = {
            "id": room_id,
            "project_id": project3_id,
            "name": room_info["name"],
            "dimensions": {
                "length": length,
                "width": width,
                "height": height
            },
            "surfaces": {
                "walls": {
                    "type": "wall",
                    "area": wall_area_net,
                    "height": height,
                    "deductions": door_area + window_area
                },
                "ceiling": {
                    "type": "ceiling",
                    "area": ceiling_area
                }
            },
            "total_area": total_area
        }

        db.save_room(room_data)
        print(f"   ✓ Added room: {room_info['name']} ({total_area:.0f} sqft)")

    # Summary
    print("\n" + "=" * 60)
    print("✅ DEMO DATA SEEDING COMPLETE")
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"   • 3 projects created")
    print(f"   • 18 total rooms")
    print(f"   • 9,800 total sqft")
    print(f"   • $20,500 total estimated value")
    print()
    print("🚀 Ready to demo!")
    print()
    print("Test the API:")
    print("   GET  http://localhost:8000/projects")
    print("   GET  http://localhost:8000/projects/{project_id}")
    print("   POST http://localhost:8000/projects/{project_id}/assembly-expansion")
    print()


if __name__ == "__main__":
    try:
        seed_demo_projects()
    except Exception as e:
        print(f"\n❌ Error seeding demo data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
