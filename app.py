import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import json
import re
from google.api_core.exceptions import NotFound

# Configure API Key (Use environment variables or secrets management in production)
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


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
    
    Optional fields with defaults:
    - budget ("Budget", "Mid-range", "Luxury") - default to "Mid-range"
    - interests (list of activities) - extract from context
    - experience_type ("Most Famous", "Mix", "Offbeat Gems") - default to "Mix"
    
    Example output for "5 days in Kerala with nature focus":
    {{
        "destination": "Kerala",
        "duration": 5,
        "budget": "Mid-range",
        "interests": ["Nature"],
        "experience_type": "Mix"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        if st.session_state.debug_mode:
            st.write("Raw API Response:", response.text)
            
        json_str = re.sub(r'```json|```', '', response.text).strip()
        
        try:
            data = json.loads(json_str)
            required_fields = ['destination', 'duration']
            if not all(field in data for field in required_fields):
                raise ValueError("Missing required fields")
            
            data.setdefault('budget', 'Mid-range')
            data.setdefault('interests', [])
            data.setdefault('experience_type', 'Mix')
            
            # Clean up interests if provided
            if 'interests' in data and isinstance(data['interests'], str):
                data['interests'] = [data['interests']]
            
            if st.session_state.debug_mode:
                st.write("Parsed Data:", data)
            return data
        
        except (json.JSONDecodeError, ValueError) as e:
            if st.session_state.debug_mode:
                st.error(f"JSON Parsing Error: {str(e)}")
                st.write("Problematic JSON string:", json_str)
            return None
    
    except Exception as e:
        if st.session_state.debug_mode:
            st.error(f"API Error: {str(e)}")
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
    except Exception as e:
        if st.session_state.debug_mode:
            st.error(f"Attractions Error: {str(e)}")
        return ["Attractions list unavailable"]


def generate_itinerary(data):
    """
    Generates a structured travel itinerary based on user inputs.
    """
    prompt = f"""
    Create a detailed {data['duration']}-day {data['budget']} itinerary for {data['destination']}.
    
    Preferences:
    - Interests: {', '.join(data['interests']) if data['interests'] else 'Not specified'}
    - Experience Type: {data['experience_type']}
    
    Include these sections for each day:
    - Morning activities
    - Afternoon activities
    - Evening activities
    - Recommended dining options matching the budget
    - Transportation tips between locations
    
    Format the response in markdown with clear headings.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        if st.session_state.debug_mode:
            st.error(f"Itinerary Generation Error: {str(e)}")
        return "Could not generate itinerary. Please try again with more details."


# Configure Streamlit UI
st.set_page_config(page_title="AI Travel Planner", page_icon="✈️", layout="wide")

# Sidebar options
with st.sidebar:
    st.header("Settings")
    input_mode = st.radio("Input Method:", ["Natural Language", "Form"], horizontal=True)
    st.session_state.debug_mode = st.checkbox("Debug Mode", False)
    if st.session_state.debug_mode:
        st.info("Debug mode activated. Additional information will be shown.")

st.title("AI Travel Planner")
st.caption("Powered by AI for personalized travel planning")

if input_mode == "Natural Language":
    user_query = st.text_area(
        "Enter your travel details:", 
        placeholder="e.g., '5 days in Kerala with nature focus, mid-range budget'",
        value="5 days in Kerala with nature focus"
    )
    
    if st.button("Generate Itinerary"):
        # Basic input validation
        if not user_query or len(user_query.split()) < 5:
            st.warning("Please provide more details about your trip (destination, duration, and interests)")
            st.stop()
            
        with st.spinner("Processing your request..."):
            parsed_data = parse_natural_language(user_query)
            
            if parsed_data:
                st.success("Successfully parsed your request!")
                
                with st.expander("Show parsed details", expanded=False):
                    st.json(parsed_data)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(f"Top {parsed_data['experience_type']} Attractions")
                    attractions = get_top_attractions(parsed_data['destination'], parsed_data['experience_type'])
                    st.write("\n".join([f"- {attr}" for attr in attractions[:5]]))
                
                with col2:
                    st.subheader("Trip Summary")
                    st.write(f"**Destination:** {parsed_data['destination']}")
                    st.write(f"**Duration:** {parsed_data['duration']} days")
                    st.write(f"**Budget:** {parsed_data['budget']}")
                    st.write(f"**Interests:** {', '.join(parsed_data['interests']) if parsed_data['interests'] else 'Not specified'}")
                
                st.subheader("Your Personalized Itinerary")
                itinerary = generate_itinerary(parsed_data)
                st.markdown(itinerary)
                
                st.session_state.parsed_data = parsed_data
            else:
                st.error("Could not process your request. Please include:")
                st.markdown("""
                - Destination (e.g., "Kerala")
                - Duration (e.g., "5 days")
                - Optional: Budget level, specific interests
                """)
                if st.session_state.debug_mode:
                    st.write("Debug: Parsing returned None")

else:  # Form input mode
    with st.form("travel_form"):
        st.subheader("Enter Trip Details")
        destination = st.text_input("Destination", placeholder="e.g., Kerala, Japan")
        days = st.slider("Duration (days)", 1, 21, 5)
        budget = st.selectbox("Budget", ["Budget", "Mid-range", "Luxury"], index=1)
        interests = st.multiselect("Interests", 
                                 ["Adventure", "Food", "History", "Nature", "Shopping", "Relaxation", "Culture"],
                                 default=["Nature"])
        experience_type = st.radio("Experience Type", 
                                 ["Most Famous", "Mix", "Offbeat Gems"], 
                                 horizontal=True, index=1)
        
        if st.form_submit_button("Generate Itinerary"):
            with st.spinner("Creating your personalized itinerary..."):
                data = {
                    "destination": destination,
                    "duration": days,
                    "budget": budget,
                    "interests": interests,
                    "experience_type": experience_type
                }
                
                st.session_state.parsed_data = data
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(f"Top {experience_type} Attractions")
                    attractions = get_top_attractions(destination, experience_type)
                    st.write("\n".join([f"- {attr}" for attr in attractions[:5]]))
                
                with col2:
                    st.subheader("Trip Summary")
                    st.write(f"**Destination:** {destination}")
                    st.write(f"**Duration:** {days} days")
                    st.write(f"**Budget:** {budget}")
                    st.write(f"**Interests:** {', '.join(interests)}")
                
                st.subheader("Your Personalized Itinerary")
                itinerary = generate_itinerary(data)
                st.markdown(itinerary)

# Debug information
if st.session_state.debug_mode and 'parsed_data' in st.session_state:
    st.subheader("Debug Information")
    st.json(st.session_state.parsed_data)