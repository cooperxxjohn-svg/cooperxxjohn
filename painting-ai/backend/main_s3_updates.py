"""
S3 Integration Updates for main.py
Replace the upload and export endpoints with these S3-enabled versions
"""

# Add this import at the top of main.py
from s3_service import S3Service, get_s3_service
from io import BytesIO
import tempfile

# Initialize S3 service (add after other service initializations)
try:
    s3_service = get_s3_service()
    USE_S3 = True
except Exception as e:
    print(f"⚠️  S3 not configured: {e}")
    print("   Falling back to local storage")
    s3_service = None
    USE_S3 = False


# ==============================================================================
# UPDATED UPLOAD ENDPOINT WITH S3
# ==============================================================================

@app.post("/projects/{project_id}/upload")
async def upload_drawing(
    project_id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload and process a drawing - S3-enabled version"""

    # Verify project exists
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # File validation
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit
    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content and validate size
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Validate file is not corrupted (basic check for PDF)
    if file_ext == ".pdf" and not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Corrupted or invalid PDF file")

    file_id = str(uuid.uuid4())

    # Upload to S3 or local storage
    if USE_S3 and s3_service:
        # S3 Storage
        s3_key = f"{project_id}/{file_id}{file_ext}"

        try:
            # Upload to S3 using BytesIO
            file_obj = BytesIO(content)
            upload_result = s3_service.upload_file_obj(
                file_obj=file_obj,
                s3_key=s3_key,
                metadata={
                    'project_id': project_id,
                    'file_id': file_id,
                    'original_filename': file.filename,
                    'uploaded_at': datetime.utcnow().isoformat()
                },
                content_type=s3_service._get_content_type(file.filename)
            )

            # Generate signed URL for download
            signed_url = s3_service.generate_signed_url(
                s3_key=s3_key,
                download_filename=file.filename
            )

            # Store S3 info in database
            storage_info = {
                'storage': 's3',
                's3_key': s3_key,
                's3_bucket': s3_service.bucket_uploads,
                'download_url': signed_url,
                'url_expires_at': (datetime.utcnow() + timedelta(seconds=s3_service.signed_url_expiry)).isoformat()
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload to S3: {str(e)}"
            )

    else:
        # Local Storage (fallback)
        project_upload_dir = UPLOAD_DIR / project_id
        project_upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = project_upload_dir / f"{file_id}{file_ext}"

        # Save file locally
        with open(file_path, "wb") as f:
            f.write(content)

        storage_info = {
            'storage': 'local',
            'file_path': str(file_path)
        }

    # Initialize processing status
    processing_status = {
        "file_id": file_id,
        "filename": file.filename,
        "status": "queued",
        "progress": 0,
        "message": "File uploaded, queued for processing",
        "uploaded_at": datetime.utcnow().isoformat(),
        "file_size": file_size,
        **storage_info  # Add storage info (S3 or local)
    }

    # Store status in project data
    project_data = project.copy()
    if "uploads" not in project_data:
        project_data["uploads"] = {}
    project_data["uploads"][file_id] = processing_status
    db.update_project(project_id, project_data)

    # Update project status
    db.update_project(project_id, {"status": "processing"})

    # Process in background
    if background_tasks:
        # For S3, we need to download the file temporarily for processing
        if USE_S3:
            background_tasks.add_task(
                process_drawing_s3,
                project_id=project_id,
                s3_key=s3_key,
                file_id=file_id
            )
        else:
            background_tasks.add_task(
                process_drawing,
                project_id=project_id,
                file_path=str(file_path),
                file_id=file_id
            )

    response = {
        "message": "File uploaded successfully and queued for processing",
        "file_id": file_id,
        "filename": file.filename,
        "file_size": file_size,
        "status": "queued",
        "project_id": project_id
    }

    # Add download URL if S3
    if USE_S3 and 'download_url' in storage_info:
        response['download_url'] = storage_info['download_url']
        response['url_expires_at'] = storage_info['url_expires_at']

    return response


async def process_drawing_s3(project_id: str, s3_key: str, file_id: str):
    """Background task to process a drawing from S3"""
    temp_file = None

    try:
        # Update status: Starting
        update_processing_status(project_id, file_id, "processing", 10, "Starting AI analysis...")

        # Download file from S3 to temporary location
        update_processing_status(project_id, file_id, "processing", 20, "Downloading from S3...")

        # Create temporary file
        file_ext = Path(s3_key).suffix
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)

        # Download from S3
        s3_service.s3_client.download_file(
            s3_service.bucket_uploads,
            s3_key,
            temp_file.name
        )

        # Continue with existing processing logic
        update_processing_status(project_id, file_id, "processing", 30, "Analyzing drawing with AI...")
        detection = detector.analyze_drawing(temp_file.name)

        # ... (rest of processing logic same as original process_drawing)
        # Update status: AI Complete
        update_processing_status(project_id, file_id, "processing", 60, f"Detected {detection.total_rooms} rooms, saving...")

        # Save rooms to database
        for i, room in enumerate(detection.rooms):
            room_id = str(uuid.uuid4())

            room_data = {
                "id": room_id,
                "project_id": project_id,
                "name": room.name,
                "number": room.number,
                "dimensions": room.dimensions,
                "surfaces": {
                    name: {
                        "type": surface.type,
                        "area": surface.area,
                        "linear_feet": surface.linear_feet,
                        "height": surface.height,
                        "deductions": surface.deductions
                    }
                    for name, surface in room.surfaces.items()
                },
                "total_area": room.total_area
            }

            db.save_room(room_data)

            # Update progress
            progress = 60 + int((i + 1) / len(detection.rooms) * 30)
            update_processing_status(project_id, file_id, "processing", progress, f"Saved room {i+1}/{len(detection.rooms)}")

        # Update project totals
        update_processing_status(project_id, file_id, "processing", 95, "Calculating project totals...")

        project = db.get_project(project_id)
        rooms = db.get_project_rooms(project_id)

        total_sqft = sum(r["total_area"] for r in rooms)

        db.update_project(project_id, {
            "status": "complete",
            "total_rooms": len(rooms),
            "total_sqft": total_sqft,
            "updated_at": datetime.utcnow().isoformat()
        })

        # Final status update
        update_processing_status(
            project_id,
            file_id,
            "complete",
            100,
            f"Complete! Detected {len(rooms)} rooms, {total_sqft:.0f} sqft total"
        )

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing drawing from S3: {error_details}")

        # Update status: Failed
        update_processing_status(project_id, file_id, "failed", 0, f"Error: {str(e)}")

        db.update_project(project_id, {
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat()
        })

    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


# ==============================================================================
# UPDATED EXPORT ENDPOINTS WITH S3
# ==============================================================================

@app.get("/projects/{project_id}/export/excel")
async def export_excel(project_id: str):
    """Export project to Excel - S3-enabled version"""

    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    rooms = db.get_project_rooms(project_id)

    if USE_S3 and s3_service:
        # Generate Excel to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            temp_path = tmp_file.name

        try:
            # Generate Excel file
            exporter.generate_excel(project, rooms, temp_path)

            # Upload to S3
            export_id = str(uuid.uuid4())
            s3_key = f"{project_id}/{export_id}_takeoff.xlsx"

            upload_result = s3_service.upload_file(
                file_path=temp_path,
                s3_key=s3_key,
                bucket=s3_service.bucket_exports,
                metadata={
                    'project_id': project_id,
                    'export_id': export_id,
                    'export_type': 'excel',
                    'generated_at': datetime.utcnow().isoformat()
                }
            )

            # Generate signed URL
            signed_url = s3_service.generate_signed_url(
                s3_key=s3_key,
                bucket=s3_service.bucket_exports,
                download_filename=f"{project['name']}_Takeoff.xlsx"
            )

            # Clean up temp file
            os.unlink(temp_path)

            # Return download info
            return {
                "export_type": "excel",
                "download_url": signed_url,
                "expires_at": (datetime.utcnow() + timedelta(seconds=s3_service.signed_url_expiry)).isoformat(),
                "filename": f"{project['name']}_Takeoff.xlsx",
                "project_id": project_id,
                "storage": "s3",
                "s3_key": s3_key
            }

        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

    else:
        # Local storage (existing behavior)
        output_path = OUTPUT_DIR / f"{project_id}_takeoff.xlsx"
        exporter.generate_excel(project, rooms, output_path)

        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"{project['name']}_Takeoff.xlsx"
        )


@app.get("/projects/{project_id}/export/pdf")
async def export_pdf(project_id: str):
    """Export project to PDF proposal - S3-enabled version"""

    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    rooms = db.get_project_rooms(project_id)

    if USE_S3 and s3_service:
        # Generate PDF to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            temp_path = tmp_file.name

        try:
            # Generate PDF file
            exporter.generate_pdf(project, rooms, temp_path)

            # Upload to S3
            export_id = str(uuid.uuid4())
            s3_key = f"{project_id}/{export_id}_proposal.pdf"

            upload_result = s3_service.upload_file(
                file_path=temp_path,
                s3_key=s3_key,
                bucket=s3_service.bucket_exports,
                metadata={
                    'project_id': project_id,
                    'export_id': export_id,
                    'export_type': 'pdf',
                    'generated_at': datetime.utcnow().isoformat()
                }
            )

            # Generate signed URL
            signed_url = s3_service.generate_signed_url(
                s3_key=s3_key,
                bucket=s3_service.bucket_exports,
                download_filename=f"{project['name']}_Proposal.pdf"
            )

            # Clean up temp file
            os.unlink(temp_path)

            # Return download info
            return {
                "export_type": "pdf",
                "download_url": signed_url,
                "expires_at": (datetime.utcnow() + timedelta(seconds=s3_service.signed_url_expiry)).isoformat(),
                "filename": f"{project['name']}_Proposal.pdf",
                "project_id": project_id,
                "storage": "s3",
                "s3_key": s3_key
            }

        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

    else:
        # Local storage (existing behavior)
        output_path = OUTPUT_DIR / f"{project_id}_proposal.pdf"
        exporter.generate_pdf(project, rooms, output_path)

        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=f"{project['name']}_Proposal.pdf"
        )


# ==============================================================================
# NEW ENDPOINT: Refresh Signed URL
# ==============================================================================

@app.get("/projects/{project_id}/uploads/{file_id}/download-url")
async def get_upload_download_url(project_id: str, file_id: str):
    """
    Generate fresh signed URL for uploaded file

    Useful when original URL expires (after 24 hours)
    """
    if not USE_S3 or not s3_service:
        raise HTTPException(
            status_code=501,
            detail="S3 storage not configured. File downloads not available."
        )

    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get upload info from project
    if "uploads" not in project or file_id not in project["uploads"]:
        raise HTTPException(status_code=404, detail="Upload not found")

    upload_info = project["uploads"][file_id]

    if upload_info.get("storage") != "s3":
        raise HTTPException(
            status_code=400,
            detail="File not stored in S3"
        )

    s3_key = upload_info.get("s3_key")
    if not s3_key:
        raise HTTPException(
            status_code=500,
            detail="S3 key not found in upload record"
        )

    # Generate fresh signed URL
    try:
        signed_url = s3_service.generate_signed_url(
            s3_key=s3_key,
            download_filename=upload_info.get("filename", "download")
        )

        return {
            "download_url": signed_url,
            "expires_at": (datetime.utcnow() + timedelta(seconds=s3_service.signed_url_expiry)).isoformat(),
            "file_id": file_id,
            "filename": upload_info.get("filename")
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate download URL: {str(e)}"
        )


# ==============================================================================
# HEALTH CHECK UPDATE
# ==============================================================================

@app.get("/health")
async def health_check():
    """Health check with S3 status"""
    return {
        "status": "healthy",
        "detector": "ready",
        "database": "connected" if db.is_connected() else "disconnected",
        "s3": "enabled" if USE_S3 else "disabled (using local storage)"
    }
