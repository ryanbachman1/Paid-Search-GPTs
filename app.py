import streamlit as st
import pandas as pd
from io import BytesIO
from rapidfuzz import fuzz

st.title("Negative Keyword Mapping Tool")

# User inputs
advertiser_name = st.text_input("Enter Advertiser Name")
advertiser_brand = st.text_input("Enter Advertiser Brand")
advertiser_market = st.text_input("Enter Advertiser Market")
uploaded_file = st.file_uploader("Upload Search Terms File (.xlsx or .csv)", type=["xlsx", "csv"])

# Adjustable threshold
threshold = st.slider("Fuzzy Match Threshold", min_value=50, max_value=100, value=80, step=1)

# File format toggle
export_format = st.radio("Download Format", options=["Excel (.xlsx)", "CSV (.csv)"])

# Scoring and labeling
def label_confidence(score):
    if score >= 90:
        return "High Relevance"
    elif score >= 80:
        return "Medium Relevance"
    else:
        return "Low Relevance"

# Scoring logic
def score_and_flag(df, advertiser_name, brand, market, threshold):
    df.columns = [col.strip().lower() for col in df.columns]
    if 'search_term' not in df.columns:
        raise ValueError("File must contain a 'search_term' column.")

    advertiser_name = advertiser_name.lower()
    brand = brand.lower()
    market = market.lower()
    full_brand_market = f"{brand} {market}"

    scores, labels = [], []

    for term in df['search_term']:
        term = str(term).lower()
        score_name = fuzz.token_set_ratio(term, advertiser_name)
        score_combo = fuzz.token_set_ratio(term, full_brand_market)
        score = max(score_name, score_combo)
        scores.append(score)
        labels.append(label_confidence(score))

    df['fuzzy_score'] = scores
    df['confidence'] = labels

    # Filter for negatives
    negatives = df[df['fuzzy_score'] < threshold]

    return df[['search_term', 'fuzzy_score', 'confidence']], negatives

# Excel and CSV output
def generate_file(df, format):
    output = BytesIO()
    if format == "Excel (.xlsx)":
        df.to_excel(output, index=False, engine='openpyxl')
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"
    else:
        df.to_csv(output, index=False)
        mime = "text/csv"
        ext = "csv"
    output.seek(0)
    return output, mime, ext

# Run app
if advertiser_name and advertiser_brand and advertiser_market and uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    try:
        full_df, flagged_df = score_and_flag(df, advertiser_name, advertiser_brand, advertiser_market, threshold)

        st.subheader("📉 Negative Keyword Recommendations")
        st.success(f"{len(flagged_df)} terms flagged as negative (Low Relevance)")
        st.dataframe(flagged_df)

        # Full file
        full_data, mime, ext = generate_file(full_df, export_format)
        st.download_button(
            label=f"📥 Download Full Scored Report ({ext})",
            data=full_data,
            file_name=f"full_scored_keywords.{ext}",
            mime=mime
        )

        # Negative keywords only
        negative_data, mime, ext = generate_file(flagged_df, export_format)
        st.download_button(
            label=f"📥 Download Negative Keyword List ({ext})",
            data=negative_data,
            file_name=f"negative_keywords.{ext}",
            mime=mime
        )

    except ValueError as e:
        st.error(str(e))
