"""
Analytics Service
Track usage, performance, and business metrics
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
from pathlib import Path


class AnalyticsService:
    """Analytics and monitoring service"""

    def __init__(self, database):
        """
        Initialize analytics service

        Args:
            database: Database instance
        """
        self.db = database

    def get_overview_stats(self, user_id: Optional[str] = None) -> Dict:
        """
        Get overview statistics

        Args:
            user_id: Optional user ID (if None, returns system-wide stats)

        Returns:
            dict with overview metrics
        """
        # Get all data
        projects = self.db.get_all_projects()
        users = self.db.get_all_users()

        # Filter by user if specified
        if user_id:
            projects = [p for p in projects if p.get("owner_id") == user_id]
            users = [u for u in users if u["id"] == user_id]

        # Calculate metrics
        total_projects = len(projects)
        total_users = len(users)

        # Project status breakdown
        status_counts = defaultdict(int)
        for project in projects:
            status_counts[project.get("status", "unknown")] += 1

        # Calculate total value
        total_value = sum(p.get("estimated_cost", 0) for p in projects)

        # Active users (created project in last 30 days)
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
        active_users = len(set(
            p.get("owner_id") for p in projects
            if p.get("created_at", "") >= thirty_days_ago
        ))

        # Plan breakdown
        plan_counts = defaultdict(int)
        for user in users:
            plan_counts[user.get("plan", "free")] += 1

        return {
            "overview": {
                "total_projects": total_projects,
                "total_users": total_users,
                "total_value": total_value,
                "active_users": active_users
            },
            "projects_by_status": dict(status_counts),
            "users_by_plan": dict(plan_counts),
            "generated_at": datetime.utcnow().isoformat()
        }

    def get_usage_metrics(self, days: int = 30) -> Dict:
        """
        Get usage metrics over time

        Args:
            days: Number of days to analyze

        Returns:
            dict with daily usage metrics
        """
        # Get API usage data
        usage_file = self.db.data_dir / "api_usage.json"

        if not usage_file.exists():
            return {
                "days": days,
                "metrics": [],
                "total_requests": 0
            }

        with open(usage_file, 'r') as f:
            usage_data = json.load(f)

        # Filter to date range
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent_usage = [u for u in usage_data if u.get("timestamp", "") >= cutoff]

        # Group by day
        daily_usage = defaultdict(lambda: {
            "requests": 0,
            "endpoints": defaultdict(int),
            "users": set()
        })

        for entry in recent_usage:
            date = entry.get("timestamp", "")[:10]  # YYYY-MM-DD
            daily_usage[date]["requests"] += 1
            daily_usage[date]["endpoints"][entry.get("endpoint", "unknown")] += 1
            daily_usage[date]["users"].add(entry.get("user_id"))

        # Format results
        metrics = []
        for date in sorted(daily_usage.keys()):
            data = daily_usage[date]
            metrics.append({
                "date": date,
                "requests": data["requests"],
                "unique_users": len(data["users"]),
                "top_endpoints": sorted(
                    data["endpoints"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            })

        return {
            "days": days,
            "total_requests": len(recent_usage),
            "metrics": metrics
        }

    def get_conversion_metrics(self) -> Dict:
        """
        Get trial-to-paid conversion metrics

        Returns:
            dict with conversion stats
        """
        users = self.db.get_all_users()

        # Analyze subscription status
        total_users = len(users)
        trialing = len([u for u in users if u.get("subscription_status") == "trialing"])
        active = len([u for u in users if u.get("subscription_status") == "active"])
        past_due = len([u for u in users if u.get("subscription_status") == "past_due"])
        canceled = len([u for u in users if u.get("subscription_status") == "canceled"])
        inactive = len([u for u in users if u.get("subscription_status") not in ["trialing", "active"]])

        # Calculate conversion rate
        converted = active
        eligible = trialing + active + canceled  # Users who started trials
        conversion_rate = (converted / eligible * 100) if eligible > 0 else 0

        # Plan distribution
        plan_counts = defaultdict(int)
        for user in users:
            if user.get("subscription_status") in ["trialing", "active"]:
                plan_counts[user.get("plan", "free")] += 1

        return {
            "total_users": total_users,
            "subscription_status": {
                "trialing": trialing,
                "active": active,
                "past_due": past_due,
                "canceled": canceled,
                "inactive": inactive
            },
            "conversion": {
                "converted_users": converted,
                "eligible_users": eligible,
                "conversion_rate": round(conversion_rate, 2)
            },
            "active_plans": dict(plan_counts)
        }


if __name__ == "__main__":
    print("📊 Analytics Service Ready")
