"""
Simple Flask Web Interface for BOQ Estimation
Single-file application with embedded HTML templates
"""

import os
import csv
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from decimal import Decimal

from flask import Flask, request, render_template_string, send_file, session, redirect, url_for, flash
from werkzeug.utils import secure_filename

# Import BOQ estimation system
from boq_estimator import BOQEstimator
from boq_schema import ContractDetails

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['UPLOAD_FOLDER'] = Path('temp_uploads')
app.config['OUTPUT_FOLDER'] = Path('temp_outputs')

# Create directories
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
app.config['OUTPUT_FOLDER'].mkdir(exist_ok=True)

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

# ============================================================================
# HTML TEMPLATES (Embedded)
# ============================================================================

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BOQ Estimation - AI Powered</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        primary: '#2563eb',
                        secondary: '#10b981',
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
        <!-- Header -->
        <div class="text-center mb-12">
            <h1 class="text-5xl font-bold text-gray-900 mb-4">
                BOQ Estimation System
            </h1>
            <p class="text-xl text-gray-600">
                AI-powered Bill of Quantities generation for construction projects
            </p>
            <div class="mt-4 inline-flex items-center px-4 py-2 bg-green-100 rounded-full">
                <span class="text-green-800 font-semibold">✓ CPWD Compliant</span>
            </div>
        </div>

        <!-- Flash Messages -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                <div class="mb-6 p-4 rounded-lg {% if category == 'error' %}bg-red-100 border-l-4 border-red-500 text-red-700{% else %}bg-green-100 border-l-4 border-green-500 text-green-700{% endif %}">
                    {{ message }}
                </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <!-- Upload Form -->
        <div class="bg-white rounded-2xl shadow-2xl p-8 mb-8">
            <form method="POST" action="/generate" enctype="multipart/form-data" id="uploadForm">
                <!-- Step 1: Upload Drawing -->
                <div class="mb-8">
                    <div class="flex items-center mb-4">
                        <div class="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-bold mr-3">1</div>
                        <h2 class="text-2xl font-bold text-gray-900">Upload Construction Drawing</h2>
                    </div>
                    <div class="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-primary transition-colors cursor-pointer" id="dropZone">
                        <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                            <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <label for="drawing" class="cursor-pointer">
                            <span class="text-primary font-semibold">Click to upload</span>
                            <span class="text-gray-600"> or drag and drop</span>
                        </label>
                        <p class="text-sm text-gray-500 mt-2">PDF files only (Max 50MB)</p>
                        <input type="file" name="drawing" id="drawing" accept=".pdf" required class="hidden">
                    </div>
                    <div id="fileName" class="mt-4 text-sm text-gray-600 hidden"></div>
                </div>

                <!-- Step 2: Project Details -->
                <div class="mb-8">
                    <div class="flex items-center mb-4">
                        <div class="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-bold mr-3">2</div>
                        <h2 class="text-2xl font-bold text-gray-900">Enter Project Details</h2>
                    </div>
                    <div class="grid md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">Project Name *</label>
                            <input type="text" name="project_name" required
                                   class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                   placeholder="e.g., Government Office Building">
                        </div>
                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">Location *</label>
                            <input type="text" name="location" required
                                   class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                   placeholder="e.g., New Delhi">
                        </div>
                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">Department</label>
                            <input type="text" name="department" value="CPWD"
                                   class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent">
                        </div>
                        <div>
                            <label class="block text-sm font-semibold text-gray-700 mb-2">Contract Number</label>
                            <input type="text" name="contract_no"
                                   class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                   placeholder="Optional">
                        </div>
                    </div>
                </div>

                <!-- Submit Button -->
                <button type="submit" id="submitBtn"
                        class="w-full bg-gradient-to-r from-primary to-blue-600 text-white font-bold py-4 rounded-xl hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200">
                    <span id="btnText">🚀 Generate BOQ Estimate</span>
                    <span id="btnLoading" class="hidden">⏳ Processing... (2-3 minutes)</span>
                </button>
            </form>
        </div>

        <!-- Features -->
        <div class="grid md:grid-cols-3 gap-6">
            <div class="bg-white rounded-xl p-6 shadow-lg">
                <div class="text-3xl mb-3">🤖</div>
                <h3 class="font-bold text-gray-900 mb-2">AI-Powered</h3>
                <p class="text-gray-600 text-sm">Claude Vision AI extracts quantities from drawings</p>
            </div>
            <div class="bg-white rounded-xl p-6 shadow-lg">
                <div class="text-3xl mb-3">⚡</div>
                <h3 class="font-bold text-gray-900 mb-2">Lightning Fast</h3>
                <p class="text-gray-600 text-sm">Generate complete BOQ in 2-3 minutes</p>
            </div>
            <div class="bg-white rounded-xl p-6 shadow-lg">
                <div class="text-3xl mb-3">✓</div>
                <h3 class="font-bold text-gray-900 mb-2">CPWD Compliant</h3>
                <p class="text-gray-600 text-sm">Automatic validation against standards</p>
            </div>
        </div>
    </div>

    <script>
        // File upload handling
        const fileInput = document.getElementById('drawing');
        const dropZone = document.getElementById('dropZone');
        const fileName = document.getElementById('fileName');
        const form = document.getElementById('uploadForm');
        const submitBtn = document.getElementById('submitBtn');
        const btnText = document.getElementById('btnText');
        const btnLoading = document.getElementById('btnLoading');

        dropZone.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                fileName.textContent = '📄 ' + e.target.files[0].name;
                fileName.classList.remove('hidden');
            }
        });

        // Drag and drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('border-primary', 'bg-blue-50');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('border-primary', 'bg-blue-50');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('border-primary', 'bg-blue-50');
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                fileName.textContent = '📄 ' + e.dataTransfer.files[0].name;
                fileName.classList.remove('hidden');
            }
        });

        // Form submission
        form.addEventListener('submit', () => {
            submitBtn.disabled = true;
            btnText.classList.add('hidden');
            btnLoading.classList.remove('hidden');
        });
    </script>
</body>
</html>
"""

RESULTS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BOQ Results - {{ boq.contract.contract_name }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="mb-8">
            <a href="/" class="text-primary hover:underline mb-4 inline-block">← Create New Estimate</a>
            <h1 class="text-4xl font-bold text-gray-900 mb-2">{{ boq.contract.contract_name }}</h1>
            <div class="flex items-center space-x-4 text-gray-600">
                <span>📍 {{ boq.contract.location }}</span>
                <span>🏛️ {{ boq.contract.department }}</span>
                <span>🆔 {{ boq.boq_id }}</span>
            </div>
        </div>

        <!-- Summary Cards -->
        <div class="grid md:grid-cols-3 gap-6 mb-8">
            <div class="bg-white rounded-xl p-6 shadow-lg">
                <div class="text-sm text-gray-600 mb-2">Total Estimated Cost</div>
                <div class="text-3xl font-bold text-primary">₹ {{ "{:,.2f}".format(boq.total_amount|float) }}</div>
                {% if boq.gst_percentage %}
                <div class="text-sm text-gray-500 mt-2">+ GST @ {{ boq.gst_percentage }}%</div>
                {% endif %}
            </div>
            <div class="bg-white rounded-xl p-6 shadow-lg">
                <div class="text-sm text-gray-600 mb-2">Total Items</div>
                <div class="text-3xl font-bold text-gray-900">{{ total_items }}</div>
            </div>
            <div class="bg-white rounded-xl p-6 shadow-lg">
                <div class="text-sm text-gray-600 mb-2">Validation Status</div>
                <div class="text-2xl font-bold {% if validation.is_valid %}text-green-600{% else %}text-yellow-600{% endif %}">
                    {% if validation.is_valid %}✓ Compliant{% else %}⚠️ {{ validation.total_issues }} Issues{% endif %}
                </div>
            </div>
        </div>

        <!-- Download Button -->
        <div class="bg-white rounded-xl p-6 shadow-lg mb-8">
            <h2 class="text-xl font-bold text-gray-900 mb-4">Download BOQ</h2>
            <div class="flex gap-4">
                <a href="/download/csv" class="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold inline-flex items-center">
                    📊 Download CSV
                </a>
                <a href="/download/excel" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold inline-flex items-center">
                    📑 Download Excel
                </a>
                <a href="/download/pdf" class="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-semibold inline-flex items-center">
                    📄 Download PDF
                </a>
            </div>
        </div>

        <!-- BOQ Table -->
        <div class="bg-white rounded-xl shadow-lg overflow-hidden">
            <div class="px-6 py-4 bg-gradient-to-r from-primary to-blue-600">
                <h2 class="text-2xl font-bold text-white">Bill of Quantities</h2>
            </div>

            {% for section in boq.sections %}
            <div class="border-b border-gray-200 last:border-b-0">
                <div class="px-6 py-4 bg-gray-50">
                    <h3 class="text-xl font-bold text-gray-900">Section {{ section.section_no }}: {{ section.title }}</h3>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full">
                        <thead class="bg-gray-100">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Item No.</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Description</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Unit</th>
                                <th class="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Quantity</th>
                                <th class="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Rate (₹)</th>
                                <th class="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Amount (₹)</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-200">
                            {% for item in section.items %}
                            <tr class="hover:bg-gray-50">
                                <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ item.item_no }}</td>
                                <td class="px-4 py-3 text-sm text-gray-900">
                                    {{ item.description }}
                                    {% if item.specification %}
                                    <div class="text-xs text-gray-500 mt-1">{{ item.specification }}</div>
                                    {% endif %}
                                </td>
                                <td class="px-4 py-3 text-sm text-gray-700">{{ item.unit.value if item.unit else '-' }}</td>
                                <td class="px-4 py-3 text-sm text-right text-gray-900">{{ "{:,.2f}".format(item.quantity|float) if item.quantity else '-' }}</td>
                                <td class="px-4 py-3 text-sm text-right text-gray-900">{{ "{:,.2f}".format(item.unit_rate|float) if item.unit_rate else '-' }}</td>
                                <td class="px-4 py-3 text-sm text-right font-semibold text-gray-900">{{ "{:,.2f}".format(item.total_amount|float) if item.total_amount else '-' }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                        <tfoot class="bg-gray-100">
                            <tr>
                                <td colspan="5" class="px-4 py-3 text-right font-bold text-gray-900">Section Total:</td>
                                <td class="px-4 py-3 text-right font-bold text-gray-900">
                                    ₹ {{ "{:,.2f}".format(section.items|sum(attribute='total_amount')|float) }}
                                </td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
            </div>
            {% endfor %}

            <!-- Grand Total -->
            <div class="px-6 py-6 bg-gradient-to-r from-gray-100 to-gray-200">
                <div class="flex justify-between items-center text-2xl font-bold">
                    <span class="text-gray-900">Grand Total:</span>
                    <span class="text-primary">₹ {{ "{:,.2f}".format(boq.total_amount|float) }}</span>
                </div>
                {% if boq.gst_percentage %}
                <div class="flex justify-between items-center text-lg text-gray-700 mt-2">
                    <span>GST ({{ boq.gst_percentage }}%):</span>
                    <span>₹ {{ "{:,.2f}".format((boq.total_amount|float) * (boq.gst_percentage|float / 100)) }}</span>
                </div>
                <div class="flex justify-between items-center text-2xl font-bold text-primary mt-2">
                    <span>Total with GST:</span>
                    <span>₹ {{ "{:,.2f}".format((boq.total_amount|float) * (1 + boq.gst_percentage|float / 100)) }}</span>
                </div>
                {% endif %}
            </div>
        </div>

        <!-- Back Button -->
        <div class="mt-8 text-center">
            <a href="/" class="bg-gray-600 hover:bg-gray-700 text-white px-8 py-3 rounded-lg font-semibold inline-block">
                Create Another Estimate
            </a>
        </div>
    </div>
</body>
</html>
"""

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Render upload page"""
    return render_template_string(INDEX_HTML)


@app.route('/generate', methods=['POST'])
def generate_boq():
    """Generate BOQ from uploaded drawing"""
    try:
        # Validate API key
        if not ANTHROPIC_API_KEY:
            flash('System configuration error: API key not configured', 'error')
            return redirect(url_for('index'))

        # Validate file
        if 'drawing' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('index'))

        file = request.files['drawing']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('index'))

        if not file.filename.lower().endswith('.pdf'):
            flash('Only PDF files are supported', 'error')
            return redirect(url_for('index'))

        # Get form data
        project_name = request.form.get('project_name', '').strip()
        location = request.form.get('location', '').strip()

        if not project_name or not location:
            flash('Project name and location are required', 'error')
            return redirect(url_for('index'))

        # Save uploaded file
        job_id = f"BOQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        job_dir = app.config['UPLOAD_FOLDER'] / job_id
        job_dir.mkdir(exist_ok=True)

        filename = secure_filename(file.filename)
        file_path = job_dir / filename
        file.save(file_path)

        # Create contract details
        contract = ContractDetails(
            contract_name=project_name,
            contract_no=request.form.get('contract_no', '').strip() or None,
            department=request.form.get('department', 'CPWD').strip(),
            location=location,
            client=None,
            tender_date=None,
            completion_period_days=365,
            estimated_cost=None,
            contract_value=None
        )

        # Output directory
        output_dir = app.config['OUTPUT_FOLDER'] / job_id
        output_dir.mkdir(exist_ok=True)

        # Run BOQ estimation
        estimator = BOQEstimator(
            anthropic_api_key=ANTHROPIC_API_KEY,
            enable_logging=True
        )

        boq_doc = estimator.estimate_from_drawings(
            drawing_paths=[str(file_path)],
            contract_details=contract,
            output_dir=output_dir,
            merge_duplicates=True,
            validate=True
        )

        # Validate
        from boq_validator import CPWDValidator
        validator = CPWDValidator()
        is_valid, validation_results = validator.validate_document(boq_doc)

        # Store in session
        session['job_id'] = job_id
        session['boq_data'] = boq_doc.dict()
        session['validation'] = {
            'is_valid': is_valid,
            'total_issues': len(validation_results),
            'errors': [{'category': r.category, 'message': r.message, 'severity': r.severity}
                      for r in validation_results if r.severity == 'error'],
            'warnings': [{'category': r.category, 'message': r.message, 'severity': r.severity}
                        for r in validation_results if r.severity == 'warning'],
        }

        return redirect(url_for('results'))

    except Exception as e:
        flash(f'Error generating BOQ: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/results')
def results():
    """Display BOQ results"""
    boq_data = session.get('boq_data')
    validation = session.get('validation')

    if not boq_data:
        flash('No BOQ data available', 'error')
        return redirect(url_for('index'))

    from boq_schema import BOQDocument
    boq = BOQDocument(**boq_data)

    # Calculate total items
    total_items = sum(len(section.items) for section in boq.sections)

    return render_template_string(
        RESULTS_HTML,
        boq=boq,
        validation=validation,
        total_items=total_items
    )


@app.route('/download/<format>')
def download(format: str):
    """Download BOQ in specified format"""
    try:
        job_id = session.get('job_id')
        boq_data = session.get('boq_data')

        if not job_id or not boq_data:
            flash('No BOQ data available', 'error')
            return redirect(url_for('index'))

        from boq_schema import BOQDocument
        boq = BOQDocument(**boq_data)
        output_dir = app.config['OUTPUT_FOLDER'] / job_id

        # Sanitize filename
        safe_name = "".join(c for c in boq.contract.contract_name if c.isalnum() or c in (' ', '-', '_')).strip()
        base_filename = f"BOQ_{safe_name}_{job_id}"

        if format == 'csv':
            csv_path = output_dir / f"{base_filename}.csv"
            export_to_csv(boq, csv_path)
            return send_file(csv_path, as_attachment=True, download_name=f"{base_filename}.csv")

        elif format == 'excel':
            excel_path = output_dir / f"{boq.boq_id}.xlsx"
            if not excel_path.exists():
                estimator = BOQEstimator(anthropic_api_key=ANTHROPIC_API_KEY)
                estimator.export_to_excel(boq, excel_path)
            return send_file(excel_path, as_attachment=True, download_name=f"{base_filename}.xlsx")

        elif format == 'pdf':
            # Use the web_app.py export_to_pdf function
            from web_app import export_to_pdf
            pdf_path = export_to_pdf(boq, output_dir / base_filename)
            return send_file(pdf_path, as_attachment=True, download_name=f"{base_filename}.pdf")

        else:
            flash('Invalid download format', 'error')
            return redirect(url_for('results'))

    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('results'))


def export_to_csv(boq_doc, output_path: Path) -> Path:
    """Export BOQ to CSV"""
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Header
        writer.writerow(['BOQ Estimate'])
        writer.writerow(['Project:', boq_doc.contract.contract_name])
        writer.writerow(['Location:', boq_doc.contract.location])
        writer.writerow(['Department:', boq_doc.contract.department])
        writer.writerow(['Generated:', boq_doc.created_date.strftime('%Y-%m-%d %H:%M')])
        writer.writerow([])

        # Column headers
        writer.writerow(['Item No.', 'Description', 'Unit', 'Quantity', 'Rate (₹)', 'Amount (₹)'])

        # Items
        for section in boq_doc.sections:
            writer.writerow([])
            writer.writerow([f'Section {section.section_no}:', section.title])

            for item in section.items:
                writer.writerow([
                    item.item_no,
                    item.description,
                    item.unit.value if item.unit else '',
                    f"{float(item.quantity):.2f}" if item.quantity else '',
                    f"{float(item.unit_rate):.2f}" if item.unit_rate else '',
                    f"{float(item.total_amount):.2f}" if item.total_amount else ''
                ])

        # Total
        writer.writerow([])
        writer.writerow(['Total:', '', '', '', '', f"{float(boq_doc.total_amount):.2f}"])

    return output_path


@app.route('/health')
def health():
    """Health check"""
    return {'status': 'ok', 'api_configured': bool(ANTHROPIC_API_KEY)}


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8000)),
        debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    )
