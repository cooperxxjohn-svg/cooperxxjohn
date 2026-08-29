"""
PHASE 1: Download and Extract Public BOQ Data
Downloads publicly available BOQ documents and extracts line items
"""

import os
import requests
import time
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Public BOQ sources found via web search
PUBLIC_BOQ_SOURCES = [
    {
        'name': 'MCGM_Civil_BOQ',
        'url': 'https://www.mcgm.gov.in/irj/go/km/docs/documents/Tenders/ETH/ETH_7000013952_Civil%20BOQ.pdf',
        'source': 'MCGM Mumbai',
        'type': 'pdf'
    },
    {
        'name': 'GSHP_BOQ',
        'url': 'https://gshp2.gov.in/sites/default/files/tenders/Section%207%20BOQ%2027052013.pdf',
        'source': 'Gujarat State Health Portal',
        'type': 'pdf'
    },
    {
        'name': 'Nepal_Polytechnic_Civil',
        'url': 'https://www.mea.gov.in/Portal/Tender/2556_1/2_2._BOQ.pdf',
        'source': 'MEA India',
        'type': 'pdf'
    },
    {
        'name': 'NIELIT_Campus_BOQ',
        'url': 'https://www.nielit.gov.in/sites/default/files/agartal_volI3.pdf',
        'source': 'NIELIT Agartala',
        'type': 'pdf'
    },
    {
        'name': 'BITM_BOQ',
        'url': 'https://bitm.gov.in/wp-content/uploads/2020/09/BOQ.pdf',
        'source': 'BITM',
        'type': 'pdf'
    },
    {
        'name': 'IITB_COPT_BOQ',
        'url': 'https://www.iitb.ac.in/deanpl/tenders/coptb/d2.pdf',
        'source': 'IIT Bombay',
        'type': 'pdf'
    },
]

def download_file(url, output_path, timeout=30):
    """Download file with retry logic"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        print(f"  Downloading: {url}")
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            file_size = os.path.getsize(output_path) / 1024  # KB
            print(f"  ✓ Downloaded: {file_size:.1f} KB")
            return True
        else:
            print(f"  ✗ Failed: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def download_all_sources():
    """Download all public BOQ sources"""
    os.makedirs('raw_data', exist_ok=True)

    print("=" * 80)
    print("PHASE 1: DOWNLOADING PUBLIC BOQ DATA")
    print("=" * 80)

    results = []

    for i, source in enumerate(PUBLIC_BOQ_SOURCES, 1):
        print(f"\n[{i}/{len(PUBLIC_BOQ_SOURCES)}] {source['name']}")
        print(f"  Source: {source['source']}")

        filename = f"{source['name']}.{source['type']}"
        output_path = os.path.join('raw_data', filename)

        success = download_file(source['url'], output_path)

        results.append({
            'name': source['name'],
            'source': source['source'],
            'url': source['url'],
            'downloaded': success,
            'file_path': output_path if success else None
        })

        time.sleep(2)  # Be nice to servers

    # Save download log
    df = pd.DataFrame(results)
    df.to_csv('raw_data/download_log.csv', index=False)

    print("\n" + "=" * 80)
    print("DOWNLOAD SUMMARY")
    print("=" * 80)
    print(f"Total sources: {len(results)}")
    print(f"Successful: {sum(r['downloaded'] for r in results)}")
    print(f"Failed: {sum(not r['downloaded'] for r in results)}")
    print(f"\nDownload log saved to: raw_data/download_log.csv")

    return results

if __name__ == '__main__':
    results = download_all_sources()
