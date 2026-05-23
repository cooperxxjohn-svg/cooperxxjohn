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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================================
# HEALTH & INFO ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "running",
        "version": "2.0.0",
        "services": ["BOQ Generator", "Construction Estimator"]
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
        result = boq_generator.process(filepath)

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
        logger.info(f"Generating {trade} estimate from manual input")

        # Generate estimate based on trade
        if trade == "drywall":
            result = estimator.generate_drywall_estimate(data)
        elif trade == "painting":
            result = estimator.generate_painting_estimate(data)
        else:
            return jsonify({"error": f"Unsupported trade: {trade}"}), 400

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
        result = estimator.process_floor_plan(filepath, trade=trade)

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
