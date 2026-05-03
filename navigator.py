import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re
import requests
import what3words

# --- CONFIGURATION ---
API_KEY = "XMDPVNNL" 
geocoder = what3words.Geocoder(API_KEY)

# --- GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # ttl="0s" means the app won't "cache" old data; it fetches fresh from the sheet every time
        return conn.read(ttl="0s")
    except:
        # If the sheet is brand new and empty, this creates the structure
        return pd.DataFrame(columns=["name", "w3w", "lat", "lng", "note"])

def save_data(new_row):
    df = load_data()
    # If you save a farm with the same name, this line removes the old one first (The Overwrite)
    if not df.empty:
        df = df[df['name'].str.lower() != new_row['name'].lower()]
    
    updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    conn.update(data=updated_df)
    st.cache_data.clear()

def get_coords(input_string):
    """Handles short links, long links, and raw coordinates."""
    # 1. Check for raw lat,lng numbers
    raw_match = re.search(r"(-?\d+\.\d+),\s*(-?\d+\.\d+)", input_string)
    if raw_match:
        return float(raw_match.group(1)), float(raw_match.group(2))
    
    # 2. Expand short Google links
    if "goo.gl" in input_string or "maps.app.goo.gl" in input_string:
        try:
            response = requests.get(input_string, allow_redirects=True, timeout=5)
            input_string = response.url
        except: pass

    # 3. Extract from long URL
    long_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", input_string)
    if long_match:
        return float(long_match.group(1)), float(long_match.group(2))
    return None, None

# --- APP INTERFACE ---
st.set_page_config(page_title="Round Ready", page_icon="📦")
st.title("📦 Round Ready")

tab1, tab2 = st.tabs(["Quick Search", "Add New Farm"])

# --- TAB 1: SEARCH ---
with tab1:
    df = load_data()
    search_term = st.text_input("Search Farm Name (e.g. 'Hillside'):").lower()
    
    if search_term and not df.empty:
        # This looks for your search term anywhere in the farm name
        results = df[df['name'].str.contains(search_term, case=False, na=False)]
        if not results.empty:
            for _, row in results.iterrows():
                with st.expander(f"📍 {row['name'].title()}", expanded=True):
                    st.write(f"**3 Words:** {row['w3w']}")
                    st.info(f"💡 {row['note']}")
                    # This uses the 'google.navigation' protocol which opens the App directly
                    nav_url = f"google.navigation:q={row['lat']},{row['lng']}"
                    st.link_button(f"🚀 NAVIGATE TO GATE", nav_url, use_container_width=True)
        else:
            st.warning("No matches found in your library.")
    elif df.empty:
        st.write("Your library is currently empty. Add your first farm in the next tab!")

# --- TAB 2: ADD NEW ---
with tab2:
    st.subheader("Save a Cheat")
    new_name = st.text_input("Farm/House Name:")
    new_w3w = st.text_input("What3Words (Optional):")
    location_input = st.text_input("Paste Google Maps Link or coordinates:")
    new_note = st.text_input("Delivery Note (e.g. 'Hidden track on right'):")
    
    if st.button("💾 SAVE TO GOOGLE SHEETS", use_container_width=True):
        lat, lng = get_coords(location_input)
        if lat and lng and new_name:
            new_row = {
                "name": new_name, 
                "w3w": new_w3w, 
                "lat": lat, 
                "lng": lng, 
                "note": new_note
            }
            save_data(new_row)
            st.success(f"Saved {new_name}! Open your Google Sheets app to see it.")
        else:
            st.error("Could not find coordinates. Make sure you use a valid Google Maps link.")
