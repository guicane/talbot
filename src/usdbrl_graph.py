""""
Dynamic Currency Exchange Rate Graph Generator
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


def get_currency_history(from_currency, to_currency, days=30):
    """
    Fetch historical exchange rate data for the specified currency pair and timeframe.

    Tries querying from_currency-to_currency first. If that fails, queries the reverse
    pair to_currency-from_currency and inverts the rates.

    Args:
        from_currency (str): Source currency code (e.g., "USD")
        to_currency (str): Target currency code (e.g., "BRL")
        days (int): Number of days of historical data to fetch

    Returns:
        pandas.DataFrame: DataFrame with dates and exchange rates, or None
    """
    from_curr = from_currency.upper()
    to_curr = to_currency.upper()

    pair = f"{from_curr}-{to_curr}"
    url = f"https://economia.awesomeapi.com.br/json/daily/{pair}/{days}"
    invert = False

    try:
        response = requests.get(url, timeout=10)

        # If not successful or not a list, try the reverse pair
        if not response.ok or not isinstance(response.json(), list):
            pair = f"{to_curr}-{from_curr}"
            url = f"https://economia.awesomeapi.com.br/json/daily/{pair}/{days}"
            response = requests.get(url, timeout=10)

            if not response.ok or not isinstance(response.json(), list):
                print(f"[ERROR] AwesomeAPI does not support forward or reverse pair for {from_curr}/{to_curr}")
                return None
            invert = True

        dates = []
        rates = []

        for item in response.json():
            dates.append(datetime.fromtimestamp(int(item.get("timestamp"))).strftime("%Y-%m-%d"))
            rates.append(1.0 / float(item.get("bid")) if invert else float(item.get("bid")))

        return pd.DataFrame({
            'date': pd.to_datetime(dates),
            'rate': rates
        }).sort_values('date')

    except (requests.RequestException, pd.errors.EmptyDataError, ValueError, KeyError) as e:
        print(f"[ERROR] Failed to fetch historical data for {from_curr}/{to_curr}: {e}")
        return None


def create_currency_graph(from_currency, to_currency, days=30):
    """
    Create a graph of the from_currency/to_currency exchange rate.

    Args:
        from_currency (str): Source currency code
        to_currency (str): Target currency code
        days (int): Number of days of historical data to show

    Returns:
        bytes: Raw image bytes that can be sent by the bot
        dict: Summary statistics of the exchange rate
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    df = get_currency_history(from_currency, to_currency, days)

    if df is None or len(df) < 2:
        return None, {"error": f"Could not retrieve exchange rate data for {from_currency}/{to_currency}"}

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(df['date'], df['rate'], marker='o', linestyle='-', color='#1f77b4')

    # Dynamic title and labels
    chart_title = f"{from_currency}/{to_currency} Exchange Rate"
    plt.title(chart_title)
    plt.xlabel('Date')
    plt.ylabel(f'{to_currency} per 1 {from_currency}')
    plt.grid(True, linestyle='--', alpha=0.7)

    # Format y-axis dynamically based on currency
    symbols = {
        "BRL": "R$ ",
        "USD": "$ ",
        "EUR": "€ ",
        "GBP": "£ ",
        "JPY": "¥ "
    }
    symbol = symbols.get(to_currency, "")

    last_rate = df['rate'].iloc[-1]
    if last_rate < 0.1:
        fmt = f'{symbol}%.4f'
    elif last_rate < 1.0:
        fmt = f'{symbol}%.3f'
    else:
        fmt = f'{symbol}%.2f'

    plt.gca().yaxis.set_major_formatter(plt.matplotlib.ticker.FormatStrFormatter(fmt))

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


async def handle_currency_graph_command(update, context):
    """
    Handler for the /currency_graph command in a Telegram bot.
    """
    print(f"Received /currency_graph command from user {update.message.from_user.id}")
    # Check if arguments are provided
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Incorrect format. Use: /currency_graph <from_currency> <to_currency> [days]\n"
            "Example: /currency_graph USD BRL\n"
            "Example: /currency_graph GBP EUR 30"
        )
        return

    from_curr = context.args[0].upper()
    to_curr = context.args[1].upper()

    # Default days to 30
    days = 30
    if len(context.args) >= 3 and context.args[2].isdigit():
        days = min(int(context.args[2]), 365)  # Limit to 1 year max

    # Send a "processing" message
    message = await update.message.reply_text(f"Generating {from_curr}/{to_curr} exchange rate graph...")

    # Generate the graph in a non-blocking thread
    result = await asyncio.to_thread(create_currency_graph, from_curr, to_curr, days)
    img_bytes, stats = result if result else (None, None)

    if img_bytes is None:
        await update.message.reply_text(
            f"Sorry, I couldn't retrieve the exchange rate data for {from_curr}/{to_curr}. "
            "Please check that both currencies are valid and supported."
        )
        try:
            await message.delete()
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        return

    # Format symbol for message caption
    symbols = {
        "BRL": "R$",
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥"
    }
    sym = symbols.get(to_curr, to_curr)

    # Adjust decimal places for display
    last_rate = stats['current_rate']
    decimals = 4 if last_rate < 0.1 else (3 if last_rate < 1.0 else 2)

    # Send the graph
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=img_bytes,
        caption=f"📊 {from_curr}/{to_curr} Exchange Rate - Last {days} days\n\n"
                f"📈 Current rate: {sym} {stats['current_rate']:.{decimals}f}\n"
                f"📊 Average: {sym} {stats['avg_rate']:.{decimals}f}\n"
                f"📉 Range: {sym} {stats['min_rate']:.{decimals}f} - {sym} {stats['max_rate']:.{decimals}f}\n"
                f"🔄 Change: {stats['change_pct']:.2f}%\n"
                f"⏱️ Period: {stats['period']}"
    )

    # Delete the "processing" message
    try:
        await message.delete()
    except Exception:  # pylint: disable=broad-exception-caught
        pass


def register_handlers_usdbrl(app) -> None:
    """
    Register the /currency_graph command handler with the Telegram application.
    """
    print("Registering /currency_graph command handler")
    app.add_handler(CommandHandler("currency_graph", handle_currency_graph_command))
