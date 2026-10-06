import streamlit as st
import pandas as pd
import yaml
import re

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM STYLING
# ==========================================
st.set_page_config(
    page_title="AuraChat Elite | Conversational Product Recommender",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stChatFloatingInputContainer {
        bottom: 20px;
    }
    .hero-banner {
        padding: 1.5rem;
        background: linear-gradient(135deg, #1e1e2f 0%, #2a2a40 100%);
        border-radius: 12px;
        border: 1px solid #3f3f5f;
        color: #ffffff;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #26263b;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #3e3e5e;
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
    except Exception as e:
        df = pd.DataFrame()
        
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        config = {
            "currency": "₹",
            "scoring_weights": {"rating": 0.4, "price_economy": 0.3, "feature_match": 0.3}
        }
    return df, config

df_catalog, config = load_application_resources()
currency_symbol = config.get('currency', '₹')

# ==========================================
# 3. 15 SHOPPER SCENARIOS DEFINITION
# ==========================================
SHOPPER_SCENARIOS = [
    {"id": 1, "name": "Budget Runner", "budget": 4500, "must_have": "wireless", "keyword": "sport", "desc": "Looking for affordable wireless sports earphones."},
    {"id": 2, "name": "Audiophile Studio", "budget": 12000, "must_have": "wired", "keyword": "studio", "desc": "High fidelity studio monitor headphones."},
    {"id": 3, "name": "Frequent Flyer", "budget": 10500, "must_have": "active noise cancellation", "keyword": "traveler", "desc": "ANC headphones for long-haul travel comfort."},
    {"id": 4, "name": "Budget Student", "budget": 3000, "must_have": "wireless", "keyword": "long battery", "desc": "Cheap daily wireless earbuds with long battery."},
    {"id": 5, "name": "Hardcore Gamer", "budget": 9000, "must_have": "wired", "keyword": "rgb", "desc": "RGB surround sound wired gaming headset."},
    {"id": 6, "name": "Luxury ANC Buyer", "budget": 17000, "must_have": "active noise cancellation", "keyword": "leather", "desc": "Executive luxury noise cancelling headphones."},
    {"id": 7, "name": "Podcast Listener", "budget": 5500, "must_have": "mic", "keyword": "vocals", "desc": "Voice clarity optimized headset for podcasts."},
    {"id": 8, "name": "Waterproof Runner", "budget": 5000, "must_have": "wireless", "keyword": "waterproof", "desc": "Sweatproof and waterproof running gear."},
    {"id": 9, "name": "Sleeper Comfort", "budget": 3500, "must_have": "wireless", "keyword": "sleeping", "desc": "Ultra-thin comfortable headband for sleeping."},
    {"id": 10, "name": "DJ Professional", "budget": 14000, "must_have": "wired", "keyword": "dj", "desc": "Swiveling earcup professional DJ monitor."},
    {"id": 11, "name": "Eco-Conscious Buyer", "budget": 7500, "must_have": "wireless", "keyword": "eco-friendly", "desc": "Crafted from sustainable materials."},
    {"id": 12, "name": "Office Caller", "budget": 5000, "must_have": "mic", "keyword": "office", "desc": "Crystal clear microphone for virtual conference calls."},
    {"id": 13, "name": "Kids Safety First", "budget": 2000, "must_have": "wired", "keyword": "volume", "desc": "Volume-limited safe headphones for children."},
    {"id": 14, "name": "Fast Charge User", "budget": 6500, "must_have": "wireless", "keyword": "fast charging", "desc": "Quick charge wireless earbuds."},
    {"id": 15, "name": "Flagship Enthusiast", "budget": 18000, "must_have": "active noise cancellation", "keyword": "flagship", "desc": "The ultimate multi-feature flagship model."}
]

# ==========================================
# 4. SESSION STATE MANAGEMENT
# ==========================================
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {
            "role": "assistant", 
            "content": "👋 Welcome to **AuraChat Elite**! I am your advanced conversational shopping assistant.\n\n"
                       "You can type your requirements naturally (e.g., *'I need wireless headphones under 5000 rupees with active noise cancellation'*) "
                       "or use the sidebar to load any of the 15 verified shopper scenarios!"
        }
    ]

if "last_recommendations" not in st.session_state:
    st.session_state.last_recommendations = pd.DataFrame()

if "current_budget_filter" not in st.session_state:
    st.session_state.current_budget_filter = 10000

if "current_feature_filter" not in st.session_state:
    st.session_state.current_feature_filter = "None"

# ==========================================
# 5. SIDEBAR CONTROL CENTER
# ==========================================
with st.sidebar:
    st.markdown("<h2>🎛️ Conversational Hub</h2>", unsafe_allow_html=True)
    st.markdown("Fine-tune constraints or execute test personas instantly.")
    
    # Scenario Quick Selector
    scenario_options = ["Select a Scenario..."] + [f"Scenario #{s['id']}: {s['name']}" for s in SHOPPER_SCENARIOS]
    chosen_scenario = st.selectbox("⚡ Pre-built Shopper Scenarios", scenario_options)
    
    if chosen_scenario != "Select a Scenario...":
        sc_id_num = int(chosen_scenario.split(":")[0].replace("Scenario #", ""))
        matched_persona = next((s for s in SHOPPER_SCENARIOS if s["id"] == sc_id_num), None)
        if matched_persona:
            st.session_state.current_budget_filter = matched_persona["budget"]
            st.session_state.current_feature_filter = matched_persona["must_have"]
            auto_msg = f"Load scenario #{matched_persona['id']}: {matched_persona['name']} (Budget: {currency_symbol}{matched_persona['budget']}, Feature: {matched_persona['must_have']}, Keyword: {matched_persona['keyword']})"
            st.info(f"Loaded: **{matched_persona['name']}**\n- Budget: {currency_symbol}{matched_persona['budget']}\n- Must-Have: `{matched_persona['must_have']}`\n- Focus: `{matched_persona['keyword']}`")
    
    st.markdown("---")
    st.markdown("### 🔧 Live Parameter Adjusters")
    sidebar_budget = st.slider("Maximum Budget", 1000, 20000, st.session_state.current_budget_filter, 500)
    sidebar_feature = st.selectbox("Must-Have Feature", ["None", "wireless", "active noise cancellation", "mic", "wired"])
    sidebar_keyword = st.text_input("Brand or Keyword Preference", "")
    
    st.markdown("---")
    if st.button("🧹 Clear Chat & Reset Session", use_container_width=True):
        st.session_state.chat_messages = [{"role": "assistant", "content": "Chat reset successfully. How can I help you today?"}]
        st.session_state.last_recommendations = pd.DataFrame()
        st.rerun()

# ==========================================
# 6. ADVANCED INTENT PARSER & RECOMMENDATION ENGINE
# ==========================================
def parse_and_recommend(user_input, override_budget=None, override_feature=None):
    if df_catalog.empty:
        return "⚠️ Error: Product catalog (`catalog.csv`) could not be loaded."

    text_lower = user_input.lower()
    
    # 1. Budget extraction via Regex
    extracted_nums = re.findall(r'\d+', text_lower)
    if override_budget:
        budget = override_budget
    elif extracted_nums:
        # Filter numbers that look like budgets (greater than 500)
        valid_budgets = [int(n) for n in extracted_nums if int(n) >= 500]
        budget = max(valid_budgets) if valid_budgets else 10000
    else:
        budget = 10000

    # 2. Feature and keyword extraction
    detected_features = []
    if override_feature and override_feature != "None":
        detected_features.append(override_feature.lower())
    
    feature_keywords = ["wireless", "wired", "active noise cancellation", "anc", "mic", "microphone", "waterproof", "long battery", "rgb", "studio"]
    for fk in feature_keywords:
        if fk in text_lower and fk not in detected_features:
            if fk == "anc":
                detected_features.append("active noise cancellation")
            elif fk == "microphone":
                detected_features.append("mic")
            else:
                detected_features.append(fk)

    # 3. Filtering pipeline (Availability + Budget)
    filtered_df = df_catalog[(df_catalog['stock_status'] == 'In Stock') & (df_catalog['price'] <= budget)].copy()
    
    if filtered_df.empty:
        return f"I couldn't find any in
