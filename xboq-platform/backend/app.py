"""
XBOQ Platform - Unified Backend
Combines BOQ Generator + Construction Estimator
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import modules
from modules.boq_generator import BOQGenerator
from modules.estimator import ConstructionEstimator
from utils.pdf_processor import PDFProcessor
from database import get_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CORS Configuration - Allow both development and production origins
ALLOWED_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
CORS(app, resources={r"/*": {
    "origins": ALLOWED_ORIGINS if os.getenv('FLASK_ENV') == 'production' else "*"
}})

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize services
boq_generator = BOQGenerator()
estimator = ConstructionEstimator()
db = get_database()

# Create default demo user for testing (until we have auth)
try:
    demo_user = db.get_user_by_email('demo@xboq.ai')
    if not demo_user:
        demo_user = db.create_user(email='demo@xboq.ai', name='Demo User')
        logger.info(f"Created demo user: {demo_user.email}")
except Exception as e:
    logger.error(f"Error creating demo user: {e}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================================
# HEALTH & INFO ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    db_healthy = db.health_check()
    return jsonify({
        "status": "running",
        "version": "2.0.0",
        "services": ["BOQ Generator", "Construction Estimator"],
        "database": "connected" if db_healthy else "disconnected"
    })

@app.route('/api/products', methods=['GET'])
def get_products():
    """List available products"""
    return jsonify({
        "products": [
            {
                "id": "boq",
                "name": "BOQ Generator",
                "description": "Extract Bill of Quantities from tender documents",
                "icon": "📋",
                "route": "/boq",
                "available": True
            },
            {
                "id": "estimator",
                "name": "Construction Estimator",
                "description": "Generate estimates for drywall, painting, concrete",
                "icon": "🏗️",
                "route": "/estimator",
                "available": True
            }
        ]
    })

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """List supported construction trades for estimator"""
    return jsonify({
        "trades": [
            {
                "id": "drywall",
                "name": "Drywall",
                "description": "Drywall installation and finishing",
                "available": True
            },
            {
                "id": "painting",
                "name": "Painting",
                "description": "Interior/exterior painting",
                "available": True
            },
            {
                "id": "concrete",
                "name": "Concrete",
                "description": "Concrete work",
                "available": False,
                "coming_soon": True
            }
        ]
    })


# ============================================================================
# BOQ GENERATOR ENDPOINTS
# ============================================================================

@app.route('/api/boq/upload', methods=['POST'])
def upload_tender():
    """
    Upload tender document and extract BOQ
    Original XBOQ functionality
    """
    try:
        logger.info("=== BOQ UPLOAD REQUEST ===")

        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Only PDF files allowed"}), 400

        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        logger.info(f"BOQ file saved: {filepath} ({file_size_mb:.2f} MB)")

        # Process tender document
        logger.info("Starting BOQ generation...")
        import time
        start_time = time.time()
        result = boq_generator.process(filepath)
        extraction_time = time.time() - start_time

        # Save to database
        try:
            # Get demo user (until we have auth)
            demo_user = db.get_user_by_email('demo@xboq.ai')

            # Create project
            project = db.create_project(
                user_id=demo_user.id,
                project_type='boq',
                name=result.get('boq', {}).get('project_name', filename),
                file_name=filename,
                file_url=filepath
            )

            # Update project status
            db.update_project(project.id, status='complete')

            # Save BOQ data
            boq_data = result.get('boq', {})
            boq = db.create_boq(
                project_id=project.id,
                project_name=boq_data.get('project_name', 'Unnamed Project'),
                sections=boq_data.get('sections', []),
                total_items=boq_data.get('total_items', 0),
                extraction_time=extraction_time
            )

            # Add database IDs to response
            result['project_id'] = project.id
            result['boq_id'] = boq.id

            logger.info(f"BOQ saved to database: project_id={project.id}, boq_id={boq.id}")
        except Exception as db_error:
            logger.error(f"Database save error: {db_error}")
            # Continue even if DB save fails (for now)

        # Clean up
        try:
            os.remove(filepath)
        except:
            pass

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"BOQ Error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e), "status": "error"}), 500


# ============================================================================
# CONSTRUCTION ESTIMATOR ENDPOINTS
# ============================================================================

@app.route('/api/estimate/manual', methods=['POST'])
def manual_estimate():
    """
    Generate estimate from manual room input (no file upload)
    New Construction Estimator functionality
    """
    try:
        logger.info("=== MANUAL ESTIMATE REQUEST ===")

        data = request.get_json()

        if not data:
            return jsonify({"error": "No input data provided"}), 400

        trade = data.get('trade', 'drywall')
        project_type = data.get('project_type', 'residential')
        logger.info(f"Generating {trade} estimate from manual input")

        # Generate estimate based on trade
        import time
        start_time = time.time()
        if trade == "drywall":
            result = estimator.generate_drywall_estimate(data)
        elif trade == "painting":
            result = estimator.generate_painting_estimate(data)
        else:
            return jsonify({"error": f"Unsupported trade: {trade}"}), 400
        calculation_time = time.time() - start_time

        # Save to database
        try:
            demo_user = db.get_user_by_email('demo@xboq.ai')
            estimate_data = result.get('estimate', {})

            # Create project
            project_name = f"{trade.capitalize()} Estimate - {len(data.get('rooms', []))} room(s)"
            project = db.create_project(
                user_id=demo_user.id,
                project_type='estimate',
                name=project_name
            )
            db.update_project(project.id, status='complete')

            # Save estimate
            summary = estimate_data.get('summary', {})
            estimate = db.create_estimate(
                project_id=project.id,
                trade=trade,
                project_type=project_type,
                rooms=estimate_data.get('rooms', []),
                summary=summary,
                total_cost=summary.get('total_cost'),
                total_sqft=summary.get('total_sqft'),
                total_labor_hours=summary.get('total_labor_hours'),
                calculation_time=calculation_time
            )

            # Add database IDs to response
            result['project_id'] = project.id
            result['estimate_id'] = estimate.id

            logger.info(f"Estimate saved to database: project_id={project.id}, estimate_id={estimate.id}")
        except Exception as db_error:
            logger.error(f"Database save error: {db_error}")

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Manual Estimate Error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route('/api/estimate/upload', methods=['POST'])
def upload_floor_plan():
    """
    Upload floor plan and generate estimate
    New Construction Estimator functionality
    """
    try:
        logger.info("=== FLOOR PLAN UPLOAD REQUEST ===")

        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Only PDF, PNG, JPG files allowed"}), 400

        trade = request.form.get('trade', 'drywall')

        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        logger.info(f"Floor plan saved: {filepath} ({file_size_mb:.2f} MB)")

        # Process floor plan
        logger.info(f"Starting {trade} estimate from floor plan...")
        import time
        start_time = time.time()
        result = estimator.process_floor_plan(filepath, trade=trade)
        calculation_time = time.time() - start_time

        # Save to database
        try:
            demo_user = db.get_user_by_email('demo@xboq.ai')
            estimate_data = result.get('estimate', {})

            # Create project
            project = db.create_project(
                user_id=demo_user.id,
                project_type='estimate',
                name=f"{trade.capitalize()} - {filename}",
                file_name=filename,
                file_url=filepath
            )
            db.update_project(project.id, status='complete')

            # Save estimate
            summary = estimate_data.get('summary', {})
            estimate = db.create_estimate(
                project_id=project.id,
                trade=trade,
                rooms=estimate_data.get('rooms', []),
                summary=summary,
                total_cost=summary.get('total_cost'),
                total_sqft=summary.get('total_sqft'),
                total_labor_hours=summary.get('total_labor_hours'),
                calculation_time=calculation_time
            )

            # Add database IDs to response
            result['project_id'] = project.id
            result['estimate_id'] = estimate.id

            logger.info(f"Floor plan estimate saved: project_id={project.id}, estimate_id={estimate.id}")
        except Exception as db_error:
            logger.error(f"Database save error: {db_error}")

        # Clean up
        try:
            os.remove(filepath)
        except:
            pass

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Floor Plan Estimate Error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e), "status": "error"}), 500


# ============================================================================
# DATA RETRIEVAL ENDPOINTS
# ============================================================================

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects for demo user"""
    try:
        demo_user = db.get_user_by_email('demo@xboq.ai')
        if not demo_user:
            return jsonify({"error": "User not found"}), 404

        project_type = request.args.get('type')  # 'boq' or 'estimate'
        limit = int(request.args.get('limit', 50))

        projects = db.get_user_projects(demo_user.id, project_type=project_type, limit=limit)

        return jsonify({
            "projects": [p.to_dict() for p in projects],
            "total": len(projects)
        }), 200

    except Exception as e:
        logger.error(f"Get projects error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get single project with full details"""
    try:
        project = db.get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        response = project.to_dict()

        # Include BOQ data if it's a BOQ project
        if project.type == 'boq':
            boq = db.get_boq_by_project(project_id)
            if boq:
                response['boq'] = boq.to_dict()

        # Include Estimate data if it's an estimate project
        elif project.type == 'estimate':
            estimate = db.get_estimate_by_project(project_id)
            if estimate:
                response['estimate'] = estimate.to_dict()

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Get project error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    try:
        success = db.delete_project(project_id)
        if success:
            return jsonify({"status": "deleted", "project_id": project_id}), 200
        else:
            return jsonify({"error": "Project not found"}), 404

    except Exception as e:
        logger.error(f"Delete project error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/boqs/<int:boq_id>', methods=['GET'])
def get_boq(boq_id):
    """Get BOQ by ID"""
    try:
        boq = db.get_boq(boq_id)
        if not boq:
            return jsonify({"error": "BOQ not found"}), 404

        return jsonify(boq.to_dict()), 200

    except Exception as e:
        logger.error(f"Get BOQ error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/estimates/<int:estimate_id>', methods=['GET'])
def get_estimate(estimate_id):
    """Get estimate by ID"""
    try:
        estimate = db.get_estimate(estimate_id)
        if not estimate:
            return jsonify({"error": "Estimate not found"}), 404

        return jsonify(estimate.to_dict()), 200

    except Exception as e:
        logger.error(f"Get estimate error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get user statistics"""
    try:
        demo_user = db.get_user_by_email('demo@xboq.ai')
        if not demo_user:
            return jsonify({"error": "User not found"}), 404

        stats = db.get_user_stats(demo_user.id)
        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Get stats error: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ANALYTICS & TRACKING (Future)
# ============================================================================

@app.route('/api/analytics/track', methods=['POST'])
def track_usage():
    """Track API usage (placeholder for future database)"""
    data = request.get_json()
    logger.info(f"Usage tracked: {data.get('action')}")
    return jsonify({"status": "tracked"}), 200


if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("XBOQ PLATFORM - UNIFIED API SERVER")
    logger.info("=" * 80)
    logger.info("Products Available:")
    logger.info("  1. BOQ Generator - Upload tender documents")
    logger.info("  2. Construction Estimator - Drywall, Painting, Concrete")
    logger.info("=" * 80)
    logger.info("Endpoints:")
    logger.info("  GET  /health")
    logger.info("  GET  /api/products")
    logger.info("  GET  /api/trades")
    logger.info("")
    logger.info("  BOQ Generator:")
    logger.info("    POST /api/boq/upload")
    logger.info("")
    logger.info("  Construction Estimator:")
    logger.info("    POST /api/estimate/manual")
    logger.info("    POST /api/estimate/upload")
    logger.info("=" * 80)

    app.run(host='0.0.0.0', port=5000, debug=True)
