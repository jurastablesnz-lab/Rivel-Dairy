import streamlit as st
import pandas as pd
import numpy as np

# Simplified NASEM 2021 Dairy Equations (starter version)
@st.cache_data
def load_feed_library():
    feeds = pd.DataFrame({
        'Name': ['Ryegrass Pasture (Autumn)', 'PKE', 'Maize Silage', 'Canola Meal', 'Kikuyu Pasture', 'Barley Grain'],
        'ME_MJ': [11.5, 10.2, 10.8, 12.1, 10.8, 13.0],
        'CP_g': [180, 160, 80, 380, 140, 120],
        'NDF_g': [350, 750, 400, 280, 420, 180],
        'Starch_g': [50, 20, 300, 10, 30, 600],
        'Fat_g': [30, 50, 30, 40, 25, 20],
        'Cost_NZD': [0.25, 0.35, 0.28, 0.45, 0.22, 0.38]
    })
    return feeds

def predict_dairy(cow_weight, dim, current_milk, feeds_df, amounts):
    dmi = sum(amounts)
    if dmi == 0: return None
    
    me_intake = sum(feeds_df['ME_MJ'] * amounts)
    cp_intake = sum((feeds_df['CP_g']/1000) * amounts) * 1000
    mp_supply = cp_intake * 0.64 + me_intake * 2.5

    milk_from_me = max(0, (me_intake - 0.08 * cow_weight**0.75 - 10) / 5.0)
    milk_from_mp = mp_supply / 95
    predicted_milk = min(milk_from_me, milk_from_mp, current_milk * 1.15)

    fat_pct = 4.0 + 0.04 * (sum(feeds_df['Fat_g'] * amounts) / dmi) - 0.1
    protein_pct = 3.3 + 0.008 * (mp_supply / predicted_milk)
    milk_solids = predicted_milk * (fat_pct + protein_pct) / 100

    energy_balance = me_intake - (0.08 * cow_weight**0.75 + predicted_milk * 5.0 + 10)
    lwg = max(-1.0, energy_balance / 28)

    total_cost = sum(feeds_df['Cost_NZD'] * amounts)

    return {
        'Milk_kg': round(predicted_milk, 1),
        'Fat_pct': round(fat_pct, 2),
        'Protein_pct': round(protein_pct, 2),
        'Milk_Solids_kg': round(milk_solids, 2),
        'LWG_kg_day': round(lwg, 2),
        'Methane_g': round(21 * dmi + 200),
        'Cost_per_cow': round(total_cost, 2),
        'DMI_kg': round(dmi, 1)
    }

# Streamlit UI starts here
st.set_page_config(page_title="Rivel – NZ Dairy Optimizer", layout="centered")
st.title("🥛 Rivel – NZ Dairy Ration Optimizer")
st.markdown("##### Predict milk solids, live-weight gain & methane instantly")

col1, col2 = st.columns(2)
with col1:
    cow_weight = st.slider("Cow live weight (kg)", 400, 750, 550)
    current_milk = st.number_input("Current milk yield (kg/day)", 15.0, 55.0, 32.0)
with col2:
    dim = st.slider("Days in milk", 0, 305, 120)

st.markdown("### Feed intake (kg DM per cow per day)")
feeds = load_feed_library()
amounts = []
for i, feed in feeds.iterrows():
    default = 12.0 if "Pasture" in feed['Name'] else 0.0
    amt = st.slider(feed['Name'], 0.0, 20.0, default, step=0.5, key=feed['Name'])
    amounts.append(amt)

if st.button("🔥 Run Prediction", type="primary"):
    results = predict_dairy(cow_weight, dim, current_milk, feeds, amounts)
    if results:
        st.success("Prediction complete!")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Milk Solids", f"{results['Milk_Solids_kg']} kg")
        c2.metric("Milk Yield", f"{results['Milk_kg']} kg")
        c3.metric("Live-weight gain", f"{results['LWG_kg_day']} kg/day")
        c4.metric("Cost per cow", f"${results['Cost_per_cow']}")

        st.info(f"Total DMI: {results['DMI_kg']} kg  |  Methane: {results['Methane_g']} g/day")