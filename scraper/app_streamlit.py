"""
BOQ Line Item Classifier - Streamlit UI
Usage: streamlit run app_streamlit.py
"""

import streamlit as st
import pandas as pd
import pickle
import json
from pathlib import Path
import io

@st.cache_resource
def load_model():
    """Load trained classifier (cached)"""
    model_path = 'artifacts/boq_classifier.pkl'

    if not Path(model_path).exists():
        st.error(f"Model not found at {model_path}")
        st.error("Please run train_classifier.py first")
        st.stop()

    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    # Load metadata
    with open('artifacts/model_metadata.json', 'r') as f:
        metadata = json.load(f)

    with open('artifacts/keywords_by_category.json', 'r') as f:
        keywords = json.load(f)

    return model, metadata, keywords

def predict_single(model, description):
    """Predict category for single description"""
    prediction = model.predict([description])[0]

    try:
        proba = model.predict_proba([description])[0]
        confidence = proba.max()

        # Get top 3 predictions
        top_indices = proba.argsort()[-3:][::-1]
        top_categories = [model.classes_[i] for i in top_indices]
        top_confidences = [proba[i] for i in top_indices]

        return prediction, confidence, top_categories, top_confidences
    except:
        return prediction, 1.0, [prediction], [1.0]

def main():
    st.set_page_config(
        page_title="BOQ Classifier",
        page_icon="🏗️",
        layout="wide"
    )

    st.title("🏗️ BOQ Line Item Classifier")
    st.markdown("Automatically categorize construction BOQ line items")

    # Load model
    model, metadata, keywords = load_model()

    # Sidebar
    st.sidebar.header("Model Info")
    st.sidebar.metric("Accuracy", f"{metadata['test_accuracy']:.1%}")
    st.sidebar.metric("Categories", metadata['num_categories'])
    st.sidebar.metric("Training Items", metadata['train_size'])

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Categories")
    for cat in sorted(metadata['categories']):
        st.sidebar.markdown(f"• {cat.replace('_', ' ').title()}")

    # Main content
    tab1, tab2, tab3 = st.tabs(["Single Item", "Bulk Upload", "Keywords"])

    # Tab 1: Single item classification
    with tab1:
        st.header("Classify Single Item")

        description = st.text_area(
            "Enter BOQ item description:",
            height=150,
            placeholder="E.g., Providing and laying cement concrete grade M20 in foundation..."
        )

        if st.button("Classify", type="primary"):
            if description.strip():
                prediction, confidence, top_cats, top_confs = predict_single(model, description)

                st.success(f"**Category:** {prediction.replace('_', ' ').upper()}")
                st.info(f"**Confidence:** {confidence:.1%}")

                st.markdown("### Top 3 Predictions")
                for cat, conf in zip(top_cats, top_confs):
                    st.progress(conf, text=f"{cat.replace('_', ' ').title()}: {conf:.1%}")

                # Show keywords
                if prediction in keywords:
                    st.markdown("### Key Terms for this Category")
                    kw_list = keywords[prediction]
                    st.markdown(", ".join([f"`{kw}`" for kw in kw_list[:10]]))

            else:
                st.warning("Please enter a description")

    # Tab 2: Bulk upload
    with tab2:
        st.header("Bulk Classification")

        st.markdown("""
        Upload a CSV file with a `description` column. The system will classify all items.
        """)

        uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])

        if uploaded_file is not None:
            # Read CSV
            df = pd.read_csv(uploaded_file)

            if 'description' not in df.columns:
                st.error("CSV must have a 'description' column")
            else:
                st.success(f"Loaded {len(df)} items")

                if st.button("Classify All", type="primary"):
                    with st.spinner("Classifying..."):
                        # Predict
                        predictions = model.predict(df['description'])

                        try:
                            proba = model.predict_proba(df['description'])
                            confidences = proba.max(axis=1)
                        except:
                            confidences = [1.0] * len(df)

                        df['category'] = predictions
                        df['confidence'] = confidences

                    st.success("Classification complete!")

                    # Summary
                    st.markdown("### Summary")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("Total Items", len(df))
                        st.metric("Avg Confidence", f"{df['confidence'].mean():.1%}")

                    with col2:
                        st.markdown("**Items per Category:**")
                        st.dataframe(
                            df['category'].value_counts().reset_index(),
                            hide_index=True,
                            use_container_width=True
                        )

                    # Show results
                    st.markdown("### Results")
                    st.dataframe(df, use_container_width=True)

                    # Download button
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_str = csv_buffer.getvalue()

                    st.download_button(
                        label="📥 Download Results CSV",
                        data=csv_str,
                        file_name="boq_classified.csv",
                        mime="text/csv"
                    )

    # Tab 3: Keywords by category
    with tab3:
        st.header("Top Keywords by Category")

        category = st.selectbox(
            "Select category:",
            options=sorted(keywords.keys()),
            format_func=lambda x: x.replace('_', ' ').title()
        )

        if category:
            kw_list = keywords[category]

            st.markdown(f"### {category.replace('_', ' ').title()}")
            st.markdown("Top 10 keywords that indicate this category:")

            # Display as tags
            cols = st.columns(5)
            for i, kw in enumerate(kw_list[:10]):
                with cols[i % 5]:
                    st.markdown(f"`{kw}`")

if __name__ == '__main__':
    main()
