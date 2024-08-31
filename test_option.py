from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from helpers import options, load_stocks

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

assets = load_stocks.load_symbols('option_symbols.txt')
#assets = ['AAPL']

for symbol in assets:
    calls = options.get_option_calls(symbol, market_client, trading_client)
    puts = options.get_option_puts(symbol, market_client, trading_client)

    calls = [c for c in calls if float(c.close_price) < 4]
    puts = [c for c in puts if float(c.close_price) < 4]

    call_strikes = [c.strike_price for c in calls]
    put_strikes = [c.strike_price for c in puts]

    print(f'{symbol} Call strikes {list(set(call_strikes))}')
    print(f'{symbol} Put strikes {list(set(put_strikes))}')