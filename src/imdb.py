"""
Module for interacting with the OMDB API and handling the /imdb command for Telegram.
"""

import os
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler

# OMDB API Key (Get one from https://www.omdbapi.com/apikey.aspx)
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
if not OMDB_API_KEY:
    raise ValueError("OMDB_API_KEY environment variable is not set!")

def search_movies(movie_name: str):
    """
    Fetch a list of potential movie matches from the OMDB API.

    :param movie_name: The name of the movie to search for.
    :return: A list of movie matches or None if no matches are found.
    """
    url = f"https://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={movie_name}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("Response") == "True" and "Search" in data:
            return data["Search"]
        return None
    except requests.RequestException as exc:
        print("Error fetching movie search results: %s", exc)
        return None


def get_movie_info(movie_id: str) -> str:
    """
    Fetch detailed movie information from the OMDB API.

    :param movie_id: The IMDb ID of the movie.
    :return: A formatted string with movie details or an error message.
    """
    url = f"http://www.omdbapi.com/?i={movie_id}&apikey={OMDB_API_KEY}&plot=short"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data["Response"] == "True":
            title = data["Title"]
            year = data["Year"]
            plot = data["Plot"]
            imdb_id = data["imdbID"]
            imdb_rating = data["imdbRating"]
            # Extract Rotten Tomatoes rating if available
            rotten_tomatoes_rating = "N/A"
            if "Ratings" in data:
                for rating in data["Ratings"]:
                    if rating["Source"] == "Rotten Tomatoes":
                        rotten_tomatoes_rating = rating["Value"]
                        break

            return (
                f"🎬 [{title}](https://www.imdb.com/title/{imdb_id}/) ({year})\n"
                f"⭐ IMDb Score: {imdb_rating}/10\n"
                f"🍅 Rotten Tomatoes: {rotten_tomatoes_rating}\n"
                f"📖 {plot}"
            )
        return "Movie details not found. Please try again."
    except requests.RequestException as exc:
        print("Error fetching movie details: %s", exc)
        return "Error retrieving movie details. Please try again later."


async def imdb_command(update: Update, context: CallbackContext) -> None:
    """
    Handle the /imdb command for Telegram. Searches for movies and displays results.
    """
    print("Received /imdb command from user %s", update.message.from_user.id)
    if not context.args:
        await context.bot.send_message(
            chat_id=update.message.chat_id, text="Usage: /imdb <movie name>"
        )
        return

    movie_name = " ".join(context.args)
    movie_results = search_movies(movie_name)

    if not movie_results:
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="No matches found. Please refine your search."
        )
        return

    if len(movie_results) == 1:
        movie_info = get_movie_info(movie_results[0]["imdbID"])
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=movie_info,
            parse_mode="Markdown"
        )
        return

    keyboard = []
    for movie in movie_results[:5]:
        keyboard.append([
            InlineKeyboardButton(
                f"{movie['Title']} ({movie['Year']})",
                callback_data=f"movie_{movie['imdbID']}"
            )
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Please select a movie:",
        reply_markup=reply_markup
    )


async def movie_selection(update: Update, _context: CallbackContext) -> None:
    """
    Callback handler for movie selection from inline buttons.

    Fetches detailed movie info based on the user's selection and edits the message.
    """
    query = update.callback_query
    await query.answer()

    movie_id = query.data.split("_")[1]
    movie_info = get_movie_info(movie_id)
    await query.edit_message_text(text=movie_info, parse_mode="Markdown")


def register_imdb_handler(app) -> None:
    """
    Register the /imdb command and its callback query handler with the Telegram application.
    """
    print("Registering /imdb command handler and callback query handler")
    app.add_handler(CommandHandler("imdb", imdb_command))
    app.add_handler(CallbackQueryHandler(movie_selection, pattern="^movie_.*"))
