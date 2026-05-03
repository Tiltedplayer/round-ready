import streamlit as st
import json
import os
import re
import what3words

# --- CONFIGURATION ---
API_KEY = "XMDPVNNL"  # <--- Paste your key here!
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
    # Save using the house/farm name as the key for easy searching
    lib[name.lower()] = {"w3w": w3w, "lat": lat, "lng": lng, "note": note}
    with open(DATA_FILE, "w") as f:
        json.dump(lib, f)

def extract_coords_from_url(url):
    """Pulls lat/lng out of a Google Maps link if you paste one."""
    regex = r"@(-?\d+\.\d+),(-?\d+\.\d+)"
    match = re.search(regex, url)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None

# --- APP INTERFACE ---
st.set_page_config(page_title="Round Ready", page_icon="📦")

# --- SIDEBAR SEARCH ---
with st.sidebar:
    st.header("🔎 Farm Library")
    library = load_library()
    search_term = st.text_input("Search by Farm/House Name:").lower()
    
    if search_term:
        results = {k: v for k, v in library.items() if search_term in k}
        if results:
            for name, info in results.items():
                st.subheader(name.title())
                st.write(f"📍 {info['w3w']}")
                st.info(f"💡 {info['note']}")
                nav_url = f"https://www.google.com/maps/dir/?api=1&destination={info['lat']},{info['lng']}&travelmode=driving&dir_action=navigate"
                st.link_button(f"GO TO {name.upper()}", nav_url)
                st.divider()
        else:
            st.write("No matches found.")

# --- MAIN PANEL ---
st.title("📦 Round Ready")
st.caption("Precision Navigation")

tab1, tab2 = st.tabs(["New Search", "Add to Library"])

with tab1:
    st.subheader("Quick Launch")
    w3w_input = st.text_input("Enter 3 words (e.g. filled.count.soap):").strip().lower()
    
    if st.button("🚀 START NAVIGATION"):
        try:
            res = geocoder.convert_to_coordinates(w3w_input)
            lat, lng = res['coordinates']['lat'], res['coordinates']['lng']
            nav_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}&travelmode=driving&dir_action=navigate"
            st.link_button("Open Locked GPS", nav_url)
        except:
            st.error("Could not convert. If you're on the Free Plan, use the 'Add to Library' tab to save this spot manually first.")

with tab2:
    st.subheader("Save a New Cheat")
    new_name = st.text_input("Farm or House Name:")
    new_w3w = st.text_input("3 Word Address (for your records):")
    location_input = st.text_input("Paste Google Maps Link (for the coordinates):")
    new_note = st.text_input("Driver's Tip (e.g. 'Hidden gate on left'):")
    
    if st.button("💾 SAVE FARM TO LIBRARY"):
        lat, lng = extract_coords_from_url(location_input)
        if lat and lng and new_name:
            save_to_library(new_name, new_w3w, lat, lng, new_note)
            st.success(f"Saved {new_name}! You can now find it in the sidebar.")
        else:
            st.error("Please provide a Name and a valid Google Maps Link.")