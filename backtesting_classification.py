from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from strats import short_enter
from helpers import get_data, features, class_model, short_classifier
from datetime import datetime, timedelta
from helpers.load_stocks import load_symbol_information

import os
import pandas as pd
import numpy as np
import numbers
import math

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

symbol_info = load_symbol_information('option_symbols.txt')

data = []
accuracies = []
years = [2024]

for year in years:
    for info in symbol_info:
        start = datetime(year, 1, 1, 12, 30)

        total_actions = 0
        correct_actions = 0

        time_window = info['time_window']
        symbol = info['symbol']
        day_diff = info['day_diff']
        look_back = info['look_back']
        look_forward = info['look_forward']

        correct_bar_amt = math.floor(look_forward / 2)

        for w in range(2):
            st = start - timedelta(days=day_diff-1)
            end = start - timedelta(days=1)
            print(f'Model start {st} model end {end}')
            bars = class_model.get_model_bars(symbol, market_client, st, end, time_window, short_classifier.classification, look_back, look_forward)
            model, model_bars, accuracy, buys, sells = class_model.generate_model(symbol, bars)

            if start > datetime.now():
                break

            start_dt = start
            end_dt = start + timedelta(days=31)
            print(f'Predict start {start_dt} model end {end_dt}')
            bars = get_data.get_bars(symbol, start_dt, end_dt, market_client, time_window)
            bars = features.feature_engineer_df(bars, look_back)

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
                h_pred = features.drop_prices(h.copy(), look_back)
                pred = class_model.predict(model, h_pred)

                if pred != 'Hold':
                    total_actions = total_actions + 1

                    price = row['close']
                    loc = indexes.get_loc(index)

                    next_price = -1
                    next_date = ''

                    if isinstance(loc, numbers.Number):
                        next_close_bars = bars[loc+1:loc+look_forward].copy()

                        if next_close_bars.empty:
                            continue

                        next_close_bars['diff'] = next_close_bars['close'] - price

                        amt = 0
                        max_diff = 0

                        if pred == 'Sell':
                            diffdf = next_close_bars[next_close_bars['diff'] < 0]['close']
                            amt = len(diffdf)
                            d = float(diffdf.min())
                            max_diff = features.get_percentage_diff(d, price, False)
                            correct = amt >= correct_bar_amt and max_diff < 3
                        else:
                            diffdf = next_close_bars[next_close_bars['diff'] < 0]['close']
                            amt = len(diffdf)
                            d = float(diffdf.min())
                            max_diff = features.get_percentage_diff(d, price, False)
                            correct = amt >= correct_bar_amt and max_diff > -3

                        type = 'Incorrect'
                        if correct:
                            correct_actions = correct_actions + 1
                            type = 'Correct'

                        print(f'{type} {pred} on {index} amount bars in right direction {amt} with max var of {max_diff} current accuracy {correct_actions/total_actions}')

                        data.append({
                            'symbol': symbol,
                            'class': pred,
                            'trade_time': index[1],
                            'trade_price': price, 
                            'amount_correct': amt,
                            'max_var': max_diff,
                            'correct': correct
                            })
                    else:
                        print('Location of index messed up')

            start = start + timedelta(days=31)
        
        acc = correct_actions / total_actions
        accuracies.append({
            'symbol': symbol,
            'accuracy': acc,
            'year': year
        })

dfa = pd.DataFrame(accuracies)
dfa.to_csv('backtest_acc.csv', index=True)

df = pd.DataFrame(data)
df.to_csv('backtest.csv', index=True)