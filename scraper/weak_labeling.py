"""
PHASE 3: Weak Labeling Using Keyword-Based Rules
Creates labels without human annotation
"""

import pandas as pd
import numpy as np
from collections import defaultdict

# Define categories and their keywords
CATEGORY_KEYWORDS = {
    'demolition': [
        'demolish', 'demolition', 'removing', 'removal', 'dismantling',
        'breaking', 'dismember', 'razed', 'tear down', 'wreck'
    ],
    'earthwork': [
        'excavation', 'excavate', 'earth', 'soil', 'filling', 'backfill',
        'trenching', 'cutting', 'leveling', 'grading', 'compaction'
    ],
    'concrete': [
        'concrete', 'cement concrete', 'rcc', 'pcc', 'reinforced cement concrete',
        'plain cement concrete', 'lean concrete', 'grade concrete', 'm10', 'm15', 'm20', 'm25', 'm30'
    ],
    'masonry': [
        'brick', 'masonry', 'block work', 'brickwork', 'stone masonry',
        'hollow block', 'solid block', 'cement block'
    ],
    'steel': [
        'reinforcement', 'steel reinforcement', 'tmt', 'hysd', 'mild steel bars',
        'steel bars', 'rebar', 'structural steel', 'steel frame'
    ],
    'carpentry_joinery': [
        'wood', 'wooden', 'timber', 'carpentry', 'joinery', 'teak',
        'plywood', 'particle board', 'mdf', 'laminate'
    ],
    'doors_windows_glazing': [
        'door', 'window', 'glass', 'glazing', 'shutter', 'frame',
        'aluminum window', 'upvc door', 'wooden door', 'paneled door'
    ],
    'waterproofing': [
        'waterproof', 'damp', 'membrane', 'bitumen', 'torch on',
        'app membrane', 'sealant', 'moisture barrier'
    ],
    'flooring_tiling': [
        'tile', 'tiling', 'flooring', 'floor finish', 'vitrified',
        'ceramic', 'marble', 'granite', 'mosaic', 'terrazzo'
    ],
    'plaster_painting': [
        'plaster', 'plastering', 'paint', 'painting', 'finish',
        'cement plaster', 'gypsum plaster', 'enamel', 'emulsion', 'whitewash', 'putty'
    ],
    'plumbing_sanitary': [
        'plumbing', 'sanitary', 'pipe', 'drainage', 'sewer', 'water supply',
        'wc', 'wash basin', 'sink', 'tap', 'faucet', 'cpvc', 'upvc', 'hdpe pipe'
    ],
    'electrical': [
        'electrical', 'wiring', 'conduit', 'cable', 'switch', 'socket',
        'mcb', 'db', 'distribution board', 'light', 'lighting', 'fan'
    ],
    'hvac_fire': [
        'hvac', 'air conditioning', 'ventilation', 'fire alarm', 'fire fighting',
        'sprinkler', 'smoke detector', 'fire extinguisher', 'ahu', 'vrf'
    ],
    'facade_cladding': [
        'facade', 'cladding', 'acp', 'aluminum composite panel', 'curtain wall',
        'exterior wall', 'veneer', 'elevation'
    ],
    'roofing': [
        'roof', 'roofing', 'rcc roof', 'slab', 'terrace', 'roof slab',
        'waterproofing roof', 'parapet', 'chajja'
    ],
    'paving_external': [
        'paving', 'pavement', 'pathway', 'driveway', 'paver', 'cobble',
        'interlocking', 'compound wall', 'boundary wall', 'gate'
    ],
    'utilities_storm_sanitary': [
        'manhole', 'chamber', 'septic tank', 'soak pit', 'sump',
        'overhead tank', 'gully trap', 'inspection chamber'
    ],
    'misc_general_conditions': [
        'testing', 'quality', 'survey', 'layout', 'site clearance',
        'temporary', 'scaffolding', 'centering', 'shuttering', 'formwork'
    ]
}

def score_text_for_category(text, category_keywords):
    """Score how well text matches a category"""
    if not text:
        return 0.0

    text_lower = text.lower()
    matches = sum(1 for kw in category_keywords if kw in text_lower)

    # Normalize by keyword count
    score = matches / len(category_keywords)
    return min(score * 10, 1.0)  # Scale up but cap at 1.0

def label_with_confidence(text):
    """Label text with all categories and confidence scores"""
    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = score_text_for_category(text, keywords)
        scores[category] = score

    # Get top category
    top_category = max(scores, key=scores.get)
    top_confidence = scores[top_category]

    return top_category, top_confidence, scores

def apply_weak_labels():
    """Apply weak labeling to dataset"""
    print("=" * 80)
    print("PHASE 3: WEAK LABELING")
    print("=" * 80)

    # Load cleaned data
    df = pd.read_csv('data/boq_items.csv')
    print(f"\nItems to label: {len(df)}")

    print("\n[1/2] Applying labeling functions...")
    results = []
    for idx, row in df.iterrows():
        category, confidence, all_scores = label_with_confidence(row['description_cleaned'])

        results.append({
            'id': row['id'],
            'description': row['description'],
            'description_cleaned': row['description_cleaned'],
            'source': row['source'],
            'category': category,
            'confidence': confidence,
            **{f'score_{cat}': score for cat, score in all_scores.items()}
        })

        if (idx + 1) % 1000 == 0:
            print(f"  Processed {idx + 1}/{len(df)}")

    df_labeled = pd.DataFrame(results)

    print("\n[2/2] Filtering low-confidence labels...")
    before = len(df_labeled)
    # Keep only items with confidence > 0.1
    df_labeled = df_labeled[df_labeled['confidence'] > 0.1]
    after = len(df_labeled)
    print(f"  Removed {before - after} low-confidence items")
    print(f"  Remaining: {after}")

    # Save labeled dataset
    output_path = 'data/boq_items_labeled.csv'
    df_labeled.to_csv(output_path, index=False)

    print("\n" + "=" * 80)
    print("LABELING SUMMARY")
    print("=" * 80)
    print(f"Labeled items: {len(df_labeled)}")
    print(f"\nItems per category:")
    print(df_labeled['category'].value_counts())

    print(f"\nAverage confidence per category:")
    avg_conf = df_labeled.groupby('category')['confidence'].mean().sort_values(ascending=False)
    for cat, conf in avg_conf.items():
        print(f"  {cat:30s}: {conf:.3f}")

    print(f"\nLabeled dataset saved to: {output_path}")

    # Show examples from each category
    print("\n" + "=" * 80)
    print("SAMPLE ITEMS PER CATEGORY (top 2 each)")
    print("=" * 80)

    for category in sorted(df_labeled['category'].unique()):
        category_items = df_labeled[df_labeled['category'] == category].nlargest(2, 'confidence')

        print(f"\n{category.upper().replace('_', ' ')}")
        print("-" * 80)

        for idx, row in category_items.iterrows():
            print(f"  Confidence: {row['confidence']:.3f}")
            print(f"  {row['description_cleaned'][:90]}...")

    return df_labeled

if __name__ == '__main__':
    df_labeled = apply_weak_labels()
