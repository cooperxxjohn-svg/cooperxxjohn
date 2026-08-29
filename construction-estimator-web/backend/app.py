from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import logging
from werkzeug.utils import secure_filename
import PyPDF2
import fitz
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 100 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

class ConstructionEstimator:
    """
    Processes floor plans and generates construction estimates using Claude.
    Supports: Drywall, Painting, Concrete
    """

    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))
        logger.info("Construction Estimator initialized")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF floor plan"""
        logger.info(f"Extracting text from: {pdf_path}")
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- PAGE {page_num + 1} ---\n{page_text}\n"
            logger.info(f"Extracted {len(text)} characters")
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
        return text

    def extract_text_with_ocr(self, pdf_path: str) -> str:
        """Use OCR for image-based PDFs"""
        logger.info("Running OCR on PDF...")
        text = ""
        try:
            images = convert_from_path(pdf_path)
            for page_num, image in enumerate(images):
                page_text = pytesseract.image_to_string(image, lang='eng')
                if page_text.strip():
                    text += f"\n--- PAGE {page_num + 1} ---\n{page_text}\n"
            logger.info(f"OCR extracted {len(text)} characters")
        except Exception as e:
            logger.error(f"OCR error: {e}")
        return text

    def generate_drywall_estimate(self, input_data: dict) -> dict:
        """Generate drywall estimate from user input or extracted floor plan"""
        logger.info("Generating drywall estimate...")

        prompt = f"""You are a professional construction estimator. Generate a detailed drywall estimate.

INPUT DATA:
{json.dumps(input_data, indent=2)}

Analyze the floor plan or room descriptions and create a comprehensive drywall estimate.

Return ONLY valid JSON in this format:
{{
    "project_name": "...",
    "summary": {{
        "total_walls": 0,
        "wall_sqft": 0,
        "ceiling_sqft": 0,
        "total_sqft": 0
    }},
    "materials": {{
        "sheets": 0,
        "compound_lbs": 0,
        "tape_lf": 0,
        "screws": 0,
        "corner_bead_lf": 0
    }},
    "labor": {{
        "hanging_hours": 0,
        "taping_hours": 0,
        "finishing_hours": 0,
        "total_hours": 0
    }},
    "costs": {{
        "material_cost": 0,
        "labor_cost": 0,
        "subtotal": 0,
        "overhead": 0,
        "profit": 0,
        "total_cost": 0,
        "cost_per_sqft": 0
    }},
    "rooms": [
        {{
            "name": "...",
            "walls": [...],
            "sqft": 0
        }}
    ]
}}

Use industry standards:
- ASTM C840 finish levels
- 15% waste factor for materials
- Standard labor rates: $65/hr commercial
- Overhead: 25%, Profit: 25%
"""

        try:
            response = self.client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Try to parse JSON
            try:
                estimate_json = json.loads(response_text)
                logger.info("Successfully generated drywall estimate")
                return {
                    "status": "success",
                    "trade": "drywall",
                    "estimate": estimate_json
                }
            except json.JSONDecodeError:
                # Return as text if not valid JSON
                return {
                    "status": "partial",
                    "trade": "drywall",
                    "estimate": response_text
                }
        except Exception as e:
            logger.error(f"Error with Claude: {e}")
            return {"status": "error", "error": str(e)}

    def generate_painting_estimate(self, input_data: dict) -> dict:
        """Generate painting estimate"""
        logger.info("Generating painting estimate...")

        prompt = f"""You are a professional painting estimator. Generate a detailed painting estimate.

INPUT DATA:
{json.dumps(input_data, indent=2)}

Return ONLY valid JSON:
{{
    "project_name": "...",
    "summary": {{
        "total_area": 0,
        "wall_area": 0,
        "ceiling_area": 0,
        "trim_lf": 0
    }},
    "materials": {{
        "primer_gallons": 0,
        "paint_gallons": 0,
        "supplies": "..."
    }},
    "labor": {{
        "prep_hours": 0,
        "primer_hours": 0,
        "paint_hours": 0,
        "total_hours": 0
    }},
    "costs": {{
        "material_cost": 0,
        "labor_cost": 0,
        "subtotal": 0,
        "overhead": 0,
        "profit": 0,
        "total_cost": 0,
        "cost_per_sqft": 0
    }}
}}

Use standards:
- Coverage: 350-400 sqft/gallon
- 2 coats standard
- Labor: $50-60/hr
"""

        try:
            response = self.client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            try:
                estimate_json = json.loads(response_text)
                return {
                    "status": "success",
                    "trade": "painting",
                    "estimate": estimate_json
                }
            except json.JSONDecodeError:
                return {
                    "status": "partial",
                    "trade": "painting",
                    "estimate": response_text
                }
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"status": "error", "error": str(e)}

    def process_floor_plan(self, pdf_path: str, trade: str = "drywall") -> dict:
        """Main processing pipeline for floor plans"""
        logger.info(f"Processing floor plan for {trade} estimate")

        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)

        # If minimal text, try OCR
        if len(text) < 100:
            logger.info("Minimal text extracted, trying OCR...")
            text = self.extract_text_with_ocr(pdf_path)

        if not text or len(text) < 50:
            return {
                "status": "error",
                "error": "Could not extract meaningful data from floor plan"
            }

        # Prepare input data
        input_data = {
            "source": "floor_plan_pdf",
            "extracted_text": text[:3000],  # Limit for API
            "trade": trade
        }

        # Generate estimate based on trade
        if trade == "drywall":
            return self.generate_drywall_estimate(input_data)
        elif trade == "painting":
            return self.generate_painting_estimate(input_data)
        else:
            return {"status": "error", "error": f"Unsupported trade: {trade}"}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "running", "version": "1.0.0", "service": "Construction Estimator API"})


@app.route('/estimate/manual', methods=['POST'])
def manual_estimate():
    """Generate estimate from manual room input (no file upload)"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No input data provided"}), 400

        trade = data.get('trade', 'drywall')

        estimator = ConstructionEstimator()

        if trade == "drywall":
            result = estimator.generate_drywall_estimate(data)
        elif trade == "painting":
            result = estimator.generate_painting_estimate(data)
        else:
            return jsonify({"error": f"Unsupported trade: {trade}"}), 400

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route('/estimate/upload', methods=['POST'])
def upload_floor_plan():
    """Generate estimate from uploaded floor plan PDF"""
    try:
        logger.info("Received floor plan upload")

        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Only PDF, PNG, JPG files allowed"}), 400

        trade = request.form.get('trade', 'drywall')

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        logger.info(f"File saved: {filepath} ({file_size_mb:.2f} MB)")

        # Process floor plan
        estimator = ConstructionEstimator()
        result = estimator.process_floor_plan(filepath, trade=trade)

        # Clean up uploaded file
        try:
            os.remove(filepath)
        except:
            pass

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route('/trades', methods=['GET'])
def get_supported_trades():
    """List supported construction trades"""
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


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("CONSTRUCTION ESTIMATOR API - Starting")
    logger.info("=" * 60)
    logger.info("Endpoints:")
    logger.info("  POST /estimate/manual - Generate estimate from JSON input")
    logger.info("  POST /estimate/upload - Upload floor plan PDF")
    logger.info("  GET  /trades - List supported trades")
    logger.info("  GET  /health - Health check")
    logger.info("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
