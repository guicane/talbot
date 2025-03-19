import requests
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import io
import base64
from telegram import Update
from telegram.ext import CommandHandler, Application

def get_btc_usd_data(days=30):
    """
    Fetch BTC/USD exchange rate data for the specified number of days.
    
    Args:
        days (int): Number of days of historical data to fetch
        
    Returns:
        pandas.DataFrame: DataFrame with dates and exchange rates
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Format dates for API
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    
    # Use CoinGecko API for Bitcoin price data
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range?vs_currency=usd&from={start_timestamp}&to={end_timestamp}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if not response.ok or 'prices' not in data:
            return None
            
        # Process the data - CoinGecko returns [timestamp, price] pairs
        price_data = data['prices']
        
        # Create DataFrame
        df = pd.DataFrame(price_data, columns=['timestamp', 'price'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Drop duplicates and ensure chronological order
        df = df.drop_duplicates(subset='date').sort_values('date')
        
        # Select only the columns we need
        return df[['date', 'price']]
        
    except Exception as e:
        print(f"Error fetching Bitcoin price data: {e}")
        return None

def create_btc_usd_graph(days=30, chart_title="BTC/USD Exchange Rate"):
    """
    Create a graph of the BTC/USD exchange rate.
    
    Args:
        days (int): Number of days of historical data to show
        chart_title (str): Title for the chart
        
    Returns:
        str: Base64 encoded image that can be sent by the bot
        dict: Summary statistics of the exchange rate
    """
    df = get_btc_usd_data(days)
    
    if df is None or len(df) < 2:
        return None, {"error": "Could not retrieve Bitcoin price data"}
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(df['date'], df['price'], marker='', linestyle='-', color='#f7931a')  # Bitcoin orange color
    
    # Add a fill below the line for visual appeal
    plt.fill_between(df['date'], df['price'], alpha=0.2, color='#f7931a')
    
    plt.title(chart_title)
    plt.xlabel('Date')
    plt.ylabel('USD per 1 BTC')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Format the y-axis to show currency format
    plt.gca().yaxis.set_major_formatter(plt.matplotlib.ticker.FormatStrFormatter('$%,.0f'))
    
    # Rotate date labels for better readability
    plt.xticks(rotation=45)
    
    # Tight layout to ensure all elements are visible
    plt.tight_layout()
    
    # Save the plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    
    # Encode the image as base64
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    # Calculate summary statistics
    current_price = df['price'].iloc[-1]
    start_price = df['price'].iloc[0]
    
    stats = {
        "current_price": current_price,
        "avg_price": df['price'].mean(),
        "min_price": df['price'].min(),
        "max_price": df['price'].max(),
        "change_usd": current_price - start_price,
        "change_pct": ((current_price - start_price) / start_price) * 100,
        "period": f"{df['date'].iloc[0].strftime('%Y-%m-%d')} to {df['date'].iloc[-1].strftime('%Y-%m-%d')}"
    }
    
    return img_str, stats

# Example of integration with a bot framework (e.g., python-telegram-bot)
def handle_btc_price_command(update, context):
    """
    Handler for the /btc_usd command in a Telegram bot.
    
    Example usage with python-telegram-bot:
    from telegram import Update
    from telegram.ext import CommandHandler, CallbackContext
    
    dispatcher.add_handler(CommandHandler("btc_usd", handle_btc_price_command))
    """
    # Parse arguments (default to 30 days if not specified)
    days = 30
    if context.args and context.args[0].isdigit():
        days = min(int(context.args[0]), 365)  # Limit to 1 year max
    
    # Send a "processing" message
    message = update.message.reply_text("Generating BTC/USD price graph...")
    
    # Generate the graph
    img_str, stats = create_btc_usd_graph(days)
    
    if img_str is None:
        update.message.reply_text("Sorry, I couldn't retrieve the Bitcoin price data. Please try again later.")
        return
    
    # Format the change with appropriate sign and color indicator
    change_sign = "+" if stats['change_pct'] >= 0 else ""
    
    # Send the graph
    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=img_str,
        caption=f"📊 Bitcoin Price (BTC/USD) - Last {days} days\n\n"
               f"💰 Current price: ${stats['current_price']:,.2f}\n"
               f"📈 Change: {change_sign}{stats['change_pct']:.2f}% (${change_sign}{stats['change_usd']:,.2f})\n"
               f"📊 Range: ${stats['min_price']:,.2f} - ${stats['max_price']:,.2f}\n"
               f"⏱️ Period: {stats['period']}"
    )
    
    # Delete the "processing" message
    message.delete()

    def register_btcusdgraph_handler(app):
      
        """
        Register the /btc_usd command and its callback query handler with the Telegram application.
        """
   
        print("Registering /brl_usd command handler")
        app.add_handler(CommandHandler("btc_usd", handle_btc_price_command))
