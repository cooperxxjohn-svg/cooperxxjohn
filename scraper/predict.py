"""
BOQ Line Item Classifier - Prediction CLI
Usage: python predict.py input.csv output.csv
"""

import sys
import pandas as pd
import pickle
import json
from pathlib import Path

def load_model():
    """Load trained classifier"""
    model_path = 'artifacts/boq_classifier.pkl'

    if not Path(model_path).exists():
        print(f"ERROR: Model not found at {model_path}")
        print("Please run train_classifier.py first")
        sys.exit(1)

    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    return model

def predict_items(model, descriptions):
    """Predict categories for descriptions"""
    # Get predictions
    predictions = model.predict(descriptions)

    # Get probabilities
    try:
        proba = model.predict_proba(descriptions)
        confidences = proba.max(axis=1)
    except:
        confidences = [1.0] * len(descriptions)

    return predictions, confidences

def main():
    """Main CLI"""
    if len(sys.argv) != 3:
        print("Usage: python predict.py input.csv output.csv")
        print()
        print("Input CSV should have a 'description' column")
        print("Output CSV will have 'category' and 'confidence' columns added")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    print("=" * 80)
    print("BOQ LINE ITEM CLASSIFIER")
    print("=" * 80)

    # Load model
    print("\n[1/3] Loading model...")
    model = load_model()
    print("  ✓ Model loaded")

    # Load input
    print(f"\n[2/3] Loading input: {input_path}")
    if not Path(input_path).exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    df = pd.read_csv(input_path)

    if 'description' not in df.columns:
        print("ERROR: Input CSV must have a 'description' column")
        sys.exit(1)

    print(f"  Items to classify: {len(df)}")

    # Predict
    print("\n[3/3] Classifying items...")
    predictions, confidences = predict_items(model, df['description'])

    df['category'] = predictions
    df['confidence'] = confidences

    # Save output
    df.to_csv(output_path, index=False)

    print(f"\n✓ Results saved to: {output_path}")

    # Summary
    print("\n" + "=" * 80)
    print("CLASSIFICATION SUMMARY")
    print("=" * 80)
    print(f"Total items: {len(df)}")
    print(f"\nItems per category:")
    print(df['category'].value_counts())
    print(f"\nAverage confidence: {df['confidence'].mean():.3f}")

    # Show sample
    print("\n" + "=" * 80)
    print("SAMPLE PREDICTIONS (first 5)")
    print("=" * 80)
    for idx, row in df.head(5).iterrows():
        print(f"\n{idx+1}. {row['description'][:70]}...")
        print(f"   → {row['category'].upper()} (confidence: {row['confidence']:.3f})")

if __name__ == '__main__':
    main()
