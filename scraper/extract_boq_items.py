"""
PHASE 1B: Extract BOQ Line Items from Downloaded PDFs
Parses PDF documents and extracts construction line items
"""

import os
import re
import pandas as pd
from PyPDF2 import PdfReader
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def clean_text(text):
    """Clean extracted text"""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', str(text))
    return text.strip()

def is_likely_boq_line(text):
    """Heuristic to identify BOQ line items"""
    if not text or len(text) < 10:
        return False

    # Look for construction keywords
    construction_keywords = [
        'excavation', 'concrete', 'cement', 'steel', 'brick', 'masonry',
        'plaster', 'paint', 'rcc', 'pcc', 'foundation', 'beam', 'column',
        'slab', 'floor', 'wall', 'door', 'window', 'tile', 'waterproof',
        'earthwork', 'filling', 'sand', 'aggregate', 'reinforcement',
        'shuttering', 'centering', 'formwork', 'finishing', 'plastering',
        'whitewash', 'distemper', 'enamel', 'plumbing', 'sanitary',
        'electrical', 'wiring', 'conduit', 'pipe', 'drain', 'sewer',
        'manhole', 'chamber', 'tank', 'pump', 'motor', 'fitting',
        'roofing', 'sheet', 'gutter', 'flashing', 'insulation'
    ]

    text_lower = text.lower()
    return any(kw in text_lower for kw in construction_keywords)

def extract_from_pdf(pdf_path, source_name):
    """Extract BOQ items from a single PDF"""
    items = []

    print(f"\n  Processing: {Path(pdf_path).name}")

    try:
        reader = PdfReader(pdf_path)
        print(f"    Pages: {len(reader.pages)}")

        for page_num, page in enumerate(reader.pages, 1):
            # Extract text
            text = page.extract_text()
            if not text:
                continue

            # Extract from text line by line
            lines = text.split('\n')
            for line_idx, line in enumerate(lines):
                if is_likely_boq_line(line):
                    items.append({
                        'id': f"{source_name}_p{page_num}_l{line_idx}",
                        'description': clean_text(line),
                        'source': source_name,
                        'page': page_num,
                        'extraction_method': 'text'
                    })

        print(f"    Extracted: {len(items)} items")

    except Exception as e:
        print(f"    ✗ Error: {e}")

    return items

def extract_all_pdfs():
    """Extract items from all downloaded PDFs"""
    print("=" * 80)
    print("EXTRACTING BOQ LINE ITEMS FROM PDFs")
    print("=" * 80)

    # Read download log
    download_log = pd.read_csv('raw_data/download_log.csv')
    successful_downloads = download_log[download_log['downloaded'] == True]

    all_items = []

    for idx, row in successful_downloads.iterrows():
        pdf_path = row['file_path']
        if os.path.exists(pdf_path):
            items = extract_from_pdf(pdf_path, row['name'])
            all_items.extend(items)

    # Create DataFrame
    df = pd.DataFrame(all_items)

    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Total items extracted: {len(df)}")
    print(f"Sources processed: {df['source'].nunique()}")
    print(f"\nItems per source:")
    print(df['source'].value_counts())

    # Save raw extracted items
    output_path = 'data/boq_items_raw.csv'
    os.makedirs('data', exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\nRaw items saved to: {output_path}")

    # Show sample
    print("\n" + "=" * 80)
    print("SAMPLE ITEMS (first 10)")
    print("=" * 80)
    for idx, row in df.head(10).iterrows():
        print(f"{idx+1}. [{row['source']}] {row['description'][:80]}...")

    return df

if __name__ == '__main__':
    df = extract_all_pdfs()
