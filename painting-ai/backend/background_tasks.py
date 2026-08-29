"""
Background Tasks
Async task processing without Celery (lightweight implementation)
"""

import asyncio
from typing import Dict, Callable
from datetime import datetime
from email_service import get_email_service

# Initialize email service
email_service = get_email_service()


async def send_email_async(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str = None
):
    """
    Send email in background

    Args:
        to_email: Recipient email
        subject: Email subject
        html_content: HTML body
        text_content: Plain text body
    """
    try:
        email_service.send_email(to_email, subject, html_content, text_content)
        print(f"✅ Background email sent: {subject}")
    except Exception as e:
        print(f"❌ Background email failed: {e}")


async def send_welcome_email_async(user: Dict):
    """Send welcome email in background"""
    try:
        email_service.send_welcome_email(user)
        print(f"✅ Welcome email sent to {user['email']}")
    except Exception as e:
        print(f"❌ Welcome email failed: {e}")


async def send_project_complete_email_async(user: Dict, project: Dict):
    """Send project complete email in background"""
    try:
        email_service.send_project_complete_email(user, project)
        print(f"✅ Project complete email sent to {user['email']}")
    except Exception as e:
        print(f"❌ Project complete email failed: {e}")


async def send_export_ready_email_async(user: Dict, project: Dict, export_format: str):
    """Send export ready email in background"""
    try:
        email_service.send_export_ready_email(user, project, export_format)
        print(f"✅ Export ready email sent to {user['email']}")
    except Exception as e:
        print(f"❌ Export ready email failed: {e}")


async def send_payment_succeeded_email_async(user: Dict, amount: float, plan: str):
    """Send payment succeeded email in background"""
    try:
        email_service.send_payment_succeeded_email(user, amount, plan)
        print(f"✅ Payment success email sent to {user['email']}")
    except Exception as e:
        print(f"❌ Payment success email failed: {e}")


async def send_payment_failed_email_async(user: Dict, plan: str):
    """Send payment failed email in background"""
    try:
        email_service.send_payment_failed_email(user, plan)
        print(f"✅ Payment failed email sent to {user['email']}")
    except Exception as e:
        print(f"❌ Payment failed email failed: {e}")


async def process_drawing_async(
    project_id: str,
    file_path: str,
    detector,
    calculator,
    db
):
    """
    Process drawing with AI detection in background

    Args:
        project_id: Project ID
        file_path: Path to uploaded file
        detector: PaintingDetector instance
        calculator: PaintCalculator instance
        db: Database instance
    """
    try:
        print(f"🔄 Starting background processing: {project_id}")

        # Update status
        db.update_project(project_id, {
            "status": "processing",
            "updated_at": datetime.utcnow().isoformat()
        })

        # Detect rooms
        rooms = await asyncio.to_thread(
            detector.analyze_floor_plan,
            file_path
        )

        if not rooms:
            db.update_project(project_id, {
                "status": "failed",
                "error": "No rooms detected",
                "updated_at": datetime.utcnow().isoformat()
            })
            return

        # Calculate estimates
        total_sqft = 0
        total_gallons = 0
        total_hours = 0
        total_cost = 0

        for room in rooms:
            # Calculate paint
            paint_info = calculator.calculate_paint(
                room.total_area,
                coats=2
            )

            # Calculate labor
            labor_info = calculator.calculate_labor(
                room.total_area,
                surface_type="smooth_drywall"
            )

            # Calculate cost
            cost_info = calculator.calculate_cost(
                room.total_area,
                paint_price=55.0,
                labor_rate=50.0
            )

            # Update room with calculations
            room_data = {
                "id": room.id,
                "project_id": project_id,
                "name": room.name,
                "dimensions": {
                    "length": room.length,
                    "width": room.width,
                    "height": room.height
                },
                "total_area": room.total_area,
                "surfaces": {
                    surf.name: {
                        "area": surf.area,
                        "surface_type": surf.surface_type
                    }
                    for surf in room.surfaces
                },
                "paint_gallons": paint_info["gallons_needed"],
                "labor_hours": labor_info["total_hours"],
                "estimated_cost": cost_info["total_cost"]
            }

            db.save_room(room_data)

            total_sqft += room.total_area
            total_gallons += paint_info["gallons_needed"]
            total_hours += labor_info["total_hours"]
            total_cost += cost_info["total_cost"]

        # Update project
        db.update_project(project_id, {
            "status": "complete",
            "total_rooms": len(rooms),
            "total_sqft": total_sqft,
            "total_gallons": total_gallons,
            "total_labor_hours": total_hours,
            "estimated_cost": total_cost,
            "processed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })

        print(f"✅ Background processing complete: {project_id}")

        # Send email notification
        project = db.get_project(project_id)
        user = db.get_user_by_id(project.get("owner_id"))
        if user:
            await send_project_complete_email_async(user, project)

    except Exception as e:
        print(f"❌ Background processing failed: {e}")
        db.update_project(project_id, {
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat()
        })


async def generate_export_async(
    project_id: str,
    export_format: str,
    exporter,
    db
):
    """
    Generate export in background

    Args:
        project_id: Project ID
        export_format: "excel" or "pdf"
        exporter: ExportGenerator instance
        db: Database instance
    """
    try:
        print(f"🔄 Generating {export_format} export: {project_id}")

        project = db.get_project(project_id)
        rooms = db.get_project_rooms(project_id)

        if export_format == "excel":
            file_path = await asyncio.to_thread(
                exporter.generate_excel,
                project,
                rooms
            )
        else:  # pdf
            file_path = await asyncio.to_thread(
                exporter.generate_pdf,
                project,
                rooms
            )

        print(f"✅ Export generated: {file_path}")

        # Send email notification
        user = db.get_user_by_id(project.get("owner_id"))
        if user:
            await send_export_ready_email_async(user, project, export_format)

        return file_path

    except Exception as e:
        print(f"❌ Export generation failed: {e}")
        raise


if __name__ == "__main__":
    print("🔄 Background Tasks Module")
    print("Available async tasks:")
    print("  - send_email_async()")
    print("  - send_welcome_email_async()")
    print("  - send_project_complete_email_async()")
    print("  - send_export_ready_email_async()")
    print("  - send_payment_succeeded_email_async()")
    print("  - send_payment_failed_email_async()")
    print("  - process_drawing_async()")
    print("  - generate_export_async()")
