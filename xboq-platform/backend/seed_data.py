"""
Seed Database with Sample Data
Useful for development and testing
"""

import sys
from database import get_database
from datetime import datetime

def clear_database():
    """Clear all data from database"""
    db = get_database()
    print("🗑️  Clearing database...")

    # Drop and recreate tables
    db.drop_tables()
    db.create_tables()
    print("✅ Database cleared")

def seed_users():
    """Create sample users"""
    db = get_database()
    print("\n👥 Creating users...")

    users_data = [
        {"email": "demo@xboq.ai", "name": "Demo User"},
        {"email": "john@contractor.com", "name": "John Smith"},
        {"email": "sarah@builder.com", "name": "Sarah Johnson"},
        {"email": "mike@estimate.com", "name": "Mike Davis"},
    ]

    users = []
    for user_data in users_data:
        user = db.create_user(**user_data)
        users.append(user)
        print(f"   ✓ Created: {user.name} ({user.email})")

    return users

def seed_boq_projects(users):
    """Create sample BOQ projects"""
    db = get_database()
    print("\n📋 Creating BOQ projects...")

    projects_data = [
        {
            "user": users[0],
            "name": "Government Office Building - Phase 1",
            "sections": [
                {
                    "name": "Site Preparation",
                    "items": [
                        {"item": "Site clearing", "description": "Clear vegetation and debris", "quantity": 5000, "unit": "sqm"},
                        {"item": "Excavation", "description": "General excavation", "quantity": 850, "unit": "cum"},
                        {"item": "Leveling", "description": "Site leveling and compaction", "quantity": 5000, "unit": "sqm"}
                    ]
                },
                {
                    "name": "Concrete Work",
                    "items": [
                        {"item": "PCC 1:4:8", "description": "Plain cement concrete for foundation", "quantity": 125, "unit": "cum"},
                        {"item": "RCC M25", "description": "Reinforced cement concrete", "quantity": 450, "unit": "cum"},
                        {"item": "RCC M30", "description": "High strength RCC for columns", "quantity": 180, "unit": "cum"}
                    ]
                },
                {
                    "name": "Masonry",
                    "items": [
                        {"item": "Brick masonry", "description": "230mm thick wall in CM 1:6", "quantity": 2500, "unit": "sqm"},
                        {"item": "Block masonry", "description": "200mm AAC blocks", "quantity": 1800, "unit": "sqm"}
                    ]
                },
                {
                    "name": "Finishing",
                    "items": [
                        {"item": "Plastering", "description": "12mm cement plaster", "quantity": 4000, "unit": "sqm"},
                        {"item": "Floor tiles", "description": "600x600mm vitrified tiles", "quantity": 3200, "unit": "sqm"},
                        {"item": "Paint", "description": "Two coats acrylic emulsion", "quantity": 8000, "unit": "sqm"}
                    ]
                }
            ]
        },
        {
            "user": users[1],
            "name": "Commercial Plaza - Tender BOQ",
            "sections": [
                {
                    "name": "Foundation",
                    "items": [
                        {"item": "Excavation", "description": "Foundation pit excavation", "quantity": 450, "unit": "cum"},
                        {"item": "PCC", "description": "Lean concrete base", "quantity": 65, "unit": "cum"}
                    ]
                },
                {
                    "name": "Structural",
                    "items": [
                        {"item": "RCC columns", "description": "M30 grade columns", "quantity": 280, "unit": "cum"},
                        {"item": "RCC beams", "description": "M30 grade beams", "quantity": 320, "unit": "cum"},
                        {"item": "RCC slabs", "description": "M25 grade slabs", "quantity": 450, "unit": "cum"}
                    ]
                }
            ]
        },
        {
            "user": users[2],
            "name": "Residential Complex - Block A",
            "sections": [
                {
                    "name": "Civil Works",
                    "items": [
                        {"item": "Excavation", "description": "Earth excavation", "quantity": 650, "unit": "cum"},
                        {"item": "Concrete M20", "description": "Foundation concrete", "quantity": 180, "unit": "cum"},
                        {"item": "Brickwork", "description": "230mm brick walls", "quantity": 3500, "unit": "sqm"}
                    ]
                }
            ]
        }
    ]

    for project_data in projects_data:
        user = project_data["user"]
        name = project_data["name"]
        sections = project_data["sections"]

        # Create project
        project = db.create_project(
            user_id=user.id,
            project_type='boq',
            name=name,
            file_name=f"{name.lower().replace(' ', '_')}.pdf"
        )

        # Update status
        db.update_project(project.id, status='complete')

        # Create BOQ
        total_items = sum(len(section["items"]) for section in sections)
        boq = db.create_boq(
            project_id=project.id,
            project_name=name,
            sections=sections,
            total_items=total_items,
            extraction_time=2.5
        )

        print(f"   ✓ {name} ({total_items} items)")

def seed_estimate_projects(users):
    """Create sample estimate projects"""
    db = get_database()
    print("\n🏗️  Creating estimate projects...")

    estimates_data = [
        {
            "user": users[0],
            "name": "Office Drywall Installation",
            "trade": "drywall",
            "project_type": "commercial",
            "rooms": [
                {
                    "name": "Conference Room A",
                    "length": 30,
                    "width": 20,
                    "height": 10,
                    "doors": 2,
                    "windows": 4
                },
                {
                    "name": "Conference Room B",
                    "length": 25,
                    "width": 18,
                    "height": 10,
                    "doors": 2,
                    "windows": 3
                },
                {
                    "name": "Open Office Area",
                    "length": 50,
                    "width": 40,
                    "height": 10,
                    "doors": 4,
                    "windows": 10
                }
            ],
            "summary": {
                "total_sqft": 5260,
                "total_cost": 18500,
                "total_labor_hours": 185,
                "total_materials_cost": 9800,
                "total_labor_cost": 8700
            }
        },
        {
            "user": users[1],
            "name": "Home Interior Painting",
            "trade": "painting",
            "project_type": "residential",
            "rooms": [
                {
                    "name": "Master Bedroom",
                    "length": 16,
                    "width": 14,
                    "height": 9,
                    "doors": 2,
                    "windows": 2
                },
                {
                    "name": "Living Room",
                    "length": 22,
                    "width": 18,
                    "height": 9,
                    "doors": 2,
                    "windows": 4
                },
                {
                    "name": "Kitchen",
                    "length": 12,
                    "width": 10,
                    "height": 9,
                    "doors": 1,
                    "windows": 1
                },
                {
                    "name": "Bedroom 2",
                    "length": 12,
                    "width": 12,
                    "height": 9,
                    "doors": 1,
                    "windows": 2
                }
            ],
            "summary": {
                "total_sqft": 2480,
                "total_cost": 3250,
                "total_labor_hours": 42,
                "total_materials_cost": 1450,
                "total_labor_cost": 1800
            }
        },
        {
            "user": users[2],
            "name": "Warehouse Drywall",
            "trade": "drywall",
            "project_type": "industrial",
            "rooms": [
                {
                    "name": "Storage Area",
                    "length": 80,
                    "width": 60,
                    "height": 14,
                    "doors": 6,
                    "windows": 8
                },
                {
                    "name": "Office Section",
                    "length": 40,
                    "width": 30,
                    "height": 10,
                    "doors": 4,
                    "windows": 6
                }
            ],
            "summary": {
                "total_sqft": 8960,
                "total_cost": 32500,
                "total_labor_hours": 285,
                "total_materials_cost": 17200,
                "total_labor_cost": 15300
            }
        },
        {
            "user": users[3],
            "name": "Retail Store Painting",
            "trade": "painting",
            "project_type": "commercial",
            "rooms": [
                {
                    "name": "Sales Floor",
                    "length": 45,
                    "width": 35,
                    "height": 12,
                    "doors": 3,
                    "windows": 6
                },
                {
                    "name": "Storage Room",
                    "length": 20,
                    "width": 15,
                    "height": 10,
                    "doors": 1,
                    "windows": 0
                }
            ],
            "summary": {
                "total_sqft": 3620,
                "total_cost": 5450,
                "total_labor_hours": 68,
                "total_materials_cost": 2180,
                "total_labor_cost": 3270
            }
        }
    ]

    for estimate_data in estimates_data:
        user = estimate_data["user"]
        name = estimate_data["name"]

        # Create project
        project = db.create_project(
            user_id=user.id,
            project_type='estimate',
            name=name
        )

        # Update status
        db.update_project(project.id, status='complete')

        # Create estimate
        summary = estimate_data["summary"]
        estimate = db.create_estimate(
            project_id=project.id,
            trade=estimate_data["trade"],
            project_type=estimate_data["project_type"],
            rooms=estimate_data["rooms"],
            summary=summary,
            total_cost=summary["total_cost"],
            total_sqft=summary["total_sqft"],
            total_labor_hours=summary.get("total_labor_hours"),
            calculation_time=1.8
        )

        print(f"   ✓ {name} (${summary['total_cost']:,.0f}, {len(estimate_data['rooms'])} rooms)")

def print_summary():
    """Print database summary"""
    db = get_database()

    print("\n" + "="*70)
    print("📊 DATABASE SUMMARY")
    print("="*70)

    # Count users
    users = db.get_all_users()
    print(f"\n👥 Users: {len(users)}")
    for user in users:
        stats = db.get_user_stats(user.id)
        print(f"   • {user.name} ({user.email})")
        print(f"     - Projects: {stats['total_projects']} (BOQ: {stats['boq_projects']}, Estimates: {stats['estimate_projects']})")

    # Summary stats
    print(f"\n📊 Overall Statistics:")
    total_projects = sum(db.get_user_stats(u.id)['total_projects'] for u in users)
    total_boqs = sum(db.get_user_stats(u.id)['boq_projects'] for u in users)
    total_estimates = sum(db.get_user_stats(u.id)['estimate_projects'] for u in users)

    print(f"   • Total Projects: {total_projects}")
    print(f"   • BOQ Projects: {total_boqs}")
    print(f"   • Estimate Projects: {total_estimates}")

    print("\n" + "="*70)
    print("✅ Seed data created successfully!")
    print("="*70 + "\n")

def main():
    """Main seeding function"""
    print("\n" + "="*70)
    print("🌱 XBOQ DATABASE SEEDER")
    print("="*70)

    # Clear existing data
    clear_database()

    # Seed users
    users = seed_users()

    # Seed projects
    seed_boq_projects(users)
    seed_estimate_projects(users)

    # Print summary
    print_summary()

    print("\n💡 Tip: Start the backend to see the data:")
    print("   python app.py")
    print("\n💡 Access via API:")
    print("   curl http://localhost:5000/api/projects")
    print("   curl http://localhost:5000/api/stats")
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Seeding cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
