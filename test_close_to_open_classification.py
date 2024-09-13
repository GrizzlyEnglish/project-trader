from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data import TimeFrame, TimeFrameUnit
from dotenv import load_dotenv
from datetime import datetime, timedelta
from helpers import get_data, features, class_model, load_stocks

import os
import pandas as pd

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

#assets = load_stocks.load_symbols('option_symbols.txt')
assets = ['SPY', 'QQQ']
#assets = ['SPY']

start = datetime(2024, 9, 6, 11, 30)
s = start - timedelta(days=465)
e = start + timedelta(days=1)
time_window = 1


def label_to_int(row):
    if row == 'up': return 0
    elif row == 'down': return 1
    elif row == 'unknown': return 2

for symbol in assets:
    bars = get_data.get_bars(symbol, s, e, market_client, time_window, TimeFrameUnit.Hour)
    bars = features.feature_engineer_df(bars)


    up = len(bars[bars['label'] == 'up'])
    down = len(bars[bars['label'] == 'down'])
    unkown = len(bars[bars['label'] == 'unknown'])

    print(f'Up {up} Down {down} Unknown {unkown}')

    bars['label'] = bars['label'].apply(label_to_int)

    bars.pop('daydiff_open')

    model = class_model.create_model(symbol, bars, True)