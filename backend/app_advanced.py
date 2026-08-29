"""
TakeoffAI Advanced Flask Backend
Intelligent PDF/image processing with multi-stage extraction pipeline
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
from datetime import datetime
from werkzeug.utils import secure_filename
import traceback
import logging
from typing import Dict, Optional

# Import intelligent extraction engine
from extraction_engine import IntelligentExtractionEngine, ExtractionResult

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize extraction engine
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
if not anthropic_api_key:
    logger.warning("⚠️  ANTHROPIC_API_KEY not set in environment variables")
    extraction_engine = None
else:
    try:
        extraction_engine = IntelligentExtractionEngine(anthropic_api_key)
        logger.info("✓ Intelligent Extraction Engine initialized")
    except Exception as e:
        logger.error(f"Failed to initialize extraction engine: {e}")
        extraction_engine = None

# Job storage (use Redis in production)
extraction_jobs: Dict[str, Dict] = {}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'extraction_engine_ready': extraction_engine is not None,
        'features': {
            'table_extraction': True,
            'ocr_processing': True,
            'vision_api': True,
            'document_analysis': True,
            'validation': True
        }
    })


@app.route('/api/extract-advanced', methods=['POST'])
def extract_advanced():
    """
    Advanced extraction endpoint using intelligent pipeline

    Query params:
        - quick_mode: bool (default=False) - Use faster extraction
        - max_pages: int (default=None) - Limit pages to process

    Returns:
        Complete BOQ extraction with confidence scores
    """
    try:
        # Validate extraction engine
        if not extraction_engine:
            return jsonify({
                'error': 'Extraction engine not initialized. Check API key configuration.'
            }), 503

        # Validate file upload
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF and image files are allowed'}), 400

        # Get query parameters
        quick_mode = request.args.get('quick_mode', 'false').lower() == 'true'
        max_pages = request.args.get('max_pages', None)
        if max_pages:
            max_pages = int(max_pages)

        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        logger.info(f"Processing: {filename}, quick_mode={quick_mode}, max_pages={max_pages}")

        # Run intelligent extraction
        start_time = time.time()
        result = extraction_engine.process_construction_document(
            filepath,
            quick_mode=quick_mode,
            max_pages=max_pages
        )

        # Cleanup: remove uploaded file
        try:
            os.remove(filepath)
        except:
            pass

        # Prepare response
        response_data = result.to_dict()

        logger.info(f"Extraction complete: {result.line_items} items, "
                   f"confidence: {result.confidence:.2f}, "
                   f"time: {result.processing_time}s")

        return jsonify(response_data), 200

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error in advanced extraction: {error_trace}")
        return jsonify({
            'error': str(e),
            'details': 'An error occurred during extraction'
        }), 500


@app.route('/api/extract-from-drawing', methods=['POST'])
def extract_from_drawing():
    """
    Extract BOQ from architectural drawing using Vision API

    For image files (PNG, JPG) that are architectural drawings
    """
    try:
        if not extraction_engine:
            return jsonify({'error': 'Extraction engine not initialized'}), 503

        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']

        if not allowed_file(file.filename):
            return jsonify({'error': 'Only image files (PNG, JPG) are allowed'}), 400

        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        logger.info(f"Extracting from drawing: {filename}")

        # Extract using vision API
        drawing_data = extraction_engine.vision_extractor.extract_from_architectural_drawing(filepath)

        # Convert to BOQ format
        boq_items = []
        for material in drawing_data.materials:
            boq_items.append({
                'item': f"V{len(boq_items)+1}",
                'description': material.get('specification', material.get('material', '')),
                'qty': material.get('quantity', 0),
                'unit': material.get('unit', ''),
                'rate': 0,
                'amount': 0
            })

        # Cleanup
        try:
            os.remove(filepath)
        except:
            pass

        response = {
            'projectName': 'Architectural Drawing',
            'projectType': 'Construction',
            'totalValue': 0,
            'lineItems': len(boq_items),
            'accuracy': 'High' if drawing_data.confidence > 0.8 else 'Medium',
            'confidence': drawing_data.confidence,
            'boqItems': boq_items,
            'drawingData': drawing_data.to_dict()
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error extracting from drawing: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate-extraction', methods=['POST'])
def validate_extraction():
    """
    Validate extracted BOQ data and get confidence scores

    Request body:
        {
            "boqItems": [...]
        }
    """
    try:
        if not extraction_engine:
            return jsonify({'error': 'Extraction engine not initialized'}), 503

        data = request.get_json()

        if not data or 'boqItems' not in data:
            return jsonify({'error': 'Missing boqItems in request body'}), 400

        boq_items = data['boqItems']

        # Validate
        validation_result = extraction_engine.validator.validate_document(boq_items)

        return jsonify(validation_result.to_dict()), 200

    except Exception as e:
        logger.error(f"Error validating extraction: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze-document', methods=['POST'])
def analyze_document():
    """
    Analyze document structure without full extraction

    Returns document map with page types and priorities
    """
    try:
        if not extraction_engine:
            return jsonify({'error': 'Extraction engine not initialized'}), 503

        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']

        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400

        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # Analyze structure
        doc_map = extraction_engine.document_analyzer.analyze_document_structure(filepath)

        # Cleanup
        try:
            os.remove(filepath)
        except:
            pass

        # Convert to JSON-serializable format
        response = {
            'total_pages': doc_map.total_pages,
            'boq_pages': doc_map.boq_pages,
            'drawing_pages': doc_map.drawing_pages,
            'specification_pages': doc_map.specification_pages,
            'sections': doc_map.sections,
            'processing_order': doc_map.processing_order[:20],  # First 20
            'page_details': [
                {
                    'page_num': p.page_num,
                    'content_type': p.content_type.value,
                    'priority': p.priority.value,
                    'has_tables': p.has_tables,
                    'has_images': p.has_images,
                    'confidence': p.confidence
                }
                for p in doc_map.pages[:50]  # First 50 pages
            ]
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error analyzing document: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/process-drawing', methods=['POST'])
def process_drawing_legacy():
    """
    Legacy endpoint for backward compatibility
    Redirects to advanced extraction
    """
    return extract_advanced()


@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Test endpoint"""
    return jsonify({
        'message': 'TakeoffAI Advanced API is running',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat(),
        'features': {
            'intelligent_extraction': True,
            'table_extraction': True,
            'ocr_processing': True,
            'vision_api': True,
            'document_analysis': True,
            'confidence_scoring': True
        }
    })


@app.route('/api/extraction-methods', methods=['GET'])
def extraction_methods():
    """Get available extraction methods"""
    return jsonify({
        'methods': [
            {
                'name': 'Table Extraction',
                'description': 'Extract BOQ from structured tables',
                'accuracy': 'High',
                'speed': 'Fast'
            },
            {
                'name': 'OCR Processing',
                'description': 'Extract text from scanned documents with error correction',
                'accuracy': 'Medium-High',
                'speed': 'Medium'
            },
            {
                'name': 'Vision API',
                'description': 'Analyze architectural drawings with Claude Vision',
                'accuracy': 'High',
                'speed': 'Medium'
            },
            {
                'name': 'Document Analysis',
                'description': 'Intelligent page prioritization and structure detection',
                'accuracy': 'High',
                'speed': 'Very Fast'
            },
            {
                'name': 'Specification Parsing',
                'description': 'Extract BOQ from text specifications',
                'accuracy': 'Medium',
                'speed': 'Fast'
            }
        ]
    })


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("TakeoffAI Advanced Backend Server")
    print("=" * 80)
    print(f"\nServer starting on http://localhost:5000")
    print("\nEndpoints:")
    print("  POST /api/extract-advanced         - Intelligent extraction pipeline")
    print("  POST /api/extract-from-drawing     - Vision API for drawings")
    print("  POST /api/validate-extraction      - Validate and score BOQ")
    print("  POST /api/analyze-document         - Analyze document structure")
    print("  GET  /api/extraction-methods       - List available methods")
    print("  GET  /api/health                   - Health check")
    print("\nLegacy endpoint:")
    print("  POST /api/process-drawing          - Backward compatible")

    if not anthropic_api_key:
        print("\n⚠️  WARNING: ANTHROPIC_API_KEY not set!")
        print("Set it in your environment or .env file")
    else:
        print("\n✓ Anthropic API key configured")
        print("✓ Intelligent Extraction Engine ready")

    print("\nPress Ctrl+C to stop")
    print("=" * 80 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
