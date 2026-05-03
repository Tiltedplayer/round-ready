import streamlit as st
import json
import os
import re
import requests
import what3words

# --- CONFIGURATION ---
API_KEY = "YOUR_W3W_API_KEY" 
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

def extract_coords_from_url(url):
    """Expands short links and pulls lat/lng from the resulting long URL."""
    try:
        # If it's a short link, follow the redirect to get the long URL
        if "maps.app.goo.gl" in url or "goo.gl/maps" in url:
            response = requests.get(url, allow_redirects=True, timeout=5)
            url = response.url
        
        # Look for the @lat,lng pattern
        regex = r"@(-?\d+\.\d+),(-?\d+\.\d+)"
        match = re.search(regex, url)
        if match:
            return float(match.group(1)), float(match.group(2))
            
        # Fallback for links that use 'll=' instead of '@'
        ll_regex = r"ll=(-?\d+\.\d+),(-?\d+\.\d+)"
        ll_match = re.search(ll_regex, url)
        if ll_match:
            return float(ll_match.group(1)), float(ll_match.group(2))
            
    except Exception as e:
        st.error(f"Error reading link: {e}")
    return None, None

# --- APP INTERFACE ---
st.set_page_config(page_title="Round Ready", page_icon="📦", layout="wide")

# Custom CSS to make buttons bigger for mobile thumbs
st.markdown("""
    <style>
    div.stButton > button:first-child {
        height: 3em;
        width: 100%;
        font-size: 20px;
        font-weight: bold;
    }
    </style>""", unsafe_allow_headers=True)

# --- SIDEBAR SEARCH ---
with st.sidebar:
    st.header("🔎 Farm Library")
    library = load_library()
    search_term = st.text_input("Find Farm:").lower()
    
    if search_term:
        results = {k: v for k, v in library.items() if search_term in k}
        if results:
            for name, info in results.items():
                st.subheader(name.title())
                st.write(f"📍 {info['w3w']}")
                st.info(f"💡 {info['note']}")
                nav_url = f"https://www.google.com/maps/dir/?api=1&destination={info['lat']},{info['lng']}&travelmode=driving&dir_action=navigate"
                st.link_button(f"NAVIGATE TO {name.upper()}", nav_url)
                st.divider()

# --- MAIN PANEL ---
st.title("📦 Round Ready")
tab1, tab2 = st.tabs(["Quick Search", "Add New Farm"])

with tab1:
    st.subheader("Fast Launch")
    w3w_input = st.text_input("Enter 3 words:").strip().lower()
    
    if st.button("🚀 GO TO GATE"):
        try:
            res = geocoder.convert_to_coordinates(w3w_input)
            lat, lng = res['coordinates']['lat'], res['coordinates']['lng']
            nav_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}&travelmode=driving&dir_action=navigate"
            st.link_button("OPEN GPS", nav_url)
        except:
            st.error("API Limit reached. Use the 'Add New Farm' tab for this one!")

with tab2:
    st.subheader("Save a Cheat")
    new_name = st.text_input("Farm/House Name:")
    new_w3w = st.text_input("What3Words (Optional):")
    location_input = st.text_input("Paste Google Maps Link (Short or Long):")
    new_note = st.text_input("Delivery Note (e.g. 'Gate code 1234'):")
    
    if st.button("💾 SAVE TO MY ROUND"):
        lat, lng = extract_coords_from_url(location_input)
        if lat and lng and new_name:
            save_to_library(new_name, new_w3w, lat, lng, new_note)
            st.success(f"Successfully saved {new_name}!")
        else:
            st.error("Could not find coordinates. Make sure you dropped a pin in Google Maps first!")
