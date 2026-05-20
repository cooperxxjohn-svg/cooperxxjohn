"""
Stripe payment integration for Painting.ai
"""

import stripe
import os
from typing import Optional
from datetime import datetime


class PaymentManager:
    """Handle Stripe payments and subscriptions"""

    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

        # Price IDs (set these in Stripe dashboard)
        self.prices = {
            "starter": os.getenv("STRIPE_PRICE_STARTER", "price_starter"),
            "pro": os.getenv("STRIPE_PRICE_PRO", "price_pro"),
            "enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE", "price_enterprise")
        }

    def create_checkout_session(
        self,
        customer_email: str,
        plan: str = "starter",
        success_url: str = "http://localhost:3000/success",
        cancel_url: str = "http://localhost:3000/pricing"
    ) -> dict:
        """Create a Stripe checkout session"""

        try:
            session = stripe.checkout.Session.create(
                customer_email=customer_email,
                payment_method_types=['card'],
                line_items=[{
                    'price': self.prices[plan],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                metadata={
                    'plan': plan
                }
            )

            return {
                "session_id": session.id,
                "url": session.url
            }

        except Exception as e:
            print(f"Error creating checkout session: {e}")
            return None

    def create_customer_portal_session(
        self,
        customer_id: str,
        return_url: str = "http://localhost:3000/settings"
    ) -> dict:
        """Create customer portal session for managing subscription"""

        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )

            return {
                "url": session.url
            }

        except Exception as e:
            print(f"Error creating portal session: {e}")
            return None

    def verify_webhook(self, payload: bytes, sig_header: str) -> Optional[dict]:
        """Verify and parse Stripe webhook"""

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event

        except ValueError as e:
            print(f"Invalid payload: {e}")
            return None
        except stripe.error.SignatureVerificationError as e:
            print(f"Invalid signature: {e}")
            return None

    def handle_subscription_created(self, subscription):
        """Handle new subscription"""
        customer_email = subscription.customer_email
        plan = subscription.metadata.get("plan", "starter")

        print(f"New subscription: {customer_email} - {plan}")

        # Update user in database
        # This would be called from webhook handler

        return {
            "customer_email": customer_email,
            "plan": plan,
            "status": subscription.status
        }

    def handle_subscription_updated(self, subscription):
        """Handle subscription update"""
        print(f"Subscription updated: {subscription.id}")

        return {
            "status": subscription.status
        }

    def handle_subscription_deleted(self, subscription):
        """Handle subscription cancellation"""
        print(f"Subscription cancelled: {subscription.id}")

        # Downgrade user to free plan

        return {
            "status": "cancelled"
        }


payment_manager = PaymentManager()


if __name__ == "__main__":
    # Test payment system
    pm = PaymentManager()

    # Create checkout session
    session = pm.create_checkout_session(
        customer_email="test@example.com",
        plan="starter"
    )

    print(f"Checkout session created: {session}")
