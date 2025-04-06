from fastapi import FastAPI, Query
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
import requests
import re
import json
from bs4 import BeautifulSoup
from transformers import pipeline
from duckduckgo_search import DDGS

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

# Initialize pipelines at startup to avoid loading models on every request
summarizer = None
story_generator = None

@app.on_event("startup")
async def startup_event():
    global summarizer, story_generator
    try:
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        story_generator = pipeline("text-generation", model="gpt2")
    except Exception as e:
        print(f"Warning: Failed to load NLP models: {e}")
        print("Will fallback to OpenRouter for these functions")

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

def search_web(query):
    """Search the web for legends and myths using DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        return [r['href'] for r in results if 'wikipedia' not in r['href']]
    except Exception as e:
        print(f"Search error: {e}")
        return []

def get_web_content(url):
    """Fetch and extract text content from a URL"""
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])
        return text
    except:
        return ""

def filter_relevant_text(text):
    """Filter text for sentences related to legends and myths"""
    keywords = ["ghost", "haunted", "legend", "folklore", "myth", "battle", 
                "supernatural", "cursed", "divine", "ancient", "mystery", 
                "secret", "hidden", "lost", "forgotten", "tale", "story"]
    sentences = text.split(".")
    filtered = [s for s in sentences if any(k in s.lower() for k in keywords)]
    return " ".join(filtered)

def summarize_text(text, fallback_to_openrouter=True):
    """Summarize text using local model or OpenRouter fallback"""
    global summarizer
    
    if len(text) < 200:  # Text too short to summarize
        return text
        
    try:
        if summarizer:
            # Use local transformer model
            return summarizer(text, max_length=500, min_length=200, do_sample=False)[0]['summary_text']
        elif fallback_to_openrouter:
            # Fallback to OpenRouter
            prompt = f"Summarize the following text about legends and myths:\n\n{text}\n\nSummary:"
            response = client.chat.completions.create(
                model="google/gemini-pro",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
    except Exception as e:
        print(f"Summarization error: {e}")
    
    # If everything fails, return a portion of the original text
    return text[:1000] if len(text) > 1000 else text

def generate_story(summary, destination,arrival_location,departure_location,travel_season,activity_level,transport_preference,food_preferences, fallback_to_openrouter=True):
    """Generate a mysterious story based on the summary using local model or OpenRouter fallback"""
    global story_generator
    
    try:
        if story_generator:
            # Use local transformer model
            return story_generator(summary, max_length=700, do_sample=True)[0]['generated_text']
        elif fallback_to_openrouter:
            # Fallback to OpenRouter
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
            response = client.chat.completions.create(
                model="google/gemini-pro",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
    except Exception as e:
        print(f"Story generation error: {e}")
    
    # If everything fails, return the summary
    return summary

@app.get("/")
def read_root():
    return {"message": "Welcome to Katha Yatra API - Where History Becomes Mystery"}

@app.get("/mythology/")
async def get_mythology(location: str):
    """Generate mythology and legends about a specific location"""
    try:
        print(f"Searching for mythology about: {location}")
        web_results = search_web(f"{location} myths legends folklore")
        
        if not web_results:
            # Fallback to OpenRouter if no web results
            return await generate_mythology_with_ai(location)
            
        web_text = "".join([get_web_content(url) for url in web_results])
        filtered_web = filter_relevant_text(web_text)
        
        if not filtered_web.strip():
            # Fallback to OpenRouter if no relevant content
            return await generate_mythology_with_ai(location)
        
        summary = summarize_text(filtered_web)
        story = generate_story(summary, location)
        
        return {
            "story": story,
            "source": "web_enhanced"
        }
    except Exception as e:
        print(f"Error in mythology generation: {e}")
        # Fallback to OpenRouter
        return await generate_mythology_with_ai(location)

async def generate_mythology_with_ai(location):
    """Generate mythology using AI when web search fails"""
    try:
        prompt = (
            f"Create a mysterious tale, legend or myth about {location}. "
            f"Include local folklore elements, historical events with a touch of mystery, "
            f"and supernatural elements that might intrigue travelers. "
            f"Write it as a captivating short story (about 500 words) that a local guide might tell visitors."
        )
        
        response = client.chat.completions.create(
            model="google/gemini-pro",
            messages=[{"role": "user", "content": prompt}]
        )
        
        story = response.choices[0].message.content
        
        return {
            "story": story,
            "source": "ai_generated"
        }
    except Exception as e:
        print(f"AI mythology generation error: {e}")
        return {"story": f"Mysterious tales of {location} await your discovery...", "source": "fallback"}

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
