"""
Email and in-app notifications system
"""

import os
from typing import List, Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from jinja2 import Template
from datetime import datetime


class EmailService:
    """Send transactional emails via SendGrid"""

    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@paintingai.com")
        self.client = SendGridAPIClient(self.api_key) if self.api_key else None

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email"""
        if not self.client:
            print(f"📧 Email (dev mode): {to_email} - {subject}")
            return False

        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )

            response = self.client.send(message)
            return response.status_code == 202

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def send_welcome_email(self, user_email: str, user_name: str, api_key: str):
        """Send welcome email to new user"""
        template = Template("""
        <h2>Welcome to Painting.ai, {{ name }}!</h2>

        <p>We're excited to have you on board. Here's what you can do:</p>

        <ul>
            <li>📤 Upload architectural drawings (PDF, PNG, JPG)</li>
            <li>🤖 AI automatically detects rooms and surfaces</li>
            <li>📊 Generate accurate takeoffs in minutes</li>
            <li>📑 Export to Excel or PDF proposals</li>
        </ul>

        <h3>Your API Key</h3>
        <p><code>{{ api_key }}</code></p>
        <p><small>Keep this secure - it grants access to your account.</small></p>

        <h3>Get Started</h3>
        <p><a href="https://paintingai.com/app" style="background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Create Your First Project</a></p>

        <p>Need help? Reply to this email or visit our <a href="https://docs.paintingai.com">documentation</a>.</p>

        <p>Best,<br>The Painting.ai Team</p>
        """)

        html = template.render(name=user_name, api_key=api_key)

        return self.send_email(
            to_email=user_email,
            subject="Welcome to Painting.ai!",
            html_content=html
        )

    def send_processing_complete_email(
        self,
        user_email: str,
        user_name: str,
        project_name: str,
        project_id: str,
        rooms_detected: int,
        total_sqft: float
    ):
        """Notify user when AI processing is complete"""
        template = Template("""
        <h2>Your drawing is ready, {{ name }}!</h2>

        <p><strong>{{ project_name }}</strong> has been processed.</p>

        <h3>Results:</h3>
        <ul>
            <li>🏠 <strong>{{ rooms }}</strong> rooms detected</li>
            <li>📏 <strong>{{ sqft | round(0) | int }}</strong> sqft total paintable area</li>
        </ul>

        <p><a href="https://paintingai.com/app/projects/{{ project_id }}" style="background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">View Project</a></p>

        <p>Ready to generate your estimate and export to Excel or PDF.</p>

        <p>Best,<br>The Painting.ai Team</p>
        """)

        html = template.render(
            name=user_name,
            project_name=project_name,
            project_id=project_id,
            rooms=rooms_detected,
            sqft=total_sqft
        )

        return self.send_email(
            to_email=user_email,
            subject=f"✓ {project_name} - Processing Complete",
            html_content=html
        )

    def send_bid_reminder_email(
        self,
        user_email: str,
        user_name: str,
        project_name: str,
        bid_due_date: datetime
    ):
        """Remind user about upcoming bid deadline"""
        days_until_due = (bid_due_date - datetime.utcnow()).days

        template = Template("""
        <h2>Bid Deadline Reminder</h2>

        <p>Hi {{ name }},</p>

        <p>Just a reminder that your bid for <strong>{{ project_name }}</strong> is due in <strong>{{ days }} days</strong>.</p>

        <p><strong>Due date:</strong> {{ due_date.strftime('%B %d, %Y') }}</p>

        <p><a href="https://paintingai.com/app/projects" style="background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">View Project</a></p>

        <p>Good luck!</p>

        <p>Best,<br>The Painting.ai Team</p>
        """)

        html = template.render(
            name=user_name,
            project_name=project_name,
            days=days_until_due,
            due_date=bid_due_date
        )

        return self.send_email(
            to_email=user_email,
            subject=f"⏰ Bid due in {days_until_due} days - {project_name}",
            html_content=html
        )

    def send_payment_receipt_email(
        self,
        user_email: str,
        user_name: str,
        amount: float,
        receipt_url: str
    ):
        """Send payment receipt"""
        template = Template("""
        <h2>Payment Receipt</h2>

        <p>Hi {{ name }},</p>

        <p>Thanks for your payment of <strong>${{ amount }}</strong>.</p>

        <p><a href="{{ receipt_url }}">View Receipt</a></p>

        <p>Your subscription is active and you can continue using Painting.ai.</p>

        <p>Questions? Reply to this email.</p>

        <p>Best,<br>The Painting.ai Team</p>
        """)

        html = template.render(
            name=user_name,
            amount=f"{amount:.2f}",
            receipt_url=receipt_url
        )

        return self.send_email(
            to_email=user_email,
            subject=f"Payment Receipt - ${amount:.2f}",
            html_content=html
        )

    def send_team_invite_email(
        self,
        invite_email: str,
        inviter_name: str,
        organization_name: str,
        invite_link: str
    ):
        """Send team invitation"""
        template = Template("""
        <h2>You've been invited to join {{ organization }}</h2>

        <p>{{ inviter }} has invited you to join their team on Painting.ai.</p>

        <p>Painting.ai helps painting contractors generate accurate takeoffs in minutes using AI.</p>

        <p><a href="{{ link }}" style="background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Accept Invitation</a></p>

        <p>This invitation will expire in 7 days.</p>

        <p>Best,<br>The Painting.ai Team</p>
        """)

        html = template.render(
            organization=organization_name,
            inviter=inviter_name,
            link=invite_link
        )

        return self.send_email(
            to_email=invite_email,
            subject=f"Invitation to join {organization_name} on Painting.ai",
            html_content=html
        )

    def send_export_ready_email(
        self,
        user_email: str,
        user_name: str,
        project_name: str,
        export_type: str,
        download_url: str
    ):
        """Notify when export is ready"""
        template = Template("""
        <h2>Your {{ export_type }} export is ready!</h2>

        <p>Hi {{ name }},</p>

        <p>Your {{ export_type }} export for <strong>{{ project_name }}</strong> is ready to download.</p>

        <p><a href="{{ url }}" style="background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Download {{ export_type }}</a></p>

        <p><small>This link will expire in 24 hours.</small></p>

        <p>Best,<br>The Painting.ai Team</p>
        """)

        html = template.render(
            name=user_name,
            project_name=project_name,
            export_type=export_type.upper(),
            url=download_url
        )

        return self.send_email(
            to_email=user_email,
            subject=f"{export_type.upper()} Export Ready - {project_name}",
            html_content=html
        )


class NotificationManager:
    """Manage in-app and email notifications"""

    def __init__(self, db, email_service: EmailService):
        self.db = db
        self.email = email_service

    def notify_processing_complete(
        self,
        user_id: str,
        project_id: str,
        send_email: bool = True
    ):
        """Notify user when drawing processing is complete"""
        user = self.db.get_user(user_id)
        project = self.db.get_project(project_id)

        if not user or not project:
            return

        # Send email
        if send_email and user.email:
            self.email.send_processing_complete_email(
                user_email=user.email,
                user_name=user.name,
                project_name=project.name,
                project_id=project.id,
                rooms_detected=project.total_rooms,
                total_sqft=project.total_sqft
            )

        # Create in-app notification
        # (Would create Notification model instance in production)
        print(f"✓ Notification sent to {user.email}: Processing complete for {project.name}")

    def check_bid_deadlines(self):
        """Check for upcoming bid deadlines and send reminders"""
        # In production, this would be a scheduled task that runs daily
        # Get projects with bid_due_date in next 3 days
        pass


# Global instance
email_service = EmailService()


if __name__ == "__main__":
    # Test email service
    print("📧 Testing Email Service")

    service = EmailService()

    # Test welcome email (dev mode)
    service.send_welcome_email(
        user_email="test@example.com",
        user_name="Test User",
        api_key="pk_test_12345"
    )

    print("✓ Email service ready!")
