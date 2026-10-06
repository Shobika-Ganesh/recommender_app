import streamlit as st
import pandas as pd
import yaml

# 1. High-End Page Setup & Styling
st.set_page_config(
    page_title="AuraSound | Conversational Recommender", 
    page_icon="🎧", 
    layout="wide"
)

# Custom CSS Injection for a sleek modern aesthetic
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1f2937;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
    }
    .hero-box {
        padding: 2rem;
        border-radius: 12px;
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 1px solid #374151;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Hero Header
st.markdown("""
    <div class="hero-box">
        <h1 style='color: #f3f4f6; margin-bottom: 0px;'>🎧 AuraSound AI Recommender</h1>
        <p style='color: #9ca3af; font-size: 1.1rem; margin-top: 5px;'>
            Next-generation conversational preference matching engine. Transparent scoring, real-time filters, and zero opaque suggestions.
        </p>
    </div>
""", unsafe_allow_html=True)

# 2. Data Loading
@st.cache_data
def load_data():
    df = pd.read_csv("catalog.csv")
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    return df, config

df_catalog, config = load_data()
currency = config.get('currency', '₹')

# 3. 15 Conversational Scenarios Definition
scenarios = [
    {"id": 1, "name": "Budget Runner", "budget": 4500, "must_have": "wireless", "keyword": "sport"},
    {"id": 2, "name": "Audiophile Studio", "budget": 12000, "must_have": "wired", "keyword": "studio"},
    {"id": 3, "name": "Frequent Flyer", "budget": 10500, "must_have": "active noise cancellation", "keyword": "traveler"},
    {"id": 4, "name": "Budget Student", "budget": 3000, "must_have": "wireless", "keyword": "long battery"},
    {"id": 5, "name": "Hardcore Gamer", "budget": 9000, "must_have": "wired", "keyword": "rgb"},
    {"id": 6, "name": "Luxury ANC Buyer", "budget": 17000, "must_have": "active noise cancellation", "keyword": "leather"},
    {"id": 7, "name": "Podcast Listener", "budget": 5500, "must_have": "mic", "keyword": "vocals"},
    {"id": 8, "name": "Waterproof Runner", "budget": 5000, "must_have": "wireless", "keyword": "waterproof"},
    {"id": 9, "name": "Sleeper Comfort", "budget": 3500, "must_have": "wireless", "keyword": "sleeping"},
    {"id": 10, "name": "DJ Professional", "budget": 14000, "must_have": "wired", "keyword": "dj"},
    {"id": 11, "name": "Eco-Conscious Buyer", "budget": 7500, "must_have": "wireless", "keyword": "eco-friendly"},
    {"id": 12, "name": "Office Caller", "budget": 5000, "must_have": "mic", "keyword": "office"},
    {"id": 13, "name": "Kids Safety First", "budget": 2000, "must_have": "wired", "keyword": "volume"},
    {"id": 14, "name": "Fast Charge User", "budget": 6500, "must_have": "wireless", "keyword": "fast charging"},
    {"id": 15, "name": "Flagship Enthusiast", "budget": 18000, "must_have": "active noise cancellation", "keyword": "flagship"}
]

# Session State initialization for scenario override
if 'selected_budget' not in st.session_state:
    st.session_state.selected_budget = 8000
if 'selected_must_have' not in st.session_state:
    st.session_state.selected_must_have = "wireless"
if 'selected_keyword' not in st.session_state:
    st.session_state.selected_keyword = ""

# 4. Interactive Sidebar (Conversational Control Center)
st.sidebar.markdown("<h2>💬 Conversational Hub</h2>", unsafe_allow_html=True)
st.sidebar.markdown("Fine-tune your criteria or load pre-tested buyer personas instantly.")

# Scenario Quick-Loader
selected_scenario_name = st.sidebar.selectbox(
    "⚡ Quick-Load Buyer Persona (15 Scenarios)", 
    ["Custom Input"] + [f"#{s['id']}: {s['name']}" for s in scenarios]
)

if selected_scenario_name != "Custom Input":
    sc_id = int(selected_scenario_name.split(":")[0].replace("#", ""))
    matched_sc = next(s for s in scenarios if s["id"] == sc_id)
    st.session_state.selected_budget = matched_sc["budget"]
    st.session_state.selected_must_have = matched_sc["must_have"]
    st.session_state.selected_keyword = matched_sc["keyword"]

st.sidebar.markdown("---")
max_budget = st.sidebar.slider("Maximum Budget (₹)", 1000, 20000, st.session_state.selected_budget, 500)
desired_feature = st.sidebar.selectbox(
    "Must-Have Technical Constraint", 
    ["None", "wireless", "active noise cancellation", "mic", "wired"],
    index=["None", "wireless", "active noise cancellation", "mic", "wired"].index(st.session_state.selected_must_have) if st.session_state.selected_must_have in ["None", "wireless", "active noise cancellation", "mic", "wired"] else 0
)
preferred_brand_keyword = st.sidebar.text_input("Brand / Keyword Intent (Optional)", st.session_state.selected_keyword)

# 5. Advanced Transparent Scoring Engine
def filter_and_score(df, budget, must_have, keyword):
    # Rule 1: Availability & Budget Constraints
    filtered = df[(df['stock_status'] == 'In Stock') & (df['price'] <= budget)].copy()
    
    if filtered.empty:
        return filtered

    # Rule 2: Must-have feature filter
    if must_have != "None":
        filtered = filtered[filtered['features'].str.contains(must_have, case=False, na=False)]
        
    if filtered.empty:
        return filtered

    weights = config['scoring_weights']
    
    scores = []
    for _, row in filtered.iterrows():
        # Normalized rating (0 to 1)
        rating_score = row['rating'] / 5.0
        
        # Economy score (higher score for better savings under budget)
        economy_score = 1.0 - (row['price'] / budget)
        
        # Intent / Keyword match score
        feature_score = 1.0 if (keyword.lower() in row['name'].lower() or keyword.lower() in row['description'].lower()) else 0.5
        if keyword == "":
            feature_score = 1.0

        # Weighted calculation
        total_score = (
            weights['rating'] * rating_score +
            weights['price_economy'] * economy_score +
            weights['feature_match'] * feature_score
        )
        scores.append(round(total_score, 3))
        
    filtered['score'] = scores
    return filtered.sort_values(by='score', ascending=False)

results = filter_and_score(df_catalog, max_budget, desired_feature, preferred_brand_keyword)

# 6. Presentation Layer: Top 3 Recommendations with Deep Explanations
st.markdown("---")
st.markdown("<h2>🏆 Top 3 Recommended Products</h2>", unsafe_allow_html=True)
st.caption(" Ranked using transparent configuration weights: Star Rating (40%), Budget Economy (30%), Feature Intent Match (30%).")

if results.empty:
    st.error("🚨 **No products match your specific criteria.** Try expanding your budget or relaxing your must-have feature constraints.")
else:
    top_3 = results.head(3)
    
    cols = st.columns(3)
    for idx, (index, row) in enumerate(top_3.iterrows()):
        with cols[idx]:
            with st.container():
                st.markdown(f"### #{idx+1} {row['name']}")
                st.markdown(f"**Price:** `{currency}{row['price']:,.2f}`")
                st.markdown(f"**Rating:** ⭐ `{row['rating']}/5.0`")
                st.markdown(f"**Match Score:** 🎯 `{row['score']}`")
                st.info(f"**Matched Features:** {row['features']}")
                
                with st.expander("⚖️ Transparent Trade-offs"):
                    savings = max_budget - row['price']
                    st.write(f"- **Budget Impact:** Costs {currency}{row['price']:,.2f} out of your {currency}{max_budget:,.2f} limit (You save {currency}{savings:,.2f}).")
                    st.write(f"- **Product Overview:** {row['description']}")
                    st.write(f"- **Availability:** {row['stock_status']}")

    # 7. Bonus: Comprehensive Side-by-Side Comparison Matrix
    st.markdown("---")
    st.markdown("<h2>📊 Side-by-Side Comparative Matrix</h2>", unsafe_allow_html=True)
    st.caption("Detailed head-to-head metrics for your top recommendations to make an informed final choice.")
    
    comparison_df = top_3[['id', 'name', 'category', 'price', 'rating', 'features', 'stock_status', 'score']].copy()
    comparison_df['price'] = comparison_df['price'].apply(lambda x: f"{currency}{x:,.2f}")
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)

# 8. Footer Note
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #6b7280; font-size: 0.9rem;'>AuraSound Intelligent Conversational Engine • Fully Compliant with Retail Recommendation Constraints</p>", 
    unsafe_allow_html=True
)
