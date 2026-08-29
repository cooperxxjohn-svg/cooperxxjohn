"""
PHASE 2: Clean and Normalize BOQ Line Items
Standardizes text, removes noise, handles abbreviations
"""

import re
import pandas as pd
from collections import Counter

# Construction abbreviation mappings
CONSTRUCTION_ABBREVS = {
    r'\brcc\b': 'reinforced cement concrete',
    r'\bpcc\b': 'plain cement concrete',
    r'\bpsc\b': 'pre-stressed concrete',
    r'\bmsrm\b': 'mild steel reinforcement bars',
    r'\btmt\b': 'thermo mechanically treated',
    r'\bhysd\b': 'high yield strength deformed',
    r'\bhdpe\b': 'high density polyethylene',
    r'\bcpvc\b': 'chlorinated polyvinyl chloride',
    r'\bupvc\b': 'unplasticized polyvinyl chloride',
    r'\bgalv\b': 'galvanized',
    r'\bgi\b': 'galvanized iron',
    r'\bms\b': 'mild steel',
    r'\bss\b': 'stainless steel',
    r'\bac\b': 'asbestos cement',
    r'\bfrp\b': 'fiber reinforced plastic',
    r'\bgrp\b': 'glass reinforced plastic',
    r'\bwbm\b': 'water bound macadam',
    r'\bgst\b': 'goods and services tax',

    # Units
    r'\bsqm\b': 'square meter',
    r'\bsqft\b': 'square feet',
    r'\bsq\.m\b': 'square meter',
    r'\bsq m\b': 'square meter',
    r'\bcum\b': 'cubic meter',
    r'\brmt\b': 'running meter',
    r'\brm\b': 'running meter',
    r'\bmt\b': 'meter',
    r'\bmtr\b': 'meter',
    r'\bm\b(?![a-z])': 'meter',
    r'\bmm\b': 'millimeter',
    r'\bcm\b': 'centimeter',
    r'\bkg\b': 'kilogram',
    r'\bton\b': 'metric ton',
    r'\bmpa\b': 'megapascal',
    r'\bdia\b': 'diameter',
    r'\bthk\b': 'thickness',
    r'\bno\.': 'number',
    r'\bnos\.': 'number',
}

def clean_text(text):
    """Clean and normalize text"""
    if pd.isna(text):
        return ""

    text = str(text)

    # Lowercase
    text = text.lower()

    # Remove special characters but keep spaces and alphanumeric
    text = re.sub(r'[^\w\s\.]', ' ', text)

    # Expand abbreviations
    for abbrev, full in CONSTRUCTION_ABBREVS.items():
        text = re.sub(abbrev, full, text, flags=re.IGNORECASE)

    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove very short words (likely noise)
    words = text.split()
    words = [w for w in words if len(w) > 1 or w.isdigit()]
    text = ' '.join(words)

    return text.strip()

def is_duplicate_or_noise(text):
    """Detect duplicates and noise"""
    if len(text) < 20:
        return True

    # Check if mostly numbers
    digit_ratio = sum(c.isdigit() for c in text) / len(text)
    if digit_ratio > 0.7:
        return True

    return False

def clean_dataset():
    """Clean the raw BOQ dataset"""
    print("=" * 80)
    print("PHASE 2: CLEANING AND NORMALIZING DATA")
    print("=" * 80)

    # Load raw data
    df = pd.read_csv('data/boq_items_raw.csv')
    print(f"\nRaw items: {len(df)}")

    # Clean descriptions
    print("\n[1/4] Cleaning text...")
    df['description_cleaned'] = df['description'].apply(clean_text)

    # Remove noise
    print("[2/4] Removing noise...")
    df = df[~df['description_cleaned'].apply(is_duplicate_or_noise)]
    print(f"  After removing noise: {len(df)}")

    # Remove duplicates
    print("[3/4] Removing duplicates...")
    before = len(df)
    df = df.drop_duplicates(subset=['description_cleaned'])
    after = len(df)
    print(f"  Removed {before - after} duplicates: {after} items remain")

    # Filter minimum length
    print("[4/4] Filtering by length...")
    df = df[df['description_cleaned'].str.len() >= 30]
    print(f"  After filtering: {len(df)}")

    # Save cleaned dataset
    output_cols = ['id', 'description', 'description_cleaned', 'source', 'page']
    df = df[output_cols]

    output_path = 'data/boq_items.csv'
    df.to_csv(output_path, index=False)

    print("\n" + "=" * 80)
    print("CLEANING SUMMARY")
    print("=" * 80)
    print(f"Final cleaned items: {len(df)}")
    print(f"Sources: {df['source'].nunique()}")
    print(f"\nItems per source:")
    print(df['source'].value_counts())

    # Most common words
    print("\n" + "=" * 80)
    print("TOP 30 CONSTRUCTION TERMS")
    print("=" * 80)

    all_words = []
    for desc in df['description_cleaned']:
        all_words.extend(desc.split())

    # Filter stopwords
    stopwords = {'of', 'and', 'the', 'in', 'to', 'for', 'with', 'as', 'per', 'or', 'at', 'on', 'by', 'from'}
    all_words = [w for w in all_words if w not in stopwords and len(w) > 3]

    word_counts = Counter(all_words)
    for i, (word, count) in enumerate(word_counts.most_common(30), 1):
        print(f"{i:2d}. {word:25s} ({count:4d})")

    print(f"\nCleaned dataset saved to: {output_path}")

    # Sample
    print("\n" + "=" * 80)
    print("SAMPLE CLEANED ITEMS (first 5)")
    print("=" * 80)
    for idx, row in df.head(5).iterrows():
        print(f"\n{idx+1}. [{row['source']}]")
        print(f"   Original: {row['description'][:80]}...")
        print(f"   Cleaned:  {row['description_cleaned'][:80]}...")

    return df

if __name__ == '__main__':
    df = clean_dataset()
