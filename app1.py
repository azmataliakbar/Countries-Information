import streamlit as st
import requests
import pandas as pd
from PIL import Image
from io import BytesIO
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

# Set page configuration
st.set_page_config(
    page_title="Country Information Cards",
    page_icon="🌎",
    layout="wide"
)

# Custom CSS for colorful text
st.markdown("""
<style>
    .title {
        color: #FF5A5F;
        font-size: 150px;
        font-weight: bold;
        text-align: center;
    }
    .subtitle {
        color: #00CED1;
        font-size: 50px;
        text-align: center;
        margin-bottom: 30px;
    }
    .country-name {
        color: #6A0DAD;
        font-size: 24px;
        font-weight: bold;
    }
    .info-label {
        color: #FF8C00;
        font-weight: bold;
    }
    .info-value {
        color: #228B22;
    }
    .card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# App title and description
st.markdown('<h1 style="color: red; text-align: center;">🌎 Country Information 🌎</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#02ecf0; text-align: center; font-size:15px; font-weight: bold;" class="country-name"">Explore countries around the world with colorful information</p>', unsafe_allow_html=True)

# Function to fetch country data


@st.cache_data
def fetch_countries():
    try:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount('https://', adapter)

        url = "https://restcountries.com/v3.1/all?fields=name,capital,flags,region,subregion,population,languages,currencies,maps"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching country data: {e}")
        return []


# Function to format population
def format_population(population):
    if population >= 1_000_000_000:
        return f"{population / 1_000_000_000:.2f} billion"
    elif population >= 1_000_000:
        return f"{population / 1_000_000:.2f} million"
    elif population >= 1_000:
        return f"{population / 1_000:.2f} thousand"
    else:
        return str(population)

# Fetch country data
countries = fetch_countries()

# Sidebar for filtering
st.sidebar.markdown('<p style="color:#FF5A5F; font-size:35px; font-weight:bold;">Filter Countries</p>', unsafe_allow_html=True)

# Search by name
search_term = st.sidebar.text_input("Search by country name", "")

# Filter by region
regions = ["All"] + sorted(list(set([country.get('region', 'Unknown') for country in countries if 'region' in country])))
selected_region = st.sidebar.selectbox("Select Region", regions)

# Filter by population
population_ranges = [
    "All",
    "Less than 1 million",
    "1-10 million",
    "10-100 million",
    "More than 100 million"
]
selected_pop_range = st.sidebar.selectbox("Population Range", population_ranges)

# Apply filters
filtered_countries = countries

# Filter by name
if search_term:
    filtered_countries = [
        country for country in filtered_countries 
        if search_term.lower() in country.get('name', {}).get('common', '').lower()
    ]

# Filter by region
if selected_region != "All":
    filtered_countries = [
        country for country in filtered_countries
        if country.get('region') == selected_region
    ]

# Filter by population
if selected_pop_range != "All":
    if selected_pop_range == "Less than 1 million":
        filtered_countries = [country for country in filtered_countries if country.get('population', 0) < 1_000_000]
    elif selected_pop_range == "1-10 million":
        filtered_countries = [country for country in filtered_countries if 1_000_000 <= country.get('population', 0) < 10_000_000]
    elif selected_pop_range == "10-100 million":
        filtered_countries = [country for country in filtered_countries if 10_000_000 <= country.get('population', 0) < 100_000_000]
    elif selected_pop_range == "More than 100 million":
        filtered_countries = [country for country in filtered_countries if country.get('population', 0) >= 100_000_000]

# Sort countries by name
filtered_countries = sorted(filtered_countries, key=lambda x: x.get('name', {}).get('common', ''))

# Display country count
st.markdown(f'<p style="color:#fc08f0; font-size:30px; font-weight: bold; text-align:center;">Showing {len(filtered_countries)} countries</p>', unsafe_allow_html=True)

# Display countries in a grid
cols_per_row = 3
for i in range(0, len(filtered_countries), cols_per_row):
    cols = st.columns(cols_per_row)
    for j in range(cols_per_row):
        if i + j < len(filtered_countries):
            country = filtered_countries[i + j]
            with cols[j]:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                
                # Flag and country name
                flag_url = country.get('flags', {}).get('png', '')
                country_name = country.get('name', {}).get('common', 'Unknown')
                
                if flag_url:
                    try:
                        response = requests.get(flag_url)
                        img = Image.open(BytesIO(response.content))
                        st.image(img, width=200)
                    except (requests.exceptions.RequestException, Image.UnidentifiedImageError, IOError) as e:
                        st.markdown("🏳️ Flag not available")
                
                st.markdown(f'<p style="color:#02ecf0; font-size:30px; font-weight: bold;" class="country-name"">{country_name}</p>', unsafe_allow_html=True)
                
                # Country information
                capital = country.get('capital', ['Unknown'])[0] if country.get('capital') else 'Unknown'
                region = country.get('region', 'Unknown')
                subregion = country.get('subregion', 'Unknown')
                population = format_population(country.get('population', 0))
                languages = ', '.join(country.get('languages', {}).values()) if country.get('languages') else 'Unknown'
                currencies = ', '.join([f"{curr.get('name', 'Unknown')} ({curr.get('symbol', 'Unknown')})" 
                for curr in country.get('currencies', {}).values()]) if country.get('currencies') else 'Unknown'
                
                info = [
                    ("Capital", capital),
                    ("Region", region),
                    ("Subregion", subregion),
                    ("Population", population),
                    ("Languages", languages),
                    ("Currencies", currencies)
                ]
                
                for label, value in info:
                    st.markdown(f'<span class="info-label">{label}:</span> <span class="info-value">{value}</span><br>', unsafe_allow_html=True)
                
                # Google Maps link
                if 'maps' in country and 'googleMaps' in country['maps']:
                    st.markdown(f'<a href="{country["maps"]["googleMaps"]}" target="_blank" style="color:#1E90FF;">View on Google Maps</a>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

                

# Footer
st.markdown("""
<div style="text-align:center; margin-top:30px; padding:10px; background-color:#f0f0f0; border-radius:5px;">
    <p style="color:#FF5A5F; font-size: 20px; font-weight: bold;">Created with Streamlit</p>
    <p style="color:#00CED1; font-size: 20px; font-weight: bold;">Data from <a href="https://restcountries.com" style="color:#00CED1;">REST Countries API</a></p>
</div>
""", unsafe_allow_html=True)

st.markdown('<h4 style="color: red; text-align: center;">📓✒️ Author: Azmat Ali 📓✒️</h4>', unsafe_allow_html=True)

# Add information about how to run and deploy
with st.expander("How to Run and Deploy This App"):
    st.markdown("""
    ### Running Locally
    1. Save this code as `app.py`
    2. Install required packages:"
    3. Create a GitHub repository and push this code
    4. Create a `requirements.txt` file with:"
    5. Go to [Streamlit Cloud](https://streamlit.io/cloud)
    6. Sign in with GitHub
    7. Click "New app"
    8. Select your repository, branch, and set the main file path to `app.py`
    9. Click "Deploy"
    """)