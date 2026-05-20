"""
Simple JSON-based database for MVP
Will migrate to PostgreSQL later
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional


class Database:
    """Simple file-based database for MVP"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.projects_file = self.data_dir / "projects.json"
        self.rooms_file = self.data_dir / "rooms.json"

        # Initialize files if they don't exist
        if not self.projects_file.exists():
            self._write_json(self.projects_file, {})

        if not self.rooms_file.exists():
            self._write_json(self.rooms_file, {})

    def _read_json(self, file_path: Path) -> Dict:
        """Read JSON file"""
        with open(file_path, "r") as f:
            return json.load(f)

    def _write_json(self, file_path: Path, data: Dict):
        """Write JSON file"""
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def is_connected(self) -> bool:
        """Check if database is accessible"""
        return self.projects_file.exists() and self.rooms_file.exists()

    # Projects
    def save_project(self, project: Dict):
        """Save a new project"""
        projects = self._read_json(self.projects_file)
        projects[project["id"]] = project
        self._write_json(self.projects_file, projects)

    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get a project by ID"""
        projects = self._read_json(self.projects_file)
        return projects.get(project_id)

    def get_all_projects(self) -> List[Dict]:
        """Get all projects"""
        projects = self._read_json(self.projects_file)
        return list(projects.values())

    def update_project(self, project_id: str, updates: Dict):
        """Update a project"""
        projects = self._read_json(self.projects_file)

        if project_id not in projects:
            raise ValueError(f"Project {project_id} not found")

        projects[project_id].update(updates)
        self._write_json(self.projects_file, projects)

    def delete_project(self, project_id: str):
        """Delete a project and all its rooms"""
        projects = self._read_json(self.projects_file)

        if project_id in projects:
            del projects[project_id]
            self._write_json(self.projects_file, projects)

        # Delete associated rooms
        rooms = self._read_json(self.rooms_file)
        rooms = {
            room_id: room
            for room_id, room in rooms.items()
            if room.get("project_id") != project_id
        }
        self._write_json(self.rooms_file, rooms)

    # Rooms
    def save_room(self, room: Dict):
        """Save a new room"""
        rooms = self._read_json(self.rooms_file)
        rooms[room["id"]] = room
        self._write_json(self.rooms_file, rooms)

    def get_room(self, room_id: str) -> Optional[Dict]:
        """Get a room by ID"""
        rooms = self._read_json(self.rooms_file)
        return rooms.get(room_id)

    def get_project_rooms(self, project_id: str) -> List[Dict]:
        """Get all rooms for a project"""
        rooms = self._read_json(self.rooms_file)
        return [
            room for room in rooms.values()
            if room.get("project_id") == project_id
        ]

    def update_room(self, room_id: str, updates: Dict):
        """Update a room"""
        rooms = self._read_json(self.rooms_file)

        if room_id not in rooms:
            raise ValueError(f"Room {room_id} not found")

        rooms[room_id].update(updates)
        self._write_json(self.rooms_file, rooms)

    def delete_room(self, room_id: str):
        """Delete a room"""
        rooms = self._read_json(self.rooms_file)

        if room_id in rooms:
            del rooms[room_id]
            self._write_json(self.rooms_file, rooms)

    # Users (Phase 3)
    def save_user(self, user: Dict):
        """Save a new user"""
        users_file = self.data_dir / "users.json"

        if not users_file.exists():
            self._write_json(users_file, {})

        users = self._read_json(users_file)
        users[user["id"]] = user
        self._write_json(users_file, users)

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        users_file = self.data_dir / "users.json"

        if not users_file.exists():
            return None

        users = self._read_json(users_file)
        return users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        users_file = self.data_dir / "users.json"

        if not users_file.exists():
            return None

        users = self._read_json(users_file)
        for user in users.values():
            if user.get("email") == email:
                return user
        return None

    # Organizations (Phase 3)
    def save_organization(self, org: Dict):
        """Save a new organization"""
        orgs_file = self.data_dir / "organizations.json"

        if not orgs_file.exists():
            self._write_json(orgs_file, {})

        orgs = self._read_json(orgs_file)
        orgs[org["id"]] = org
        self._write_json(orgs_file, orgs)


if __name__ == "__main__":
    # Test the database
    db = Database()

    # Create a test project
    project = {
        "id": "test-123",
        "name": "Test Project",
        "customer": "Test Customer",
        "created_at": "2026-05-20T00:00:00",
        "status": "created",
        "total_rooms": 0
    }

    db.save_project(project)
    print("Project saved:", db.get_project("test-123"))

    # Create a test room
    room = {
        "id": "room-456",
        "project_id": "test-123",
        "name": "Living Room",
        "dimensions": {"length": 20, "width": 15, "height": 9},
        "total_area": 630
    }

    db.save_room(room)
    print("Room saved:", db.get_room("room-456"))

    # Get project rooms
    print("Project rooms:", db.get_project_rooms("test-123"))

    # Cleanup
    db.delete_project("test-123")
    print("Database test complete")
