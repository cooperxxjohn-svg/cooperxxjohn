"""
Data Migration Script: JSON files → PostgreSQL
Migrates existing JSON data to PostgreSQL database
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database_service import DatabaseService
from database import Database as JSONDatabase
from models import Base
from sqlalchemy.exc import IntegrityError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataMigration:
    """Migrate data from JSON files to PostgreSQL"""

    def __init__(self, json_data_dir: str = "data"):
        self.json_data_dir = Path(json_data_dir)
        self.json_db = JSONDatabase()
        self.pg_db = DatabaseService()

        # Statistics
        self.stats = {
            "users": {"total": 0, "migrated": 0, "skipped": 0, "errors": 0},
            "projects": {"total": 0, "migrated": 0, "skipped": 0, "errors": 0},
            "rooms": {"total": 0, "migrated": 0, "skipped": 0, "errors": 0},
            "drawings": {"total": 0, "migrated": 0, "skipped": 0, "errors": 0},
        }

    def check_json_data_exists(self) -> bool:
        """Check if JSON data files exist"""
        if not self.json_data_dir.exists():
            logger.warning(f"JSON data directory not found: {self.json_data_dir}")
            return False

        json_files = list(self.json_data_dir.glob("*.json"))
        if not json_files:
            logger.warning(f"No JSON files found in {self.json_data_dir}")
            return False

        logger.info(f"Found {len(json_files)} JSON files in {self.json_data_dir}")
        return True

    def migrate_users(self) -> Dict[str, str]:
        """
        Migrate users from JSON to PostgreSQL
        Returns mapping of old user IDs to new user IDs
        """
        logger.info("Migrating users...")

        user_id_mapping = {}
        users_file = self.json_data_dir / "users.json"

        if not users_file.exists():
            logger.warning("users.json not found, skipping user migration")
            return user_id_mapping

        try:
            with open(users_file, 'r') as f:
                users_data = json.load(f)

            self.stats["users"]["total"] = len(users_data)

            for user_data in users_data:
                try:
                    # Check if user already exists (by email)
                    existing_user = self.pg_db.get_user_by_email(user_data.get("email"))

                    if existing_user:
                        logger.info(f"User already exists: {user_data['email']}")
                        user_id_mapping[user_data["id"]] = existing_user.id
                        self.stats["users"]["skipped"] += 1
                        continue

                    # Create user in PostgreSQL
                    new_user = self.pg_db.create_user(
                        email=user_data["email"],
                        name=user_data.get("name", "Unknown"),
                        company=user_data.get("company"),
                        password_hash=user_data.get("password_hash"),
                        api_key=user_data.get("api_key"),
                        plan=user_data.get("plan", "free"),
                        settings=user_data.get("settings", {})
                    )

                    user_id_mapping[user_data["id"]] = new_user.id
                    self.stats["users"]["migrated"] += 1
                    logger.info(f"Migrated user: {user_data['email']} ({user_data['id']} → {new_user.id})")

                except IntegrityError as e:
                    logger.error(f"Duplicate user: {user_data.get('email')} - {e}")
                    self.stats["users"]["errors"] += 1
                except Exception as e:
                    logger.error(f"Error migrating user {user_data.get('email')}: {e}")
                    self.stats["users"]["errors"] += 1

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing users.json: {e}")
        except Exception as e:
            logger.error(f"Error migrating users: {e}")

        logger.info(f"Users migration complete: {self.stats['users']['migrated']} migrated, "
                   f"{self.stats['users']['skipped']} skipped, "
                   f"{self.stats['users']['errors']} errors")

        return user_id_mapping

    def migrate_projects(self, user_id_mapping: Dict[str, str]) -> Dict[str, str]:
        """
        Migrate projects from JSON to PostgreSQL
        Returns mapping of old project IDs to new project IDs
        """
        logger.info("Migrating projects...")

        project_id_mapping = {}
        projects_file = self.json_data_dir / "projects.json"

        if not projects_file.exists():
            logger.warning("projects.json not found, skipping project migration")
            return project_id_mapping

        try:
            with open(projects_file, 'r') as f:
                projects_data = json.load(f)

            self.stats["projects"]["total"] = len(projects_data)

            for project_data in projects_data:
                try:
                    # Map old owner_id to new owner_id
                    old_owner_id = project_data.get("owner_id")
                    new_owner_id = user_id_mapping.get(old_owner_id)

                    if not new_owner_id:
                        logger.warning(f"Owner not found for project {project_data.get('id')}, skipping")
                        self.stats["projects"]["skipped"] += 1
                        continue

                    # Check if project already exists
                    existing_project = self.pg_db.get_project(project_data["id"])
                    if existing_project:
                        logger.info(f"Project already exists: {project_data['name']}")
                        project_id_mapping[project_data["id"]] = existing_project.id
                        self.stats["projects"]["skipped"] += 1
                        continue

                    # Create project in PostgreSQL
                    new_project = self.pg_db.create_project(
                        owner_id=new_owner_id,
                        name=project_data.get("name", "Untitled"),
                        customer=project_data.get("customer"),
                        status=project_data.get("status", "created"),
                        total_rooms=project_data.get("total_rooms", 0),
                        total_sqft=project_data.get("total_sqft", 0.0),
                        total_gallons=project_data.get("total_gallons", 0.0),
                        total_labor_hours=project_data.get("total_labor_hours", 0.0),
                        estimated_cost=project_data.get("estimated_cost", 0.0),
                        metadata=project_data.get("metadata", {})
                    )

                    # Preserve original ID if possible
                    project_id_mapping[project_data["id"]] = new_project.id
                    self.stats["projects"]["migrated"] += 1
                    logger.info(f"Migrated project: {project_data['name']} ({project_data['id']})")

                except Exception as e:
                    logger.error(f"Error migrating project {project_data.get('name')}: {e}")
                    self.stats["projects"]["errors"] += 1

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing projects.json: {e}")
        except Exception as e:
            logger.error(f"Error migrating projects: {e}")

        logger.info(f"Projects migration complete: {self.stats['projects']['migrated']} migrated, "
                   f"{self.stats['projects']['skipped']} skipped, "
                   f"{self.stats['projects']['errors']} errors")

        return project_id_mapping

    def migrate_rooms(self, project_id_mapping: Dict[str, str]):
        """Migrate rooms from JSON to PostgreSQL"""
        logger.info("Migrating rooms...")

        rooms_file = self.json_data_dir / "rooms.json"

        if not rooms_file.exists():
            logger.warning("rooms.json not found, skipping room migration")
            return

        try:
            with open(rooms_file, 'r') as f:
                rooms_data = json.load(f)

            self.stats["rooms"]["total"] = len(rooms_data)

            for room_data in rooms_data:
                try:
                    # Map old project_id to new project_id
                    old_project_id = room_data.get("project_id")
                    new_project_id = project_id_mapping.get(old_project_id)

                    if not new_project_id:
                        logger.warning(f"Project not found for room {room_data.get('id')}, skipping")
                        self.stats["rooms"]["skipped"] += 1
                        continue

                    # Check if room already exists
                    existing_room = self.pg_db.get_room(room_data["id"])
                    if existing_room:
                        logger.info(f"Room already exists: {room_data['name']}")
                        self.stats["rooms"]["skipped"] += 1
                        continue

                    # Create room in PostgreSQL
                    new_room = self.pg_db.create_room(
                        project_id=new_project_id,
                        name=room_data.get("name", "Untitled Room"),
                        number=room_data.get("number"),
                        length=room_data.get("length"),
                        width=room_data.get("width"),
                        height=room_data.get("height"),
                        dimensions=room_data.get("dimensions", {}),
                        surfaces=room_data.get("surfaces", {}),
                        total_area=room_data.get("total_area", 0.0),
                        notes=room_data.get("notes"),
                        metadata=room_data.get("metadata", {})
                    )

                    self.stats["rooms"]["migrated"] += 1
                    logger.debug(f"Migrated room: {room_data['name']}")

                except Exception as e:
                    logger.error(f"Error migrating room {room_data.get('name')}: {e}")
                    self.stats["rooms"]["errors"] += 1

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing rooms.json: {e}")
        except Exception as e:
            logger.error(f"Error migrating rooms: {e}")

        logger.info(f"Rooms migration complete: {self.stats['rooms']['migrated']} migrated, "
                   f"{self.stats['rooms']['skipped']} skipped, "
                   f"{self.stats['rooms']['errors']} errors")

    def verify_migration(self):
        """Verify data integrity after migration"""
        logger.info("Verifying migration...")

        try:
            with self.pg_db.get_session() as session:
                from models import User, Project, Room

                user_count = session.query(User).count()
                project_count = session.query(Project).count()
                room_count = session.query(Room).count()

                logger.info(f"PostgreSQL counts: {user_count} users, {project_count} projects, {room_count} rooms")

                # Verify relationships
                projects_with_owners = session.query(Project).join(User).count()
                rooms_with_projects = session.query(Room).join(Project).count()

                logger.info(f"Relationship integrity: {projects_with_owners}/{project_count} projects have owners")
                logger.info(f"Relationship integrity: {rooms_with_projects}/{room_count} rooms have projects")

                if projects_with_owners != project_count:
                    logger.warning("Some projects have missing owners!")

                if rooms_with_projects != room_count:
                    logger.warning("Some rooms have missing projects!")

        except Exception as e:
            logger.error(f"Error verifying migration: {e}")

    def generate_report(self) -> str:
        """Generate migration report"""
        report = []
        report.append("\n" + "="*60)
        report.append("DATA MIGRATION REPORT")
        report.append("="*60)
        report.append(f"\nMigration Date: {datetime.utcnow().isoformat()}")
        report.append(f"Source: JSON files ({self.json_data_dir})")
        report.append(f"Destination: PostgreSQL ({self.pg_db.engine.url})")

        report.append("\n" + "-"*60)
        report.append("STATISTICS")
        report.append("-"*60)

        for entity, stats in self.stats.items():
            report.append(f"\n{entity.upper()}:")
            report.append(f"  Total:    {stats['total']}")
            report.append(f"  Migrated: {stats['migrated']}")
            report.append(f"  Skipped:  {stats['skipped']}")
            report.append(f"  Errors:   {stats['errors']}")

            if stats['total'] > 0:
                success_rate = (stats['migrated'] / stats['total']) * 100
                report.append(f"  Success:  {success_rate:.1f}%")

        total_records = sum(s['total'] for s in self.stats.values())
        total_migrated = sum(s['migrated'] for s in self.stats.values())
        total_errors = sum(s['errors'] for s in self.stats.values())

        report.append("\n" + "-"*60)
        report.append("SUMMARY")
        report.append("-"*60)
        report.append(f"Total Records:  {total_records}")
        report.append(f"Total Migrated: {total_migrated}")
        report.append(f"Total Errors:   {total_errors}")

        if total_records > 0:
            overall_success = (total_migrated / total_records) * 100
            report.append(f"Success Rate:   {overall_success:.1f}%")

        report.append("\n" + "="*60)

        if total_errors > 0:
            report.append("⚠️  MIGRATION COMPLETED WITH ERRORS")
        else:
            report.append("✅ MIGRATION COMPLETED SUCCESSFULLY")

        report.append("="*60 + "\n")

        return "\n".join(report)

    def run(self, dry_run: bool = False) -> bool:
        """
        Run the complete migration process

        Args:
            dry_run: If True, only validate without migrating

        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting data migration...")

        if dry_run:
            logger.info("DRY RUN MODE - No data will be migrated")

        # Check if JSON data exists
        if not self.check_json_data_exists():
            logger.warning("No JSON data to migrate")
            return False

        # Create PostgreSQL tables if they don't exist
        try:
            logger.info("Creating PostgreSQL tables...")
            Base.metadata.create_all(self.pg_db.engine)
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False

        if dry_run:
            logger.info("Dry run complete - would migrate:")
            # Count records in JSON files
            for entity in ["users", "projects", "rooms"]:
                json_file = self.json_data_dir / f"{entity}.json"
                if json_file.exists():
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        logger.info(f"  {entity}: {len(data)} records")
            return True

        # Run migrations
        try:
            user_id_mapping = self.migrate_users()
            project_id_mapping = self.migrate_projects(user_id_mapping)
            self.migrate_rooms(project_id_mapping)

            # Verify migration
            self.verify_migration()

            # Generate and save report
            report = self.generate_report()
            print(report)

            # Save report to file
            report_file = Path("migration_report.md")
            with open(report_file, 'w') as f:
                f.write(report)
            logger.info(f"Report saved to {report_file}")

            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate JSON data to PostgreSQL")
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Directory containing JSON files (default: data)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without migrating"
    )

    args = parser.parse_args()

    migration = DataMigration(json_data_dir=args.data_dir)
    success = migration.run(dry_run=args.dry_run)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
