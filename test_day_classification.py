from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from helpers import get_data, features, class_model

import os
import pandas as pd

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

#assets = load_symbols('option_symbols.txt')
#assets = ['SPY', 'QQQ', 'NVDA']
assets = ['SPY']

start = datetime(2024, 8, 29, 11, 30)
s = start - timedelta(days=120)
e = start + timedelta(days=1)
time_window = 30

for symbol in assets:
    bars = get_data.get_bars(symbol, s, e, market_client, time_window)
    bars = features.feature_engineer_df(bars)

    indexes = pd.Index(bars.index)

    def day_label(row):
        try:
            symbol = row.name[0]
            idx = row.name[1]
            eidx = idx.replace(hour=19, minute=30)
            last_day_bar = bars.loc[(symbol,eidx)]
            sidx = idx.replace(hour=13, minute=30)
            start_day_bar = bars.loc[(symbol,sidx)]
            p_diff = features.get_percentage_diff(last_day_bar['close'], start_day_bar['open'], False)
            if (p_diff >= 0.7):
                return 'up'
            elif(p_diff <= -0.2):
                return 'down'
            else:
                return 'unknown'
        except KeyError as e:
            return 'unknown'

    bars['label'] = bars.apply(day_label, axis=1)

    def get_hour(row):
        idx = row.name[1]
        return idx.hour

    bars['hour'] = bars.apply(get_hour, axis=1)

    bars = bars[bars['hour'] == 19]
    bars.pop('hour')

    up = len(bars[bars['label'] == 'up'])
    down = len(bars[bars['label'] == 'down'])
    unkown = len(bars[bars['label'] == 'unknown'])

    print(f'Up {up} Down {down} Unknown {unkown}')

    def label_to_int(row):
        if row == 'up': return 0
        elif row == 'down': return 1
        elif row == 'unknown': return 2

    bars['label'] = bars['label'].apply(label_to_int)

    model = class_model.create_model(symbol, bars, True)

    print(bars)