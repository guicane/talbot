""""
Bitcoin to USD Exchange Rate Graph
"""

from datetime import datetime
import io
import asyncio
import pandas as pd
import requests
from telegram.ext import CommandHandler
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # pylint: disable=wrong-import-position

def get_usd_brl_data(days=30):
    """
    Fetch USD/BRL exchange rate data for the specified number of days.
    
    Args:
        days (int): Number of days of historical data to fetch
        
    Returns:
        pandas.DataFrame: DataFrame with dates and exchange rates
    """
    url = f"https://economia.awesomeapi.com.br/json/daily/USD-BRL/{days}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if not response.ok or not isinstance(data, list):
            return None

        # Process the data
        dates = []
        rates = []

        for item in data:
            ts = int(item.get("timestamp"))
            rate = float(item.get("bid"))
            date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            dates.append(date_str)
            rates.append(rate)

        # Create DataFrame
        df = pd.DataFrame({
            'date': pd.to_datetime(dates),
            'rate': rates
        }).sort_values('date')

        return df

    except requests.RequestException as e:
        print(f"Request error fetching exchange rate data: {e}")
        return None
    except pd.errors.EmptyDataError as e:
        print(f"DataFrame error in exchange rate data: {e}")
        return None
    except ValueError as e:
        print(f"JSON parsing error in exchange rate data: {e}")
        return None
    except KeyError as e:
        print(f"Missing key in exchange rate data: {e}")
        return None

def create_usd_brl_graph(days=30, chart_title="USD/BRL Exchange Rate"):
    """
    Create a graph of the USD/BRL exchange rate.
    
    Args:
        days (int): Number of days of historical data to show
        chart_title (str): Title for the chart
        
    Returns:
        bytes: Raw image bytes that can be sent by the bot
        dict: Summary statistics of the exchange rate
    """
    df = get_usd_brl_data(days)

    if df is None or len(df) < 2:
        return None, {"error": "Could not retrieve exchange rate data"}

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(df['date'], df['rate'], marker='o', linestyle='-', color='#1f77b4')
    plt.title(chart_title)
    plt.xlabel('Date')
    plt.ylabel('BRL per 1 USD')
    plt.grid(True, linestyle='--', alpha=0.7)

    # Format the y-axis to show currency format
    plt.gca().yaxis.set_major_formatter(plt.matplotlib.ticker.FormatStrFormatter('R$ %.2f'))

    # Rotate date labels for better readability
    plt.xticks(rotation=45)

    # Tight layout to ensure all elements are visible
    plt.tight_layout()

    # Save the plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_bytes = buf.getvalue()
    plt.close()

    # Calculate summary statistics
    stats = {
        "current_rate": df['rate'].iloc[-1],
        "avg_rate": df['rate'].mean(),
        "min_rate": df['rate'].min(),
        "max_rate": df['rate'].max(),
        "change_pct": ((df['rate'].iloc[-1] - df['rate'].iloc[0]) / df['rate'].iloc[0]) * 100,
        "period": f"{df['date'].iloc[0].strftime('%Y-%m-%d')} to {df['date'].iloc[-1].strftime('%Y-%m-%d')}"
    }

    return img_bytes, stats

# Example of integration with a bot framework (e.g., python-telegram-bot)
async def handle_exchange_rate_command(update, context):
    """
    Handler for the /usd_brl command in a Telegram bot.
    
    Example usage with python-telegram-bot:
    from telegram import Update
    from telegram.ext import CommandHandler, CallbackContext
    
    dispatcher.add_handler(CommandHandler("usd_brl", handle_exchange_rate_command))
    """
    # Parse arguments (default to 30 days if not specified)
    days = 30
    if context.args and context.args[0].isdigit():
        days = min(int(context.args[0]), 365)  # Limit to 1 year max

    # Send a "processing" message
    message = await update.message.reply_text("Generating USD/BRL exchange rate graph...")

    # Generate the graph in a non-blocking thread
    result = await asyncio.to_thread(create_usd_brl_graph, days)
    img_bytes, stats = result if result else (None, None)

    if img_bytes is None:
        await update.message.reply_text("Sorry, I couldn't retrieve the exchange rate data. Please try again later.")
        return

    # Send the graph
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=img_bytes,
        caption=f"BRL/USD Exchange Rate for the last {days} days\n\n"
                f"Current rate: R$ {stats['current_rate']:.2f}\n"
                f"Average: R$ {stats['avg_rate']:.2f}\n"
                f"Range: R$ {stats['min_rate']:.2f} - R$ {stats['max_rate']:.2f}\n"
                f"Change: {stats['change_pct']:.2f}%\n"
                f"Period: {stats['period']}"
    )

    # Delete the "processing" message
    await message.delete()


def register_handlers_usdbrl(app) -> None:
    """
    Register the /usd_brl command handler with the Telegram application.
    """
    print("Registering /usd_brl command handler")
    app.add_handler(CommandHandler("usd_brl", handle_exchange_rate_command))
