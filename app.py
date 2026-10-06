import streamlit as st
import pandas as pd
import yaml

# 1. Page Configuration
st.set_page_config(page_title="Conversational Product Recommender", layout="wide")
st.title("🎧 Smart Headphone Recommender")
st.write("Tell us what you're looking for, and we'll match you with the best choices transparently.")

# 2. Load Data and Config
@st.cache_data
def load_data():
    df = pd.read_csv("catalog.csv")
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    return df, config

df_catalog, config = load_data()

# 3. Sidebar Inputs (Conversational preference gathering simulation)
st.sidebar.header("🔍 Your Preferences")
max_budget = st.sidebar.slider("Maximum Budget ($)", 20, 200, 100, 5)
desired_feature = st.sidebar.selectbox("Must-Have Feature", ["None", "wireless", "active noise cancellation", "mic", "wired"])
preferred_brand_keyword = st.sidebar.text_input("Brand/Keyword Preference (Optional)", "")

# 4. Normalization and Filtering Logic
def filter_and_score(df, budget, must_have, keyword):
    # Filter out out-of-stock and over-budget products
    filtered = df[(df['stock_status'] == 'In Stock') & (df['price'] <= budget)].copy()

    if filtered.empty:
        return filtered

    # Filter by must-have feature if selected
    if must_have != "None":
        filtered = filtered[filtered['features'].str.contains(must_have, case=False, na=False)]

    if filtered.empty:
        return filtered

    weights = config['scoring_weights']

    scores = []
    for _, row in filtered.iterrows():
        # Rating score (normalized 0 to 1 based on 5.0 max)
        rating_score = row['rating'] / 5.0

        # Economy score (cheaper relative to budget is higher score)
        economy_score = 1.0 - (row['price'] / budget)

        # Feature match score
        feature_score = 1.0 if (keyword.lower() in row['name'].lower() or keyword.lower() in row['description'].lower()) else 0.5
        if keyword == "":
            feature_score = 1.0

        # Weighted final score
        total_score = (
            weights['rating'] * rating_score +
            weights['price_economy'] * economy_score +
            weights['feature_match'] * feature_score
        )
        scores.append(total_score)

    filtered['score'] = scores
    return filtered.sort_values(by='score', ascending=False)

results = filter_and_score(df_catalog, max_budget, desired_feature, preferred_brand_keyword)

# 5. Presentation Layer (Top 3 Recommendations)
st.subheader("🏆 Top 3 Recommendations for You")

if results.empty:
    st.warning("No products match your exact criteria. Try increasing your budget or changing filters!")
else:
    top_3 = results.head(3)

    cols = st.columns(3)
    for idx, (index, row) in enumerate(top_3.iterrows()):
        with cols[idx]:
            st.markdown(f"### {row['name']}")
            st.metric(label="Price", value=f"${row['price']}")
            st.write(f"**Rating:** ⭐ {row['rating']}/5.0")
            st.write(f"**Features:** {row['features']}")
            st.write(f"**Why it fits:** Matches your budget and features transparently with a match score of `{row['score']:.2f}`.")
            with st.expander("Trade-offs"):
                st.write(f"- Price point: ${row['price']} out of${max_budget} max budget.")
                st.write(f"- Description: {row['description']}")

    # 6. Bonus: Side-by-Side Comparison Card
    st.markdown("---")
    st.subheader("⚖️ Side-by-Side Comparison")
    comparison_df = top_3[['name', 'category', 'price', 'rating', 'features', 'stock_status', 'score']]
    st.dataframe(comparison_df, use_container_width=True)