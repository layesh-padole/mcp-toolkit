#!/usr/bin/env python3
"""
Simple Weather MCP Server - Provides current weather and forecast data via OpenWeather API
"""
import os
import sys
import logging
from datetime import datetime
import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("weather-server")

# Initialize MCP server
mcp = FastMCP("weather")

# Configuration
API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5"

# === UTILITY FUNCTIONS ===

def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9/5) + 32

def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return (fahrenheit - 32) * 5/9

def kelvin_to_celsius(kelvin: float) -> float:
    """Convert Kelvin to Celsius."""
    return kelvin - 273.15

def kelvin_to_fahrenheit(kelvin: float) -> float:
    """Convert Kelvin to Fahrenheit."""
    return (kelvin - 273.15) * 9/5 + 32

def format_weather_data(data: dict, units: str = "metric") -> str:
    """Format weather data into a readable string."""
    try:
        city = data.get("name", "Unknown")
        country = data.get("sys", {}).get("country", "")
        
        # Temperature
        main = data.get("main", {})
        temp = main.get("temp", 0)
        feels_like = main.get("feels_like", 0)
        temp_min = main.get("temp_min", 0)
        temp_max = main.get("temp_max", 0)
        
        # Weather description
        weather = data.get("weather", [{}])[0]
        description = weather.get("description", "").title()
        
        # Other data
        humidity = main.get("humidity", 0)
        pressure = main.get("pressure", 0)
        wind = data.get("wind", {})
        wind_speed = wind.get("speed", 0)
        clouds = data.get("clouds", {}).get("all", 0)
        
        # Unit symbols
        temp_unit = "°C" if units == "metric" else "°F"
        speed_unit = "m/s" if units == "metric" else "mph"
        
        result = f"""🌍 **{city}, {country}**

🌡️ **Temperature:** {temp:.1f}{temp_unit}
   Feels like: {feels_like:.1f}{temp_unit}
   Min: {temp_min:.1f}{temp_unit} | Max: {temp_max:.1f}{temp_unit}

☁️ **Conditions:** {description}
💧 **Humidity:** {humidity}%
🌪️ **Wind Speed:** {wind_speed:.1f} {speed_unit}
📊 **Pressure:** {pressure} hPa
☁️ **Cloudiness:** {clouds}%"""
        
        return result
    except Exception as e:
        logger.error(f"Error formatting weather data: {e}")
        return f"❌ Error formatting weather data: {str(e)}"

def format_forecast_data(data: dict, units: str = "metric") -> str:
    """Format 5-day forecast data into a readable string."""
    try:
        city = data.get("city", {}).get("name", "Unknown")
        country = data.get("city", {}).get("country", "")
        forecast_list = data.get("list", [])
        
        if not forecast_list:
            return "❌ No forecast data available"
        
        temp_unit = "°C" if units == "metric" else "°F"
        
        result = f"📅 **5-Day Forecast for {city}, {country}**\n\n"
        
        # Group by day
        current_date = ""
        for item in forecast_list:
            dt = datetime.fromtimestamp(item.get("dt", 0))
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M")
            
            # Add date header for new day
            if date_str != current_date:
                if current_date:
                    result += "\n"
                result += f"📆 **{dt.strftime('%A, %B %d')}**\n"
                current_date = date_str
            
            # Weather info
            main = item.get("main", {})
            temp = main.get("temp", 0)
            weather = item.get("weather", [{}])[0]
            description = weather.get("description", "").title()
            
            result += f"  ⏰ {time_str}: {temp:.1f}{temp_unit} - {description}\n"
        
        return result
    except Exception as e:
        logger.error(f"Error formatting forecast data: {e}")
        return f"❌ Error formatting forecast data: {str(e)}"

# === MCP TOOLS ===

@mcp.tool()
async def get_current_weather(city: str = "", units: str = "metric") -> str:
    """Get current weather for a city using OpenWeather API, supports metric (Celsius) or imperial (Fahrenheit) units."""
    logger.info(f"Getting current weather for {city} in {units} units")
    
    if not city.strip():
        return "❌ Error: City name is required"
    
    if not API_KEY.strip():
        return "❌ Error: OPENWEATHER_API_KEY not configured. Please set it in Docker secrets."
    
    if units not in ["metric", "imperial"]:
        return "❌ Error: Units must be 'metric' (Celsius) or 'imperial' (Fahrenheit)"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/weather",
                params={
                    "q": city,
                    "appid": API_KEY,
                    "units": units
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return format_weather_data(data, units)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"❌ City not found: {city}"
        elif e.response.status_code == 401:
            return "❌ Invalid API key. Please check your OPENWEATHER_API_KEY."
        else:
            return f"❌ API Error: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def get_forecast(city: str = "", units: str = "metric") -> str:
    """Get 5-day weather forecast for a city with 3-hour intervals, supports metric (Celsius) or imperial (Fahrenheit) units."""
    logger.info(f"Getting forecast for {city} in {units} units")
    
    if not city.strip():
        return "❌ Error: City name is required"
    
    if not API_KEY.strip():
        return "❌ Error: OPENWEATHER_API_KEY not configured. Please set it in Docker secrets."
    
    if units not in ["metric", "imperial"]:
        return "❌ Error: Units must be 'metric' (Celsius) or 'imperial' (Fahrenheit)"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/forecast",
                params={
                    "q": city,
                    "appid": API_KEY,
                    "units": units
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return format_forecast_data(data, units)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"❌ City not found: {city}"
        elif e.response.status_code == 401:
            return "❌ Invalid API key. Please check your OPENWEATHER_API_KEY."
        else:
            return f"❌ API Error: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Error getting forecast: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def convert_temperature(temperature: str = "", from_unit: str = "", to_unit: str = "") -> str:
    """Convert temperature between Celsius, Fahrenheit, and Kelvin units."""
    logger.info(f"Converting {temperature} from {from_unit} to {to_unit}")
    
    if not temperature.strip():
        return "❌ Error: Temperature value is required"
    
    if not from_unit.strip() or not to_unit.strip():
        return "❌ Error: Both from_unit and to_unit are required"
    
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    valid_units = ["celsius", "fahrenheit", "kelvin", "c", "f", "k"]
    if from_unit not in valid_units or to_unit not in valid_units:
        return "❌ Error: Units must be 'celsius'/'c', 'fahrenheit'/'f', or 'kelvin'/'k'"
    
    try:
        temp_value = float(temperature)
    except ValueError:
        return f"❌ Error: Invalid temperature value: {temperature}"
    
    # Normalize unit names
    from_unit = "celsius" if from_unit == "c" else from_unit
    from_unit = "fahrenheit" if from_unit == "f" else from_unit
    from_unit = "kelvin" if from_unit == "k" else from_unit
    to_unit = "celsius" if to_unit == "c" else to_unit
    to_unit = "fahrenheit" if to_unit == "f" else to_unit
    to_unit = "kelvin" if to_unit == "k" else to_unit
    
    if from_unit == to_unit:
        return f"✅ {temp_value}° {from_unit.title()} = {temp_value}° {to_unit.title()}"
    
    try:
        # Convert to Celsius first
        if from_unit == "celsius":
            celsius = temp_value
        elif from_unit == "fahrenheit":
            celsius = fahrenheit_to_celsius(temp_value)
        else:  # kelvin
            celsius = kelvin_to_celsius(temp_value)
        
        # Convert from Celsius to target unit
        if to_unit == "celsius":
            result = celsius
        elif to_unit == "fahrenheit":
            result = celsius_to_fahrenheit(celsius)
        else:  # kelvin
            result = celsius + 273.15
        
        # Format unit symbols
        from_symbol = "°C" if from_unit == "celsius" else ("°F" if from_unit == "fahrenheit" else "K")
        to_symbol = "°C" if to_unit == "celsius" else ("°F" if to_unit == "fahrenheit" else "K")
        
        return f"🌡️ **Temperature Conversion**\n{temp_value}{from_symbol} = {result:.2f}{to_symbol}"
    except Exception as e:
        logger.error(f"Error converting temperature: {e}")
        return f"❌ Error: {str(e)}"

# === SERVER STARTUP ===
if __name__ == "__main__":
    logger.info("Starting Weather MCP server...")
    
    if not API_KEY:
        logger.warning("OPENWEATHER_API_KEY not set - tools will fail until configured")
    
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)