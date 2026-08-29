from database import Database

db = Database()
projects = db.get_all_projects()
print(f"Found {len(projects)} projects")

if projects:
    p = projects[0]
    print(f"Demo: {p['name']}")
    print(f"  Rooms: {p['total_rooms']}")
    print(f"  Sqft: {p['total_sqft']}")
    print(f"  Cost: ${p['estimated_cost']}")

    rooms = db.get_project_rooms(p['id'])
    print(f"  Room details: {len(rooms)} rooms")
    for r in rooms[:3]:
        print(f"    - {r['name']}: {r['total_area']:.0f} sqft")
