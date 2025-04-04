from fastapi import FastAPI, Query
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
import requests
import re
import json

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_API_KEY = "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"  # Replace with actual key

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def clean_text(text):
    """Remove markdown symbols and excessive newlines."""
    text = re.sub(r"[#*]+", "", text)  # Remove hashtags and asterisks
    text = re.sub(r"\n\s*\n", "\n", text)  # Remove excessive newlines
    return text.strip()

def extract_story_and_itinerary(text):
    """Extract the mystery story and structured itinerary from AI-generated text."""
    # Try to identify story and itinerary sections
    story_pattern = r"(?i)(mystery|story|tale|legend|narrative|secret|forgotten|ancient|hidden).*?(?=Day 1|Day One|\nDay|\n\nDay)"
    story_match = re.search(story_pattern, text, re.DOTALL)

    story = ""
    itinerary_text = text
    
    if story_match:
        story = story_match.group(0).strip()
        # Remove the story part from the itinerary text
        itinerary_text = text[story_match.end():].strip()
    
    structured_itinerary = structure_itinerary(itinerary_text)
    
    return {
        "story": story,
        "itinerary": structured_itinerary
    }

def structure_itinerary(text):
    """Convert AI-generated text into a structured JSON format for morning, afternoon, and evening segments."""
    itinerary = {}
    current_day = None
    current_period = None
    
    # Extract historical significance for each place
    historical_notes = {}
    
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Detecting "Day" headers
        if re.match(r"(?i)^Day\s*\d+", line):
            current_day = line
            itinerary[current_day] = {"morning": [], "afternoon": [], "evening": []}
            current_period = None  # Reset period when new day starts

        # Detecting time periods
        elif re.match(r"(?i)morning", line):
            current_period = "morning"
        elif re.match(r"(?i)afternoon", line):
            current_period = "afternoon"
        elif re.match(r"(?i)evening", line):
            current_period = "evening"

        # Assigning activities to the correct time period
        elif current_day and current_period:
            # Check if this is a description or a place name
            place_match = re.match(r"^(.+?)(?:\s*[-:]\s*(.+))?$", line)
            if place_match:
                place_name = place_match.group(1).strip()
                description = place_match.group(2).strip() if place_match.group(2) else ""
                
                # Add to itinerary
                place_info = {
                    "name": place_name,
                    "description": description
                }
                
                itinerary[current_day][current_period].append(place_info)
                
                # Extract historical significance
                if description and any(keyword in description.lower() for keyword in ["ancient", "historical", "century", "built", "dynasty", "legend", "myth", "king", "queen", "archaeological"]):
                    historical_notes[place_name] = description

    return {
        "schedule": itinerary,
        "historical_notes": historical_notes
    }

@app.get("/")
def read_root():
    return {"message": "Welcome to Katha Yatra API - Where History Becomes Mystery"}

@app.get("/itinerary/")
def generate_itinerary(
    destination: str,
    arrival_location: str = Query(..., description="User's arrival location (e.g., airport/city)"),
    departure_location: str = Query(..., description="User's departure location"),
    travel_season: str = Query(..., description="Preferred travel season (e.g., Summer, Winter)"),
    activity_level: str = Query(..., description="User's comfort level with physical activity (e.g., Light, Moderate, High)"),
    transport_preference: str = Query(..., description="Preferred mode of transport (e.g., Private Car, Public Transport)"),
    food_preferences: str = Query(..., description="Food preferences and dietary restrictions")
):
    if not OPENROUTER_API_KEY:
        return {"error": "Missing API key. Set OPENROUTER_API_KEY in the environment."}

    prompt = (
        f"Create a mysterious historical adventure for a traveler to {destination}. Start with an intriguing mystery "
        f"or legend about {destination} that weaves through the locations in the itinerary. Make the story feel like "
        f"the traveler is uncovering hidden secrets or solving a historical mystery as they visit each location. "
        f"\n\nAfter the story introduction, provide a detailed 3-day itinerary that feels like chapters in this mystery. "
        f"For each location, include a brief note about its historical significance or connection to the mystery. "
        
        f"\n\nUser details: Arriving from {arrival_location}, departing from {departure_location}. "
        f"Preferred season: {travel_season}. Activity level: {activity_level}. "
        f"Preferred transport: {transport_preference}. Food preferences: {food_preferences}. "
        
        f"\n\nStructure the itinerary by day, dividing each day into Morning, Afternoon, and Evening sections. "
        f"Include must-visit places, cultural experiences, and food suggestions that relate to the historical mystery. "
        f"For each place, provide the name followed by a colon and a brief description including its historical significance."
    )

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={"model": "google/gemini-pro-vision", "messages": [{"role": "user", "content": prompt}]}
        )

        if response.status_code == 200:
            data = response.json()
            raw_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            cleaned_text = clean_text(raw_text)
            content = extract_story_and_itinerary(cleaned_text)

            return content

        return {"error": f"Failed to fetch itinerary: {response.text}"}

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

@app.get("/mysteryimage/")
def generate_mystery_image(query: str):
    """Generate a mysterious version of the search query for better image results"""
    mysterious_terms = ["ancient", "mysterious", "historical", "enigmatic", "hidden", "secret"]
    enhanced_query = f"{query} {mysterious_terms[hash(query) % len(mysterious_terms)]}"
    return {"enhanced_query": enhanced_query}
