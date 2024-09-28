from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from helpers.classifiers import runnup
from strats import short_enter
from helpers import get_data, features, class_model
from datetime import datetime, timedelta
from helpers.load_parameters import load_symbol_information
from alpaca.data.timeframe import TimeFrameUnit

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

symbol_info = load_symbol_information('short_option_symbols.txt')

data = []
accuracies = []
years = [2024]

for year in years:
    for info in symbol_info:
        start = datetime(year, 8, 1, 12, 30)

        total_actions = 0
        correct_actions = 0

        time_window = info['time_window']
        symbol = info['symbol']
        day_diff = info['day_diff']
        look_back = info['look_back']
        look_forward = info['look_forward']

        correct_bar_amt = math.floor(look_forward / 2)

        for m in range(12):
            if start > datetime.now():
                break

            st = start - timedelta(days=day_diff-1)
            end = start - timedelta(days=1)

            # Generate model
            print(f'Model start {st} model end {end}')
            bars = class_model.get_model_bars(symbol, market_client, st, end, time_window, runnup.classification, look_back, look_forward, TimeFrameUnit.Minute)
            model, model_bars, accuracy, buys, sells = class_model.generate_model(symbol, bars)

            # From the cut off date loop every day
            start_dt = start
            end_dt = start + timedelta(days=31)
            print(f'Predict start {start_dt} model end {end_dt}')

            pred_bars = get_data.get_bars(symbol, start_dt, end_dt, market_client, time_window)
            pred_bars = features.feature_engineer_df(pred_bars, look_back)
            pred_bars = features.drop_prices(pred_bars, look_back)

            if bars.empty:
                break

            # Setup labels to see if the signal matched
            actual_labels = runnup.classification(pred_bars.copy(), look_forward)
            actual_indexes = pd.Index(actual_labels.index)

            indexes = pd.Index(pred_bars.index)

            for index, row in pred_bars.iterrows():
                pred = class_model.predict(model, pd.DataFrame([row]))

                if pred != 'Hold':
                    total_actions = total_actions + 1

                    price = row['close']
                    loc = indexes.get_loc(index)

                    if isinstance(loc, numbers.Number):
                        # Get a subset from where we are
                        next_bars = pred_bars[loc+1:].copy()

                        # Actually correct if the signal matches
                        a_bar = actual_labels.iloc[loc:loc+1]
                        if a_bar.index[0][1] != row.name[1]:
                            print("bars are wrong")

                        actual_signal = a_bar.iloc[0]['label'] == pred.lower()

                        # See where we would have exited
                        profit_exit = False
                        exit = 0
                        break_out = False
                        held_count = 0
                        for index2, next_row in next_bars.iterrows():
                            diff = features.get_percentage_diff(price, next_row['close'], False)
                            # Check if we are exiting cause we are too negative
                            break_out = (pred == 'Sell' and diff > 0.07) or (pred == 'Buy' and diff < -0.07)

                            # Check if we are exiting because we are too positive
                            break_out = (pred == 'Sell' and diff < -0.07) or (pred == 'Buy' and diff > 0.07)

                            if break_out:
                                exit = next_row['close']
                                profit_exit = (pred == 'Sell' and exit < price) or (pred == 'Buy' and exit > price)
                                break

                            held_count = held_count + 1

                        type = 'Incorrect'
                        if actual_signal or profit_exit:
                            correct_actions = correct_actions + 1
                            type = 'Correct'

                        print(f'{type} {pred} on {index[1]} enter:{price} exit:{exit} held for: {held_count} accuracy: {correct_actions/total_actions}')

                        data.append({
                            'symbol': symbol,
                            'class': pred,
                            'trade_time': index[1],
                            'trade_price': price, 
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