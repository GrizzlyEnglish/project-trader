from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.timeframe import TimeFrameUnit
from dotenv import load_dotenv
from datetime import datetime, timedelta
from strats import short_enter
from helpers import features, load_stocks, class_model, short_classifier

import os
import pandas as pd

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

assets = load_stocks.load_symbols('option_symbols.txt')
assets = ['SPY']
save = False

day_span = int(os.getenv('SHORT_CLASS_DAY_SPAN'))
time_window = int(os.getenv('TIME_WINDOW'))

windows = [1, 5, 15, 30]
daydiffs = [7, 14, 30, 60, 90, 120]

results = []

for window in windows:
    for daydiff in daydiffs:
        if window == 1 and daydiff > 30:
            continue
        success = 0
        failures = 0
        for symbol in assets:
            start = datetime(2024, 8, 29, 12, 30)
            s = start - timedelta(days=daydiff)
            e = start + timedelta(days=1)

            bars = class_model.get_model_bars(symbol, market_client, s, e, window, short_classifier.classification, TimeFrameUnit.Minute)
            model, model_bars, accuracy = class_model.generate_model(symbol, bars)

            results.append([window, daydiff, accuracy])

df = pd.DataFrame(columns=['time_window', 'day diff', 'accuracy'], data=results)

print(df)