# AI Travel Planner

## Overview
AI Travel Planner is a Streamlit-based application that generates personalized travel itineraries using AI. It allows users to input their travel preferences either through natural language or a structured form and provides customized travel plans, including attractions and activities.

## Features
- **Natural Language Processing**: Accepts user input in free text format and converts it into structured data.
- **Custom Itinerary Generation**: Generates travel plans based on destination, budget, interests, and duration.
- **Top Attractions Retrieval**: Fetches top attractions for the selected destination.
- **User-Friendly Interface**: Offers both natural language and form-based input methods.

## Installation
### Prerequisites
Ensure you have Python installed on your system.

### Steps
1. Clone the repository or download the source code.
2. Navigate to the project directory.
3. Install the required dependencies using:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Usage
1. Open the application in your browser.
2. Choose between "Natural Language" or "Form" input methods.
3. Enter travel details and generate an itinerary.
4. View and refine your personalized travel plan.

## File Structure
- `app.py`: Main application file containing the Streamlit UI and AI logic.
- `requirements.txt`: Lists all necessary dependencies.

## Configuration
- Replace `GEMINI_API_KEY` in `app.py` with your actual API key before running the application.
- For production, store API keys securely using environment variables or a secrets manager.

