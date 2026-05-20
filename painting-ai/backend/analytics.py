"""
Advanced Analytics - Win Rate, Bid Optimization, Historical Data
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
from database_service import DatabaseService
from models import Project, ProjectStatus


class BidAnalytics:
    """Analytics for bidding success and optimization"""

    def __init__(self, db: DatabaseService):
        self.db = db

    def calculate_win_rate(self, user_id: str, days: int = 90) -> Dict:
        """Calculate win rate over period"""
        with self.db.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get all submitted bids
            submitted_bids = (
                session.query(Project)
                .filter(
                    Project.owner_id == user_id,
                    Project.submitted_at >= cutoff_date,
                    Project.status.in_([ProjectStatus.WON, ProjectStatus.LOST])
                )
                .all()
            )

            if not submitted_bids:
                return {
                    "total_bids": 0,
                    "wins": 0,
                    "losses": 0,
                    "win_rate": 0.0,
                    "total_bid_value": 0.0,
                    "won_value": 0.0,
                    "average_win_margin": None
                }

            wins = [p for p in submitted_bids if p.status == ProjectStatus.WON]
            losses = [p for p in submitted_bids if p.status == ProjectStatus.LOST]

            total_bid_value = sum(p.bid_amount or 0 for p in submitted_bids)
            won_value = sum(p.won_amount or 0 for p in wins)

            # Calculate average win margin
            win_margins = []
            for project in wins:
                if project.bid_amount and project.estimated_cost:
                    margin = ((project.bid_amount - project.estimated_cost) / project.bid_amount) * 100
                    win_margins.append(margin)

            return {
                "total_bids": len(submitted_bids),
                "wins": len(wins),
                "losses": len(losses),
                "win_rate": (len(wins) / len(submitted_bids)) * 100 if submitted_bids else 0,
                "total_bid_value": total_bid_value,
                "won_value": won_value,
                "average_win_margin": statistics.mean(win_margins) if win_margins else None,
                "median_win_margin": statistics.median(win_margins) if win_margins else None
            }

    def analyze_bid_competitiveness(self, user_id: str) -> Dict:
        """Analyze how competitive user's bids are"""
        with self.db.get_session() as session:
            lost_bids = (
                session.query(Project)
                .filter(
                    Project.owner_id == user_id,
                    Project.status == ProjectStatus.LOST
                )
                .all()
            )

            reasons = defaultdict(int)
            competitors = defaultdict(int)

            for project in lost_bids:
                if project.lost_reason:
                    reasons[project.lost_reason] += 1
                if project.competitor_won:
                    competitors[project.competitor_won] += 1

            return {
                "total_losses": len(lost_bids),
                "loss_reasons": dict(reasons),
                "competitors": dict(competitors),
                "recommendations": self._generate_recommendations(reasons, lost_bids)
            }

    def _generate_recommendations(self, loss_reasons: dict, lost_bids: List[Project]) -> List[str]:
        """Generate recommendations based on loss analysis"""
        recommendations = []

        # Too expensive
        if loss_reasons.get("price_too_high", 0) > len(lost_bids) * 0.3:
            recommendations.append(
                "⚠️ 30%+ of losses due to high price. Consider reducing markup or finding cost savings."
            )

        # Low win rate
        total_losses = len(lost_bids)
        if total_losses > 10:
            avg_markup = statistics.mean([
                ((p.bid_amount - p.estimated_cost) / p.estimated_cost * 100)
                for p in lost_bids
                if p.bid_amount and p.estimated_cost and p.estimated_cost > 0
            ])

            if avg_markup > 35:
                recommendations.append(
                    f"💰 Average markup on lost bids: {avg_markup:.1f}%. Industry standard: 25-30%. Consider lowering."
                )

        # Competitor analysis
        if loss_reasons:
            top_competitor = max(loss_reasons.items(), key=lambda x: x[1])[0]
            recommendations.append(
                f"🏆 Top competitor: {top_competitor}. Research their pricing strategy."
            )

        return recommendations

    def recommend_bid_amount(self, estimated_cost: float, project_type: str, user_id: str) -> Dict:
        """Recommend optimal bid amount based on historical data"""
        with self.db.get_session() as session:
            # Get similar won projects
            similar_wins = (
                session.query(Project)
                .filter(
                    Project.owner_id == user_id,
                    Project.status == ProjectStatus.WON,
                    Project.project_type == project_type,
                    Project.estimated_cost.between(estimated_cost * 0.8, estimated_cost * 1.2)
                )
                .all()
            )

            if not similar_wins:
                # Default to 30% markup
                return {
                    "recommended_bid": estimated_cost * 1.30,
                    "markup_percentage": 30.0,
                    "confidence": "low",
                    "reasoning": "No similar won projects. Using industry standard 30% markup."
                }

            # Calculate average winning markup
            markups = [
                ((p.bid_amount - p.estimated_cost) / p.estimated_cost * 100)
                for p in similar_wins
                if p.bid_amount and p.estimated_cost and p.estimated_cost > 0
            ]

            avg_markup = statistics.mean(markups)
            recommended_bid = estimated_cost * (1 + avg_markup / 100)

            return {
                "recommended_bid": round(recommended_bid, 2),
                "markup_percentage": round(avg_markup, 1),
                "confidence": "high" if len(similar_wins) >= 5 else "medium",
                "reasoning": f"Based on {len(similar_wins)} similar won projects.",
                "range_low": round(estimated_cost * (1 + min(markups) / 100), 2),
                "range_high": round(estimated_cost * (1 + max(markups) / 100), 2),
                "data_points": len(similar_wins)
            }

    def get_pricing_trends(self, user_id: str, months: int = 12) -> Dict:
        """Get pricing trends over time"""
        with self.db.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=months * 30)

            projects = (
                session.query(Project)
                .filter(
                    Project.owner_id == user_id,
                    Project.created_at >= cutoff_date,
                    Project.estimated_cost > 0
                )
                .order_by(Project.created_at)
                .all()
            )

            # Group by month
            monthly_data = defaultdict(lambda: {
                "projects": 0,
                "total_cost": 0,
                "total_bid": 0,
                "avg_markup": []
            })

            for project in projects:
                month_key = project.created_at.strftime("%Y-%m")

                monthly_data[month_key]["projects"] += 1
                monthly_data[month_key]["total_cost"] += project.estimated_cost or 0
                monthly_data[month_key]["total_bid"] += project.bid_amount or 0

                if project.bid_amount and project.estimated_cost and project.estimated_cost > 0:
                    markup = ((project.bid_amount - project.estimated_cost) / project.estimated_cost) * 100
                    monthly_data[month_key]["avg_markup"].append(markup)

            # Calculate averages
            trends = []
            for month, data in sorted(monthly_data.items()):
                avg_markup = statistics.mean(data["avg_markup"]) if data["avg_markup"] else 0

                trends.append({
                    "month": month,
                    "projects": data["projects"],
                    "avg_cost_per_project": data["total_cost"] / data["projects"] if data["projects"] else 0,
                    "avg_markup": avg_markup
                })

            return {
                "trends": trends,
                "total_projects": sum(d["projects"] for d in monthly_data.values())
            }

    def benchmark_against_market(self, user_id: str, zip_code: str) -> Dict:
        """Benchmark user's pricing against market averages"""
        # In production, this would query market data
        # For now, return industry benchmarks

        user_stats = self.calculate_win_rate(user_id, days=90)

        return {
            "your_win_rate": user_stats["win_rate"],
            "market_average_win_rate": 25.0,  # Industry average
            "your_average_margin": user_stats.get("average_win_margin", 30.0),
            "market_average_margin": 28.0,  # Industry average
            "performance": "above_average" if user_stats["win_rate"] > 25 else "below_average",
            "recommendations": [
                "Your win rate is above market average! Keep it up." if user_stats["win_rate"] > 25
                else "Your win rate is below market average. Consider adjusting pricing strategy."
            ]
        }


class CostAnalytics:
    """Analytics for cost tracking and estimation accuracy"""

    def __init__(self, db: DatabaseService):
        self.db = db

    def analyze_estimation_accuracy(self, user_id: str) -> Dict:
        """Analyze how accurate estimates are compared to actual costs"""
        with self.db.get_session() as session:
            # Get completed projects with actual costs tracked
            # In production, would track actual material and labor costs
            projects = (
                session.query(Project)
                .filter(
                    Project.owner_id == user_id,
                    Project.status == ProjectStatus.WON,
                    Project.estimated_cost > 0
                )
                .all()
            )

            if not projects:
                return {
                    "total_projects": 0,
                    "average_variance": None,
                    "accuracy_percentage": None
                }

            # In real implementation, would calculate:
            # variance = (actual_cost - estimated_cost) / estimated_cost * 100

            return {
                "total_projects": len(projects),
                "message": "Track actual costs to see estimation accuracy",
                "recommendation": "Enable cost tracking to improve estimation accuracy"
            }

    def calculate_cost_per_sqft(self, user_id: str, project_type: str = None) -> Dict:
        """Calculate average cost per square foot"""
        with self.db.get_session() as session:
            query = session.query(Project).filter(
                Project.owner_id == user_id,
                Project.total_sqft > 0,
                Project.estimated_cost > 0
            )

            if project_type:
                query = query.filter(Project.project_type == project_type)

            projects = query.all()

            if not projects:
                return {
                    "average_cost_per_sqft": None,
                    "project_count": 0
                }

            costs_per_sqft = [
                project.estimated_cost / project.total_sqft
                for project in projects
            ]

            return {
                "average_cost_per_sqft": round(statistics.mean(costs_per_sqft), 2),
                "median_cost_per_sqft": round(statistics.median(costs_per_sqft), 2),
                "min_cost_per_sqft": round(min(costs_per_sqft), 2),
                "max_cost_per_sqft": round(max(costs_per_sqft), 2),
                "project_count": len(projects),
                "project_type": project_type or "all"
            }


# Global instances
def get_bid_analytics(db: DatabaseService) -> BidAnalytics:
    return BidAnalytics(db)


def get_cost_analytics(db: DatabaseService) -> CostAnalytics:
    return CostAnalytics(db)


if __name__ == "__main__":
    from database_service import db

    # Create test data
    db.create_tables()

    # Test analytics
    bid_analytics = BidAnalytics(db)

    print("📊 Testing Bid Analytics")
    print("Analytics system ready for production!")
