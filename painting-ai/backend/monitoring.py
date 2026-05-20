"""
Monitoring and analytics for Painting.ai
"""

import time
from functools import wraps
from typing import Callable
import logging
from datetime import datetime
import json
from pathlib import Path


class Analytics:
    """Track usage analytics"""

    def __init__(self, events_file: str = "data/analytics.jsonl"):
        self.events_file = Path(events_file)
        self.events_file.parent.mkdir(exist_ok=True)

        # Create file if it doesn't exist
        if not self.events_file.exists():
            self.events_file.touch()

    def track_event(self, event_name: str, properties: dict = None, user_id: str = None):
        """Track an analytics event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_name,
            "user_id": user_id,
            "properties": properties or {}
        }

        # Append to JSONL file
        with open(self.events_file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def track_project_created(self, project_id: str, user_id: str = None):
        """Track project creation"""
        self.track_event("project_created", {"project_id": project_id}, user_id)

    def track_drawing_uploaded(self, project_id: str, file_size: int, user_id: str = None):
        """Track drawing upload"""
        self.track_event(
            "drawing_uploaded",
            {"project_id": project_id, "file_size_mb": file_size / 1024 / 1024},
            user_id
        )

    def track_processing_completed(self, project_id: str, rooms_detected: int, processing_time: float, user_id: str = None):
        """Track successful processing"""
        self.track_event(
            "processing_completed",
            {
                "project_id": project_id,
                "rooms_detected": rooms_detected,
                "processing_time_seconds": processing_time
            },
            user_id
        )

    def track_export(self, project_id: str, export_type: str, user_id: str = None):
        """Track export (Excel/PDF)"""
        self.track_event(
            "export_generated",
            {"project_id": project_id, "export_type": export_type},
            user_id
        )

    def get_stats(self, days: int = 30) -> dict:
        """Get analytics stats for last N days"""
        from collections import defaultdict
        from datetime import timedelta

        stats = {
            "total_projects": 0,
            "total_uploads": 0,
            "total_exports": 0,
            "avg_processing_time": 0,
            "avg_rooms_per_project": 0,
            "unique_users": set()
        }

        cutoff = datetime.utcnow() - timedelta(days=days)
        processing_times = []
        rooms_counts = []

        with open(self.events_file, "r") as f:
            for line in f:
                try:
                    event = json.loads(line)
                    event_time = datetime.fromisoformat(event["timestamp"])

                    if event_time < cutoff:
                        continue

                    if event["user_id"]:
                        stats["unique_users"].add(event["user_id"])

                    if event["event"] == "project_created":
                        stats["total_projects"] += 1
                    elif event["event"] == "drawing_uploaded":
                        stats["total_uploads"] += 1
                    elif event["event"] == "processing_completed":
                        processing_times.append(event["properties"]["processing_time_seconds"])
                        rooms_counts.append(event["properties"]["rooms_detected"])
                    elif event["event"] == "export_generated":
                        stats["total_exports"] += 1

                except (json.JSONDecodeError, KeyError):
                    continue

        if processing_times:
            stats["avg_processing_time"] = sum(processing_times) / len(processing_times)

        if rooms_counts:
            stats["avg_rooms_per_project"] = sum(rooms_counts) / len(rooms_counts)

        stats["unique_users"] = len(stats["unique_users"])

        return stats


class PerformanceMonitor:
    """Monitor API performance"""

    def __init__(self):
        self.logger = logging.getLogger("performance")

    def track_endpoint(self, endpoint: str):
        """Decorator to track endpoint performance"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()

                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time

                    self.logger.info(
                        f"Endpoint: {endpoint} | Duration: {duration:.2f}s | Status: success"
                    )

                    return result

                except Exception as e:
                    duration = time.time() - start_time

                    self.logger.error(
                        f"Endpoint: {endpoint} | Duration: {duration:.2f}s | Status: error | Error: {str(e)}"
                    )

                    raise

            return wrapper
        return decorator


class ErrorTracker:
    """Track and log errors"""

    def __init__(self, errors_file: str = "data/errors.jsonl"):
        self.errors_file = Path(errors_file)
        self.errors_file.parent.mkdir(exist_ok=True)

        if not self.errors_file.exists():
            self.errors_file.touch()

    def log_error(self, error: Exception, context: dict = None):
        """Log an error with context"""
        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }

        with open(self.errors_file, "a") as f:
            f.write(json.dumps(error_data) + "\n")

        logging.error(f"Error: {error_data}")

    def get_recent_errors(self, limit: int = 100) -> list:
        """Get recent errors"""
        errors = []

        try:
            with open(self.errors_file, "r") as f:
                for line in f:
                    try:
                        errors.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            # Return most recent first
            return errors[-limit:][::-1]

        except FileNotFoundError:
            return []


# Global instances
analytics = Analytics()
performance_monitor = PerformanceMonitor()
error_tracker = ErrorTracker()


if __name__ == "__main__":
    # Test analytics
    analytics.track_project_created("test-123", user_id="user-1")
    analytics.track_drawing_uploaded("test-123", file_size=1024*1024*5, user_id="user-1")
    analytics.track_processing_completed("test-123", rooms_detected=10, processing_time=25.5, user_id="user-1")
    analytics.track_export("test-123", export_type="excel", user_id="user-1")

    # Get stats
    stats = analytics.get_stats(days=30)
    print("Analytics stats:")
    print(json.dumps(stats, indent=2))

    # Test error tracking
    error_tracker.log_error(
        ValueError("Test error"),
        context={"project_id": "test-123", "action": "processing"}
    )

    errors = error_tracker.get_recent_errors(limit=10)
    print(f"\nRecent errors: {len(errors)}")
