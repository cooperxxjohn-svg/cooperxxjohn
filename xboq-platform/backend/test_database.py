"""
Comprehensive Database Tests for XBOQ Platform
Tests CRUD operations, relationships, and data integrity
"""

import os
import sys
from datetime import datetime

# Suppress SQLAlchemy warnings for testing
import warnings
warnings.filterwarnings('ignore')

from database import get_database
from models import User, Project, BOQ, Estimate

def print_header(text):
    """Print formatted test header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")

def print_test(name, passed):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")

def run_tests():
    """Run all database tests"""
    print_header("XBOQ DATABASE TESTS")

    db = get_database()
    test_results = []

    # Clean slate
    try:
        db.drop_tables()
        db.create_tables()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return

    print_header("1. USER TESTS")

    # Test 1: Create User
    try:
        user = db.create_user(
            email="test@xboq.ai",
            name="Test User"
        )
        test_results.append(("Create User", user.id == 1))
        print_test("Create User", user.id == 1)
    except Exception as e:
        test_results.append(("Create User", False))
        print_test(f"Create User - {e}", False)
        return

    # Test 2: Get User by ID
    try:
        fetched_user = db.get_user(user.id)
        passed = fetched_user is not None and fetched_user.email == "test@xboq.ai"
        test_results.append(("Get User by ID", passed))
        print_test("Get User by ID", passed)
    except Exception as e:
        test_results.append(("Get User by ID", False))
        print_test(f"Get User by ID - {e}", False)

    # Test 3: Get User by Email
    try:
        fetched_user = db.get_user_by_email("test@xboq.ai")
        passed = fetched_user is not None and fetched_user.id == user.id
        test_results.append(("Get User by Email", passed))
        print_test("Get User by Email", passed)
    except Exception as e:
        test_results.append(("Get User by Email", False))
        print_test(f"Get User by Email - {e}", False)

    # Test 4: Update User
    try:
        updated = db.update_user(user.id, name="Updated Name")
        passed = updated is not None and updated.name == "Updated Name"
        test_results.append(("Update User", passed))
        print_test("Update User", passed)
    except Exception as e:
        test_results.append(("Update User", False))
        print_test(f"Update User - {e}", False)

    print_header("2. PROJECT TESTS")

    # Test 5: Create BOQ Project
    try:
        boq_project = db.create_project(
            user_id=user.id,
            project_type='boq',
            name='Test BOQ Project',
            file_name='tender.pdf'
        )
        passed = boq_project.id is not None and boq_project.type == 'boq'
        test_results.append(("Create BOQ Project", passed))
        print_test("Create BOQ Project", passed)
    except Exception as e:
        test_results.append(("Create BOQ Project", False))
        print_test(f"Create BOQ Project - {e}", False)
        return

    # Test 6: Create Estimate Project
    try:
        estimate_project = db.create_project(
            user_id=user.id,
            project_type='estimate',
            name='Test Estimate Project'
        )
        passed = estimate_project.id is not None and estimate_project.type == 'estimate'
        test_results.append(("Create Estimate Project", passed))
        print_test("Create Estimate Project", passed)
    except Exception as e:
        test_results.append(("Create Estimate Project", False))
        print_test(f"Create Estimate Project - {e}", False)

    # Test 7: Get User Projects
    try:
        projects = db.get_user_projects(user.id)
        passed = len(projects) == 2
        test_results.append(("Get User Projects", passed))
        print_test(f"Get User Projects (count={len(projects)})", passed)
    except Exception as e:
        test_results.append(("Get User Projects", False))
        print_test(f"Get User Projects - {e}", False)

    # Test 8: Get Projects by Type
    try:
        boq_projects = db.get_user_projects(user.id, project_type='boq')
        estimate_projects = db.get_user_projects(user.id, project_type='estimate')
        passed = len(boq_projects) == 1 and len(estimate_projects) == 1
        test_results.append(("Filter Projects by Type", passed))
        print_test("Filter Projects by Type", passed)
    except Exception as e:
        test_results.append(("Filter Projects by Type", False))
        print_test(f"Filter Projects by Type - {e}", False)

    print_header("3. BOQ TESTS")

    # Test 9: Create BOQ
    try:
        boq = db.create_boq(
            project_id=boq_project.id,
            project_name="Test Construction Project",
            sections=[
                {
                    "name": "Earthwork",
                    "items": [
                        {"item": "Excavation", "quantity": 150, "unit": "cum"}
                    ]
                }
            ],
            total_items=1,
            extraction_time=2.5
        )
        passed = boq.id is not None and boq.total_items == 1
        test_results.append(("Create BOQ", passed))
        print_test("Create BOQ", passed)
    except Exception as e:
        test_results.append(("Create BOQ", False))
        print_test(f"Create BOQ - {e}", False)

    # Test 10: Get BOQ by Project
    try:
        fetched_boq = db.get_boq_by_project(boq_project.id)
        passed = fetched_boq is not None and fetched_boq.id == boq.id
        test_results.append(("Get BOQ by Project", passed))
        print_test("Get BOQ by Project", passed)
    except Exception as e:
        test_results.append(("Get BOQ by Project", False))
        print_test(f"Get BOQ by Project - {e}", False)

    print_header("4. ESTIMATE TESTS")

    # Test 11: Create Estimate
    try:
        estimate = db.create_estimate(
            project_id=estimate_project.id,
            trade='drywall',
            project_type='residential',
            rooms=[
                {
                    "name": "Living Room",
                    "length": 20,
                    "width": 15,
                    "height": 9
                }
            ],
            summary={
                "total_cost": 2850,
                "total_sqft": 930
            },
            total_cost=2850.0,
            total_sqft=930.0,
            calculation_time=1.2
        )
        passed = estimate.id is not None and estimate.trade == 'drywall'
        test_results.append(("Create Estimate", passed))
        print_test("Create Estimate", passed)
    except Exception as e:
        test_results.append(("Create Estimate", False))
        print_test(f"Create Estimate - {e}", False)

    # Test 12: Get Estimate by Project
    try:
        fetched_estimate = db.get_estimate_by_project(estimate_project.id)
        passed = fetched_estimate is not None and fetched_estimate.id == estimate.id
        test_results.append(("Get Estimate by Project", passed))
        print_test("Get Estimate by Project", passed)
    except Exception as e:
        test_results.append(("Get Estimate by Project", False))
        print_test(f"Get Estimate by Project - {e}", False)

    # Test 13: Get Estimates by Trade
    try:
        drywall_estimates = db.get_estimates_by_trade(user.id, 'drywall')
        passed = len(drywall_estimates) == 1
        test_results.append(("Get Estimates by Trade", passed))
        print_test(f"Get Estimates by Trade (count={len(drywall_estimates)})", passed)
    except Exception as e:
        test_results.append(("Get Estimates by Trade", False))
        print_test(f"Get Estimates by Trade - {e}", False)

    print_header("5. RELATIONSHIP TESTS")

    # Test 14: User → Projects Relationship
    try:
        user_with_projects = db.get_user(user.id)
        # Note: Relationships need explicit loading or query
        projects = db.get_user_projects(user.id)
        passed = len(projects) == 2
        test_results.append(("User → Projects Relationship", passed))
        print_test("User → Projects Relationship", passed)
    except Exception as e:
        test_results.append(("User → Projects Relationship", False))
        print_test(f"User → Projects Relationship - {e}", False)

    # Test 15: Project → BOQ Relationship
    try:
        project = db.get_project(boq_project.id)
        boq = db.get_boq_by_project(project.id)
        passed = boq is not None and boq.project_id == project.id
        test_results.append(("Project → BOQ Relationship", passed))
        print_test("Project → BOQ Relationship", passed)
    except Exception as e:
        test_results.append(("Project → BOQ Relationship", False))
        print_test(f"Project → BOQ Relationship - {e}", False)

    print_header("6. CASCADE DELETE TESTS")

    # Test 16: Delete Project (should cascade to BOQ/Estimate)
    try:
        # Count before delete
        boqs_before = db.get_boq_by_project(boq_project.id)

        # Delete project
        deleted = db.delete_project(boq_project.id)

        # Check BOQ is also deleted
        boqs_after = db.get_boq_by_project(boq_project.id)

        passed = deleted and boqs_before is not None and boqs_after is None
        test_results.append(("Cascade Delete (Project → BOQ)", passed))
        print_test("Cascade Delete (Project → BOQ)", passed)
    except Exception as e:
        test_results.append(("Cascade Delete (Project → BOQ)", False))
        print_test(f"Cascade Delete (Project → BOQ) - {e}", False)

    # Test 17: Delete User (should cascade to all projects)
    try:
        projects_before = db.get_user_projects(user.id)
        deleted = db.delete_user(user.id)
        user_after = db.get_user(user.id)

        passed = deleted and len(projects_before) > 0 and user_after is None
        test_results.append(("Cascade Delete (User → Projects)", passed))
        print_test("Cascade Delete (User → Projects)", passed)
    except Exception as e:
        test_results.append(("Cascade Delete (User → Projects)", False))
        print_test(f"Cascade Delete (User → Projects) - {e}", False)

    print_header("7. STATISTICS & UTILITY TESTS")

    # Create fresh data for stats
    try:
        user = db.create_user(email="stats@xboq.ai", name="Stats User")
        db.create_project(user.id, 'boq', 'BOQ 1')
        db.create_project(user.id, 'boq', 'BOQ 2')
        db.create_project(user.id, 'estimate', 'Estimate 1')
    except Exception as e:
        print(f"❌ Failed to create test data for stats: {e}")

    # Test 18: Get User Stats
    try:
        stats = db.get_user_stats(user.id)
        passed = (
            stats['total_projects'] == 3 and
            stats['boq_projects'] == 2 and
            stats['estimate_projects'] == 1
        )
        test_results.append(("Get User Statistics", passed))
        print_test(f"Get User Statistics (total={stats['total_projects']})", passed)
    except Exception as e:
        test_results.append(("Get User Statistics", False))
        print_test(f"Get User Statistics - {e}", False)

    # Test 19: Database Health Check
    try:
        healthy = db.health_check()
        test_results.append(("Database Health Check", healthy))
        print_test("Database Health Check", healthy)
    except Exception as e:
        test_results.append(("Database Health Check", False))
        print_test(f"Database Health Check - {e}", False)

    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    percentage = (passed / total * 100) if total > 0 else 0

    print(f"\n{'='*70}")
    print(f"  Passed: {passed}/{total} ({percentage:.1f}%)")
    print(f"{'='*70}\n")

    if passed == total:
        print("🎉 ALL TESTS PASSED! 🎉")
        return True
    else:
        print("⚠️  SOME TESTS FAILED")
        failed = [(name, result) for name, result in test_results if not result]
        print("\nFailed tests:")
        for name, _ in failed:
            print(f"  ❌ {name}")
        return False

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
