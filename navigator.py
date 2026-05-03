import streamlit as st
import pandas as pd
import re
import requests
import what3words

# --- CONFIGURATION ---
API_KEY = "XMDPVNNL" 
geocoder = what3words.Geocoder(API_KEY)

# --- GOOGLE SHEETS SETTINGS ---
# We grab the ID from your URL for direct access
SHEET_ID = "1X1-iwZ7toc-grYlNWTbgR5_pbopJnL-KUIE5QJrfFXI"
csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def load_data():
    try:
        # Direct read from the CSV export link
        return pd.read_csv(csv_url)
    except:
        return pd.DataFrame(columns=["name", "w3w", "lat", "lng", "note"])

def save_data(new_row):
    # This uses the Streamlit GSheets connection for the WRITE part only
    from streamlit_gsheets import GSheetsConnection
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    df = load_data()
    if not df.empty:
        df = df[df['name'].str.lower() != new_row['name'].lower()]
    
    updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    # Force the update
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

# --- APP INTERFACE ---
st.set_page_config(page_title="Round Ready", page_icon="📦")
st.title("📦 Round Ready")

tab1, tab2 = st.tabs(["Quick Search", "Add New Farm"])

with tab1:
    df = load_data()
    search_term = st.text_input("Search Farm Name:").lower()
    if search_term and not df.empty:
        # Improved search logic
        results = df[df['name'].astype(str).str.contains(search_term, case=False, na=False)]
        for _, row in results.iterrows():
            with st.expander(f"📍 {str(row['name']).title()}", expanded=True):
                st.write(f"**3 Words:** {row['w3w']}")
                st.info(f"💡 {row['note']}")
                st.link_button(f"🚀 NAVIGATE", f"google.navigation:q={row['lat']},{row['lng']}", use_container_width=True)
    elif df.empty:
        st.write("No farms saved yet.")

with tab2:
    st.subheader("Save a Cheat")
    new_name = st.text_input("Farm Name:")
    new_w3w = st.text_input("3 Words:")
    location_input = st.text_input("Google Link or Coordinates:")
    new_note = st.text_input("Note:")
    
    if st.button("💾 SAVE TO CLOUD", use_container_width=True):
        lat, lng = get_coords(location_input)
        if lat and lng and new_name:
            new_row = {"name": new_name, "w3w": new_w3w, "lat": lat, "lng": lng, "note": new_note}
            try:
                save_data(new_row)
                st.success("Successfully saved to your Google Sheet!")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Please provide a name and a valid location link/coordinates.")
