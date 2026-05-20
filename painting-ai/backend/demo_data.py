"""
Demo data loader - Creates sample project for testing
"""

import json
from database import Database
from datetime import datetime


def load_demo_project():
    """Create a demo project with sample data"""

    db = Database()

    # Create demo project
    project = {
        "id": "demo-office-2026",
        "name": "Downtown Office Renovation",
        "customer": "ABC Commercial Properties",
        "created_at": datetime.utcnow().isoformat(),
        "status": "complete",
        "total_rooms": 8,
        "total_sqft": 3450,
        "total_gallons": 28,
        "total_labor_hours": 52,
        "estimated_cost": 4850
    }

    db.save_project(project)

    # Create demo rooms
    rooms = [
        {
            "id": "room-lobby",
            "project_id": "demo-office-2026",
            "name": "Lobby",
            "number": "101",
            "dimensions": {"length": 30, "width": 20, "height": 12},
            "surfaces": {
                "walls": {"type": "wall", "area": 1100, "deductions": 100, "height": 12},
                "ceiling": {"type": "ceiling", "area": 600},
                "trim": {"type": "trim", "area": 95, "linear_feet": 95}
            },
            "total_area": 1795
        },
        {
            "id": "room-conf-a",
            "project_id": "demo-office-2026",
            "name": "Conference Room A",
            "number": "205",
            "dimensions": {"length": 25, "width": 18, "height": 10},
            "surfaces": {
                "walls": {"type": "wall", "area": 790, "deductions": 60, "height": 10},
                "ceiling": {"type": "ceiling", "area": 450},
                "trim": {"type": "trim", "area": 81, "linear_feet": 81}
            },
            "total_area": 1321
        },
        {
            "id": "room-office-1",
            "project_id": "demo-office-2026",
            "name": "Office 1",
            "number": "201",
            "dimensions": {"length": 15, "width": 12, "height": 9},
            "surfaces": {
                "walls": {"type": "wall", "area": 450, "deductions": 35, "height": 9},
                "ceiling": {"type": "ceiling", "area": 180},
                "trim": {"type": "trim", "area": 48, "linear_feet": 48}
            },
            "total_area": 678
        },
        {
            "id": "room-office-2",
            "project_id": "demo-office-2026",
            "name": "Office 2",
            "number": "202",
            "dimensions": {"length": 15, "width": 12, "height": 9},
            "surfaces": {
                "walls": {"type": "wall", "area": 450, "deductions": 35, "height": 9},
                "ceiling": {"type": "ceiling", "area": 180},
                "trim": {"type": "trim", "area": 48, "linear_feet": 48}
            },
            "total_area": 678
        },
        {
            "id": "room-office-3",
            "project_id": "demo-office-2026",
            "name": "Office 3",
            "number": "203",
            "dimensions": {"length": 12, "width": 10, "height": 9},
            "surfaces": {
                "walls": {"type": "wall", "area": 360, "deductions": 28, "height": 9},
                "ceiling": {"type": "ceiling", "area": 120},
                "trim": {"type": "trim", "area": 40, "linear_feet": 40}
            },
            "total_area": 520
        },
        {
            "id": "room-break-room",
            "project_id": "demo-office-2026",
            "name": "Break Room",
            "number": "104",
            "dimensions": {"length": 18, "width": 14, "height": 9},
            "surfaces": {
                "walls": {"type": "wall", "area": 528, "deductions": 42, "height": 9},
                "ceiling": {"type": "ceiling", "area": 252},
                "trim": {"type": "trim", "area": 58, "linear_feet": 58}
            },
            "total_area": 838
        },
        {
            "id": "room-storage",
            "project_id": "demo-office-2026",
            "name": "Storage Room",
            "number": "105",
            "dimensions": {"length": 10, "width": 8, "height": 9},
            "surfaces": {
                "walls": {"type": "wall", "area": 288, "deductions": 21, "height": 9},
                "ceiling": {"type": "ceiling", "area": 80},
                "trim": {"type": "trim", "area": 33, "linear_feet": 33}
            },
            "total_area": 401
        },
        {
            "id": "room-hallway",
            "project_id": "demo-office-2026",
            "name": "Main Hallway",
            "number": "100",
            "dimensions": {"length": 40, "width": 6, "height": 9},
            "surfaces": {
                "walls": {"type": "wall", "area": 792, "deductions": 70, "height": 9},
                "ceiling": {"type": "ceiling", "area": 240},
                "trim": {"type": "trim", "area": 85, "linear_feet": 85}
            },
            "total_area": 1117
        }
    ]

    for room in rooms:
        db.save_room(room)

    print(f"✓ Demo project created: {project['id']}")
    print(f"  - {len(rooms)} rooms")
    print(f"  - {project['total_sqft']:,.0f} sqft total")
    print(f"  - ${project['estimated_cost']:,.0f} estimated cost")

    return project["id"]


if __name__ == "__main__":
    project_id = load_demo_project()
    print(f"\n🎨 Demo project ready!")
    print(f"   View at: http://localhost:3000/projects/{project_id}")
