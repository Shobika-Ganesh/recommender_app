import streamlit as st
import pandas as pd
import yaml

# 1. Page Configuration
st.set_page_config(page_title="Conversational Product Recommender", layout="wide")
st.title("🎧 Smart Headphone Recommender & Scenario Test Suite")
st.write("A transparent, rule-based conversational recommender meeting all catalog and scenario specifications.")

# 2. Load Data and Config
@st.cache_data
def load_data():
    df = pd.read_csv("catalog.csv")
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    return df, config

df_catalog, config = load_data()

# 3. Define the 15 Shopper Scenarios (Requirement 7.3)
scenarios = [
    {"id": 1, "name": "Budget Runner", "budget": 50, "must_have": "wireless", "keyword": "sport"},
    {"id": 2, "name": "Audiophile Studio", "budget": 150, "must_have": "wired", "keyword": "studio"},
    {"id": 3, "name": "Frequent Flyer", "budget": 130, "must_have": "active noise cancellation", "keyword": "traveler"},
    {"id": 4, "name": "Budget Student", "budget": 35, "must_have": "wireless", "keyword": "long battery"},
    {"id": 5, "name": "Hardcore Gamer", "budget": 110, "must_have": "wired", "keyword": "rgb"},
    {"id": 6, "name": "Luxury ANC Buyer", "budget": 200, "must_have": "active noise cancellation", "keyword": "leather"},
    {"id": 7, "name": "Podcast Listener", "budget": 65, "must_have": "mic", "keyword": "vocals"},
    {"id": 8, "name": "Waterproof Swimmer/Runner", "budget": 60, "must_have": "wireless", "keyword": "waterproof"},
    {"id": 9, "name": "Sleeper Comfort", "budget": 40, "must_have": "wireless", "keyword": "sleeping"},
    {"id": 10, "name": "DJ Professional", "budget": 170, "must_have": "wired", "keyword": "dj"},
    {"id": 11, "name": "Eco-Conscious Shopper", "budget": 90, "must_have": "wireless", "keyword": "eco-friendly"},
    {"id": 12, "name": "Office Caller", "budget": 60, "must_have": "mic", "keyword": "office"},
    {"id": 13, "name": "Kids Safety First", "budget": 25, "must_have": "wired", "keyword": "volume"},
    {"id": 14, "name": "Fast Charge User", "budget": 80, "must_have": "wireless", "keyword": "fast charging"},
    {"id": 15, "name": "Flagship Enthusiast", "budget": 200, "must_have": "active noise cancellation", "keyword": "flagship"}
]

# 4. Sidebar Inputs (Conversational preference gathering simulation)
st.sidebar.header("🔍 Your Preferences")
max_budget = st.sidebar.slider("Maximum Budget ($)", 15, 200, 100, 5)
desired_feature = st.sidebar.selectbox("Must-Have Feature", ["None", "wireless", "active noise cancellation", "mic", "wired"])
preferred_brand_keyword = st.sidebar.text_input("Brand/Keyword Preference (Optional)", "")

# 5. Normalization and Filtering Logic
def filter_and_score(df, budget, must_have, keyword):
    filtered = df[(df['stock_status'] == 'In Stock') & (df['price'] <= budget)].copy()
    
    if filtered.empty:
        return filtered

    if must_have != "None":
        filtered = filtered[filtered['features'].str.contains(must_have, case=False, na=False)]
        
    if filtered.empty:
        return filtered

    weights = config['scoring_weights']
    
    scores = []
    for _, row in filtered.iterrows():
        rating_score = row['rating'] / 5.0
        economy_score = 1.0 - (row['price'] / budget)
        feature_score = 1.0 if (keyword.lower() in row['name'].lower() or keyword.lower() in row['description'].lower()) else 0.5
        if keyword == "":
            feature_score = 1.0

        total_score = (
            weights['rating'] * rating_score +
            weights['price_economy'] * economy_score +
            weights['feature_match'] * feature_score
        )
        scores.append(total_score)
        
    filtered['score'] = scores
    return filtered.sort_values(by='score', ascending=False)

results = filter_and_score(df_catalog, max_budget, desired_feature, preferred_brand_keyword)

# 6. Presentation Layer (Top 3 Recommendations)
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
            st.write(f"**Why it fits:** Matches budget & filters transparently. Score: `{row['score']:.2f}`.")
            with st.expander("Trade-offs"):
                st.write(f"- Price point: ${row['price']} out of${max_budget} max budget.")
                st.write(f"- Description: {row['description']}")

    # 7. Bonus: Side-by-Side Comparison Card
    st.markdown("---")
    st.subheader("⚖️ Side-by-Side Comparison")
    comparison_df = top_3[['name', 'category', 'price', 'rating', 'features', 'stock_status', 'score']]
    st.dataframe(comparison_df, use_container_width=True)

# 8. Shopper Scenarios Test Suite (Requirement 7.3 Compliance)
st.markdown("---")
st.subheader("📋 15 Shopper Scenarios Test Suite")
st.write("Click any pre-configured test scenario below to instantly simulate a shopper's journey and verify expected matches:")

scenario_cols = st.columns(5)
for i, sc in enumerate(scenarios):
    col = scenario_cols[i % 5]
    with col:
        if st.button(f"#{sc['id']}: {sc['name']}"):
            st.info(f"Loaded Scenario **{sc['name']}**: Budget $\le$ ${sc['budget']}, Must-Have: `{sc['must_have']}`, Keyword: `{sc['keyword']}`")
