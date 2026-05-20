"""
Email Service using SendGrid
Sends transactional emails for notifications
"""

import os
from typing import Dict, List, Optional
from datetime import datetime

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    print("⚠️ SendGrid not installed. Run: pip install sendgrid")
    SENDGRID_AVAILABLE = False

# Configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@painting.ai")
FROM_NAME = os.getenv("FROM_NAME", "Painting.ai")


class EmailService:
    """Handle email sending with SendGrid"""

    def __init__(self):
        """Initialize email service"""
        self.api_key = SENDGRID_API_KEY
        self.from_email = FROM_EMAIL
        self.from_name = FROM_NAME

        if SENDGRID_AVAILABLE and self.api_key:
            self.client = SendGridAPIClient(self.api_key)
        else:
            self.client = None
            if not SENDGRID_AVAILABLE:
                print("⚠️ SendGrid not available - emails will be logged only")
            elif not self.api_key:
                print("⚠️ SENDGRID_API_KEY not set - emails will be logged only")

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send email via SendGrid

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body (optional)

        Returns:
            bool: True if sent successfully
        """
        if not self.client:
            print(f"📧 [MOCK] Email to {to_email}: {subject}")
            return True

        try:
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            if text_content:
                message.plain_text_content = Content("text/plain", text_content)

            response = self.client.send(message)

            if response.status_code in [200, 201, 202]:
                print(f"✅ Email sent to {to_email}: {subject}")
                return True
            else:
                print(f"❌ Email failed ({response.status_code}): {subject}")
                return False

        except Exception as e:
            print(f"❌ Email error: {e}")
            return False

    def send_welcome_email(self, user: Dict) -> bool:
        """
        Send welcome email after registration

        Args:
            user: User dict with email, name

        Returns:
            bool: Success status
        """
        subject = "Welcome to Painting.ai! 🎨"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center;">
                <h1 style="color: white; margin: 0;">Welcome to Painting.ai!</h1>
            </div>

            <div style="padding: 40px; background: #f9fafb;">
                <p>Hi {user.get('name', 'there')}!</p>

                <p>Thanks for signing up! Your account is ready to go.</p>

                <h3>What's Next?</h3>
                <ol>
                    <li><strong>Upload a floor plan</strong> - Drop a PDF or image</li>
                    <li><strong>Review detected rooms</strong> - AI finds rooms automatically</li>
                    <li><strong>Generate estimate</strong> - Get detailed line items</li>
                    <li><strong>Download exports</strong> - Professional Excel & PDF</li>
                </ol>

                <div style="background: #e0e7ff; padding: 20px; border-radius: 8px; margin: 30px 0;">
                    <h3 style="margin-top: 0;">🎁 Your 14-Day Free Trial</h3>
                    <p>You have full access to all features for 14 days.</p>
                    <p><strong>Trial ends:</strong> {user.get('settings', {}).get('trial_ends', 'N/A')}</p>
                </div>

                <a href="https://painting.ai/dashboard"
                   style="display: inline-block; background: #667eea; color: white; padding: 15px 30px;
                          text-decoration: none; border-radius: 5px; margin: 20px 0;">
                    Get Started →
                </a>

                <hr style="margin: 40px 0; border: none; border-top: 1px solid #e5e7eb;">

                <p style="color: #6b7280; font-size: 14px;">
                    Need help? Reply to this email or visit our
                    <a href="https://docs.painting.ai">documentation</a>.
                </p>

                <p style="color: #6b7280; font-size: 14px;">
                    <strong>Your API Key:</strong> {user.get('api_key', 'N/A')}<br>
                    (Keep this secret!)
                </p>
            </div>

            <div style="padding: 20px; text-align: center; color: #9ca3af; font-size: 12px;">
                <p>Painting.ai - AI-powered takeoffs for painting contractors</p>
                <p>&copy; 2026 Painting.ai. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to Painting.ai!

        Hi {user.get('name', 'there')}!

        Thanks for signing up! Your account is ready to go.

        What's Next?
        1. Upload a floor plan - Drop a PDF or image
        2. Review detected rooms - AI finds rooms automatically
        3. Generate estimate - Get detailed line items
        4. Download exports - Professional Excel & PDF

        Your 14-Day Free Trial
        You have full access to all features for 14 days.
        Trial ends: {user.get('settings', {}).get('trial_ends', 'N/A')}

        Get Started: https://painting.ai/dashboard

        Your API Key: {user.get('api_key', 'N/A')}
        (Keep this secret!)

        Need help? Reply to this email or visit https://docs.painting.ai
        """

        return self.send_email(user["email"], subject, html_content, text_content)

    def send_project_complete_email(self, user: Dict, project: Dict) -> bool:
        """
        Send email when project processing is complete

        Args:
            user: User dict
            project: Project dict

        Returns:
            bool: Success status
        """
        subject = f"✅ Your project '{project['name']}' is ready!"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #10b981; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">Project Complete! ✅</h1>
            </div>

            <div style="padding: 40px; background: #f9fafb;">
                <p>Hi {user.get('name')}!</p>

                <p>Great news! Your project <strong>{project['name']}</strong> has been processed.</p>

                <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb;">
                    <h3 style="margin-top: 0;">Project Summary</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li>🏠 <strong>Rooms detected:</strong> {project.get('total_rooms', 0)}</li>
                        <li>📏 <strong>Total area:</strong> {project.get('total_sqft', 0):,.0f} sqft</li>
                        <li>💰 <strong>Estimated cost:</strong> ${project.get('estimated_cost', 0):,.2f}</li>
                    </ul>
                </div>

                <a href="https://painting.ai/projects/{project['id']}"
                   style="display: inline-block; background: #10b981; color: white; padding: 15px 30px;
                          text-decoration: none; border-radius: 5px; margin: 20px 0;">
                    View Project →
                </a>

                <p><strong>Next steps:</strong></p>
                <ol>
                    <li>Review detected rooms</li>
                    <li>Make any corrections needed</li>
                    <li>Generate detailed assembly breakdown</li>
                    <li>Download Excel/PDF exports</li>
                </ol>
            </div>

            <div style="padding: 20px; text-align: center; color: #9ca3af; font-size: 12px;">
                <p>&copy; 2026 Painting.ai</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(user["email"], subject, html_content)

    def send_export_ready_email(self, user: Dict, project: Dict, export_format: str) -> bool:
        """
        Send email when export is ready

        Args:
            user: User dict
            project: Project dict
            export_format: "excel" or "pdf"

        Returns:
            bool: Success status
        """
        subject = f"📄 Your {export_format.upper()} export is ready!"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #3b82f6; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">Export Ready! 📄</h1>
            </div>

            <div style="padding: 40px; background: #f9fafb;">
                <p>Hi {user.get('name')}!</p>

                <p>Your {export_format.upper()} export for <strong>{project['name']}</strong> is ready to download.</p>

                <a href="https://painting.ai/projects/{project['id']}/export/{export_format}"
                   style="display: inline-block; background: #3b82f6; color: white; padding: 15px 30px;
                          text-decoration: none; border-radius: 5px; margin: 20px 0;">
                    Download {export_format.upper()} →
                </a>

                <p style="color: #6b7280; font-size: 14px;">
                    Link expires in 24 hours.
                </p>
            </div>

            <div style="padding: 20px; text-align: center; color: #9ca3af; font-size: 12px;">
                <p>&copy; 2026 Painting.ai</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(user["email"], subject, html_content)

    def send_payment_succeeded_email(self, user: Dict, amount: float, plan: str) -> bool:
        """
        Send email for successful payment

        Args:
            user: User dict
            amount: Payment amount
            plan: Plan name

        Returns:
            bool: Success status
        """
        subject = f"✅ Payment received - ${amount:.2f}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #10b981; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">Payment Received ✅</h1>
            </div>

            <div style="padding: 40px; background: #f9fafb;">
                <p>Hi {user.get('name')}!</p>

                <p>Thank you! Your payment has been processed successfully.</p>

                <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb;">
                    <h3 style="margin-top: 0;">Payment Details</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li><strong>Amount:</strong> ${amount:.2f}</li>
                        <li><strong>Plan:</strong> {plan.title()}</li>
                        <li><strong>Date:</strong> {datetime.utcnow().strftime('%B %d, %Y')}</li>
                    </ul>
                </div>

                <a href="https://painting.ai/settings/billing"
                   style="display: inline-block; background: #10b981; color: white; padding: 15px 30px;
                          text-decoration: none; border-radius: 5px; margin: 20px 0;">
                    View Receipt →
                </a>

                <p style="color: #6b7280; font-size: 14px;">
                    Your subscription is active and will renew automatically next month.
                </p>
            </div>

            <div style="padding: 20px; text-align: center; color: #9ca3af; font-size: 12px;">
                <p>&copy; 2026 Painting.ai</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(user["email"], subject, html_content)

    def send_payment_failed_email(self, user: Dict, plan: str) -> bool:
        """
        Send email for failed payment

        Args:
            user: User dict
            plan: Plan name

        Returns:
            bool: Success status
        """
        subject = "⚠️ Payment failed - Action required"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #ef4444; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">Payment Failed ⚠️</h1>
            </div>

            <div style="padding: 40px; background: #f9fafb;">
                <p>Hi {user.get('name')}!</p>

                <p>We were unable to process your payment for your {plan.title()} plan.</p>

                <div style="background: #fef2f2; padding: 20px; border-radius: 8px; border: 1px solid #fecaca;">
                    <h3 style="margin-top: 0; color: #dc2626;">Action Required</h3>
                    <p>Please update your payment method to avoid service interruption.</p>
                </div>

                <a href="https://painting.ai/settings/billing"
                   style="display: inline-block; background: #ef4444; color: white; padding: 15px 30px;
                          text-decoration: none; border-radius: 5px; margin: 20px 0;">
                    Update Payment Method →
                </a>

                <p style="color: #6b7280; font-size: 14px;">
                    If your payment method isn't updated within 7 days, your account will be downgraded to the free plan.
                </p>

                <p>Need help? <a href="mailto:support@painting.ai">Contact support</a></p>
            </div>

            <div style="padding: 20px; text-align: center; color: #9ca3af; font-size: 12px;">
                <p>&copy; 2026 Painting.ai</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(user["email"], subject, html_content)


# Helper function
def get_email_service() -> EmailService:
    """Create EmailService instance"""
    return EmailService()


if __name__ == "__main__":
    print("📧 Email Service Test")

    service = EmailService()

    # Test user
    test_user = {
        "email": "test@example.com",
        "name": "Test User",
        "api_key": "pk_test123",
        "settings": {
            "trial_ends": "2026-06-03"
        }
    }

    # Test welcome email
    print("\n1. Testing welcome email...")
    service.send_welcome_email(test_user)

    # Test project complete
    print("\n2. Testing project complete email...")
    test_project = {
        "id": "proj_123",
        "name": "Office Renovation",
        "total_rooms": 8,
        "total_sqft": 2500,
        "estimated_cost": 5000
    }
    service.send_project_complete_email(test_user, test_project)

    print("\n✅ Email service test complete!")
