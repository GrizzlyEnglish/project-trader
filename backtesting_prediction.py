from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from helpers.trend_logic import weight_symbol_current_status
from helpers.get_data import get_bars
from datetime import datetime, timedelta
from helpers.load_stocks import load_symbols

import os
import pandas as pd

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

indexes = [[], []] 
data = []

holding = {}

#symbols = load_symbols()
symbols = [ 'QQQ', 'CHWY', 'HIMS' ]

year = 2024

start = datetime(year, 1, 1, 12, 30)

data = []

force_counter = -1

while (start.year == 2024):
    weekday = start.weekday()
    if weekday <= 5:
        print(start)

        force_model = False

        if force_counter > 30 or force_counter == -1:
            force_model = True
            force_counter = 0

        weights = weight_symbol_current_status(symbols, market_client, start, force_model)

        for w in weights:
            symbol = w['symbol']
            predicted = w['predicted_price']
            diff = 1

            if weekday == 4:
                diff = 3

            actual_df = get_bars(symbol, start, start + timedelta(days=1), market_client)

            if not actual_df.empty:
                actual = actual_df.iloc[-1]['close']
                current = actual_df.iloc[0]['close']
                diff = actual - current
                pdiff = predicted - actual
                data.append({
                    'symbol': symbol,
                    'date': start,
                    'current_price': current,
                    'predicted_price': predicted,
                    'actual_price': actual,
                    'weight': w['weight'],
                    'cross': w['cross'],
                    'predicted_cross': w['predicted_cross'],
                    'rsi': w['rsi'],
                    'macd': w['macd'],
                    'obv': w['obv'],
                    'roc': w['roc'],
                    'res_sup': w['res_sup'],
                    'next_day_diff': diff,
                    'predicted_diff': pdiff,
                    'weight_correct': (w['weight'] ^ diff) >= 0,
                })

    start = start + timedelta(days=1)
    force_counter = force_counter + 1

    if start.date() == datetime.now().date():
        break

df = pd.DataFrame(data)
df.to_csv('backtest.csv', index=True)