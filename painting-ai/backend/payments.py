"""
Stripe Payment Integration
Handles subscriptions, checkout, and webhook events
"""

import os
try:
    import stripe
except ImportError:
    print("⚠️ Stripe not installed. Run: pip install stripe")
    stripe = None

from typing import Dict, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException

# Initialize Stripe
if stripe:
    stripe.api_key = os.getenv("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Pricing Plans
PLANS = {
    "starter": {
        "name": "Starter",
        "price": 99.00,
        "price_id": os.getenv("STRIPE_STARTER_PRICE_ID", "price_starter"),
        "interval": "month",
        "features": [
            "50 projects per month",
            "AI room detection",
            "Excel & PDF exports",
            "Email support"
        ],
        "limits": {
            "projects_per_month": 50,
            "api_access": False,
            "team_members": 1
        }
    },
    "pro": {
        "name": "Pro",
        "price": 299.00,
        "price_id": os.getenv("STRIPE_PRO_PRICE_ID", "price_pro"),
        "interval": "month",
        "features": [
            "Unlimited projects",
            "AI room detection",
            "Assembly expansion (80-120 line items)",
            "Excel & PDF exports",
            "Public API access",
            "Priority support",
            "Custom materials database"
        ],
        "limits": {
            "projects_per_month": -1,  # Unlimited
            "api_access": True,
            "team_members": 5
        }
    },
    "enterprise": {
        "name": "Enterprise",
        "price": None,  # Custom pricing
        "price_id": None,
        "interval": "month",
        "features": [
            "Everything in Pro",
            "Unlimited team members",
            "White-label exports",
            "Custom integrations",
            "Dedicated account manager",
            "SLA guarantee",
            "Custom training"
        ],
        "limits": {
            "projects_per_month": -1,
            "api_access": True,
            "team_members": -1  # Unlimited
        }
    }
}


class PaymentService:
    """Handle Stripe payment operations"""

    def __init__(self, database):
        """
        Initialize payment service

        Args:
            database: Database or DatabaseService instance
        """
        self.db = database
        if not stripe:
            print("⚠️ Stripe not available - payments disabled")

    def create_checkout_session(
        self,
        user_id: str,
        plan: str,
        success_url: str,
        cancel_url: str
    ) -> Dict:
        """
        Create Stripe checkout session

        Args:
            user_id: User ID
            plan: Plan name (starter, pro)
            success_url: Redirect URL on success
            cancel_url: Redirect URL on cancel

        Returns:
            dict with checkout_url and session_id

        Raises:
            HTTPException: If plan invalid or Stripe error
        """
        if not stripe:
            raise HTTPException(status_code=503, detail="Payments not configured")

        if plan not in ["starter", "pro"]:
            raise HTTPException(status_code=400, detail=f"Invalid plan: {plan}")

        if plan == "enterprise":
            raise HTTPException(
                status_code=400,
                detail="Enterprise plans require custom setup. Contact sales."
            )

        user = self.db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        plan_info = PLANS[plan]
        price_id = plan_info["price_id"]

        try:
            # Create or get Stripe customer
            customer_id = user.get("stripe_customer_id")

            if not customer_id:
                customer = stripe.Customer.create(
                    email=user["email"],
                    name=user["name"],
                    metadata={
                        "user_id": user_id,
                        "plan": plan
                    }
                )
                customer_id = customer.id

                # Save customer ID
                self.db.update_user(user_id, {"stripe_customer_id": customer_id})

            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id,
                    "plan": plan
                },
                subscription_data={
                    "trial_period_days": 14,  # 14-day trial
                    "metadata": {
                        "user_id": user_id,
                        "plan": plan
                    }
                }
            )

            return {
                "checkout_url": session.url,
                "session_id": session.id,
                "plan": plan,
                "price": plan_info["price"]
            }

        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))

    def create_portal_session(self, user_id: str, return_url: str) -> Dict:
        """
        Create Stripe customer portal session

        Allows customers to manage subscription, update payment method,
        view invoices, cancel subscription.

        Args:
            user_id: User ID
            return_url: URL to return to after portal

        Returns:
            dict with portal_url
        """
        if not stripe:
            raise HTTPException(status_code=503, detail="Payments not configured")

        user = self.db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        customer_id = user.get("stripe_customer_id")
        if not customer_id:
            raise HTTPException(
                status_code=400,
                detail="No active subscription found"
            )

        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )

            return {"portal_url": session.url}

        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))

    def handle_checkout_completed(self, session: Dict):
        """
        Handle successful checkout completion

        Args:
            session: Stripe checkout session object
        """
        user_id = session["metadata"]["user_id"]
        plan = session["metadata"]["plan"]
        customer_id = session["customer"]
        subscription_id = session["subscription"]

        # Update user
        updates = {
            "stripe_customer_id": customer_id,
            "stripe_subscription_id": subscription_id,
            "plan": plan,
            "subscription_status": "trialing",  # Start in trial
            "trial_ends": (datetime.utcnow() + timedelta(days=14)).isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        self.db.update_user(user_id, updates)

        print(f"✅ Checkout completed: User {user_id} subscribed to {plan}")

    def handle_subscription_updated(self, subscription: Dict):
        """
        Handle subscription status changes

        Args:
            subscription: Stripe subscription object
        """
        customer_id = subscription["customer"]
        status = subscription["status"]  # trialing, active, past_due, canceled

        # Find user by customer ID
        users = self.db.get_all_users() if hasattr(self.db, 'get_all_users') else []

        user = None
        for u in users:
            if u.get("stripe_customer_id") == customer_id:
                user = u
                break

        if not user:
            print(f"⚠️ User not found for customer {customer_id}")
            return

        # Update subscription status
        updates = {
            "subscription_status": status,
            "updated_at": datetime.utcnow().isoformat()
        }

        # If trial ended, mark as active
        if status == "active" and subscription.get("trial_end"):
            updates["trial_ends"] = None

        # If canceled, downgrade to free
        if status == "canceled":
            updates["plan"] = "free"

        self.db.update_user(user["id"], updates)

        print(f"✅ Subscription updated: User {user['id']} status={status}")

    def handle_payment_succeeded(self, invoice: Dict):
        """
        Handle successful payment

        Args:
            invoice: Stripe invoice object
        """
        customer_id = invoice["customer"]
        amount_paid = invoice["amount_paid"] / 100  # Convert cents to dollars

        print(f"✅ Payment succeeded: Customer {customer_id} paid ${amount_paid}")

    def handle_payment_failed(self, invoice: Dict):
        """
        Handle failed payment

        Args:
            invoice: Stripe invoice object
        """
        customer_id = invoice["customer"]

        print(f"❌ Payment failed: Customer {customer_id}")

    def get_usage_stats(self, user_id: str, month: Optional[str] = None) -> Dict:
        """
        Get usage statistics for plan enforcement

        Args:
            user_id: User ID
            month: Month to check (YYYY-MM), defaults to current month

        Returns:
            dict with usage stats
        """
        if month is None:
            month = datetime.utcnow().strftime("%Y-%m")

        # Get all projects for user
        projects = self.db.get_all_projects()
        user_projects = [p for p in projects if p.get("owner_id") == user_id]

        # Filter to current month
        month_projects = [
            p for p in user_projects
            if p.get("created_at", "").startswith(month)
        ]

        user = self.db.get_user_by_id(user_id)
        plan = user.get("plan", "free")
        plan_limits = PLANS.get(plan, {}).get("limits", {})

        projects_limit = plan_limits.get("projects_per_month", 0)
        projects_used = len(month_projects)
        projects_remaining = max(0, projects_limit - projects_used) if projects_limit > 0 else -1

        return {
            "user_id": user_id,
            "plan": plan,
            "month": month,
            "projects_used": projects_used,
            "projects_limit": projects_limit,
            "projects_remaining": projects_remaining,
            "api_access": plan_limits.get("api_access", False),
            "team_members_limit": plan_limits.get("team_members", 1)
        }

    def check_plan_limit(self, user_id: str, action: str = "create_project") -> bool:
        """
        Check if user can perform action based on plan limits

        Args:
            user_id: User ID
            action: Action to check (create_project, api_access)

        Returns:
            bool: True if allowed

        Raises:
            HTTPException: If limit exceeded
        """
        user = self.db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        plan = user.get("plan", "free")

        # Check subscription status
        status = user.get("subscription_status", "inactive")
        if status not in ["active", "trialing"]:
            raise HTTPException(
                status_code=403,
                detail="Subscription inactive. Please upgrade your plan."
            )

        if action == "create_project":
            stats = self.get_usage_stats(user_id)
            limit = stats["projects_limit"]

            # Unlimited
            if limit == -1:
                return True

            # Check limit
            if stats["projects_used"] >= limit:
                raise HTTPException(
                    status_code=403,
                    detail=f"Monthly project limit reached ({limit} projects). Upgrade to Pro for unlimited projects."
                )

            return True

        elif action == "api_access":
            plan_info = PLANS.get(plan, {})
            if not plan_info.get("limits", {}).get("api_access", False):
                raise HTTPException(
                    status_code=403,
                    detail="API access requires Pro or Enterprise plan."
                )

            return True

        return True


# Helper function to create payment service
def get_payment_service(db) -> PaymentService:
    """Create PaymentService instance"""
    return PaymentService(db)


if __name__ == "__main__":
    print("💳 Stripe Payment Integration")
    print(f"📊 Available Plans:")
    for plan_name, plan_info in PLANS.items():
        print(f"\n{plan_info['name']}:")
        if plan_info["price"]:
            print(f"  Price: ${plan_info['price']}/month")
        else:
            print(f"  Price: Custom")
        print(f"  Features:")
        for feature in plan_info["features"]:
            print(f"    - {feature}")
