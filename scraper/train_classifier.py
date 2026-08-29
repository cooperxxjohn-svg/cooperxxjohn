"""
PHASE 4: Train BOQ Classifier
TF-IDF + Linear SVM for categorization
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import json

def train_classifier():
    """Train TF-IDF + SVM classifier"""
    print("=" * 80)
    print("PHASE 4: TRAINING BOQ CLASSIFIER")
    print("=" * 80)

    # Load labeled data
    df = pd.read_csv('data/boq_items_labeled.csv')
    print(f"\nTraining data: {len(df)} items")
    print(f"Categories: {df['category'].nunique()}")

    # Prepare data
    X = df['description_cleaned']
    y = df['category']

    print("\n[1/5] Splitting train/test...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"  Train: {len(X_train)} items")
    print(f"  Test:  {len(X_test)} items")

    # Build pipeline
    print("\n[2/5] Building TF-IDF + SVM pipeline...")
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),  # unigrams, bigrams, trigrams
            min_df=2,
            max_df=0.9,
            sublinear_tf=True
        )),
        ('clf', SGDClassifier(
            loss='hinge',  # Linear SVM
            penalty='l2',
            alpha=1e-4,
            max_iter=100,
            random_state=42,
            class_weight='balanced'  # Handle class imbalance
        ))
    ])

    # Train
    print("\n[3/5] Training classifier...")
    pipeline.fit(X_train, y_train)
    print("  ✓ Training complete")

    # Evaluate on test set
    print("\n[4/5] Evaluating on test set...")
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"  Test Accuracy: {accuracy:.3f}")

    # Cross-validation
    print("\n[5/5] Cross-validation (5-fold)...")
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')
    print(f"  CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")

    # Detailed classification report
    print("\n" + "=" * 80)
    print("CLASSIFICATION REPORT")
    print("=" * 80)
    print(classification_report(y_test, y_pred, zero_division=0))

    # Save model
    artifacts_dir = 'artifacts'
    import os
    os.makedirs(artifacts_dir, exist_ok=True)

    model_path = f'{artifacts_dir}/boq_classifier.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(pipeline, f)
    print(f"\n✓ Model saved to: {model_path}")

    # Save category mappings
    categories = sorted(df['category'].unique())
    categories_path = f'{artifacts_dir}/categories.json'
    with open(categories_path, 'w') as f:
        json.dump(categories, f, indent=2)
    print(f"✓ Categories saved to: {categories_path}")

    # Save metadata
    metadata = {
        'train_size': len(X_train),
        'test_size': len(X_test),
        'num_categories': len(categories),
        'categories': categories,
        'test_accuracy': float(accuracy),
        'cv_accuracy_mean': float(cv_scores.mean()),
        'cv_accuracy_std': float(cv_scores.std())
    }

    metadata_path = f'{artifacts_dir}/model_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Metadata saved to: {metadata_path}")

    # Analyze feature importance (top keywords per category)
    print("\n" + "=" * 80)
    print("TOP 10 KEYWORDS PER CATEGORY")
    print("=" * 80)

    vectorizer = pipeline.named_steps['tfidf']
    classifier = pipeline.named_steps['clf']

    feature_names = np.array(vectorizer.get_feature_names_out())

    keywords_by_category = {}

    for i, category in enumerate(classifier.classes_):
        # Get coefficients for this category
        coef = classifier.coef_[i]
        top_indices = np.argsort(coef)[-10:][::-1]
        top_keywords = feature_names[top_indices].tolist()

        keywords_by_category[category] = top_keywords

        print(f"\n{category.upper().replace('_', ' ')}:")
        print(f"  {', '.join(top_keywords)}")

    # Save keywords
    keywords_path = f'{artifacts_dir}/keywords_by_category.json'
    with open(keywords_path, 'w') as f:
        json.dump(keywords_by_category, f, indent=2)
    print(f"\n✓ Keywords saved to: {keywords_path}")

    print("\n" + "=" * 80)
    print("TRAINING COMPLETE!")
    print("=" * 80)
    print(f"Model: {model_path}")
    print(f"Accuracy: {accuracy:.1%}")
    print(f"Categories: {len(categories)}")

    return pipeline, metadata

if __name__ == '__main__':
    pipeline, metadata = train_classifier()
