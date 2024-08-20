from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from strats import classification
from helpers.load_stocks import load_symbols

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

#assets = load_symbols('option_symbols.txt')
assets = ['SPY', 'QQQ']

start = datetime(2024, 8, 1, 12, 30)
s = start - timedelta(days=60)
e = start + timedelta(days=1)
time_window = 15

for symbol in assets:
    bars = classification.get_model_bars(symbol, market_client, s, e, time_window)
    model = classification.generate_model(symbol, bars)
    print()