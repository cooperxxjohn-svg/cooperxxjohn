"""
Flask Web Application for BOQ Estimation System
Production-ready web interface for contractors to upload drawings and generate BOQ estimates
"""

import os
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from decimal import Decimal
import json
import tempfile
import shutil

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    jsonify,
    session
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import secrets

# Import BOQ estimation system
from boq_estimator import BOQEstimator, quick_estimate
from boq_schema import ContractDetails, BOQDocument
from boq_validator import CPWDValidator
from config import BOQConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = Path('uploads')
app.config['OUTPUT_FOLDER'] = Path('outputs')
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Create necessary directories
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
app.config['OUTPUT_FOLDER'].mkdir(exist_ok=True)

# Check for API key
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    logger.warning("ANTHROPIC_API_KEY not found in environment variables")


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def cleanup_old_files(directory: Path, max_age_hours: int = 24):
    """Remove files older than max_age_hours from directory"""
    try:
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        for file_path in directory.glob('*'):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                logger.info(f"Cleaned up old file: {file_path}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


def generate_job_id() -> str:
    """Generate unique job ID"""
    return f"BOQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(4)}"


def export_to_csv(boq_doc: BOQDocument, output_path: Path) -> Path:
    """Export BOQ document to CSV format"""
    csv_path = output_path.with_suffix('.csv')

    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Header information
        writer.writerow(['BOQ Estimate'])
        writer.writerow(['Project Name:', boq_doc.contract.contract_name])
        writer.writerow(['Location:', boq_doc.contract.location])
        writer.writerow(['Department:', boq_doc.contract.department])
        writer.writerow(['Generated:', boq_doc.created_date.strftime('%Y-%m-%d %H:%M')])
        writer.writerow([])

        # Column headers
        writer.writerow([
            'Item No.',
            'Description',
            'Category',
            'Unit',
            'Quantity',
            'Rate (₹)',
            'Amount (₹)',
            'Location',
            'Drawing Ref'
        ])

        # BOQ items
        for section in boq_doc.sections:
            writer.writerow([])
            writer.writerow([f'Section {section.section_no}:', section.title])

            for item in section.items:
                writer.writerow([
                    item.item_no,
                    item.description,
                    item.category.value if item.category else '',
                    item.unit.value if item.unit else '',
                    f"{float(item.quantity):.2f}" if item.quantity else '',
                    f"{float(item.unit_rate):.2f}" if item.unit_rate else '',
                    f"{float(item.total_amount):.2f}" if item.total_amount else '',
                    item.location or '',
                    item.drawing_reference or ''
                ])

        # Summary
        writer.writerow([])
        writer.writerow(['Summary'])
        writer.writerow(['Total Amount (₹):', f"{float(boq_doc.total_amount):.2f}"])

        if boq_doc.gst_percentage:
            gst_amount = float(boq_doc.total_amount) * float(boq_doc.gst_percentage) / 100
            writer.writerow([f'GST ({boq_doc.gst_percentage}%):', f"{gst_amount:.2f}"])
            writer.writerow(['Grand Total (₹):', f"{float(boq_doc.total_amount) + gst_amount:.2f}"])

    return csv_path


def export_to_pdf(boq_doc: BOQDocument, output_path: Path) -> Path:
    """Export BOQ document to PDF format using ReportLab"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        logger.error("ReportLab not installed. Installing via CSV export fallback.")
        # Fallback to CSV if ReportLab not available
        return export_to_csv(boq_doc, output_path)

    pdf_path = output_path.with_suffix('.pdf')
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=landscape(A4),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=0.5*inch
    )

    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#2c5282'),
        spaceAfter=12
    )

    # Title
    elements.append(Paragraph("Bill of Quantities (BOQ) Estimate", title_style))
    elements.append(Spacer(1, 0.2*inch))

    # Contract Details Table
    contract_data = [
        ['Project Name:', boq_doc.contract.contract_name],
        ['Location:', boq_doc.contract.location],
        ['Department:', boq_doc.contract.department],
        ['Client:', boq_doc.contract.client or 'N/A'],
        ['Generated:', boq_doc.created_date.strftime('%Y-%m-%d %H:%M')],
    ]

    contract_table = Table(contract_data, colWidths=[2*inch, 5*inch])
    contract_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a202c')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))

    elements.append(contract_table)
    elements.append(Spacer(1, 0.3*inch))

    # BOQ Items
    for section in boq_doc.sections:
        elements.append(Paragraph(f"Section {section.section_no}: {section.title}", heading_style))

        # Table headers
        table_data = [[
            'Item No.',
            'Description',
            'Unit',
            'Quantity',
            'Rate (₹)',
            'Amount (₹)'
        ]]

        # Add items
        for item in section.items:
            table_data.append([
                item.item_no,
                Paragraph(item.description[:80] + '...' if len(item.description) > 80 else item.description, styles['Normal']),
                item.unit.value if item.unit else '',
                f"{float(item.quantity):.2f}" if item.quantity else '',
                f"{float(item.unit_rate):.2f}" if item.unit_rate else '',
                f"{float(item.total_amount):.2f}" if item.total_amount else ''
            ])

        # Create table
        item_table = Table(table_data, colWidths=[0.8*inch, 3.5*inch, 0.6*inch, 0.9*inch, 0.9*inch, 1.1*inch])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))

        elements.append(item_table)
        elements.append(Spacer(1, 0.2*inch))

    # Summary
    elements.append(Spacer(1, 0.2*inch))
    total_amount = float(boq_doc.total_amount)

    summary_data = [
        ['Subtotal:', f"₹ {total_amount:,.2f}"]
    ]

    if boq_doc.gst_percentage:
        gst_amount = total_amount * float(boq_doc.gst_percentage) / 100
        summary_data.append([f'GST ({boq_doc.gst_percentage}%):', f"₹ {gst_amount:,.2f}"])
        summary_data.append(['Grand Total:', f"₹ {(total_amount + gst_amount):,.2f}"])

    summary_table = Table(summary_data, colWidths=[6*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#2c5282')),
    ]))

    elements.append(summary_table)

    # Build PDF
    doc.build(elements)
    return pdf_path


@app.route('/')
def index():
    """Render home page with upload form"""
    # Cleanup old files on each page load
    cleanup_old_files(app.config['UPLOAD_FOLDER'])
    cleanup_old_files(app.config['OUTPUT_FOLDER'])

    return render_template('index.html')


@app.route('/estimate', methods=['POST'])
def create_estimate():
    """Handle BOQ estimation request"""
    try:
        # Validate API key
        if not ANTHROPIC_API_KEY:
            flash('System configuration error: API key not configured', 'error')
            return redirect(url_for('index'))

        # Validate file upload
        if 'drawings' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('index'))

        files = request.files.getlist('drawings')
        if not files or files[0].filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('index'))

        # Validate contract details
        project_name = request.form.get('project_name', '').strip()
        location = request.form.get('location', '').strip()

        if not project_name or not location:
            flash('Project name and location are required', 'error')
            return redirect(url_for('index'))

        # Generate job ID
        job_id = generate_job_id()
        job_dir = app.config['UPLOAD_FOLDER'] / job_id
        job_dir.mkdir(exist_ok=True)

        # Save uploaded files
        drawing_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = job_dir / filename
                file.save(file_path)
                drawing_paths.append(str(file_path))
                logger.info(f"Saved file: {file_path}")

        if not drawing_paths:
            flash('No valid PDF files uploaded', 'error')
            shutil.rmtree(job_dir)
            return redirect(url_for('index'))

        # Create contract details
        contract = ContractDetails(
            contract_name=project_name,
            contract_no=request.form.get('contract_no', '').strip() or None,
            department=request.form.get('department', 'CPWD').strip(),
            location=location,
            client=request.form.get('client', '').strip() or None,
            tender_date=datetime.now() if request.form.get('tender_date') else None,
            completion_period_days=int(request.form.get('completion_days', 365)),
            estimated_cost=Decimal(request.form.get('estimated_cost', 0)) if request.form.get('estimated_cost') else None,
            contract_value=None
        )

        # Output directory for this job
        output_dir = app.config['OUTPUT_FOLDER'] / job_id
        output_dir.mkdir(exist_ok=True)

        # Run BOQ estimation
        logger.info(f"Starting BOQ estimation for job {job_id}")
        estimator = BOQEstimator(
            anthropic_api_key=ANTHROPIC_API_KEY,
            enable_logging=True
        )

        boq_doc = estimator.estimate_from_drawings(
            drawing_paths=drawing_paths,
            contract_details=contract,
            output_dir=output_dir,
            merge_duplicates=True,
            validate=True
        )

        logger.info(f"BOQ estimation completed for job {job_id}")

        # Validate BOQ
        validator = CPWDValidator()
        is_valid, validation_results = validator.validate_document(boq_doc)

        # Store validation results
        validation_summary = {
            'is_valid': is_valid,
            'total_issues': len(validation_results),
            'errors': [r for r in validation_results if r.severity == 'error'],
            'warnings': [r for r in validation_results if r.severity == 'warning'],
            'info': [r for r in validation_results if r.severity == 'info']
        }

        # Save BOQ to session
        session['job_id'] = job_id
        session['boq_data'] = boq_doc.dict()
        session['validation'] = {
            'is_valid': validation_summary['is_valid'],
            'total_issues': validation_summary['total_issues'],
            'errors': [{'category': r.category, 'message': r.message, 'severity': r.severity} for r in validation_summary['errors']],
            'warnings': [{'category': r.category, 'message': r.message, 'severity': r.severity} for r in validation_summary['warnings']],
            'info': [{'category': r.category, 'message': r.message, 'severity': r.severity} for r in validation_summary['info']]
        }

        return redirect(url_for('results'))

    except RequestEntityTooLarge:
        flash('File too large. Maximum size is 50MB', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error during estimation: {e}", exc_info=True)
        flash(f'Error processing request: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/results')
def results():
    """Display BOQ estimation results"""
    try:
        job_id = session.get('job_id')
        boq_data = session.get('boq_data')
        validation = session.get('validation')

        if not job_id or not boq_data:
            flash('No estimation results available', 'error')
            return redirect(url_for('index'))

        # Reconstruct BOQ document
        boq_doc = BOQDocument(**boq_data)

        # Calculate summary by category
        category_summary = {}
        for section in boq_doc.sections:
            for item in section.items:
                if item.category:
                    cat = item.category.value
                    if cat not in category_summary:
                        category_summary[cat] = {
                            'quantity': 0,
                            'amount': Decimal(0)
                        }
                    category_summary[cat]['amount'] += item.total_amount or Decimal(0)

        return render_template(
            'results.html',
            job_id=job_id,
            boq=boq_doc,
            validation=validation,
            category_summary=category_summary
        )

    except Exception as e:
        logger.error(f"Error displaying results: {e}", exc_info=True)
        flash(f'Error displaying results: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/download/<format>')
def download(format: str):
    """Download BOQ in specified format (csv, pdf, json, excel)"""
    try:
        job_id = session.get('job_id')
        boq_data = session.get('boq_data')

        if not job_id or not boq_data:
            flash('No estimation results available', 'error')
            return redirect(url_for('index'))

        boq_doc = BOQDocument(**boq_data)
        output_dir = app.config['OUTPUT_FOLDER'] / job_id

        # Sanitize project name for filename
        safe_project_name = "".join(c for c in boq_doc.contract.contract_name if c.isalnum() or c in (' ', '-', '_')).strip()
        base_filename = f"BOQ_{safe_project_name}_{job_id}"

        if format == 'csv':
            csv_path = export_to_csv(boq_doc, output_dir / base_filename)
            return send_file(
                csv_path,
                as_attachment=True,
                download_name=f"{base_filename}.csv",
                mimetype='text/csv'
            )

        elif format == 'pdf':
            pdf_path = export_to_pdf(boq_doc, output_dir / base_filename)
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f"{base_filename}.pdf",
                mimetype='application/pdf'
            )

        elif format == 'json':
            json_path = output_dir / f"{base_filename}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(boq_doc.dict(), f, indent=2, default=str)
            return send_file(
                json_path,
                as_attachment=True,
                download_name=f"{base_filename}.json",
                mimetype='application/json'
            )

        elif format == 'excel':
            excel_path = output_dir / f"{boq_doc.boq_id}.xlsx"
            if not excel_path.exists():
                # Generate Excel if not already created
                from boq_estimator import BOQEstimator
                estimator = BOQEstimator(anthropic_api_key=ANTHROPIC_API_KEY)
                estimator.export_to_excel(boq_doc, excel_path)

            return send_file(
                excel_path,
                as_attachment=True,
                download_name=f"{base_filename}.xlsx",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        else:
            flash('Invalid download format', 'error')
            return redirect(url_for('results'))

    except Exception as e:
        logger.error(f"Error during download: {e}", exc_info=True)
        flash(f'Error generating download: {str(e)}', 'error')
        return redirect(url_for('results'))


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'api_key_configured': bool(ANTHROPIC_API_KEY)
    })


@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('error.html', error_code=404, error_message="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return render_template('error.html', error_code=500, error_message="Internal server error"), 500


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    """Handle file too large errors"""
    flash('File too large. Maximum size is 50MB', 'error')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    )
