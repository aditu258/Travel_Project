import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import json
import re
from google.api_core.exceptions import NotFound

# Configure API Key (Use environment variables or secrets management in production)
GEMINI_API_KEY = "GEMINI_API_KEY"

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    st.session_state.debug_mode = False  # Initialize debug mode
except Exception as e:
    st.error(f"API Configuration Error: {str(e)}")
    st.stop()


def parse_natural_language(query):
    """
    Parses the user query and converts it into structured JSON data.
    Handles missing values, vague inputs, and assigns default values where needed.
    """
    prompt = f"""
    Convert this travel request to JSON format:
    "{query}"
    
    Required fields:
    - destination (specific location)
    - duration (in days, as a number)
    - budget ("Budget", "Mid-range", "Luxury")
    - interests (list of activities)
    - experience_type ("Most Famous", "Mix", "Offbeat Gems")
    """
    
    try:
        response = model.generate_content(prompt)
        json_str = re.sub(r'```json|```', '', response.text).strip()
        
        try:
            data = json.loads(json_str)
            required_fields = ['destination', 'duration', 'budget']
            if not all(field in data for field in required_fields):
                raise ValueError("Missing required fields")
            
            data.setdefault('interests', [])
            data.setdefault('experience_type', 'Mix')
            return data
        
        except (json.JSONDecodeError, ValueError):
            return None
    
    except Exception as e:
        if st.session_state.debug_mode:
            st.error(f"Parsing Error: {str(e)}")
        return None


def get_top_attractions(destination, experience_type="Mix"):
    """
    Retrieves top attractions for a given destination based on user preferences.
    """
    query_types = {
        "Most Famous": f"top 10 attractions in {destination}",
        "Mix": f"best things to do in {destination}",
        "Offbeat Gems": f"hidden gems in {destination}"
    }
    url = f"https://www.google.com/search?q={query_types[experience_type].replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        return [h3.text for h3 in soup.find_all("h3")[:7] if h3.text and "›" not in h3.text]
    except:
        return ["Attractions list unavailable"]


def generate_itinerary(data):
    """
    Generates a structured travel itinerary based on user inputs.
    """
    prompt = f"""
    Create a {data['duration']}-day {data['budget']} itinerary for {data['destination']}.
    
    Preferences:
    - Interests: {', '.join(data['interests'])}
    - Experience Type: {data['experience_type']}
    
    Include:
    - Suggested activities, restaurants, and transportation details.
    - Estimated costs and time allocations.
    """
    response = model.generate_content(prompt)
    return response.text

# Configure Streamlit UI
st.set_page_config(page_title="AI Travel Planner", page_icon="✈️", layout="wide")

# Sidebar options
with st.sidebar:
    st.header("Settings")
    input_mode = st.radio("Input Method:", ["Natural Language", "Form"], horizontal=True)
    st.session_state.debug_mode = st.checkbox("Debug Mode", False)

st.title("AI Travel Planner")
st.caption("Powered by AI for personalized travel planning")

if input_mode == "Natural Language":
    user_query = st.text_area("Enter your travel details:", "5 days in Kerala with nature focus")
    
    if st.button("Generate Itinerary"):
        with st.spinner("Processing..."):
            parsed_data = parse_natural_language(user_query)
            
            if parsed_data:
                attractions = get_top_attractions(parsed_data['destination'], parsed_data['experience_type'])
                itinerary = generate_itinerary(parsed_data)
                
                st.subheader(f"Top Attractions in {parsed_data['destination']}")
                st.write("\n".join([f"- {attr}" for attr in attractions[:5]]))
                
                st.subheader("Your Personalized Itinerary")
                st.markdown(itinerary)
                
                st.session_state.parsed_data = parsed_data
            else:
                st.warning("Could not process your request. Please provide more details.")

else:
    with st.form("travel_form"):
        destination = st.text_input("Destination", placeholder="e.g., Kyoto, Iceland")
        days = st.slider("Duration (days)", 1, 21, 5)
        budget = st.selectbox("Budget", ["Budget", "Mid-range", "Luxury"])
        interests = st.multiselect("Interests", ["Adventure", "Food", "History", "Nature", "Shopping", "Relaxation"], default=["Food"])
        experience_type = st.radio("Experience Type", ["Most Famous", "Mix", "Offbeat Gems"], horizontal=True)
        
        if st.form_submit_button("Generate Itinerary"):
            with st.spinner("Generating itinerary..."):
                data = {
                    "destination": destination,
                    "duration": days,
                    "budget": budget,
                    "interests": interests,
                    "experience_type": experience_type
                }
                attractions = get_top_attractions(destination, experience_type)
                itinerary = generate_itinerary(data)
                
                st.subheader(f"Top {experience_type} Attractions")
                st.write("\n".join([f"- {attr}" for attr in attractions[:5]]))
                
                st.subheader("Your Personalized Itinerary")
                st.markdown(itinerary)
                
                st.session_state.parsed_data = data

# Debug information
if st.session_state.debug_mode and 'parsed_data' in st.session_state:
    st.subheader("Debug Information")
    st.json(st.session_state.parsed_data)
