"""
TakeoffAI Flask Backend
Accepts PDF uploads, extracts text, and generates BOQ using Claude API
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
import PyPDF2
from anthropic import Anthropic
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import traceback

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize Anthropic client
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
if not anthropic_api_key:
    print("WARNING: ANTHROPIC_API_KEY not set in environment variables")
    anthropic_client = None
else:
    anthropic_client = Anthropic(api_key=anthropic_api_key)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(pdf_path):
    """Extract text content from PDF file using PyPDF2"""
    try:
        text_content = []
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)

            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    text_content.append(f"--- Page {page_num + 1} ---\n{text}")

        return '\n\n'.join(text_content), num_pages
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


def analyze_with_claude(pdf_text, filename):
    """Send extracted text to Claude API for BOQ generation"""
    if not anthropic_client:
        raise Exception("Anthropic API client not initialized. Please set ANTHROPIC_API_KEY.")

    prompt = f"""You are an expert construction estimator analyzing architectural/construction drawings.

Analyze the following text extracted from a construction drawing PDF named "{filename}" and generate a detailed Bill of Quantities (BOQ).

EXTRACTED TEXT:
{pdf_text}

Please analyze this drawing and provide:
1. Project identification (name, type)
2. A comprehensive BOQ with all identifiable items

Return your response as a valid JSON object with this EXACT structure:
{{
  "projectName": "Identified project name or 'Construction Project'",
  "projectType": "Type of construction (Residential/Commercial/Infrastructure/etc.)",
  "totalValue": 0.0,
  "lineItems": 0,
  "accuracy": "High/Medium/Low based on drawing clarity",
  "boqItems": [
    {{
      "item": "Item code or number",
      "description": "Detailed description of work",
      "qty": 0.0,
      "unit": "Unit of measurement (cum, sqm, kg, etc.)",
      "rate": 0.0,
      "amount": 0.0
    }}
  ]
}}

IMPORTANT GUIDELINES:
- Extract actual quantities and specifications from the drawing
- Use standard units: cum (cubic meter), sqm (square meter), m (meter), kg, nos (numbers), etc.
- Estimate rates based on typical Indian construction costs (CPWD/DSR rates)
- Calculate amount = qty × rate for each item
- Calculate totalValue as sum of all amounts
- Set lineItems to the count of BOQ items
- If the drawing is unclear, set accuracy to "Low" and make reasonable assumptions
- Return ONLY the JSON object, no additional text"""

    try:
        start_time = time.time()

        message = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        processing_time = round(time.time() - start_time, 2)

        # Extract response text
        response_text = message.content[0].text

        # Try to parse JSON from response
        # Sometimes Claude might wrap JSON in markdown code blocks
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        boq_data = json.loads(response_text)

        # Add processing time to response
        boq_data['processingTime'] = processing_time

        # Ensure all required fields exist
        if 'projectName' not in boq_data:
            boq_data['projectName'] = 'Construction Project'
        if 'projectType' not in boq_data:
            boq_data['projectType'] = 'General Construction'
        if 'accuracy' not in boq_data:
            boq_data['accuracy'] = 'Medium'
        if 'boqItems' not in boq_data:
            boq_data['boqItems'] = []

        # Calculate totals
        total_value = sum(item.get('amount', 0) for item in boq_data['boqItems'])
        boq_data['totalValue'] = round(total_value, 2)
        boq_data['lineItems'] = len(boq_data['boqItems'])

        return boq_data

    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse Claude response as JSON: {str(e)}\nResponse: {response_text[:500]}")
    except Exception as e:
        raise Exception(f"Claude API error: {str(e)}")


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'api_initialized': anthropic_client is not None
    })


@app.route('/api/process-drawing', methods=['POST'])
def process_drawing():
    """
    Main endpoint to process PDF drawings
    Accepts PDF upload, extracts text, and generates BOQ using Claude
    """
    try:
        # Validate file upload
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # Extract text from PDF
        print(f"Extracting text from {filename}...")
        pdf_text, num_pages = extract_text_from_pdf(filepath)

        if not pdf_text.strip():
            return jsonify({
                'error': 'No text could be extracted from the PDF. The file might be image-based or corrupted.'
            }), 400

        print(f"Extracted {len(pdf_text)} characters from {num_pages} pages")

        # Analyze with Claude API
        print(f"Sending to Claude API for analysis...")
        boq_data = analyze_with_claude(pdf_text, filename)

        print(f"BOQ generated successfully: {boq_data['lineItems']} items, Total: ₹{boq_data['totalValue']:,.2f}")

        # Cleanup: remove uploaded file
        try:
            os.remove(filepath)
        except:
            pass

        return jsonify(boq_data), 200

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error processing drawing: {error_trace}")
        return jsonify({
            'error': str(e),
            'details': 'An error occurred while processing the drawing'
        }), 500


@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify API is working"""
    return jsonify({
        'message': 'TakeoffAI API is running',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("TakeoffAI Backend Server")
    print("=" * 80)
    print(f"\nServer starting on http://localhost:5000")
    print(f"API Endpoint: POST http://localhost:5000/api/process-drawing")
    print(f"CORS enabled for: http://localhost:3000")

    if not anthropic_api_key:
        print("\n⚠️  WARNING: ANTHROPIC_API_KEY not set!")
        print("Set it in your environment or .env file")
    else:
        print("\n✓ Anthropic API key configured")

    print("\nPress Ctrl+C to stop")
    print("=" * 80 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
