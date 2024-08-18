from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from strats import classification
from helpers import get_data, features
from datetime import datetime, timedelta
from helpers.load_stocks import load_symbols

import os
import pandas as pd
import numpy as np
import numbers

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

#assets = load_symbols('option_symbols.txt')
assets = ['qqq']

data = []
accuracies = []
time_window = 15
years = [2024]

for year in years:
    for s in assets:
        start = datetime(year, 8, 1, 12, 30)
        model = classification.generate_model(s, market_client, start - timedelta(days=60), start - timedelta(days=1), time_window)

        for w in range(12):
            print(start)

            if start > datetime.now():
                break

            start_dt = start - timedelta(days=60)
            end_dt = start + timedelta(days=31)
            bars = get_data.get_bars(s, start_dt, end_dt, market_client, time_window)
            bars = features.feature_engineer_df(bars)

            if bars.empty:
                break

            indexes = pd.Index(bars.index)

            total_actions = 0
            correct_actions = 0

            for index,row in bars.iterrows():
                if index[1].month == start.month:
                    start_idx = indexes.get_loc(index)
                    bars_altered = bars[start_idx:]
                    break

            for index, row in bars_altered.iterrows():
                h = bars.loc[[index]]
                h_pred = features.drop_prices(h.copy())
                pred = classification.predict(model, h_pred)

                if pred != 'Hold':
                    total_actions = total_actions + 1

                    price = row['close']
                    loc = indexes.get_loc(index)

                    next_price = -1
                    next_date = ''

                    if isinstance(loc, numbers.Number):
                        b = bars[loc:]
                        r = pd.DataFrame()
                        td = 'unknown'
                        if pred == 'Sell':
                            r = b[b['close'] > row['close']]
                        else:
                            r = b[b['close'] < row['close']]
                        if not r.empty:
                            idx = r.index[0][1]
                            td = idx - index[1]

                        if td != 'unknown' and td._m >= 30:
                            correct_actions = correct_actions + 1

                        data.append({
                            'symbol': s,
                            'class': pred,
                            'date': index[1],
                            'current_price': price, 
                            'time_to_diff': td
                            })
                    else:
                        print('Location of index messed up')

            start = start + timedelta(days=31)
        
        acc = correct_actions / total_actions
        accuracies.append({
            'symbol': s,
            'accuracy': acc,
            'year': year
        })

dfa = pd.DataFrame(accuracies)
dfa.to_csv('backtest_acc.csv', index=True)

df = pd.DataFrame(data)
df.to_csv('backtest.csv', index=True)