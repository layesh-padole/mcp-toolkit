import json
import os
from dotenv import load_dotenv
load_dotenv()
import requests
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# this code will help me get structured output
class WeatherResponse(BaseModel):
    temperature: float
    apparent_temperature: float
    humidity: int
    wind_speed: float
    precipitation: float
    response: str  # natural language answer

# Tool 1: Geocoding
def get_coordinates(location: str) -> dict:
    """Get latitude and longitude for a given location name."""
    print("✅ get_coordinates tool called")
    url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
    r = requests.get(url, headers={"User-Agent": "Gemini-Demo"})
    data = r.json()
    #print(data)
    if not data:
        return {"error": "Location not found"}
    return {"latitude": float(data[0]["lat"]), "longitude": float(data[0]["lon"])}

# tool 2: Get weather
def get_weather(latitude: float, longitude: float) -> dict:
    """Get current weather details for given coordinates."""
    print("✅ get_weather tool called")
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        f"&current=temperature_2m,wind_speed_10m,"
        f"relative_humidity_2m,apparent_temperature,precipitation"
    )
    r = requests.get(url)
    data = r.json()
    #print(data)
    return data["current"]  # return everything

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

config = types.GenerateContentConfig(
    tools=[get_weather, get_coordinates],
    response_schema=WeatherResponse,

)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What's the weather like in Pune today?",
    config=config,
)

print(response.text)
