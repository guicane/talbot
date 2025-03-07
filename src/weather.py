from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import requests
import os
import logging
from bs4 import BeautifulSoup

# Enable logging to file with script name as prefix
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - [Weather] %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_debug.log"),  # Log to a file
        logging.StreamHandler()  # Log to console as well
    ]
)
logger = logging.getLogger(__name__)

# Function to fetch the weather from wx.ja91.uk for Saltney
def get_saltney_weather() -> str:
    url = "http://wx.ja91.uk/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        temperature_element = soup.find(text="Outside Temperature")
        
        if temperature_element:
            temperature_value = temperature_element.find_next().text.strip()
            return f"Current Outside Temperature in Saltney: {temperature_value}\nProvided to you by Jake's Weather Station\nhttp://wx.ja91.uk"
        else:
            logger.warning("Could not find 'Outside Temperature' field on wx.ja91.uk")
            return "Weather data for Saltney is unavailable."
    except requests.RequestException as e:
        logger.error(f"Error fetching Saltney weather: {e}")
        return "Unable to retrieve Saltney weather at this time."

# Function to get current weather for a given location or UK postcode using Open-Meteo API
def get_weather(location: str) -> str:
    if location.lower() == "saltney":
        return get_saltney_weather()
    
    logger.info(f"Fetching weather for: {location}")
    geocode_data = None
    
    # Check if input is a UK postcode (basic pattern matching)
    if location.replace(" ", "").isalnum() and any(char.isdigit() for char in location):
        logger.info("Detected UK postcode, using Nominatim geocoding")
        geocode_url = f"https://nominatim.openstreetmap.org/search?format=json&q={location}, UK"
        geocode_response = requests.get(geocode_url, headers={"User-Agent": "Mozilla/5.0"})
        
        if geocode_response.status_code == 200 and geocode_response.json():
            geocode_data = geocode_response.json()[0]
            latitude, longitude = float(geocode_data['lat']), float(geocode_data['lon'])
            logger.info(f"Geocoded {location} to lat: {latitude}, lon: {longitude}")
    
    # If no valid data from Nominatim, try Open-Meteo's geocoding API for city names
    if not geocode_data:
        logger.info("Using Open-Meteo's geocoding API")
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=en&format=json"
        geocode_response = requests.get(geocode_url)
        
        if geocode_response.status_code == 200 and 'results' in geocode_response.json():
            geocode_data = geocode_response.json()['results'][0]
            latitude, longitude = float(geocode_data['latitude']), float(geocode_data['longitude'])
            logger.info(f"Geocoded {location} to lat: {latitude}, lon: {longitude}")
    
    if not geocode_data:
        logger.warning(f"Location not found: {location}")
        return "Location not found. Please enter a valid city name or UK postcode."
    
    # Weather API to get current weather
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
    weather_response = requests.get(weather_url)
    
    if weather_response.status_code == 200:
        weather_data = weather_response.json()['current_weather']
        temperature = weather_data['temperature']
        weather_description = "Rainy" if weather_data['weathercode'] in [61, 63, 65, 80, 81, 82] else "Clear/Cloudy"
        logger.info(f"Weather data: {temperature}°C, Condition: {weather_description}")
        
        return f"Current weather in {location}:\n🌡 Temperature: {temperature}°C\n☁ Condition: {weather_description}"
    else:
        logger.error(f"Error fetching weather data: {weather_response.text}")
        return "Error retrieving weather data. Please try again later."

# Telegram command handler for /weather
async def weather_command(update: Update, context: CallbackContext) -> None:
    logger.info(f"Received /weather command from user {update.message.from_user.id}")
    if not context.args:
        logger.warning("No location provided with /weather command")
        await context.bot.send_message(chat_id=update.message.chat_id, text="Usage: /weather <city or UK postcode>")
        return
    
    location = " ".join(context.args)
    weather_report = get_weather(location)
    logger.info(f"Sending weather report for {location}")
    
    await context.bot.send_message(chat_id=update.message.chat_id, text=weather_report)

# Function to register the /weather command
def register_weather_handler(app: Application) -> None:
    from telegram.ext import Application  # Ensure Application is imported
    logger.info("Registering /weather command handler")
    app.add_handler(CommandHandler("weather", weather_command))
