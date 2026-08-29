"""
XBOQ Enhanced API Server
Flask REST API for maximum-accuracy BOQ extraction
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
from datetime import datetime
from werkzeug.utils import secure_filename
import traceback
import logging
import json

from xboq_enhanced import XBOQEnhanced

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=['*'])  # Configure for production

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'xboq_output'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize XBOQ Enhanced
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
if not anthropic_api_key:
    logger.warning("⚠️  ANTHROPIC_API_KEY not set in environment variables")
    xboq_engine = None
else:
    try:
        xboq_engine = XBOQEnhanced(anthropic_api_key)
        logger.info("✓ XBOQ Enhanced Engine initialized")
    except Exception as e:
        logger.error(f"Failed to initialize XBOQ engine: {e}")
        xboq_engine = None


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'xboq_engine_ready': xboq_engine is not None,
        'features': {
            'document_analysis': True,
            'quality_enhancement': True,
            'multi_method_extraction': True,
            'table_extraction': True,
            'ocr_processing': True,
            'vision_api': True,
            'confidence_scoring': True,
            'validation': True,
            'batch_processing': True
        }
    })


@app.route('/api/xboq/extract', methods=['POST'])
def extract_xboq():
    """
    XBOQ Enhanced extraction endpoint

    Query params:
        - quick_mode: bool (default=false) - Quick processing
        - save_result: bool (default=true) - Save result to file

    Returns:
        Complete extraction result with confidence scores
    """
    try:
        # Validate engine
        if not xboq_engine:
            return jsonify({
                'error': 'XBOQ engine not initialized. Check API key configuration.'
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
        save_result = request.args.get('save_result', 'true').lower() == 'true'

        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        logger.info(f"Processing: {filename}, quick_mode={quick_mode}")

        # Run XBOQ Enhanced extraction
        start_time = time.time()
        result = xboq_engine.process_drawing_intelligent(
            filepath,
            quick_mode=quick_mode
        )

        # Save result if requested
        if save_result and result.get('success'):
            output_file = os.path.join(
                OUTPUT_FOLDER,
                f"{timestamp}_{os.path.splitext(filename)[0]}_result.json"
            )
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            result['output_file'] = output_file

        # Cleanup: remove uploaded file
        try:
            os.remove(filepath)
        except:
            pass

        logger.info(f"Extraction complete: {result.get('total_components', 0)} components, "
                   f"confidence: {result.get('overall_confidence', 0):.2f}")

        return jsonify(result), 200

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error in XBOQ extraction: {error_trace}")
        return jsonify({
            'error': str(e),
            'details': 'An error occurred during extraction',
            'success': False
        }), 500


@app.route('/api/xboq/batch', methods=['POST'])
def extract_batch():
    """
    Batch processing endpoint

    Accepts multiple files and processes them
    """
    try:
        if not xboq_engine:
            return jsonify({'error': 'XBOQ engine not initialized'}), 503

        # Get uploaded files
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400

        files = request.files.getlist('files')

        if len(files) == 0:
            return jsonify({'error': 'No files selected'}), 400

        # Save all files
        saved_paths = []
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                saved_paths.append(filepath)

        if len(saved_paths) == 0:
            return jsonify({'error': 'No valid files uploaded'}), 400

        logger.info(f"Batch processing {len(saved_paths)} files")

        # Process batch
        results = xboq_engine.process_batch(
            saved_paths,
            output_dir=os.path.join(OUTPUT_FOLDER, f"batch_{timestamp}")
        )

        # Cleanup
        for path in saved_paths:
            try:
                os.remove(path)
            except:
                pass

        # Summary
        summary = {
            'total_processed': len(results),
            'successful': len([r for r in results if r.get('success', False)]),
            'failed': len([r for r in results if not r.get('success', False)]),
            'results': results
        }

        return jsonify(summary), 200

    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/xboq/analyze', methods=['POST'])
def analyze_document():
    """
    Analyze document structure without full extraction

    Returns page types, priorities, and structure map
    """
    try:
        if not xboq_engine:
            return jsonify({'error': 'XBOQ engine not initialized'}), 503

        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']

        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400

        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
        file.save(filepath)

        # Analyze structure
        doc_map = xboq_engine.document_analyzer.analyze_document_structure(filepath)

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
            'processing_order': doc_map.processing_order[:20],
            'page_details': [
                {
                    'page_num': p.page_num,
                    'content_type': p.content_type.value,
                    'priority': p.priority.value,
                    'has_tables': p.has_tables,
                    'has_images': p.has_images,
                    'confidence': p.confidence
                }
                for p in doc_map.pages[:50]
            ]
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error analyzing document: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/xboq/validate', methods=['POST'])
def validate_boq():
    """
    Validate BOQ components and get confidence scores

    Request body:
        {
            "components": [...]
        }
    """
    try:
        if not xboq_engine:
            return jsonify({'error': 'XBOQ engine not initialized'}), 503

        data = request.get_json()

        if not data or 'components' not in data:
            return jsonify({'error': 'Missing components in request body'}), 400

        components = data['components']

        # Validate
        validation_result = xboq_engine.validator.validate_document(components)

        return jsonify(validation_result.to_dict()), 200

    except Exception as e:
        logger.error(f"Error validating: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Test endpoint"""
    return jsonify({
        'message': 'XBOQ Enhanced API is running',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat(),
        'features': {
            'intelligent_extraction': True,
            'multi_method': True,
            'confidence_scoring': True,
            'batch_processing': True,
            'validation': True
        }
    })


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("XBOQ Enhanced API Server")
    print("=" * 80)
    print(f"\nServer starting on http://localhost:5000")
    print("\nEndpoints:")
    print("  POST /api/xboq/extract     - Maximum accuracy extraction")
    print("  POST /api/xboq/batch       - Batch processing")
    print("  POST /api/xboq/analyze     - Document structure analysis")
    print("  POST /api/xboq/validate    - Validate and score BOQ")
    print("  GET  /api/health           - Health check")

    if not anthropic_api_key:
        print("\n⚠️  WARNING: ANTHROPIC_API_KEY not set!")
        print("Set it in your environment or .env file")
    else:
        print("\n✓ Anthropic API key configured")
        print("✓ XBOQ Enhanced Engine ready")
        print("✓ All intelligent processors initialized")

    print("\nPress Ctrl+C to stop")
    print("=" * 80 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
