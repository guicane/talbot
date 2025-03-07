from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
import requests
import logging
import os

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - [IMDb] %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# OMDB API Key (Get one from https://www.omdbapi.com/apikey.aspx)
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
if not OMDB_API_KEY:
    raise ValueError("OMDB_API_KEY environment variable is not set!")

# Function to fetch a list of potential movie matches
def search_movies(movie_name: str):
    url = f"https://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={movie_name}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("Response") == "True" and "Search" in data:
            return data["Search"]  # Returns a list of potential matches
        else:
            return None
    except requests.RequestException as e:
        logger.error(f"Error fetching movie search results: {e}")
        return None

# Function to fetch detailed movie information
def get_movie_info(movie_id: str) -> str:
    url = f"http://www.omdbapi.com/?i={movie_id}&apikey={OMDB_API_KEY}&plot=short"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data["Response"] == "True":
            title = data["Title"]
            year = data["Year"]
            plot = data["Plot"]
            imdbID = data["imdbID"]
            imdb_rating = data["imdbRating"]
            rotten_tomatoes = data
            # Extract Rotten Tomatoes rating if available
            rotten_tomatoes_rating = "N/A"
            if "Ratings" in data:
                for rating in data["Ratings"]:
                    if rating["Source"] == "Rotten Tomatoes":
                        rotten_tomatoes_rating = rating["Value"]
                        break

            return (f"🎬 [{title}](https://www.imdb.com/title/{imdbID}/) ({year})\n"
                    f"⭐ IMDb Score: {imdb_rating}/10\n🍅 Rotten Tomatoes: {rotten_tomatoes_rating}\n"
                    f"📖 {plot}")

        else:
            return "Movie details not found. Please try again."
    except requests.RequestException as e:
        logger.error(f"Error fetching movie details: {e}")
        return "Error retrieving movie details. Please try again later."

# Telegram command handler for /imdb
async def imdb_command(update: Update, context: CallbackContext) -> None:
    logger.info(f"Received /imdb command from user {update.message.from_user.id}")
    
    if not context.args:
        await context.bot.send_message(chat_id=update.message.chat_id, text="Usage: /imdb <movie name>")
        return
    
    movie_name = " ".join(context.args)
    movie_results = search_movies(movie_name)
    
    if not movie_results:
        await context.bot.send_message(chat_id=update.message.chat_id, text="No matches found. Please refine your search.")
        return
    
    if len(movie_results) == 1:
        # If only one result, fetch and display movie info immediately
        movie_info = get_movie_info(movie_results[0]['imdbID'])
        await context.bot.send_message(chat_id=update.message.chat_id, text=movie_info, parse_mode="Markdown")
        return
    
    keyboard = []
    for movie in movie_results[:5]:  # Limit to first 5 matches
        keyboard.append([
            InlineKeyboardButton(f"{movie['Title']} ({movie['Year']})", callback_data=f"movie_{movie['imdbID']}")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.message.chat_id, text="Please select a movie:", reply_markup=reply_markup)

# Callback handler when user selects a movie from inline buttons
async def movie_selection(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    movie_id = query.data.split("_")[1]  # Extract IMDb ID from callback data
    movie_info = get_movie_info(movie_id)
    
    await query.edit_message_text(text=movie_info, parse_mode="Markdown")

# Function to register the /imdb command and callback handler
def register_imdb_handler(app):
    logger.info("Registering /imdb command handler and callback query handler")
    app.add_handler(CommandHandler("imdb", imdb_command))
    app.add_handler(CallbackQueryHandler(movie_selection, pattern="^movie_.*"))
