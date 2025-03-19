import requests
from datetime import datetime
import json
import os
from telegram import Update
from telegram.ext import CommandHandler, Application


class CurrencyConverter:
    def __init__(self, cache_duration=3600):
        """
        Initialize the currency converter.
        
        Args:
            cache_duration (int): How long to cache rates in seconds (default: 1 hour)
        """
        self.base_url = "https://api.exchangerate.host/latest"
        self.cache_path = "currency_rates_cache.json"
        self.cache_duration = cache_duration
        self.rates = {}
        self.last_update = None
        self.base_currency = "USD"
        
        # Load cache if it exists
        self._load_cache()
        
    def _load_cache(self):
        """Load cached exchange rates if they exist and aren't expired."""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r') as file:
                    cache = json.load(file)
                    self.rates = cache.get('rates', {})
                    self.last_update = datetime.fromisoformat(cache.get('timestamp', '2000-01-01T00:00:00'))
                    self.base_currency = cache.get('base', 'USD')
                    
                    # Check if cache is valid
                    time_diff = (datetime.now() - self.last_update).total_seconds()
                    if time_diff > self.cache_duration:
                        self._update_rates()
            except Exception as e:
                print(f"Error loading cache: {e}")
                self._update_rates()
        else:
            self._update_rates()
            
    def _save_cache(self):
        """Save current rates to cache."""
        cache = {
            'rates': self.rates,
            'timestamp': datetime.now().isoformat(),
            'base': self.base_currency
        }
        
        try:
            with open(self.cache_path, 'w') as file:
                json.dump(cache, file)
        except Exception as e:
            print(f"Error saving cache: {e}")
            
    def _update_rates(self):
        """Fetch the latest exchange rates from the API."""
        try:
            response = requests.get(self.base_url)
            data = response.json()
            
            if response.status_code == 200 and 'rates' in data:
                self.rates = data['rates']
                self.base_currency = data['base']
                self.last_update = datetime.now()
                self._save_cache()
                return True
            else:
                print(f"API Error: {data.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"Error updating rates: {e}")
            return False
            
    def get_rate(self, from_currency, to_currency):
        """
        Get the exchange rate between two currencies.
        
        Args:
            from_currency (str): The source currency code (e.g., "USD")
            to_currency (str): The target currency code (e.g., "EUR")
            
        Returns:
            float: Exchange rate or None if unable to get rate
        """
        # Check if we need to update the cache
        if not self.last_update or (datetime.now() - self.last_update).total_seconds() > self.cache_duration:
            self._update_rates()
            
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # If currencies are the same, rate is 1
        if from_currency == to_currency:
            return 1.0
            
        # Check if we have both currencies in our rates
        if from_currency not in self.rates or to_currency not in self.rates:
            # Try one more time with a fresh update
            if self._update_rates():
                if from_currency not in self.rates or to_currency not in self.rates:
                    return None
            else:
                return None
                
        # Calculate the exchange rate
        # If base is EUR and we want USD to JPY:
        # USD to EUR rate = 1 / rate[USD]
        # EUR to JPY rate = rate[JPY]
        # USD to JPY = (1 / rate[USD]) * rate[JPY]
        
        # Convert from source currency to base currency
        if from_currency == self.base_currency:
            from_rate = 1.0
        else:
            from_rate = 1.0 / self.rates[from_currency]
            
        # Convert from base currency to target currency
        if to_currency == self.base_currency:
            to_rate = 1.0
        else:
            to_rate = self.rates[to_currency]
            
        return from_rate * to_rate
    
    def convert(self, amount, from_currency, to_currency):
        """
        Convert an amount from one currency to another.
        
        Args:
            amount (float): The amount to convert
            from_currency (str): The source currency code
            to_currency (str): The target currency code
            
        Returns:
            dict: Conversion result or error information
        """
        rate = self.get_rate(from_currency, to_currency)
        
        if rate is None:
            return {
                "success": False,
                "error": f"Could not get exchange rate for {from_currency} to {to_currency}"
            }
            
        converted_amount = amount * rate
        
        return {
            "success": True,
            "from": {
                "currency": from_currency.upper(),
                "amount": amount
            },
            "to": {
                "currency": to_currency.upper(),
                "amount": converted_amount
            },
            "rate": rate,
            "timestamp": datetime.now().isoformat()
        }
        
    def get_available_currencies(self):
        """Get list of available currency codes."""
        # Make sure we have updated rates
        if not self.rates:
            self._update_rates()
            
        return sorted(list(self.rates.keys()))
        
    def get_popular_currencies(self):
        """Return a list of popular currency codes."""
        return [
            "USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF",
            "CNY", "HKD", "NZD", "MXN", "SGD", "INR", "BRL", 
            "RUB", "ZAR", "TRY", "BTC", "ETH"
        ]

# Example of integration with a Telegram bot
def handle_convert_command(update, context):
    """
    Handler for the /convert command in a Telegram bot.
    
    Usage: /convert <amount> <from_currency> <to_currency>
    Example: /convert 100 USD EUR
    """
    # Check if we have the right number of arguments
    if len(context.args) != 3:
        update.message.reply_text(
            "⚠️ Incorrect format. Use: /convert <amount> <from_currency> <to_currency>\n"
            "Example: /convert 100 USD EUR"
        )
        return
        
    try:
        amount = float(context.args[0])
        from_currency = context.args[1].upper()
        to_currency = context.args[2].upper()
        
        # Initialize converter
        converter = CurrencyConverter()
        
        # Perform conversion
        result = converter.convert(amount, from_currency, to_currency)
        
        if result["success"]:
            # Format numbers based on common currency display practices
            if to_currency in ["BTC", "ETH", "XRP"]:
                # Cryptocurrencies often need more decimal places
                amount_str = f"{result['to']['amount']:.8f}"
            else:
                # Regular currencies typically use 2 decimal places
                amount_str = f"{result['to']['amount']:.2f}"
                
            update.message.reply_text(
                f"💱 Currency Conversion Result:\n\n"
                f"{result['from']['amount']} {result['from']['currency']} = "
                f"{amount_str} {result['to']['currency']}\n\n"
                f"Rate: 1 {result['from']['currency']} = {result['rate']:.6f} {result['to']['currency']}\n"
                f"Updated: {datetime.fromisoformat(result['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            update.message.reply_text(
                f"❌ Conversion error: {result['error']}\n\n"
                f"Please check that both currencies are valid."
            )
            
    except ValueError:
        update.message.reply_text("❌ Invalid amount. Please provide a valid number.")
    except Exception as e:
        update.message.reply_text(f"❌ An error occurred: {str(e)}")

def handle_currencies_command(update, context):
    """Handler for a command that shows available currencies."""
    converter = CurrencyConverter()
    popular = converter.get_popular_currencies()
    
    update.message.reply_text(
        f"💲 Popular Currencies:\n{', '.join(popular)}\n\n"
        f"Use /convert <amount> <from_currency> <to_currency> to convert between currencies.\n"
        f"Example: /convert 100 USD EUR"
    )

def register_converter_handler(app):
      
        """
        Register the /convert command and its callback query handler with the Telegram application.
        """
   
        print("Registering /convert command handler")
        app.add_handler(CommandHandler("convert", handle_convert_command))
        

def register_currency_handler(app):
      
        """
        Register the /currencies command and its callback query handler with the Telegram application.
        """
   
        print("Registering /currencies command handler")
        app.add_handler(CommandHandler("currencies", handle_currencies_command))