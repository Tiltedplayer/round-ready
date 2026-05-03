import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re
import requests

# --- CONFIGURATION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        return conn.read(ttl="0s")
    except:
        return pd.DataFrame(columns=["name", "w3w", "lat", "lng", "note"])

def save_data(new_row):
    df = load_data()
    if not df.empty:
        df = df[df['name'].str.lower() != new_row['name'].lower()]
    updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    conn.update(data=updated_df)
    st.cache_data.clear()

def get_coords(input_string):
    raw_match = re.search(r"(-?\d+\.\d+),\s*(-?\d+\.\d+)", input_string)
    if raw_match:
        return float(raw_match.group(1)), float(raw_match.group(2))
    if "goo.gl" in input_string or "maps.app.goo.gl" in input_string:
        try:
            response = requests.get(input_string, allow_redirects=True, timeout=5)
            input_string = response.url
        except: pass
    long_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", input_string)
    if long_match:
        return float(long_match.group(1)), float(long_match.group(2))
    return None, None

# --- SIDEBAR NAV ---
st.sidebar.title("Settings")
page = st.sidebar.radio("Go to:", ["🔎 Search Library", "➕ Add New Farm"])

# --- MAIN INTERFACE ---
st.title("📦 Round Ready")

if page == "🔎 Search Library":
    df = load_data()
    search_term = st.text_input("Enter farm name:").lower()
    if search_term and not df.empty:
        results = df[df['name'].str.contains(search_term, case=False, na=False)]
        if not results.empty:
            for _, row in results.iterrows():
                with st.expander(f"📍 {row['name'].title()}", expanded=True):
                    st.write(f"**3 Words:** {row['w3w']}")
                    st.info(f"💡 {row['note']}")
                    nav_url = f"google.navigation:q={row['lat']},{row['lng']}"
                    st.link_button(f"🚀 NAVIGATE TO GATE", nav_url, use_container_width=True)
        else:
            st.warning("No matches found.")
    elif df.empty:
        st.write("Your library is empty. Use the sidebar to add a farm!")

else:
    st.subheader("Save a New Cheat")
    new_name = st.text_input("Farm/House Name:")
    new_w3w = st.text_input("What3Words (Optional):")
    location_input = st.text_input("Paste Google Maps Link or coordinates:")
    new_note = st.text_input("Delivery Note:")
    
    if st.button("💾 SAVE TO CLOUD", use_container_width=True):
        lat, lng = get_coords(location_input)
        if lat and lng and new_name:
            save_data({"name": new_name, "w3w": new_w3w, "lat": lat, "lng": lng, "note": new_note})
            st.success(f"Saved {new_name}! It's now in your Google Sheet.")
            st.balloons()
        else:
            st.error("Missing name or valid location link.")
