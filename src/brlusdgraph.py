import requests
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import io
import base64
from telegram import Update
from telegram.ext import CommandHandler, Application



def get_brl_usd_data(days=30):
    """
    Fetch BRL/USD exchange rate data for the specified number of days.
    
    Args:
        days (int): Number of days of historical data to fetch
        
    Returns:
        pandas.DataFrame: DataFrame with dates and exchange rates
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Format dates for API
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    # Free API endpoint for currency exchange data
    url = f"https://api.exchangerate.host/timeseries?start_date={start_str}&end_date={end_str}&base=USD&symbols=BRL"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if not response.ok or 'rates' not in data:
            return None
            
        # Process the data
        dates = []
        rates = []
        
        for date, rate_data in data['rates'].items():
            if 'BRL' in rate_data:
                dates.append(date)
                rates.append(rate_data['BRL'])
        
        # Create DataFrame
        df = pd.DataFrame({
            'date': pd.to_datetime(dates),
            'rate': rates
        }).sort_values('date')
        
        return df
        
    except Exception as e:
        print(f"Error fetching exchange rate data: {e}")
        return None

def create_brl_usd_graph(days=30, chart_title="BRL/USD Exchange Rate"):
    """
    Create a graph of the BRL/USD exchange rate.
    
    Args:
        days (int): Number of days of historical data to show
        chart_title (str): Title for the chart
        
    Returns:
        str: Base64 encoded image that can be sent by the bot
        dict: Summary statistics of the exchange rate
    """
    df = get_brl_usd_data(days)
    
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
    
    # Encode the image as base64
    img_str = base64.b64encode(buf.read()).decode('utf-8')
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
    
    return img_str, stats

# Example of integration with a bot framework (e.g., python-telegram-bot)
def handle_exchange_rate_command(update, context):
    """
    Handler for the /brl_usd command in a Telegram bot.
    
    Example usage with python-telegram-bot:
    from telegram import Update
    from telegram.ext import CommandHandler, CallbackContext
    
    dispatcher.add_handler(CommandHandler("brl_usd", handle_exchange_rate_command))
    """
    # Parse arguments (default to 30 days if not specified)
    days = 30
    if context.args and context.args[0].isdigit():
        days = min(int(context.args[0]), 365)  # Limit to 1 year max
    
    # Send a "processing" message
    message = update.message.reply_text("Generating BRL/USD exchange rate graph...")
    
    # Generate the graph
    img_str, stats = create_brl_usd_graph(days)
    
    if img_str is None:
        update.message.reply_text("Sorry, I couldn't retrieve the exchange rate data. Please try again later.")
        return
    
    # Send the graph
    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=img_str,
        caption=f"BRL/USD Exchange Rate for the last {days} days\n\n"
               f"Current rate: R$ {stats['current_rate']:.2f}\n"
               f"Average: R$ {stats['avg_rate']:.2f}\n"
               f"Range: R$ {stats['min_rate']:.2f} - R$ {stats['max_rate']:.2f}\n"
               f"Change: {stats['change_pct']:.2f}%\n"
               f"Period: {stats['period']}"
    )
    
    # Delete the "processing" message
    message.delete()

    def register_brlusdgraph_handler(app):
      
        """
        Register the /brl_usd command and its callback query handler with the Telegram application.
        """
   
        print("Registering /brl_usd command handler")
        app.add_handler(CommandHandler("brl_usd", handle_exchange_rate_command))
    
