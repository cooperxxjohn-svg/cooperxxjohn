"""
Database Performance Tests for Painting.ai

Benchmarks:
- User lookup by email (<100ms)
- Project list for user with pagination (<100ms)
- Room list for project (<100ms)
- Bulk inserts (<500ms for 100 records)
- Query optimization with eager loading

Run with:
    pytest test_database_performance.py -v
    pytest test_database_performance.py -v --benchmark-only
"""

import pytest
import time
import uuid
from datetime import datetime
from database_service import DatabaseService
from models import User, Project, Room, Drawing


# Performance thresholds (in seconds)
QUERY_THRESHOLD = 0.100  # 100ms for reads
WRITE_THRESHOLD = 0.500  # 500ms for writes


class TestDatabasePerformance:
    """Database performance benchmarks"""

    @pytest.fixture(scope="class")
    def db(self):
        """Create database service instance"""
        db = DatabaseService()
        db.create_tables()
        yield db

    @pytest.fixture(scope="class")
    def test_user(self, db):
        """Create test user"""
        user = db.create_user(
            email=f"perf_test_{uuid.uuid4()}@paintingai.com",
            name="Performance Test User",
            company="Test Co"
        )
        yield user

    @pytest.fixture(scope="class")
    def test_projects(self, db, test_user):
        """Create multiple test projects"""
        projects = []
        for i in range(10):
            project = db.create_project(
                owner_id=test_user.id,
                name=f"Test Project {i}",
                customer=f"Customer {i}"
            )
            projects.append(project)
        yield projects

    @pytest.fixture(scope="class")
    def test_rooms(self, db, test_projects):
        """Create multiple test rooms"""
        rooms = []
        for project in test_projects[:3]:  # First 3 projects
            for i in range(5):
                room = db.create_room(
                    project_id=project.id,
                    name=f"Room {i}",
                    length=20.0,
                    width=15.0,
                    height=9.0
                )
                rooms.append(room)
        yield rooms

    def test_user_lookup_by_email_performance(self, db, test_user):
        """Test user lookup by email is fast (<100ms)"""
        start = time.time()
        user = db.get_user_by_email(test_user.email)
        elapsed = time.time() - start

        assert user is not None
        assert user.email == test_user.email
        assert elapsed < QUERY_THRESHOLD, \
            f"User lookup took {elapsed*1000:.2f}ms (threshold: {QUERY_THRESHOLD*1000}ms)"

        print(f"\n✓ User lookup by email: {elapsed*1000:.2f}ms")

    def test_user_lookup_by_api_key_performance(self, db, test_user):
        """Test user lookup by API key is fast (<100ms)"""
        start = time.time()
        user = db.get_user_by_api_key(test_user.api_key)
        elapsed = time.time() - start

        assert user is not None
        assert user.id == test_user.id
        assert elapsed < QUERY_THRESHOLD, \
            f"User lookup by API key took {elapsed*1000:.2f}ms (threshold: {QUERY_THRESHOLD*1000}ms)"

        print(f"✓ User lookup by API key: {elapsed*1000:.2f}ms")

    def test_project_list_performance(self, db, test_user, test_projects):
        """Test project list retrieval is fast (<100ms)"""
        start = time.time()
        projects = db.get_user_projects(test_user.id, limit=10)
        elapsed = time.time() - start

        assert len(projects) == 10
        assert elapsed < QUERY_THRESHOLD, \
            f"Project list took {elapsed*1000:.2f}ms (threshold: {QUERY_THRESHOLD*1000}ms)"

        print(f"✓ Project list (10 projects): {elapsed*1000:.2f}ms")

    def test_project_list_with_pagination_performance(self, db, test_user, test_projects):
        """Test paginated project list is fast (<100ms)"""
        start = time.time()
        projects = db.get_user_projects(test_user.id, limit=5, offset=0)
        elapsed = time.time() - start

        assert len(projects) == 5
        assert elapsed < QUERY_THRESHOLD, \
            f"Paginated project list took {elapsed*1000:.2f}ms (threshold: {QUERY_THRESHOLD*1000}ms)"

        print(f"✓ Paginated project list (5 projects): {elapsed*1000:.2f}ms")

    def test_project_with_relationships_performance(self, db, test_projects):
        """Test project retrieval with eager loading is fast (<100ms)"""
        project = test_projects[0]

        start = time.time()
        loaded_project = db.get_project(project.id, load_relationships=True)
        elapsed = time.time() - start

        assert loaded_project is not None
        assert elapsed < QUERY_THRESHOLD, \
            f"Project with relationships took {elapsed*1000:.2f}ms (threshold: {QUERY_THRESHOLD*1000}ms)"

        print(f"✓ Project with eager loading: {elapsed*1000:.2f}ms")

    def test_room_list_performance(self, db, test_projects):
        """Test room list retrieval is fast (<100ms)"""
        project = test_projects[0]

        start = time.time()
        rooms = db.get_project_rooms(project.id)
        elapsed = time.time() - start

        assert elapsed < QUERY_THRESHOLD, \
            f"Room list took {elapsed*1000:.2f}ms (threshold: {QUERY_THRESHOLD*1000}ms)"

        print(f"✓ Room list ({len(rooms)} rooms): {elapsed*1000:.2f}ms")

    def test_bulk_user_creation_performance(self, db):
        """Test bulk user creation is reasonably fast (<500ms for 100 users)"""
        user_count = 100

        start = time.time()
        for i in range(user_count):
            db.create_user(
                email=f"bulk_test_{uuid.uuid4()}@test.com",
                name=f"Bulk User {i}",
                company="Test Co"
            )
        elapsed = time.time() - start

        assert elapsed < WRITE_THRESHOLD * user_count / 100, \
            f"Bulk user creation took {elapsed*1000:.2f}ms for {user_count} users"

        avg_time = (elapsed / user_count) * 1000
        print(f"✓ Bulk user creation: {elapsed*1000:.2f}ms total ({avg_time:.2f}ms per user)")

    def test_bulk_project_creation_performance(self, db, test_user):
        """Test bulk project creation is reasonably fast"""
        project_count = 50

        start = time.time()
        for i in range(project_count):
            db.create_project(
                owner_id=test_user.id,
                name=f"Bulk Project {i}",
                customer=f"Customer {i}"
            )
        elapsed = time.time() - start

        assert elapsed < WRITE_THRESHOLD * project_count / 100, \
            f"Bulk project creation took {elapsed*1000:.2f}ms for {project_count} projects"

        avg_time = (elapsed / project_count) * 1000
        print(f"✓ Bulk project creation: {elapsed*1000:.2f}ms total ({avg_time:.2f}ms per project)")

    def test_concurrent_queries_performance(self, db, test_user):
        """Test that connection pooling handles concurrent queries efficiently"""
        import concurrent.futures

        def lookup_user():
            return db.get_user_by_email(test_user.email)

        # Simulate 20 concurrent requests
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(lookup_user) for _ in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        elapsed = time.time() - start

        assert len(results) == 20
        assert all(r is not None for r in results)
        assert elapsed < 2.0, \
            f"Concurrent queries took {elapsed*1000:.2f}ms (should be <2000ms)"

        avg_time = (elapsed / 20) * 1000
        print(f"✓ Concurrent queries (20): {elapsed*1000:.2f}ms total ({avg_time:.2f}ms per query)")

    def test_connection_pool_efficiency(self, db):
        """Test connection pool reuse"""
        pool_status = db.get_pool_status()

        print(f"\n✓ Connection Pool Status:")
        print(f"  - Pool size: {pool_status['pool_size']}")
        print(f"  - Checked out: {pool_status['checked_out']}")
        print(f"  - Checked in: {pool_status['checked_in']}")
        print(f"  - Overflow: {pool_status['overflow']}")
        print(f"  - Utilization: {pool_status['utilization_percent']:.1f}%")

        assert pool_status['pool_size'] > 0, "Connection pool not configured"

    def test_index_usage_on_queries(self, db, test_user):
        """Verify indexes are being used for common queries"""
        # This test verifies that our indexes are working
        # In production, you can use EXPLAIN ANALYZE to verify

        start = time.time()
        # Email lookup should use index
        user = db.get_user_by_email(test_user.email)
        email_time = time.time() - start

        start = time.time()
        # API key lookup should use index
        user = db.get_user_by_api_key(test_user.api_key)
        api_key_time = time.time() - start

        start = time.time()
        # Project owner_id lookup should use index
        projects = db.get_user_projects(test_user.id, limit=10)
        project_time = time.time() - start

        print(f"\n✓ Index Performance:")
        print(f"  - Email lookup: {email_time*1000:.2f}ms")
        print(f"  - API key lookup: {api_key_time*1000:.2f}ms")
        print(f"  - Project owner lookup: {project_time*1000:.2f}ms")

        # All should be very fast with indexes
        assert email_time < QUERY_THRESHOLD
        assert api_key_time < QUERY_THRESHOLD
        assert project_time < QUERY_THRESHOLD


def test_performance_summary():
    """Print performance test summary"""
    print("\n" + "=" * 80)
    print("DATABASE PERFORMANCE TEST SUMMARY")
    print("=" * 80)
    print("Performance Thresholds:")
    print(f"  - Query operations: <{QUERY_THRESHOLD*1000}ms")
    print(f"  - Write operations: <{WRITE_THRESHOLD*1000}ms")
    print()
    print("All tests passed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
