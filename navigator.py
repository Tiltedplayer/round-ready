import streamlit as st
import json
import os
import re
import requests
import what3words

# --- CONFIGURATION ---
API_KEY = "XMDPVNNL" 
geocoder = what3words.Geocoder(API_KEY)
DATA_FILE = "farm_library.json"

# --- DATA HELPERS ---
def load_library():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_to_library(name, w3w, lat, lng, note):
    lib = load_library()
    lib[name.lower()] = {"w3w": w3w, "lat": lat, "lng": lng, "note": note}
    with open(DATA_FILE, "w") as f:
        json.dump(lib, f)

def get_coords(input_string):
    """Smarter coordinate finder for short links, long links, or raw numbers."""
    # 1. Check if it's just raw coordinates (e.g., 53.2,-1.4)
    raw_match = re.search(r"(-?\d+\.\d+),\s*(-?\d+\.\d+)", input_string)
    if raw_match:
        return float(raw_match.group(1)), float(raw_match.group(2))
    
    # 2. If it's a short maps.app.goo.gl link, we have to 'unmask' it
    if "maps.app.goo.gl" in input_string or "goo.gl/maps" in input_string:
        try:
            response = requests.get(input_string, allow_redirects=True, timeout=5)
            input_string = response.url # This is now the LONG version
        except:
            return None, None

    # 3. Look for the @lat,lng pattern in the long URL
    long_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", input_string)
    if long_match:
        return float(long_match.group(1)), float(long_match.group(2))
    
    return None, None

# --- APP INTERFACE ---
st.set_page_config(page_title="Round Ready", page_icon="📦")

# --- SIDEBAR SEARCH ---
with st.sidebar:
    st.header("🔎 Farm Library")
    library = load_library()
    search_term = st.text_input("Search Farm Name:").lower()
    
    if search_term:
        results = {k: v for k, v in library.items() if search_term in k}
        if results:
            for name, info in results.items():
                st.subheader(name.title())
                st.info(f"💡 {info['note']}")
                nav_url = f"google.navigation:q={info['lat']},{info['lng']}"
                st.link_button(f"🚀 GO TO {name.upper()}", nav_url, use_container_width=True)
                st.divider()

# --- MAIN PANEL ---
st.title("📦 Round Ready")

tab1, tab2 = st.tabs(["Quick Search", "Add New Farm"])

with tab1:
    w3w_input = st.text_input("Enter 3 words (e.g. filled.count.soap):").strip().lower()
    if st.button("START NAVIGATION", use_container_width=True):
        try:
            res = geocoder.convert_to_coordinates(w3w_input)
            lat, lng = res['coordinates']['lat'], res['coordinates']['lng']
            st.link_button("Open Locked GPS", f"google.navigation:q={lat},{lng}")
        except:
            st.error("API Error. Use 'Add New Farm' to save this spot manually.")

with tab2:
    st.subheader("Save a Cheat")
    new_name = st.text_input("Farm/House Name:")
    new_w3w = st.text_input("What3Words (Optional):")
    location_input = st.text_input("Paste Google Maps Link (Short or Long) OR raw coordinates:")
    new_note = st.text_input("Delivery Note (e.g. 'Gate code 1234'):")
    
    if st.button("💾 SAVE TO MY ROUND", use_container_width=True):
        lat, lng = get_coords(location_input)
        if lat and lng and new_name:
            save_to_library(new_name, new_w3w, lat, lng, new_note)
            st.success(f"Saved {new_name}! Check the sidebar search.")
        else:
            st.error("Could not find coordinates. Make sure you dropped a pin in Google Maps first!")
