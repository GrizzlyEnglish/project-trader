from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from strats import short_enter
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

assets = load_symbols('option_symbols.txt')
assets = ['spy', 'qqq']

data = []
accuracies = []
time_window = int(os.getenv('TIME_WINDOW'))
day_span = int(os.getenv('SHORT_CLASS_DAY_SPAN'))
years = [2024]
next_close_bars = int(60/time_window)

for year in years:
    for s in assets:
        start = datetime(year, 1, 1, 12, 30)

        total_actions = 0
        correct_actions = 0

        for w in range(12):
            st = start - timedelta(days=day_span-1)
            end = start - timedelta(days=1)
            print(f'Model start {st} model end {end}')
            bars = short_enter.get_model_bars(s, market_client, st, end, time_window)
            model, model_bars = short_enter.generate_model(s, bars)

            if start > datetime.now():
                break

            start_dt = start
            end_dt = start + timedelta(days=31)
            print(f'Predict start {start_dt} model end {end_dt}')
            bars = get_data.get_bars(s, start_dt, end_dt, market_client, time_window)
            bars = features.feature_engineer_df(bars)

            if bars.empty:
                break

            indexes = pd.Index(bars.index)

            for index,row in bars.iterrows():
                if index[1].month == start.month:
                    start_idx = indexes.get_loc(index)
                    bars_altered = bars[start_idx:]
                    break

            for index, row in bars_altered.iterrows():
                h = bars.loc[[index]]
                h_pred = features.drop_prices(h.copy())
                pred = short_enter.predict(model, h_pred)

                if pred != 'Hold':
                    total_actions = total_actions + 1

                    price = row['close']
                    loc = indexes.get_loc(index)

                    next_price = -1
                    next_date = ''

                    if isinstance(loc, numbers.Number):
                        next_close_bars = bars[loc+1:loc+7]

                        if next_close_bars.empty:
                            continue

                        next_closes = next_close_bars['close']

                        max_nc = max(next_closes)
                        min_nc = min(next_closes)

                        slope = features.slope(next_closes)
                        correct = False
                        dist = -1
                        rev_bar = pd.DataFrame()

                        if pred == 'Sell':
                            correct = slope < 0
                            rev_bar = next_close_bars[next_close_bars['close'] > price]
                        else:
                            correct = slope > 0
                            rev_bar = next_close_bars[next_close_bars['close'] < price]

                        if not rev_bar.empty:
                            idx = rev_bar.index[0]
                            idx_loc = indexes.get_loc(idx)
                            dist = idx_loc - loc

                        if correct:
                            correct_actions = correct_actions + 1

                        data.append({
                            'symbol': s,
                            'class': pred,
                            'trade_time': index[1],
                            'trade_price': price, 
                            'dist_to_reversal': dist,
                            'next_close_slope': slope,
                            'correct': correct
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