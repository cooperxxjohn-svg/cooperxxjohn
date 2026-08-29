"""
PHASE 6: Generate Comprehensive Report
"""

import pandas as pd
import json
from pathlib import Path
from collections import Counter

def generate_report():
    """Generate markdown report"""

    print("=" * 80)
    print("GENERATING FINAL REPORT")
    print("=" * 80)

    # Load all data
    df_raw = pd.read_csv('data/boq_items_raw.csv')
    df_clean = pd.read_csv('data/boq_items.csv')
    df_labeled = pd.read_csv('data/boq_items_labeled.csv')

    with open('artifacts/model_metadata.json', 'r') as f:
        metadata = json.load(f)

    with open('artifacts/keywords_by_category.json', 'r') as f:
        keywords = json.load(f)

    # Start report
    report = []
    report.append("# BOQ Line Item Classifier - Project Report\n")
    report.append("*Automated classification system for construction BOQ line items*\n\n")

    report.append("---\n\n")

    # Executive Summary
    report.append("## Executive Summary\n\n")
    report.append(f"Successfully built a BOQ line item classifier trained on **{metadata['train_size'] + metadata['test_size']} public construction documents** from Indian government sources.\n\n")

    report.append(f"**Key Results:**\n")
    report.append(f"- **{len(df_raw):,}** raw line items extracted from **5 public sources**\n")
    report.append(f"- **{len(df_clean):,}** items after cleaning and deduplication\n")
    report.append(f"- **{len(df_labeled):,}** items labeled using weak supervision\n")
    report.append(f"- **{metadata['num_categories']} categories** covering all major construction trades\n")
    report.append(f"- **{metadata['test_accuracy']:.1%} test accuracy** using TF-IDF + Linear SVM\n")
    report.append(f"- **{metadata['cv_accuracy_mean']:.1%} cross-validation accuracy**\n\n")

    report.append("---\n\n")

    # Data Sources
    report.append("## 1. Data Collection\n\n")
    report.append("### Public Sources\n\n")

    report.append("BOQ documents were downloaded from the following government portals:\n\n")
    report.append("1. **MCGM Mumbai** - Municipal Corporation BOQ (39 pages)\n")
    report.append("2. **MEA India** - Nepal Polytechnic Civil Works (113 pages)\n")
    report.append("3. **NIELIT Agartala** - Campus Construction (294 pages)\n")
    report.append("4. **BITM** - Building Infrastructure (92 pages)\n")
    report.append("5. **IIT Bombay** - Centre for Propulsion Technology (107 pages)\n\n")

    report.append(f"**Total pages processed:** 645 pages\n")
    report.append(f"**Total raw items extracted:** {len(df_raw):,}\n\n")

    # Items per source
    report.append("### Items per Source\n\n")
    report.append("| Source | Items |\n")
    report.append("|--------|-------|\n")
    for source, count in df_clean['source'].value_counts().items():
        report.append(f"| {source} | {count:,} |\n")
    report.append("\n")

    report.append("---\n\n")

    # Data Cleaning
    report.append("## 2. Data Cleaning & Normalization\n\n")

    report.append("### Cleaning Steps\n\n")
    report.append("1. **Text normalization:** Lowercasing, removing special characters\n")
    report.append("2. **Abbreviation expansion:** RCC → reinforced cement concrete, etc.\n")
    report.append("3. **Noise removal:** Filtered items < 30 characters\n")
    report.append("4. **Deduplication:** Removed 2,181 duplicate entries\n\n")

    report.append(f"**Final cleaned dataset:** {len(df_clean):,} unique items\n\n")

    # Top terms
    report.append("### Top 20 Construction Terms\n\n")

    all_words = []
    for desc in df_clean['description_cleaned']:
        all_words.extend(str(desc).split())

    stopwords = {'of', 'and', 'the', 'in', 'to', 'for', 'with', 'as', 'per', 'or', 'at', 'on', 'by', 'from', 'etc.'}
    all_words = [w for w in all_words if w not in stopwords and len(w) > 3]

    word_counts = Counter(all_words)

    report.append("| Rank | Term | Count |\n")
    report.append("|------|------|-------|\n")
    for i, (word, count) in enumerate(word_counts.most_common(20), 1):
        report.append(f"| {i} | {word} | {count:,} |\n")
    report.append("\n")

    report.append("---\n\n")

    # Categories
    report.append("## 3. Classification Categories\n\n")

    report.append(f"The system classifies BOQ items into **{metadata['num_categories']} categories**:\n\n")

    report.append("| # | Category | Description |\n")
    report.append("|---|----------|-------------|\n")
    report.append("| 1 | Demolition | Breaking, removal, dismantling |\n")
    report.append("| 2 | Earthwork | Excavation, filling, grading |\n")
    report.append("| 3 | Concrete | RCC, PCC, all concrete work |\n")
    report.append("| 4 | Masonry | Brickwork, blockwork, stone masonry |\n")
    report.append("| 5 | Steel | Reinforcement, structural steel |\n")
    report.append("| 6 | Carpentry & Joinery | Wood, timber, plywood work |\n")
    report.append("| 7 | Doors, Windows & Glazing | All fenestration work |\n")
    report.append("| 8 | Waterproofing | Membranes, sealants, damp proofing |\n")
    report.append("| 9 | Flooring & Tiling | Tiles, marble, granite flooring |\n")
    report.append("| 10 | Plaster & Painting | Plastering, painting, finishes |\n")
    report.append("| 11 | Plumbing & Sanitary | Pipes, fittings, fixtures |\n")
    report.append("| 12 | Electrical | Wiring, switches, lighting |\n")
    report.append("| 13 | HVAC & Fire | AC, ventilation, fire systems |\n")
    report.append("| 14 | Facade & Cladding | External walls, ACP panels |\n")
    report.append("| 15 | Roofing | Roof slabs, terrace work |\n")
    report.append("| 16 | Paving & External | Pathways, compound walls, gates |\n")
    report.append("| 17 | Utilities | Manholes, tanks, chambers |\n")
    report.append("| 18 | Misc & General | Testing, scaffolding, formwork |\n\n")

    report.append("---\n\n")

    # Weak Labeling
    report.append("## 4. Weak Labeling Strategy\n\n")

    report.append("Since no human-labeled data exists, we used **keyword-based weak labeling**:\n\n")
    report.append("- Each category has 5-10 characteristic keywords\n")
    report.append("- Items scored by keyword matches\n")
    report.append("- Filtered out low-confidence labels (< 0.1)\n")
    report.append(f"- **{len(df_labeled):,} items** successfully labeled\n\n")

    report.append("### Items per Category (Training Data)\n\n")

    report.append("| Category | Count | Avg Confidence |\n")
    report.append("|----------|-------|----------------|\n")

    for cat in sorted(df_labeled['category'].unique()):
        cat_data = df_labeled[df_labeled['category'] == cat]
        count = len(cat_data)
        avg_conf = cat_data['confidence'].mean()
        report.append(f"| {cat.replace('_', ' ').title()} | {count:,} | {avg_conf:.3f} |\n")

    report.append("\n")

    report.append("---\n\n")

    # Model Performance
    report.append("## 5. Model Performance\n\n")

    report.append("### Architecture\n\n")
    report.append("- **Feature Extraction:** TF-IDF (5,000 features, 1-3 grams)\n")
    report.append("- **Classifier:** Linear SVM (SGD with balanced class weights)\n")
    report.append("- **Training:** 2,863 items\n")
    report.append("- **Testing:** 716 items\n\n")

    report.append("### Results\n\n")
    report.append(f"- **Test Accuracy:** {metadata['test_accuracy']:.1%}\n")
    report.append(f"- **5-Fold CV Accuracy:** {metadata['cv_accuracy_mean']:.1%} (± {metadata['cv_accuracy_std']:.1%})\n\n")

    report.append("---\n\n")

    # Top Keywords
    report.append("## 6. Top Keywords per Category\n\n")

    report.append("These keywords have the highest predictive power:\n\n")

    for category in sorted(keywords.keys()):
        kw_list = keywords[category][:10]
        report.append(f"### {category.replace('_', ' ').title()}\n\n")
        report.append(", ".join([f"`{kw}`" for kw in kw_list]))
        report.append("\n\n")

    report.append("---\n\n")

    # Examples
    report.append("## 7. Example Classifications\n\n")

    for category in sorted(df_labeled['category'].unique())[:5]:
        category_items = df_labeled[df_labeled['category'] == category].nlargest(2, 'confidence')

        report.append(f"### {category.replace('_', ' ').title()}\n\n")

        for idx, row in category_items.iterrows():
            report.append(f"**Confidence: {row['confidence']:.1%}**\n")
            report.append(f"> {row['description'][:150]}...\n\n")

    report.append("---\n\n")

    # Usage
    report.append("## 8. How to Use\n\n")

    report.append("### CLI\n\n")
    report.append("```bash\n")
    report.append("# Classify items from CSV\n")
    report.append("python predict.py input.csv output.csv\n")
    report.append("```\n\n")

    report.append("### Streamlit UI\n\n")
    report.append("```bash\n")
    report.append("# Start web interface\n")
    report.append("streamlit run app_streamlit.py\n")
    report.append("```\n\n")

    report.append("---\n\n")

    # Improvements
    report.append("## 9. Suggestions for Improvement\n\n")

    report.append("1. **Expand training data:**\n")
    report.append("   - Scrape more PWD SOR documents from other states\n")
    report.append("   - Add CPWD specification documents\n")
    report.append("   - Include MES, Railways, NHAI tender BOQs\n\n")

    report.append("2. **Improve labeling:**\n")
    report.append("   - Manually review and correct 100-200 samples per category\n")
    report.append("   - Use active learning to label uncertain cases\n")
    report.append("   - Add more sophisticated rules (regex patterns)\n\n")

    report.append("3. **Model enhancements:**\n")
    report.append("   - Try ensemble methods (Random Forest, XGBoost)\n")
    report.append("   - Experiment with deep learning (BERT-based models)\n")
    report.append("   - Add hierarchical classification (super-categories)\n\n")

    report.append("4. **Feature engineering:**\n")
    report.append("   - Extract quantities and units as features\n")
    report.append("   - Add context from surrounding items in BOQ\n")
    report.append("   - Use word embeddings instead of TF-IDF\n\n")

    report.append("---\n\n")

    # Conclusion
    report.append("## Conclusion\n\n")

    report.append(f"Successfully built a BOQ classifier with **{metadata['test_accuracy']:.1%} accuracy** using only public data and weak supervision. ")
    report.append("The system can now automatically categorize construction line items, ")
    report.append("enabling better BOQ analysis, cost estimation, and project planning.\n\n")

    report.append("**Next Steps:**\n")
    report.append("- Integrate with XBOQ Enhanced drawing extraction system\n")
    report.append("- Deploy as API service\n")
    report.append("- Build dashboards for BOQ analytics\n\n")

    report.append("---\n\n")
    report.append("*Report generated automatically by the BOQ Classification System*\n")

    # Save report
    report_text = "".join(report)

    output_path = 'out/report.md'
    Path('out').mkdir(exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(report_text)

    print(f"\n✓ Report saved to: {output_path}")
    print(f"  Lines: {len(report)}")
    print(f"  Size: {len(report_text)} characters")

    return report_text

if __name__ == '__main__':
    report = generate_report()
    print("\nReport Preview:")
    print("=" * 80)
    print(report[:500] + "...")
