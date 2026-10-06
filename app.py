import streamlit as st
import pandas as pd
import yaml
import re

# ==========================================
# 1. PAGE CONFIGURATION & LUXURY STYLING
# ==========================================
st.set_page_config(
    page_title="AuraSound Visual AI | Conversational Recommender",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {
        background-color: #0b0f19;
    }
    .hero-banner {
        padding: 2rem;
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        border-radius: 16px;
        border: 1px solid #4338ca;
        color: #ffffff;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.3);
    }
    .product-card {
        background-color: #111827;
        border: 1px solid #1f2937;
        padding: 20px;
        border-radius: 14px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease;
        margin-bottom: 1rem;
    }
    .product-card:hover {
        transform: translateY(-4px);
        border-style: solid;
        border-color: #6366f1;
    }
    .stChatMessage {
        border-radius: 12px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA AND CONFIGURATION LOADING
# ==========================================
@st.cache_data
def load_application_resources():
    try:
        df = pd.read_csv("catalog.csv")
    except Exception:
        df = pd.DataFrame()
        
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
    except Exception:
        config = {
            "currency": "₹",
            "scoring_weights": {"rating": 0.4, "price_economy": 0.3, "feature_match": 0.3}
        }
    return df, config

df_catalog, config = load_application_resources()
currency_symbol = config.get('currency', '₹')

# Add high-res headphone image placeholders to catalog if missing
if not df_catalog.empty and 'image_url' not in df_catalog.columns:
    sample_images = [
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=60",
        "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=500&auto=format&fit=crop&q=60",
        "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=500&auto=format&fit=crop&q=60",
        "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=500&auto=format&fit=crop&q=60",
        "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500&auto=format&fit=crop&q=60"
    ]
    df_catalog['image_url'] = [sample_images[i % len(sample_images)] for i in range(len(df_catalog))]

# ==========================================
# 3. 15 SHOPPER SCENARIOS DEFINITION
# ==========================================
SHOPPER_SCENARIOS = [
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

# ==========================================
# 4. SESSION STATE INITIALIZATION
# ==========================================
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {
            "role": "assistant", 
            "content": "✨ Welcome to **AuraSound Visual AI**! Type your preferences naturally below (e.g., *'I need wireless headphones under 6000 rupees with noise cancellation'*) or select a scenario from the sidebar!"
        }
    ]

if "last_recommendations" not in st.session_state:
    st.session_state.last_recommendations = pd.DataFrame()

if "current_budget_filter" not in st.session_state:
    st.session_state.current_budget_filter = 10000

# ==========================================
# 5. SIDEBAR CONTROL HUB
# ==========================================
with st.sidebar:
    st.markdown("<h2>⚡ Quick Personas</h2>", unsafe_allow_html=True)
    scenario_options = ["Select a Scenario..."] + [f"Scenario #{s['id']}: {s['name']}" for s in SHOPPER_SCENARIOS]
    chosen_scenario = st.selectbox("Load Test Persona", scenario_options)
    
    if chosen_scenario != "Select a Scenario...":
        sc_id_num = int(chosen_scenario.split(":")[0].replace("Scenario #", ""))
        matched_persona = next((s for s in SHOPPER_SCENARIOS if s["id"] == sc_id_num), None)
        if matched_persona:
            st.session_state.current_budget_filter = matched_persona["budget"]
            st.success(f"Loaded **{matched_persona['name']}** (Budget: {currency_symbol}{matched_persona['budget']})")
    
    st.markdown("---")
    st.markdown("### 🎛️ Live Parameter Filters")
    sidebar_budget = st.slider("Max Budget Limit", 1000, 20000, st.session_state.current_budget_filter, 500)
    sidebar_feature = st.selectbox("Must-Have Feature Constraint", ["None", "wireless", "active noise cancellation", "mic", "wired"])
    
    st.markdown("---")
    if st.button("🔄 Reset Conversation", use_container_width=True):
        st.session_state.chat_messages = [{"role": "assistant", "content": "Chat reset! How can I help you find headphones today?"}]
        st.session_state.last_recommendations = pd.DataFrame()
        st.rerun()

# ==========================================
# 6. RECOMMENDATION ENGINE LOGIC
# ==========================================
def parse_and_recommend(user_input, override_budget=None, override_feature=None):
    if df_catalog.empty:
        return "⚠️ Error: Catalog could not be loaded."

    text_lower = user_input.lower()
    
    extracted_nums = re.findall(r'\d+', text_lower)
    if override_budget:
        budget = override_budget
    elif extracted_nums:
        valid_budgets = [int(n) for n in extracted_nums if int(n) >= 500]
        budget = max(valid_budgets) if valid_budgets else 10000
    else:
        budget = 10000

    detected_features = []
    if override_feature and override_feature != "None":
        detected_features.append(override_feature.lower())
    
    for fk in ["wireless", "wired", "active noise cancellation", "anc", "mic", "waterproof", "rgb", "studio"]:
        if fk in text_lower and fk not in detected_features:
            detected_features.append("active noise cancellation" if fk == "anc" else fk)

    filtered_df = df_catalog[(df_catalog['stock_status'] == 'In Stock') & (df_catalog['price'] <= budget)].copy()
    
    if filtered_df.empty:
        return f"I couldn't find any in-stock items under **{currency_symbol}{budget:,}**. Try increasing your budget!"

    if detected_features:
        query_string = '|'.join(detected_features)
        feature_subset = filtered_df[filtered_df['features'].str.contains(query_string, case=False, na=False)]
        if not feature_subset.empty:
            filtered_df = feature_subset

    weights = config.get('scoring_weights', {'rating': 0.4, 'price_economy': 0.3, 'feature_match': 0.3})
    scoring_results = []
    
    for _, row in filtered_df.iterrows():
        rating_score = row['rating'] / 5.0
        economy_score = 1.0 - (row['price'] / budget)
        keyword_match = 1.0 if any(word in row['name'].lower() or word in row['description'].lower() for word in text_lower.split() if len(word) > 3) else 0.6
        
        total_score = (weights['rating'] * rating_score) + (weights['price_economy'] * economy_score) + (weights['feature_match'] * keyword_match)
        scoring_results.append(round(total_score, 3))

    filtered_df['score'] = scoring_results
    top_picks = filtered_df.sort_values(by='score', ascending=False).head(3)
    st.session_state.last_recommendations = top_picks

    reply = f"🎯 Found **{len(top_picks)} top matching products** under `{currency_symbol}{budget:,}` with filters: `{detected_features if detected_features else 'Best Overall'}`. Check out the interactive visual cards below!"
    return reply

# ==========================================
# 7. MAIN UI & CHAT INTERFACE
# ==========================================
st.markdown("""
    <div class="hero-banner">
        <h1 style="margin: 0;">🎧 AuraSound Visual Recommender</h1>
        <p style="color: #cbd5e1; margin-top: 5px;">
            Natural conversational AI with transparent trade-offs and instant visual product cards.
        </p>
    </div>
""", unsafe_allow_html=True)

# Render Chat History
for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Chat Input Box
if user_prompt := st.chat_input("Type your request naturally (e.g. 'I want wireless headphones under 8000 rupees with mic')"):
    st.session_state.chat_messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching catalog & calculating transparent scores..."):
            bot_reply = parse_and_recommend(user_prompt, override_budget=sidebar_budget, override_feature=sidebar_feature)
            st.markdown(bot_reply)
            
    st.session_state.chat_messages.append({"role": "assistant", "content": bot_reply})
    st.rerun()

# ==========================================
# 8. VISUAL PRODUCT CARDS (TOP 3 RECOMMENDATIONS)
# ==========================================
if not st.session_state.last_recommendations.empty:
    st.markdown("---")
    st.markdown("<h2>🌟 Top 3 Recommended Products with Visuals</h2>", unsafe_allow_html=True)
    
    cols = st.columns(3)
    for idx, (_, prod) in enumerate(st.session_state.last_recommendations.iterrows()):
        with cols[idx]:
            st.markdown(f"""
                <div class="product-card">
                    <img src="{prod['image_url']}" style="width:100%; height:160px; object-fit:cover; border-radius:10px; margin-bottom:10px;">
                    <h3 style="color:#f3f4f6; font-size:1.1rem; margin-bottom:5px;">{prod['name']}</h3>
                    <p style="color:#818cf8; font-weight:bold; font-size:1.2rem; margin:0;">{currency_symbol}{prod['price']:,.2f}</p>
                    <p style="color:#fbbf24; font-size:0.9rem;">⭐ {prod['rating']} / 5.0 | Score: <b>{prod['score']}</b></p>
                    <p style="color:#9ca3af; font-size:0.8rem; text-align:left;"><b>Features:</b> {prod['features']}</p>
                    <p style="color:#d1d5db; font-size:0.8rem; text-align:left;">{prod['description']}</p>
                </div>
            """, unsafe_allow_html=True)

    # ==========================================
    # 9. SIDE-BY-SIDE COMPARISON MATRIX
    # ==========================================
    st.markdown("---")
    st.markdown("<h2>📊 Side-by-Side Comparison Matrix</h2>", unsafe_allow_html=True)
    matrix_df = st.session_state.last_recommendations[['id', 'name', 'category', 'price', 'rating', 'features', 'stock_status', 'score']].copy()
    matrix_df['price'] = matrix_df['price'].apply(lambda val: f"{currency_symbol}{val:,.2f}")
    st.dataframe(matrix_df, use_container_width=True, hide_index=True)
