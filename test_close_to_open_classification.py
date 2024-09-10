from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
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
s = start - timedelta(days=365)
e = start + timedelta(days=1)
time_window = 30

def day_label(row):
    open_diff = row['daydiff_open']
    if open_diff < down_diff:
        return 'down'
    elif open_diff > up_diff:
        return 'up'
    else:
        return 'unknown'

def get_time(row):
    idx = row.name[1]
    return f'{idx.hour}:{idx.minute}'

def label_to_int(row):
    if row == 'up': return 0
    elif row == 'down': return 1
    elif row == 'unknown': return 2

for symbol in assets:
    bars = get_data.get_bars(symbol, s, e, market_client, time_window)
    bars = features.feature_engineer_df(bars)

    indexes = pd.Index(bars.index)

    bars['time'] = bars.apply(get_time, axis=1)
    bars = bars[bars['time'] != '13:0']

    bars['next_open'] = bars['open'].shift(-1)
    bars['next_close'] = bars['close'].shift(-1)
    bars['daydiff_open'] = bars['next_open'] - bars['close']

    for i in range(10):
        bars[f'prev_ah_{i}'] = bars['daydiff_open'].shift(i)

    bars = bars[bars['time'] == '20:0']
    bars.pop('time')

    up_diff = bars[bars['daydiff_open'] > 0]['daydiff_open'].mean()
    down_diff = bars[bars['daydiff_open'] < 0]['daydiff_open'].mean()

    print(f'up diff {up_diff} down diff {down_diff}')
        
    bars['label'] = bars.apply(day_label, axis=1)

    up = len(bars[bars['label'] == 'up'])
    down = len(bars[bars['label'] == 'down'])
    unkown = len(bars[bars['label'] == 'unknown'])

    print(f'Up {up} Down {down} Unknown {unkown}')

    bars['label'] = bars['label'].apply(label_to_int)

    bars.pop('daydiff_open')

    model = class_model.create_model(symbol, bars, True)