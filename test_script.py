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
assets = ['SPY', 'QQQ', 'NVDA']

start = datetime(2024, 8, 26, 12, 30)
s = start - timedelta(days=80)
e = start + timedelta(days=1)
time_window = 5

for symbol in assets:
    bars = classification.get_model_bars(symbol, market_client, s, e, time_window)

    b_bars = bars[bars['label'] == 'buy']
    b_bars.to_csv(f'{symbol}_buy_signals.csv', index=True)

    s_bars = bars[bars['label'] == 'sell']
    s_bars.to_csv(f'{symbol}_sell_signals.csv', index=True)

    model = classification.generate_model(symbol, bars)
    print()