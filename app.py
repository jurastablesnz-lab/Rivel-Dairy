import streamlit as st
import pandas as pd
import numpy as np

# === SEXY SKIN STARTS HERE ===
st.set_page_config(page_title="Rivel • NZ Dairy Optimizer", layout="centered")
st.markdown("""
<style>
    .css-1d391kg {padding-top: 1rem; padding-bottom: 3rem;}
    .css-1y0t9i3 {font-family: 'Inter', sans-serif;}
    .stButton>button {
        background: #0B5D3C; color: white; border-radius: 12px; height: 3.5rem;
        font-weight: 600; font-size: 1.1rem; border: none;
    }
    .stSlider>div>div>div {background: #0B5D3C;}
    section[data-testid="stSidebar"] {background: #0B4619;}
    .css-1v0mbdj {color: #0B5D3C; font-weight: 800;}
    h1 {color: #0B4619; text-align: center; font-size: 3.2rem;}
    h2 {color: #0B5D3C;}
</style>
""", unsafe_allow_html=True)

# Header with NZ vibes
st.markdown("<h1>🥛 Rivel</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#555; font-size:1.3rem;'>The FeedXL for New Zealand dairy farmers</p>", unsafe_allow_html=True)
st.markdown("---")

# === Same prediction engine (just prettier) ===
@st.cache_data
def load_feed_library():
    return pd.DataFrame({
        'Name': ['Ryegrass Pasture (Spring)', 'Ryegrass Pasture (Autumn)', 'PKE', 'Maize Silage', 'Canola Meal', 'Barley Grain', 'Tapioca'],
        'ME_MJ': [12.2, 11.5, 10.2, 10.8, 12.1, 13.0, 13.2],
        'CP_g': [220, 180, 160, 80, 380, 120, 90],
        'Cost_NZD': [0.23, 0.25, 0.35, 0.28, 0.45, 0.38, 0.40],
        'Color': ['#90EE90', '#228B22', '#8B4513', '#FFD700', '#DAA520', '#F4A460', '#D3D3D3']
    })

def predict_dairy(cow_weight, current_milk, feeds_df, amounts):
    dmi = sum(amounts)
    if dmi == 0: return None
    me_intake = sum(feeds_df['ME_MJ'] * amounts)
    cp_intake = sum((feeds_df['CP_g']/1000) * amounts) * 1000
    mp_supply = cp_intake * 0.64 + me_intake * 2.5

    milk_from_me = max(0, (me_intake - 0.08 * cow_weight**0.75 - 10) / 5.0)
    milk_from_mp = mp_supply / 95
    predicted_milk = min(milk_from_me, milk_from_mp, current_milk * 1.18)

    fat_pct = 4.1 + 0.04 * (sum(feeds_df['Cost_NZD'] * amounts) / dmi)
    protein_pct = 3.3 + 0.008 * (mp_supply / predicted_milk)
    milk_solids = predicted_milk * (fat_pct + protein_pct) / 100

    energy_balance = me_intake - (0.08 * cow_weight**0.75 + predicted_milk * 5.0 + 10)
    lwg = max(-1.2, energy_balance / 28)
    total_cost = sum(feeds_df['Cost_NZD'] * amounts)

    return {
        'Milk Solids': round(milk_solids, 2),
        'Milk Yield': round(predicted_milk, 1),
        'LWG': round(lwg, 2),
        'Cost': round(total_cost, 2),
        'DMI': round(dmi, 1),
        'Methane': round(21 * dmi + 180)
    }

# === Gorgeous layout ===
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image("https://raw.githubusercontent.com/grok-ag/rivel/main/rivel-logo.png", width=180)  # I’ll give you the real logo file in 2 mins

left, right = st.columns(2)
with left:
    cow_weight = st.slider("Cow live weight (kg)", 400, 750, 560, 10)
    current_milk = st.number_input("Current milk yield (kg/cow/day)", 15.0, 55.0, 34.0, 0.5)
with right:
    herd_size = st.number_input("Herd size", 100, 2000, 435, 50)
    st.markdown("<br>", unsafe_allow_html=True)
    season = st.selectbox("Season", ["Spring", "Summer", "Autumn", "Winter"])

st.markdown("### Feed intake (kg DM/cow/day)")
feeds = load_feed_library()
amounts = []
for i, feed in feeds.iterrows():
    default = 12.0 if "Spring" in feed['Name'] and season == "Spring" else 10.0 if "Pasture" in feed['Name'] else 0.0
    amt = st.slider(f"{feed['Name']}", 0.0, 20.0, default, step=0.5, key=feed['Name'])
    amounts.append(amt)

if st.button("🚀 Predict Milk Solids & Profit", type="primary", use_container_width=True):
    results = predict_dairy(cow_weight, current_milk, feeds, amounts)
    if results:
        st.balloons()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Milk Solids", f"{results['Milk Solids']} kg", "per cow/day")
        c2.metric("Extra Revenue", f"+${round((results['Milk Solids'] - 1.9) * 8.50 * herd_size, 0):,}", "per day @ $8.50/kg MS")
        c3.metric("Live-weight gain", f"{results['LWG']} kg/day")
        c4.metric("Feed cost", f"${results['Cost']}/cow")

        st.success(f"Total DMI: {results['DMI']} kg · Methane: {results['Methane']} g/cow · Season: {season}")