from database import Database
from export_generator import ExportGenerator
from pathlib import Path

print("Testing exports...")

db = Database()
projects = db.get_all_projects()
project = projects[0]
rooms = db.get_project_rooms(project['id'])

output_dir = Path("../out")
output_dir.mkdir(exist_ok=True)

exporter = ExportGenerator()

# Excel
excel_path = output_dir / "demo_export.xlsx"
exporter.generate_excel(project, rooms, excel_path)
print(f"Excel: {excel_path} ({excel_path.stat().st_size} bytes)")

# PDF  
pdf_path = output_dir / "demo_proposal.pdf"
exporter.generate_pdf(project, rooms, pdf_path)
print(f"PDF: {pdf_path} ({pdf_path.stat().st_size} bytes)")

print("✓ Export test complete")
